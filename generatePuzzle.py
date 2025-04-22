import os
import sys
import random
# from PIL import Image, ImageDraw, ImageFont
from svgwrite import Drawing, rgb
from svgwrite.container import Group
import json
from math import sqrt

# Import the Rust solver
import wordgrid_solver

# Constants
NMAX = 32
ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


# Mask functions for different shapes
def circle_mask(grid, nrows, ncols):
    """Circular mask on grid."""
    radius_squared = min(ncols, nrows) ** 2 // 4
    center_x, center_y = ncols // 2, nrows // 2
    for row in range(nrows):
        for col in range(ncols):
            if (row - center_y) ** 2 + (col - center_x) ** 2 > radius_squared:
                grid[row][col] = '*'


def squares_mask(grid, nrows, ncols):
    """Mask of overlapping squares on grid."""
    a = int(0.38 * min(ncols, nrows))
    center_x, center_y = ncols // 2, nrows // 2
    for row in range(nrows):
        for col in range(ncols):
            if a <= col < ncols - a and (row < center_y - a or row > center_y + a):
                grid[row][col] = '*'
            if a <= row < nrows - a and (col < center_x - a or col > center_x + a):
                grid[row][col] = '*'


def no_mask(grid, nrows, ncols):
    """No mask applied."""
    pass


MASK_FUNCTIONS = {None: no_mask,
                  'circle': circle_mask, 'squares': squares_mask}


def create_grid(nrows, ncols, mask_type=None):
    """Creates a grid with optional mask."""
    grid = [[' '] * ncols for _ in range(nrows)]
    MASK_FUNCTIONS[mask_type](grid, nrows, ncols)
    return grid


def display_grid_text(grid):
    """Displays grid as text."""
    for row in grid:
        print(" ".join(row))


def create_puzzle_svg(filename, grid, wordlist, mask_type=None, page_number=None):
    page_width, page_height = 2480, 3508
    margin = 100
    grid_outline_width = 5
    grid_font_size = 30
    title_font_size = 40
    words_font_size = 30
    page_number_font_size = 30
    vertical_gap = 100

    if ".svg" not in filename:
        filename += ".svg"

    dwg = Drawing(filename, size=(page_width, page_height))

    grid_size = len(grid)
    cell_size = min((page_width - 2 * margin) // grid_size,
                    (page_height // 2) // grid_size)
    grid_width = grid_size * cell_size
    grid_height = grid_size * cell_size

    words_per_column = (len(wordlist) + 2) // 3
    word_list_height = words_per_column * 40 + 80

    combined_height = grid_height + vertical_gap + word_list_height
    vertical_offset = (page_height - combined_height) // 2

    grid_start_x = (page_width - grid_width) // 2
    grid_start_y = vertical_offset

    grid_group = Group()

    center_x = grid_start_x + grid_width // 2
    center_y = grid_start_y + grid_height // 2
    radius = grid_width // 2 if grid_height > grid_width else grid_height // 2

    for row in range(grid_size):
        for col in range(grid_size):
            cell_x = grid_start_x + col * cell_size
            cell_y = grid_start_y + row * cell_size

            if mask_type == "circle":
                if sqrt((cell_x + cell_size / 2 - center_x)**2 + (cell_y + cell_size / 2 - center_y)**2) > radius:
                    continue

            char_x = cell_x + cell_size // 2
            char_y = cell_y + cell_size // 2
            grid_group.add(dwg.text(grid[row][col].upper(), insert=(char_x, char_y), text_anchor="middle",
                                    alignment_baseline="central", font_size=grid_font_size, fill='black'))

    dwg.add(grid_group)

    if mask_type == "circle":
        dwg.add(dwg.circle(center=(center_x, center_y), r=radius + 40,
                fill='none', stroke='red', stroke_width=grid_outline_width))
    else:
        for row in range(grid_size):
            for col in range(grid_size):
                cell_x = grid_start_x + col * cell_size
                cell_y = grid_start_y + row * cell_size
                grid_group.add(dwg.rect(insert=(cell_x, cell_y), size=(
                    cell_size, cell_size), fill='none', stroke='black'))

        dwg.add(dwg.rect(insert=(grid_start_x, grid_start_y), size=(
            grid_width, grid_height), fill='none', stroke='red', stroke_width=grid_outline_width))

    title_y = grid_start_y + grid_height + vertical_gap
    dwg.add(dwg.text("HIDDEN WORDS", insert=(page_width // 2, title_y), text_anchor="middle",
                     alignment_baseline="central", font_size=title_font_size, fill='black'))

    words_y = title_y + 80
    column_width = (page_width - 2 * margin) // 3
    for i, word in enumerate(sorted(wordlist)):
        col = i % 3
        row = i // 3
        word_x = margin + col * column_width + column_width // 2
        word_y = words_y + row * 40
        dwg.add(dwg.text(word.upper(), insert=(word_x, word_y), text_anchor="middle",
                         alignment_baseline="central", font_size=words_font_size, fill='black'))

    if page_number is not None:
        dwg.add(dwg.text(str(page_number), insert=(page_width // 2, page_height - 100), text_anchor="middle",
                         alignment_baseline="central", font_size=page_number_font_size, fill='black'))

    dwg.save()


def create_solution_svg(filename, grid, word_positions, mask_type=None):
    grid_size = len(grid)
    cell_size = 40
    padding = 20
    width = grid_size * cell_size + 2 * padding
    height = grid_size * cell_size + 2 * padding

    if ".svg" not in filename:
        filename += ".svg"

    dwg = Drawing(filename, size=(width, height))

    def draw_grid():
        start_x = padding
        start_y = padding
        for y in range(grid_size):
            for x in range(grid_size):
                char = grid[y][x]
                cell_x = start_x + x * cell_size
                cell_y = start_y + y * cell_size
                if mask_type != "circle":
                    dwg.add(dwg.rect(insert=(cell_x, cell_y), size=(
                        cell_size, cell_size), fill='none', stroke='black'))
                char_x = cell_x + cell_size // 2
                char_y = cell_y + cell_size // 2
                dwg.add(dwg.text(char.upper(), insert=(char_x, char_y), text_anchor="middle",
                                 alignment_baseline="central", font_size=24, fill='black'))

    draw_grid()

    def highlight_word(word, start_x, start_y, end_x, end_y, color):
        for i in range(len(word)):
            x_pos = start_x + i * \
                (end_x - start_x) // (len(word) -
                                      1) if start_x != end_x else start_x
            y_pos = start_y + i * \
                (end_y - start_y) // (len(word) -
                                      1) if start_y != end_y else start_y
            cell_x = padding + x_pos * cell_size
            cell_y = padding + y_pos * cell_size
            dwg.add(dwg.rect(insert=(cell_x, cell_y), size=(
                cell_size, cell_size), fill=rgb(*color), stroke='none'))

    word_colors = {}
    for word, (start_x, start_y, end_x, end_y) in word_positions.items():
        if word not in word_colors:
            word_colors[word] = tuple(random.randint(0, 255) for _ in range(3))
        color = word_colors[word]
        highlight_word(word, start_x, start_y, end_x, end_y, color)

    for word, (start_x, start_y, end_x, end_y) in word_positions.items():
        color = word_colors[word]
        for i in range(len(word)):
            x_pos = start_x + i * \
                (end_x - start_x) // (len(word) -
                                      1) if start_x != end_x else start_x
            y_pos = start_y + i * \
                (end_y - start_y) // (len(word) -
                                      1) if start_y != end_y else start_y
            char_x = padding + x_pos * cell_size + cell_size // 2
            char_y = padding + y_pos * cell_size + cell_size // 2
            dwg.add(dwg.text(word[i].upper(), insert=(char_x, char_y), text_anchor="middle",
                             alignment_baseline="central", font_size=24, fill='black'))

    if mask_type == "circle":
        grid_center_x = padding + grid_size * cell_size // 2
        grid_center_y = padding + grid_size * cell_size // 2
        radius = grid_size * cell_size // 2 + 20
        dwg.add(dwg.circle(center=(grid_center_x, grid_center_y),
                r=radius, fill='none', stroke='red', stroke_width=5))
    else:
        dwg.add(dwg.rect(insert=(padding, padding), size=(grid_size * cell_size,
                grid_size * cell_size), fill='none', stroke='red', stroke_width=5))

    dwg.save()


def create_puzzle_and_solution(puzzle_filename, wordlist, nrows: int, ncols: int, mask_type=None, background_image=None, page_number=None):
    """
    Generates puzzle and solution SVG using the Rust-based core.
    """
    print(f"Generating puzzle (Rust): {puzzle_filename} ({nrows}x{ncols})")  # Debug info

    # Call the Rust function
    result = wordgrid_solver.generate_word_grid_rust(
        nrows=nrows,
        ncols=ncols,
        word_list=wordlist,
        allow_backwards=True,
        mask=mask_type
    )

    if result is not None:
        grid, word_positions = result
        create_puzzle_svg(puzzle_filename, grid,
                          wordlist, mask_type, page_number)

        solution_filename = f"{puzzle_filename}S"
        create_solution_svg(solution_filename, grid, word_positions, mask_type)

        print(f"Successfully generated: {puzzle_filename}.svg, {solution_filename}.svg")
        return True
    else:
        print(f"Failed to generate word search for {puzzle_filename} (Rust solver).")
        return False


def create_all_puzzles(word_json_path, background_image, puzzle_folder, start_puzzle=1):
    fails = []

    with open(word_json_path, "r") as file:
        words_data = json.load(file)

    os.makedirs(puzzle_folder, exist_ok=True)

    current_puzzle = start_puzzle
    current_topic = None
    current_mode = None

    for topic_index, (topic_name, modes) in enumerate(words_data.items(), start=1):
        print(f"Generating puzzles for topic '{topic_name}'...")

        for mode in ['Normal', 'Hard']:
            mode_data = modes.get(mode, [])

            if mode_data:
                if current_topic != topic_name or current_mode != mode:
                    transition_filename = f"{puzzle_folder}/{current_puzzle}.{topic_index}{mode[0]}"
                    create_transition_svg(
                        transition_filename + ".svg", topic_name, mode, background_image)
                    current_puzzle += 1
                    current_topic = topic_name
                    current_mode = mode

            for puzzle_number, word_list in enumerate(mode_data, start=1):
                if start_puzzle > current_puzzle:
                    current_puzzle += 1
                    continue

                word_list = [word.upper() for word in word_list]
                page_number = f"{topic_index}{mode[0]}{puzzle_number}"
                puzzle_filename = f"{puzzle_folder}/{current_puzzle}. {page_number}"
                size = 13 if "Normal" in mode else 17

                puzzle = create_puzzle_and_solution(
                    puzzle_filename, word_list, size, size, mask_type=None, background_image=background_image, page_number=page_number
                )
                current_puzzle += 1
                if puzzle is not None:
                    fails.append(page_number)

        for bonus_mode in ['Normal', 'Hard']:
            bonus_data = modes.get("Bonus", {}).get(bonus_mode, [])

            if bonus_data:
                if current_topic != topic_name or current_mode != f"Bonus {bonus_mode}":
                    transition_filename = f"{puzzle_folder}/{current_puzzle}. {topic_index}B{bonus_mode[0]}"
                    create_transition_svg(
                        transition_filename + ".svg", topic_name, f"Bonus {bonus_mode}", background_image)
                    current_puzzle += 1
                    current_topic = topic_name
                    current_mode = f"Bonus {bonus_mode}"

            for puzzle_number, word_list in enumerate(bonus_data, start=1):
                if start_puzzle > current_puzzle:
                    current_puzzle += 1
                    continue

                word_list = [word.upper() for word in word_list]
                page_number = f"{topic_index}B{bonus_mode[0]}{puzzle_number}"
                puzzle_filename = f"{puzzle_folder}/{current_puzzle}. {page_number}"
                size = 13 if "Normal" in mode else 17

                puzzle = create_puzzle_and_solution(
                    puzzle_filename, word_list, size, size, mask_type="circle", background_image=background_image, page_number=page_number
                )
                current_puzzle += 1
                if puzzle is not None:
                    fails.append(page_number)

    create_transition_svg(f"{puzzle_folder}//S.svg",
                          "SOLUTIONS", "", background_image)

    print(len(fails))
    for fail in fails:
        print(f"Failed to generate puzzle {fail}.")

    return [fail.partition(". ")[2] for fail in fails]


def create_transition_svg(filename, topic_name, mode_name, background_image=None):
    dwg = Drawing(filename, size=(2480, 3508))

    if background_image:
        dwg.add(dwg.image(background_image, insert=(
            0, 0), size=("2480px", "3508px")))

    topic_font_size = 120
    dwg.add(dwg.text(topic_name, insert=("50%", "33%"), text_anchor="middle",
            font_size=topic_font_size, font_family="Courier New", font_weight="bold"))

    mode_name = mode_name.replace(
        "Bonus Normal", "Bonus I").replace("Bonus Hard", "Bonus II")

    mode_font_size = 80
    dwg.add(dwg.text(mode_name, insert=("50%", "75%"), text_anchor="middle",
            font_size=mode_font_size, font_family="Times New Roman", font_weight="bold"))

    dwg.save()


def create_individual_puzzle(files, word_json_path, puzzle_folder, background_image):
    with open(word_json_path, "r") as file:
        words_data = json.load(file)

    os.makedirs(puzzle_folder, exist_ok=True)

    for file in files:
        try:
            page_number = file
            topic_index = int(file[0])
            bonus = True if file[1] == "B" else False
            mask_type = "circle" if bonus else None
            file = file.replace("B", "")
            mode = "Normal" if file[1] == "N" else "Hard"
            size = 13 if "Normal" in mode else 17
            puzzle_number = int(file[2:])

            if bonus:
                word_list = words_data[list(words_data.keys())[
                    topic_index - 1]]["Bonus"][mode][puzzle_number - 1]
                print(word_list)
            else:
                word_list = words_data[list(words_data.keys())[
                    topic_index - 1]][mode][puzzle_number - 1]

            word_list = [word.upper() for word in word_list]

            create_puzzle_and_solution(
                f"{puzzle_folder}/{page_number}", word_list, size, size, mask_type=mask_type, background_image=background_image, page_number=page_number
            )
        except Exception as e:
            print(f"Failed to generate puzzle {page_number}: {e}")
            print("\n\n")


def main():
    wordlist_filename = "test_words.txt"
    nrows, ncols = 15, 15
    mask_type = None

    if nrows > NMAX or ncols > NMAX:
        sys.exit(f"Maximum grid size is {NMAX}x{NMAX}")

    wordlist = [line.strip().upper() for line in open(
        wordlist_filename) if line.strip() and not line.startswith('#')]
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    base_filename = os.path.splitext(wordlist_filename)[0]
    puzzle_file = os.path.join(output_dir, f"{base_filename}-puzzle-rust")

    success = create_puzzle_and_solution(
        puzzle_file, wordlist, nrows, ncols, mask_type=mask_type
    )

    if success:
        print("SVG puzzle and solution generated successfully (Rust).")
    else:
        print("Failed to generate word search grid (Rust).")


if __name__ == "__main__":
    main()
