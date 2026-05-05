def print_board(board):
    print("\n+" + "-------+" * 3)
    for i, row in enumerate(board):
        if i > 0 and i % 3 == 0:
            print("+" + "-------+" * 3)
        row_str = "| "
        for j, num in enumerate(row):
            row_str += (str(num) if num != 0 else ".") + " "
            if (j + 1) % 3 == 0:
                row_str += "| "
        print(row_str)
    print("+" + "-------+" * 3)


def is_valid(board, row, col, num):
    # Check row
    if num in board[row]:
        return False

    # Check column
    if num in [board[r][col] for r in range(9)]:
        return False

    # Check 3x3 box
    box_row, box_col = 3 * (row // 3), 3 * (col // 3)
    for r in range(box_row, box_row + 3):
        for c in range(box_col, box_col + 3):
            if board[r][c] == num:
                return False

    return True


def solve(board):
    for row in range(9):
        for col in range(9):
            if board[row][col] == 0:
                for num in range(1, 10):
                    if is_valid(board, row, col, num):
                        board[row][col] = num
                        if solve(board):
                            return True
                        board[row][col] = 0
                return False
    return True


def input_board():
    print("\n📝 Enter your Sudoku puzzle row by row.")
    print("   Use 0 or . for empty cells, separate numbers with spaces.")
    print("   Example: 5 3 0 0 7 0 0 0 0\n")

    board = []
    for i in range(9):
        while True:
            try:
                row_input = input(f"  Row {i + 1}: ").strip().replace(".", "0").split()
                row = [int(x) for x in row_input]
                if len(row) != 9 or not all(0 <= x <= 9 for x in row):
                    print("  ❌ Enter exactly 9 numbers (0–9). Try again.")
                    continue
                board.append(row)
                break
            except ValueError:
                print("  ❌ Invalid input. Use numbers only.")
    return board


def use_sample_board():
    return [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9],
    ]


def main():
    print("=" * 40)
    print("        🧩 SUDOKU SOLVER")
    print("=" * 40)

    print("\nChoose an option:")
    print("  1. Enter your own puzzle")
    print("  2. Use a sample puzzle")

    while True:
        choice = input("\nEnter choice (1/2): ").strip()
        if choice in ("1", "2"):
            break
        print("❌ Please enter 1 or 2.")

    if choice == "1":
        board = input_board()
    else:
        board = use_sample_board()

    print("\n🔍 Your Puzzle:")
    print_board(board)

    print("\n⚙️  Solving", end="", flush=True)
    import time
    for _ in range(3):
        time.sleep(0.4)
        print(".", end="", flush=True)

    if solve(board):
        print("\n\n✅ Solved!")
        print_board(board)
    else:
        print("\n\n❌ No solution found. Check your puzzle for errors.")

    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
