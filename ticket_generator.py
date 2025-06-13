import random

def generate_ticket():
    # Step 1: Prepare columns with numbers
    columns = []
    for i in range(9):
        if i == 0:
            col = list(range(1, 10))
        elif i == 8:
            col = list(range(80, 91))
        else:
            col = list(range(i*10, i*10+10))
        random.shuffle(col)
        columns.append(col)

    # Step 2: For each row, pick 5 unique columns to place numbers
    ticket = [[0 for _ in range(9)] for _ in range(3)]
    filled_positions = [set() for _ in range(3)]
    all_positions = [(r, c) for r in range(3) for c in range(9)]

    # Ensure 5 numbers per row
    for row in range(3):
        chosen_cols = random.sample(range(9), 5)
        for col in chosen_cols:
            filled_positions[row].add(col)

    # Step 3: For each column, count how many numbers to place
    col_counts = [0]*9
    for row in range(3):
        for col in filled_positions[row]:
            col_counts[col] += 1

    # Step 4: Place numbers in the ticket
    for col in range(9):
        for _ in range(col_counts[col]):
            # Find a row for this column that needs a number
            possible_rows = [row for row in range(3) if col in filled_positions[row] and ticket[row][col] == 0]
            if possible_rows:
                row = random.choice(possible_rows)
                ticket[row][col] = columns[col].pop()

    return ticket
