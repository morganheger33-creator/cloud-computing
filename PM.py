import base64
import json
import os
import tkinter as tk
from tkinter import messagebox, ttk

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

VAULT_FILE = "vault.enc"
SALT_FILE = "salt.bin"


class PasswordManagerApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Secure Password Manager")
        self.root.geometry("600x450")

        self.fernet = None
        self.vault_data = {}

        # Show Login / Setup Screen first
        self.setup_login_screen()

    # --- Encryption Helper Methods ---
    def get_or_create_salt(self):
        """Get existing salt or generate a new one for key derivation."""
        if os.path.exists(SALT_FILE):
            with open(SALT_FILE, "rb") as f:
                return f.read()
        else:
            salt = os.urandom(16)
            with open(SALT_FILE, "wb") as f:
                f.write(salt)
            return salt

    def derive_key(self, master_password: str) -> bytes:
        """Derive a Fernet key from the master password and salt using PBKDF2."""
        salt = self.get_or_create_salt()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480_000,
        )
        return base64.urlsafe_b64encode(kdf.derive(master_password.encode()))

    def load_vault(self):
        """Decrypt and load vault data from local file."""
        if not os.path.exists(VAULT_FILE):
            return {}

        with open(VAULT_FILE, "rb") as f:
            encrypted_data = f.read()

        decrypted_bytes = self.fernet.decrypt(encrypted_data)
        return json.loads(decrypted_bytes.decode("utf-8"))

    def save_vault(self):
        """Encrypt and save vault data to local file."""
        json_data = json.dumps(self.vault_data).encode("utf-8")
        encrypted_data = self.fernet.encrypt(json_data)
        with open(VAULT_FILE, "wb") as f:
            f.write(encrypted_data)

    # --- GUI Screens ---
    def setup_login_screen(self):
        self.clear_screen()

        frame = ttk.Frame(self.root, padding=30)
        frame.pack(expand=True)

        is_new_user = not os.path.exists(VAULT_FILE)
        title_text = (
            "Create Master Password" if is_new_user else "Enter Master Password"
        )

        ttk.Label(
            frame, text=title_text, font=("Arial", 16, "bold")
        ).grid(row=0, column=0, columnspan=2, pady=10)

        ttk.Label(frame, text="Master Password:").grid(
            row=1, column=0, sticky="e", padx=5, pady=5
        )
        self.master_pwd_entry = ttk.Entry(frame, show="*")
        self.master_pwd_entry.grid(row=1, column=1, padx=5, pady=5)
        self.master_pwd_entry.focus()

        login_btn = ttk.Button(
            frame,
            text="Unlock Vault",
            command=lambda: self.unlock_vault(is_new_user),
        )
        login_btn.grid(row=2, column=0, columnspan=2, pady=15)

        self.root.bind("<Return>", lambda event: self.unlock_vault(is_new_user))

    def unlock_vault(self, is_new_user):
        master_password = self.master_pwd_entry.get()
        if not master_password:
            messagebox.showwarning(
                "Warning", "Master password cannot be empty!"
            )
            return

        key = self.derive_key(master_password)
        self.fernet = Fernet(key)

        if is_new_user:
            self.vault_data = {}
            self.save_vault()
            self.build_main_screen()
        else:
            try:
                self.vault_data = self.load_vault()
                self.build_main_screen()
            except InvalidToken:
                messagebox.showerror(
                    "Error", "Incorrect Master Password! Access Denied."
                )

    def build_main_screen(self):
        self.clear_screen()
        self.root.unbind("<Return>")

        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)

        # Left Frame: Form to Add/Edit Credential
        form_frame = ttk.LabelFrame(
            main_frame, text=" Add / Update Credential ", padding=10
        )
        form_frame.pack(side="left", fill="y", padx=10, pady=10)

        ttk.Label(form_frame, text="Website/Service:").grid(
            row=0, column=0, sticky="w", pady=2
        )
        self.site_entry = ttk.Entry(form_frame, width=22)
        self.site_entry.grid(row=1, column=0, pady=5)

        ttk.Label(form_frame, text="Username/Email:").grid(
            row=2, column=0, sticky="w", pady=2
        )
        self.user_entry = ttk.Entry(form_frame, width=22)
        self.user_entry.grid(row=3, column=0, pady=5)

        ttk.Label(form_frame, text="Password:").grid(
            row=4, column=0, sticky="w", pady=2
        )
        self.pwd_entry = ttk.Entry(form_frame, width=22, show="*")
        self.pwd_entry.grid(row=5, column=0, pady=5)

        save_btn = ttk.Button(
            form_frame, text="Save Entry", command=self.add_entry
        )
        save_btn.grid(row=6, column=0, pady=10)

        # Right Frame: Vault List
        list_frame = ttk.LabelFrame(
            main_frame, text=" Saved Credentials ", padding=10
        )
        list_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Treeview Table
        columns = ("Site", "Username", "Password")
        self.tree = ttk.Treeview(
            list_frame, columns=columns, show="headings", selectmode="browse"
        )
        self.tree.heading("Site", text="Website")
        self.tree.heading("Username", text="Username")
        self.tree.heading("Password", text="Password")

        self.tree.column("Site", width=120)
        self.tree.column("Username", width=120)
        self.tree.column("Password", width=100)

        self.tree.pack(fill="both", expand=True)

        # Bottom Buttons
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(fill="x", pady=5)

        del_btn = ttk.Button(
            btn_frame, text="Delete Selected", command=self.delete_entry
        )
        del_btn.pack(side="right", padx=5)

        self.refresh_table()

    # --- Vault Actions ---
    def add_entry(self):
        site = self.site_entry.get().strip()
        user = self.user_entry.get().strip()
        pwd = self.pwd_entry.get().strip()

        if not site or not user or not pwd:
            messagebox.showwarning("Input Error", "All fields are required!")
            return

        self.vault_data[site] = {"username": user, "password": pwd}
        self.save_vault()
        self.refresh_table()

        # Clear input fields
        self.site_entry.delete(0, tk.END)
        self.user_entry.delete(0, tk.END)
        self.pwd_entry.delete(0, tk.END)
        messagebox.showinfo("Success", f"Saved credentials for '{site}'")

    def delete_entry(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(
                "Selection Error", "Select an item to delete."
            )
            return

        item = self.tree.item(selected[0])
        site = item["values"][0]

        if messagebox.askyesno(
            "Confirm Delete", f"Delete credentials for {site}?"
        ):
            del self.vault_data[site]
            self.save_vault()
            self.refresh_table()

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for site, creds in self.vault_data.items():
            self.tree.insert(
                "", tk.END, values=(site, creds["username"], creds["password"])
            )

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = PasswordManagerApp(root)
    root.mainloop()