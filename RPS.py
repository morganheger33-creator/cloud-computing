import os
import time

# ─────────────────────────────────────────
#  ROCK PAPER SCISSORS  —  2 Player Mode
# ─────────────────────────────────────────

CHOICES = ["rock", "paper", "scissors"]
EMOJIS  = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
BEATS   = {"rock": "scissors", "paper": "rock", "scissors": "paper"}

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def print_banner():
    print("=" * 45)
    print("   ✊✋✌️   2-PLAYER ROCK PAPER SCISSORS")
    print("=" * 45)

def get_choice(player_name):
    while True:
        print(f"\n🎮 {player_name}, make your choice:")
        for i, c in enumerate(CHOICES, 1):
            print(f"  {i}. {EMOJIS[c]}  {c.capitalize()}")
        pick = input("  Enter 1, 2, or 3: ").strip()
        if pick in ("1", "2", "3"):
            return CHOICES[int(pick) - 1]
        print("  ❌ Invalid! Enter 1, 2, or 3.")

def hide_screen(next_player):
    input(f"\n🙈 Pass the device to {next_player} and press Enter...")
    clear()
    print_banner()

def determine_winner(p1_name, p1_choice, p2_name, p2_choice):
    print("\n" + "─" * 45)
    print(f"  {p1_name:>15}  vs  {p2_name}")
    print(f"  {EMOJIS[p1_choice] + ' ' + p1_choice.capitalize():>18}  vs  {EMOJIS[p2_choice]} {p2_choice.capitalize()}")
    print("─" * 45)

    if p1_choice == p2_choice:
        print("  🤝 It's a TIE!")
        return None
    elif BEATS[p1_choice] == p2_choice:
        print(f"  🏆 {p1_name} WINS this round!")
        return p1_name
    else:
        print(f"  🏆 {p2_name} WINS this round!")
        return p2_name

def print_scoreboard(scores, p1, p2, ties):
    print("\n📊 Scoreboard:")
    print(f"  {p1}: {scores[p1]} pts  |  {p2}: {scores[p2]} pts  |  Ties: {ties}")

def play_game():
    clear()
    print_banner()

    # Get player names
    print("\n👤 Enter player names:")
    p1 = input("  Player 1 name: ").strip() or "Player 1"
    p2 = input("  Player 2 name: ").strip() or "Player 2"

    # Get number of rounds
    while True:
        try:
            rounds = int(input("\n🔢 How many rounds? (1–10): ").strip())
            if 1 <= rounds <= 10:
                break
            print("  Please enter a number between 1 and 10.")
        except ValueError:
            print("  Invalid input. Enter a number.")

    scores = {p1: 0, p2: 0}
    ties = 0

    # ── GAME LOOP ──
    for round_num in range(1, rounds + 1):
        clear()
        print_banner()
        print(f"\n🔄 Round {round_num} of {rounds}")
        print_scoreboard(scores, p1, p2, ties)

        # Player 1 picks
        p1_choice = get_choice(p1)

        # Hide screen before Player 2 picks
        hide_screen(p2)

        print(f"\n✅ {p1} has already picked — no peeking!")
        p2_choice = get_choice(p2)

        # Reveal & determine winner
        clear()
        print_banner()
        print(f"\n🔄 Round {round_num} of {rounds} — RESULTS")
        winner = determine_winner(p1, p1_choice, p2, p2_choice)

        if winner:
            scores[winner] += 1
        else:
            ties += 1

        print_scoreboard(scores, p1, p2, ties)

        if round_num < rounds:
            input("\n⏭️  Press Enter for the next round...")

    # ── FINAL RESULT ──
    clear()
    print_banner()
    print("\n🎉 GAME OVER! Final Results:")
    print_scoreboard(scores, p1, p2, ties)
    print("─" * 45)

    if scores[p1] > scores[p2]:
        print(f"\n🏆 {p1} is the CHAMPION! 🎊")
    elif scores[p2] > scores[p1]:
        print(f"\n🏆 {p2} is the CHAMPION! 🎊")
    else:
        print("\n🤝 It's an overall TIE! Well played both!")

    print("─" * 45)

    # Play again?
    again = input("\n🔁 Play again? (y/n): ").strip().lower()
    if again == "y":
        play_game()
    else:
        print("\n👋 Thanks for playing! See you next time!\n")

# ── ENTRY POINT ──
if __name__ == "__main__":
    play_game()
