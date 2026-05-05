import random

def create_board(rows, cols, mines):
    board = [[' ' for _ in range(cols)] for _ in range(rows)]
    mine_positions = set()

    while len(mine_positions) < mines:
        r = random.randint(0, rows - 1)
        c = random.randint(0, cols - 1)
        mine_positions.add((r, c))

    return board, mine_positions

def count_adjacent_mines(r, c, rows, cols, mine_positions):
    count = 0
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) in mine_positions:
                count += 1
    return count

def print_board(board, revealed, mine_positions, rows, cols, game_over=False):
    print("\n    " + "  ".join(str(c) for c in range(cols)))
    print("   " + "---" * cols)

    for r in range(rows):
        row_display = f"{r} | "
        for c in range(cols):
            if game_over and (r, c) in mine_positions and not revealed[r][c]:
                row_display += "💣 "
            elif revealed[r][c]:
                if (r, c) in mine_positions:
                    row_display += "💥 "
                else:
                    num = count_adjacent_mines(r, c, rows, cols, mine_positions)
                    row_display += (str(num) if num > 0 else '·') + "  "
            else:
                row_display += "■  "
        print(row_display)
    print()

def reveal(r, c, rows, cols, revealed, mine_positions, flagged):
    if not (0 <= r < rows and 0 <= c < cols):
        return
    if revealed[r][c] or flagged[r][c]:
        return

    revealed[r][c] = True

    # Auto-reveal neighbors if no adjacent mines
    if count_adjacent_mines(r, c, rows, cols, mine_positions) == 0:
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                reveal(r + dr, c + dc, rows, cols, revealed, mine_positions, flagged)

def check_win(revealed, mine_positions, rows, cols):
    for r in range(rows):
        for c in range(cols):
            if (r, c) not in mine_positions and not revealed[r][c]:
                return False
    return True

def get_difficulty():
    print("=" * 40)
    print("        💣 MINESWEEPER")
    print("=" * 40)
    print("\nChoose difficulty:")
    print("  1. Easy    (8x8,  10 mines)")
    print("  2. Medium  (12x12, 25 mines)")
    print("  3. Hard    (16x16, 50 mines)")

    while True:
        choice = input("\nEnter choice (1/2/3): ").strip()
        if choice == "1": return 8, 8, 10
        elif choice == "2": return 12, 12, 25
        elif choice == "3": return 16, 16, 50
        else: print("❌ Please enter 1, 2, or 3.")

def main():
    rows, cols, mines = get_difficulty()
    board, mine_positions = create_board(rows, cols, mines)
    revealed = [[False] * cols for _ in range(rows)]
    flagged  = [[False] * cols for _ in range(rows)]

    print(f"\n🎯 Board: {rows}x{cols} | Mines: {mines}")
    print("Commands: reveal (r), flag (f), quit (q)")

    while True:
        print_board(board, revealed, mine_positions, rows, cols)
        print(f"🚩 Flags placed: {sum(flagged[r][c] for r in range(rows) for c in range(cols))}/{mines}")

        action = input("Action (r/f/q): ").strip().lower()

        if action == "q":
            print("\n👋 Thanks for playing!")
            break

        if action not in ("r", "f"):
            print("❌ Invalid action. Use r (reveal), f (flag), or q (quit).")
            continue

        try:
            r, c = map(int, input("Enter row and col (e.g. 3 5): ").split())
            if not (0 <= r < rows and 0 <= c < cols):
                print("❌ Out of bounds! Try again.")
                continue
        except ValueError:
            print("❌ Invalid input. Enter two numbers like: 3 5")
            continue

        if action == "f":
            if revealed[r][c]:
                print("⚠️  Already revealed!")
            else:
                flagged[r][c] = not flagged[r][c]
                status = "🚩 Flagged" if flagged[r][c] else "✅ Unflagged"
                print(f"{status} ({r}, {c})")

        elif action == "r":
            if flagged[r][c]:
                print("⚠️  Cell is flagged! Unflag it first.")
                continue
            if revealed[r][c]:
                print("⚠️  Already revealed!")
                continue

            if (r, c) in mine_positions:
                revealed[r][c] = True
                print_board(board, revealed, mine_positions, rows, cols, game_over=True)
                print("💥 BOOM! You hit a mine! Game over!\n")
                break

            reveal(r, c, rows, cols, revealed, mine_positions, flagged)

            if check_win(revealed, mine_positions, rows, cols):
                print_board(board, revealed, mine_positions, rows, cols)
                print("🎉 Congratulations! You cleared the board! You win!\n")
                break

if __name__ == "__main__":
    main()
