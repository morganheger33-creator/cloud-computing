import random
import string
import os

# File to save passwords
SAVE_FILE = "saved_passwords.txt"

def generate_password(length, use_upper, use_digits, use_symbols):
    characters = string.ascii_lowercase

    if use_upper:
        characters += string.ascii_uppercase
    if use_digits:
        characters += string.digits
    if use_symbols:
        characters += string.punctuation

    if not characters:
        return None

    password = ''.join(random.choice(characters) for _ in range(length))
    return password

def save_password(label, password):
    with open(SAVE_FILE, "a") as f:
        f.write(f"{label}: {password}\n")
    print(f"✅ Password saved to '{SAVE_FILE}'")

def view_saved_passwords():
    if not os.path.exists(SAVE_FILE):
        print("📭 No saved passwords yet.")
        return
    print("\n📋 Saved Passwords:")
    print("-" * 40)
    with open(SAVE_FILE, "r") as f:
        print(f.read())
    print("-" * 40)

def get_yes_no(prompt):
    while True:
        answer = input(prompt).strip().lower()
        if answer in ("y", "n"):
            return answer == "y"
        print("  Please enter y or n.")

def main():
    print("=" * 40)
    print("       🔐 PASSWORD GENERATOR")
    print("=" * 40)

    while True:
        print("\nWhat would you like to do?")
        print("  1. Generate a new password")
        print("  2. View saved passwords")
        print("  3. Quit")

        choice = input("\nEnter choice (1/2/3): ").strip()

        if choice == "1":
            # Get password length
            while True:
                try:
                    length = int(input("\n🔢 Password length (8–64): ").strip())
                    if 8 <= length <= 64:
                        break
                    print("  Please enter a number between 8 and 64.")
                except ValueError:
                    print("  Invalid input. Enter a number.")

            # Get character options
            print("\n⚙️  Customize your password:")
            use_upper   = get_yes_no("  Include uppercase letters? (y/n): ")
            use_digits  = get_yes_no("  Include numbers?           (y/n): ")
            use_symbols = get_yes_no("  Include symbols?           (y/n): ")

            # Generate
            password = generate_password(length, use_upper, use_digits, use_symbols)
            print(f"\n✨ Generated Password: {password}")

            # Strength hint
            if length >= 16 and use_upper and use_digits and use_symbols:
                print("💪 Strength: Very Strong")
            elif length >= 12 and (use_digits or use_symbols):
                print("👍 Strength: Strong")
            elif length >= 8:
                print("⚠️  Strength: Moderate — consider longer or more character types")

            # Save option
            save = get_yes_no("\n💾 Save this password? (y/n): ")
            if save:
                label = input("  Enter a label (e.g. Gmail, GitHub): ").strip()
                save_password(label, password)

        elif choice == "2":
            view_saved_passwords()

        elif choice == "3":
            print("\n👋 Bye! Stay secure!")
            break

        else:
            print("❌ Invalid choice. Enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
