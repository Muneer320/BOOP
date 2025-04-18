# Same as main.py but argument based instead of user input

from appendImage import append_page, append_puzzle_page
from index import create_title_page
from generatePuzzle import create_all_puzzles, create_individual_puzzle
from Words.rawWordToJSON import word_to_json
import argparse
import os
import shutil


def main():
    parser = argparse.ArgumentParser(description="Create a word search puzzle book.")
    parser.add_argument("-n", "--name", type=str, default="Where's Word-o", help="Name of the book")
    parser.add_argument("-d", "--delete", action="store_true", help="Delete puzzles after creating the book")
    parser.add_argument("-s", "--start", type=int, default=1, help="Puzzle number to start from")

    parser.add_argument("-wf", "--words-file", type=str, default="Words/words.txt", help="Path to raw words text file")
    parser.add_argument("-jf", "--json-file", type=str, default="Words/words.json", help="Path to JSON words file")
    parser.add_argument("-o", "--output", type=str, default="generated_puzzles", help="Folder to save generated puzzles")

    parser.add_argument("-nm", "--normal", type=int, default=10, help="Number of Normal mode puzzles per topic")
    parser.add_argument("-hm", "--hard", type=int, default=5, help="Number of Hard mode puzzles per topic")
    parser.add_argument("-bnm", "--bonus-normal", type=int, default=1, help="Number of Bonus Normal mode puzzles per topic")
    parser.add_argument("-bhm", "--bonus-hard", type=int, default=1, help="Number of Bonus Hard mode puzzles per topic")

    parser.add_argument("--cover", type=str, default="Assets/Cover.png", help="Cover image for the book.")
    parser.add_argument("--background", type=str, default="Assets/Background.png", help="Background image for title and transition pages")
    parser.add_argument("--puzzle-bg", type=str, default="Assets/pageBackground.png", help="Background image for puzzle pages")

    args = parser.parse_args()

    book_name = args.name
    delete_puzzles = args.delete
    start_puzzle = args.start
    word_file = args.words_file
    word_json = args.json_file
    puzzle_folder = args.output
    cover_image = args.cover
    background_image = args.background
    puzzle_background_image = args.puzzle_bg


    print(f"Initializing '{book_name}' puzzle book generation...\n")

    # Generate JSON from raw words
    print("Converting raw words to JSON...\n")
    try:
        word_to_json(file_path=word_file,
                     num_normal=args.normal,
                     num_hard=args.hard,
                     bonus_normal=args.bonus_normal,
                     bonus_hard=args.bonus_hard)
    except ValueError as e:
        print(f"Error: {e}")
        return 1

    # Remove existing book
    if os.path.exists(f"{book_name}.pdf"):
        print(f"Removing existing book: {book_name}.pdf")
        os.remove(f"{book_name}.pdf")
    
    # Add cover and title
    print("Adding cover image...\n")
    append_page(book_name, cover_image)
    print("Creating title page...\n")
    create_title_page(book_name, word_json, background_image=background_image)

    # Generate puzzles
    print("Generating puzzles...\n")
    fails = create_all_puzzles(word_json, puzzle_background_image, puzzle_folder, start_puzzle)

    # Handle failed puzzles
    if fails:
        print(f"Failed to generate {len(fails)} puzzle(s). Generating individually...\n")
        create_individual_puzzle(fails, word_json, puzzle_folder, background_image=puzzle_background_image)

    # Append puzzles and solutions to the book
    print("Appending puzzles and solutions to the book...\n")
    append_puzzle_page(f"{book_name}.pdf", puzzle_folder, background_image=puzzle_background_image)

    # Cleanup
    if delete_puzzles:
        print("Cleaning up generated puzzles...\n")
        shutil.rmtree(puzzle_folder, ignore_errors=True)
        print("Cleanup completed.\n")

    print(f"Book '{book_name}' created successfully.")
    return 0


if __name__ == '__main__':
    exit(main())
