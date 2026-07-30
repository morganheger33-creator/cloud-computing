import sys
import time
import psutil
import GPUtil

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QProgressBar, QSystemTrayIcon, QMenu, QAction, QSpinBox, 
    QFormLayout, QGroupBox, QTabWidget, QMessageBox
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon, QFont, QColor

# Matplotlib integration for real-time live graphs
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class DynamicGraphCanvas(FigureCanvas):
    """A canvas that renders live line graphs for hardware metrics."""
    def __init__(self, title, max_points=30, parent=None):
        fig = Figure(figsize=(5, 2), dpi=80)
        fig.patch.set_facecolor('#1e1e2e')  # Dark theme background
        
        self.ax = fig.add_subplot(111)
        self.ax.set_facecolor('#181825')
        self.ax.set_title(title, color='#cdd6f4', fontsize=10, fontweight='bold')
        self.ax.tick_params(colors='#a6adc8', labelsize=8)
        self.ax.grid(True, color='#313244', linestyle='--', linewidth=0.5)
        
        self.max_points = max_points
        self.data = [0] * max_points
        self.line, = self.ax.plot(self.data, color='#89b4fa', linewidth=2)
        self.ax.set_ylim(0, 100)

        super().__init__(fig)

    def update_data(self, new_value):
        self.data.append(new_value)
        self.data.pop(0)
        self.line.set_ydata(self.data)
        self.draw()


class SystemMonitorApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Sleek System Monitor")
        self.resize(500, 650)
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e2e; }
            QLabel { color: #cdd6f4; font-size: 13px; }
            QGroupBox { color: #89b4fa; font-weight: bold; border: 1px solid #313244; border-radius: 6px; margin-top: 10px; padding-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }
            QProgressBar { border: 1px solid #313244; border-radius: 5px; text-align: center; color: white; background: #181825; }
            QProgressBar::chunk { background-color: #a6e3a1; border-radius: 4px; }
            QTabWidget::pane { border: 1px solid #313244; }
            QTabBar::tab { background: #181825; color: #a6adc8; padding: 8px 16px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #313244; color: #89b4fa; font-weight: bold; }
        """)

        # Threshold Defaults
        self.ram_threshold = 85  # %
        self.cpu_threshold = 90  # %
        self.alert_cooldown = 0

        # Network speed trackers
        self.last_net_io = psutil.net_io_counters()
        self.last_time = time.time()

        self.init_ui()
        self.init_tray()

        # Update Timer (Runs every 1 second)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_metrics)
        self.timer.start(1000)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Tab 1: Live Metrics & Dashboard
        dash_tab = QWidget()
        dash_layout = QVBoxLayout(dash_tab)

        # CPU & RAM Quick Bars
        bars_group = QGroupBox("Hardware Utilization")
        bars_layout = QFormLayout()

        self.cpu_bar = QProgressBar()
        self.ram_bar = QProgressBar()
        self.disk_bar = QProgressBar()

        bars_layout.addRow("CPU Usage:", self.cpu_bar)
        bars_layout.addRow("RAM Usage:", self.ram_bar)
        bars_layout.addRow("Disk Usage:", self.disk_bar)
        bars_group.setLayout(bars_layout)
        dash_layout.addWidget(bars_group)

        # Real-time Network Tracker
        net_group = QGroupBox("Network Speed Tracker")
        net_layout = QHBoxLayout()
        self.download_label = QLabel("⬇ Download: 0.0 KB/s")
        self.upload_label = QLabel("⬆ Upload: 0.0 KB/s")
        net_layout.addWidget(self.download_label)
        net_layout.addWidget(self.upload_label)
        net_group.setLayout(net_layout)
        dash_layout.addWidget(net_group)

        # GPU Metrics
        gpu_group = QGroupBox("GPU Status")
        gpu_layout = QVBoxLayout()
        self.gpu_label = QLabel("GPU: Detecting...")
        gpu_layout.addWidget(self.gpu_label)
        gpu_group.setLayout(gpu_layout)
        dash_layout.addWidget(gpu_group)

        # Live Graphs
        self.cpu_graph = DynamicGraphCanvas("CPU Usage History (%)")
        dash_layout.addWidget(self.cpu_graph)

        self.tabs.addTab(dash_tab, "Dashboard")

        # Tab 2: Settings & Alerts
        settings_tab = QWidget()
        settings_layout = QFormLayout(settings_tab)

        self.ram_spin = QSpinBox()
        self.ram_spin.setRange(50, 99)
        self.ram_spin.setValue(self.ram_threshold)
        self.ram_spin.valueChanged.connect(self.set_ram_threshold)

        self.cpu_spin = QSpinBox()
        self.cpu_spin.setRange(50, 99)
        self.cpu_spin.setValue(self.cpu_threshold)
        self.cpu_spin.valueChanged.connect(self.set_cpu_threshold)

        settings_layout.addRow("RAM Safety Threshold (%):", self.ram_spin)
        settings_layout.addRow("CPU Safety Threshold (%):", self.cpu_spin)

        self.tabs.addTab(settings_tab, "Alert Settings")

    def init_tray(self):
        """Builds system tray integration."""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(self.style().SP_ComputerIcon))

        tray_menu = QMenu()
        show_action = QAction("Open Dashboard", self)
        show_action.triggered.connect(self.show)
        
        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(QApplication.instance().quit)

        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        # Hide window on close button click instead of quitting
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()

    def closeEvent(self, event):
        """Minimize to tray when clicking the 'X' button."""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "System Monitor",
            "App is still running in the system tray.",
            QSystemTrayIcon.Information,
            2000
        )

    def set_ram_threshold(self, val):
        self.ram_threshold = val

    def set_cpu_threshold(self, val):
        self.cpu_threshold = val

    def update_metrics(self):
        # 1. Update CPU, RAM, Disk
        cpu_p = psutil.cpu_percent()
        ram_p = psutil.virtual_memory().percent
        disk_p = psutil.disk_usage('/').percent

        self.cpu_bar.setValue(int(cpu_p))
        self.ram_bar.setValue(int(ram_p))
        self.disk_bar.setValue(int(disk_p))

        self.cpu_graph.update_data(cpu_p)

        # 2. Update Network Speeds
        current_net_io = psutil.net_io_counters()
        current_time = time.time()
        elapsed = current_time - self.last_time

        bytes_sent = current_net_io.bytes_sent - self.last_net_io.bytes_sent
        bytes_recv = current_net_io.bytes_recv - self.last_net_io.bytes_recv

        upload_speed = (bytes_sent / elapsed) / 1024  # KB/s
        download_speed = (bytes_recv / elapsed) / 1024  # KB/s

        self.upload_label.setText(f"⬆ Upload: {upload_speed:.1f} KB/s")
        self.download_label.setText(f"⬇ Download: {download_speed:.1f} KB/s")

        self.last_net_io = current_net_io
        self.last_time = current_time

        # 3. Update GPU Details
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                self.gpu_label.setText(
                    f"Model: {gpu.name}\n"
                    f"Usage: {gpu.load * 100:.1f}% | Temp: {gpu.temperature}°C | VRAM: {gpu.memoryUsed}MB / {gpu.memoryTotal}MB"
                )
            else:
                self.gpu_label.setText("No dedicated GPU detected.")
        except Exception:
            self.gpu_label.setText("GPU tracking unavailable.")

        # 4. Trigger Alerts
        self.check_alerts(cpu_p, ram_p)

    def check_alerts(self, cpu_p, ram_p):
        if self.alert_cooldown > 0:
            self.alert_cooldown -= 1
            return

        alerts = []
        if cpu_p >= self.cpu_threshold:
            alerts.append(f"High CPU Usage ({cpu_p}%)")
        if ram_p >= self.ram_threshold:
            alerts.append(f"High RAM Usage ({ram_p}%)")

        if alerts:
            message = " & ".join(alerts) + f" exceeded safety limits!"
            self.tray_icon.showMessage(
                "⚠️ Hardware Warning!",
                message,
                QSystemTrayIcon.Warning,
                5000
            )
            self.alert_cooldown = 15  # Cooldown for 15 seconds to prevent spam


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running in system tray when closed

    window = SystemMonitorApp()
    window.show()

    sys.exit(app.exec_())