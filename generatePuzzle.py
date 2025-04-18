import os
from pathlib import Path
import sys
import random
# from PIL import Image, ImageDraw, ImageFont
from svgwrite import Drawing, rgb
from svgwrite.container import Group
import json
from math import sqrt

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


def _generate_wordsearch(nrows, ncols, wordlist, allow_backwards_words=True, mask=None):
    """Attempt to make a word search with the given parameters."""

    grid = create_grid(nrows, ncols, mask)
    wordPositions = {}

    def fill_grid_randomly(grid):
        """Fill up the empty, unmasked positions with random letters."""
        for irow in range(nrows):
            for icol in range(ncols):
                if grid[irow][icol] == ' ':
                    grid[irow][icol] = random.choice(ALPHABET)

    def remove_mask(grid):
        """Remove the mask, for text output, by replacing with whitespace."""
        for irow in range(nrows):
            for icol in range(ncols):
                if grid[irow][icol] == '*':
                    grid[irow][icol] = ' '

    def test_candidate(irow, icol, dx, dy, word):
        """Test the candidate location (icol, irow) for word in orientation (dx, dy)."""
        for j in range(len(word)):
            if grid[irow][icol] not in (' ', word[j]):
                return False
            irow += dy
            icol += dx
        return True

    def place_word(word):
        """Place word randomly in the grid and return True, if possible."""

        # Left, down, and the diagonals.
        dxdy_choices = [(0, 1), (1, 0), (1, 1), (1, -1)]
        random.shuffle(dxdy_choices)
        for (dx, dy) in dxdy_choices:
            if allow_backwards_words and random.choice([True, False]):
                # If backwards words are allowed, simply reverse word.
                word = word[::-1]

            n = len(word)
            colmin = 0
            colmax = ncols - n if dx else ncols - 1
            rowmin = 0 if dy >= 0 else n - 1
            rowmax = nrows - n if dy >= 0 else nrows - 1

            if colmax - colmin < 0 or rowmax - rowmin < 0:
                # No possible place for the word in this orientation.
                continue

            # Build a list of candidate locations for the word.
            candidates = []
            for irow in range(rowmin, rowmax+1):
                for icol in range(colmin, colmax+1):
                    if test_candidate(irow, icol, dx, dy, word):
                        candidates.append((irow, icol))

            # If we don't have any candidates, try the next orientation.
            if not candidates:
                continue

            # Pick a random candidate location and place the word in this orientation.
            loc = irow, icol = random.choice(candidates)
            for j in range(n):
                grid[irow][icol] = word[j]
                irow += dy
                icol += dx

            wordPositions[word] = (loc[1], loc[0], icol-dx, irow-dy)
            # We're done: no need to try any more orientations.
            break
        else:
            # If we're here, it's because we tried all orientations but
            # couldn't find anywhere to place the word. Oh dear.
            return False
        return True

    # Iterate over the word list and try to place each word (without spaces).
    for word in wordlist:
        word = word.replace(' ', '')
        if not place_word(word):
            # We failed to place word, so bail.
            return None, None

    fill_grid_randomly(grid)
    remove_mask(grid)

    return grid, wordPositions


def generate_wordsearch(*args, **kwargs):
    """Make a word search, attempting to fit words into the specified grid."""

    # We try NATTEMPTS times (with random orientations) before giving up.
    NATTEMPTS = 50
    for i in range(NATTEMPTS):
        grid, solution = _generate_wordsearch(*args, **kwargs)
        if grid:
            print(f'Fitted the words in {i+1} attempt(s)')
            return grid, solution

    return None, None


def display_grid_text(grid):
    """Displays grid as text."""
    for row in grid:
        print(" ".join(row))





def create_puzzle_svg(filename, grid, wordlist, mask_type=None, page_number=None):
    """
    This function generates a puzzle page as an SVG with a grid of letters, an optional circle mask around the grid,
    a list of hidden words, and a page number. The output is saved as an SVG file.
    """
    page_width, page_height = 2480, 3508  # A4 size in pixels at 300 DPI
    margin = 100
    grid_outline_width = 5
    grid_font_size = 30
    title_font_size = 40
    words_font_size = 30
    page_number_font_size = 30
    vertical_gap = 100  # Gap between grid and word list

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
                # Draw gridlines only if it's not a circular mask
                if mask_type != "circle":
                    dwg.add(dwg.rect(insert=(cell_x, cell_y), size=(
                        cell_size, cell_size), fill='none', stroke='black'))
                # Draw the character inside the grid
                char_x = cell_x + cell_size // 2
                char_y = cell_y + cell_size // 2
                dwg.add(dwg.text(char.upper(), insert=(char_x, char_y), text_anchor="middle",
                                 alignment_baseline="central", font_size=24, fill='black'))

    # Draw the grid (with characters) without gridlines for circle mask
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
            # Draw a colored rectangle to highlight the cell
            dwg.add(dwg.rect(insert=(cell_x, cell_y), size=(
                cell_size, cell_size), fill=rgb(*color), stroke='none'))

    word_colors = {}
    for word, (start_x, start_y, end_x, end_y) in word_positions.items():
        if word not in word_colors:
            word_colors[word] = tuple(random.randint(0, 255) for _ in range(3))
        color = word_colors[word]
        highlight_word(word, start_x, start_y, end_x, end_y, color)

    # After highlighting, draw the letters on top of the highlights
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
            # Draw the text on top of the highlighted cell
            dwg.add(dwg.text(word[i].upper(), insert=(char_x, char_y), text_anchor="middle",
                             alignment_baseline="central", font_size=24, fill='black'))

    if mask_type == "circle":
        grid_center_x = padding + grid_size * cell_size // 2
        grid_center_y = padding + grid_size * cell_size // 2
        radius = grid_size * cell_size // 2 + 20  # Increased radius by 10
        dwg.add(dwg.circle(center=(grid_center_x, grid_center_y),
                r=radius, fill='none', stroke='red', stroke_width=5))
    else:
        dwg.add(dwg.rect(insert=(padding, padding), size=(grid_size * cell_size,
                grid_size * cell_size), fill='none', stroke='red', stroke_width=5))

    dwg.save()


def create_puzzle_and_solution(puzzle_filename, wordlist, nrows: int, ncols: int, mask_type=None, background_image=None, page_number=None):
    """
    This function generates both the puzzle image and the solution image.
    It uses the provided word list, grid dimensions, and mask type to generate both images.
    """
    # Generate the word search grid and word positions
    grid, word_positions = generate_wordsearch(
        nrows, ncols, wordlist, mask=mask_type)

    if grid:
        # Display the grid for debugging (optional)
        # display_grid_text(grid)

        # Generate the puzzle image
        create_puzzle_svg(puzzle_filename,  grid,
                          wordlist, mask_type, page_number)

        # Generate the solution image
        solution_filename = f"{puzzle_filename}S"
        create_solution_svg(solution_filename, grid, word_positions, mask_type)

        print(f"Puzzle and solution generated: {
              puzzle_filename}.svg, {solution_filename}.svg")
    else:
        print("Failed to generate word search after multiple attempts.")
        return puzzle_filename


def create_all_puzzles(word_json_path, background_image, puzzle_folder, start_puzzle=1):
    fails = []

    with open(word_json_path, "r") as file:
        words_data = json.load(file)

    os.makedirs(puzzle_folder, exist_ok=True)
    if start_puzzle == 1:
        for old_page in Path(puzzle_folder).glob("*.svg"):
            old_page.unlink()

    current_puzzle = start_puzzle
    current_topic = None
    current_mode = None

    for topic_index, (topic_name, modes) in enumerate(words_data.items(), start=1):
        print(f"Generating puzzles for topic '{topic_name}'...")

        for mode in ['Normal', 'Hard']:
            mode_data = modes.get(mode, [])

            if mode_data:
                if current_topic != topic_name or current_mode != mode:
                    transition_filename = f"{
                        puzzle_folder}/{current_puzzle}. {topic_index}{mode[0]}"
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
                puzzle_filename = f"{
                    puzzle_folder}/{current_puzzle}. {page_number}"
                size = 13 if "Normal" in mode else 17

                puzzle = create_puzzle_and_solution(
                    puzzle_filename, word_list, size, size, mask_type=None, background_image=background_image, page_number=page_number
                )
                current_puzzle += 1  # Update progress
                if puzzle is not None:
                    fails.append((puzzle_filename, word_list, size, None, page_number))

        for bonus_mode in ['Normal', 'Hard']:
            bonus_data = modes.get("Bonus", {}).get(bonus_mode, [])

            if bonus_data:
                if current_topic != topic_name or current_mode != f"Bonus {bonus_mode}":
                    transition_filename = f"{
                        puzzle_folder}/{current_puzzle}. {topic_index}B{bonus_mode[0]}"
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
                puzzle_filename = f"{
                    puzzle_folder}/{current_puzzle}. {page_number}"
                size = 13 if bonus_mode == "Normal" else 17

                puzzle = create_puzzle_and_solution(
                    puzzle_filename, word_list, size, size, mask_type="circle", background_image=background_image, page_number=page_number
                )
                current_puzzle += 1  # Update progress
                if puzzle is not None:
                    fails.append((puzzle_filename, word_list, size, "circle", page_number))

    # Make solution page
    create_transition_svg(f"{puzzle_folder}//S.svg",
                          "SOLUTIONS", "", background_image)

    print(len(fails))
    for fail in fails:
        print(f"Failed to generate puzzle {fail[4]}.")

    return fails


def create_transition_svg(filename, topic_name, mode_name, background_image=None):
    dwg = Drawing(filename, size=(2480, 3508))  # A4 size at 300 DPI

    if background_image:
        dwg.add(dwg.image(background_image, insert=(
            0, 0), size=("2480px", "3508px")))

    # Use Courier New for the topic name
    topic_font_size = 120
    dwg.add(dwg.text(topic_name, insert=("50%", "33%"), text_anchor="middle",
            font_size=topic_font_size, font_family="Courier New", font_weight="bold"))

    # Adjust mode name for Bonus modes
    mode_name = mode_name.replace(
        "Bonus Normal", "Bonus I").replace("Bonus Hard", "Bonus II")

    # Use Times New Roman for the mode name
    mode_font_size = 80
    dwg.add(dwg.text(mode_name, insert=("50%", "75%"), text_anchor="middle",
            font_size=mode_font_size, font_family="Times New Roman", font_weight="bold"))

    dwg.save()


def create_individual_puzzle(files, puzzle_folder, background_image):
    os.makedirs(puzzle_folder, exist_ok=True)
    unresolved = []
    for puzzle_filename, word_list, size, mask_type, page_number in files:
        try:
            result = create_puzzle_and_solution(
                puzzle_filename, word_list, size, size, mask_type=mask_type,
                background_image=background_image, page_number=page_number)
            if result is not None:
                unresolved.append(page_number)
        except Exception as e:
            print(f"Failed to generate puzzle {page_number}: {e}")
            unresolved.append(page_number)
    return unresolved


def main():
    wordlist_filename = "test_words.txt"
    nrows, ncols = 15, 15
    mask_type = None  # None, 'circle', 'squares'

    if nrows > NMAX or ncols > NMAX:
        sys.exit(f"Maximum grid size is {NMAX}x{NMAX}")

    wordlist = [line.strip().upper() for line in open(
        wordlist_filename) if line.strip() and not line.startswith('#')]
    grid, wordPositions = generate_wordsearch(
        nrows, ncols, wordlist, mask=mask_type)

    if grid:
        display_grid_text(grid)
        base_filename = os.path.splitext(wordlist_filename)[0]
        create_puzzle_svg(f"{base_filename}-puzzle.png",
                          grid, wordlist, mask_type, 21)
        create_solution_svg(f"{base_filename}-solution.png",
                            grid, wordPositions, mask_type)
    else:
        print("Failed to generate word search after multiple attempts.")


if __name__ == "__main__":
    main()
