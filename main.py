from appendImage import append_page, append_puzzle_page
from index import create_title_page
from generatePuzzle import create_all_puzzles, create_individual_puzzle
import os
from Words.rawWordToJSON import word_to_json

# Global book_name
book_name = "Where's Word-o"



def main():
    global book_name
    image_path = "Assets/Cover.png"
    background_image = "Assets/Background.png"
    puzzle_background_image = "Assets/pageBackground.png"
    word_json_path = "Words/words.json"
    puzzle_folder = "generated_puzzles"

    print(f"Creating book '{book_name}'.\n\n")

    start_puzzle = input("Enter the puzzle number to start from (default 1): ").strip() or "1"
    if not start_puzzle.isdigit():
        print("Invalid puzzle number. Exiting...")
        return
    start_puzzle = int(start_puzzle)

    delete_puzzles = input("Delete puzzles after making the book? (y/n, default n): ").strip().lower() or 'n'
    if delete_puzzles not in ['y', 'n']:
        print("Invalid input. Exiting...")
        return


    print("Converting raw words to JSON.\n")
    word_to_json(file_path="Words/words.txt", output_path=word_json_path)

    if start_puzzle == 1:
        if os.path.exists(f"{book_name}.pdf"):
            os.remove(f"{book_name}.pdf")
        print("Adding cover image.\n")
        append_page(book_name, image_path)

        print("Creating title page.\n")
        create_title_page(book_name, word_json_path,
                          background_image=background_image)

    print("\nGenerating puzzles and adding to the book.")
    failures = create_all_puzzles(
        word_json_path, puzzle_background_image, puzzle_folder, start_puzzle)

    if failures:
        print(f"Retrying {len(failures)} failed puzzle(s).")
        unresolved = create_individual_puzzle(
            failures, puzzle_folder, background_image=puzzle_background_image)
        if unresolved:
            raise RuntimeError(f"Could not generate {len(unresolved)} puzzle(s); book was not completed")

    print("All puzzles are made. Adding to the book...")

    append_puzzle_page(f"{book_name}.pdf", puzzle_folder,
                       background_image=puzzle_background_image)

    print("All puzzles added to the book.")

    if delete_puzzles == 'y':
        print("Deleting puzzles...")
        import shutil
        shutil.rmtree(puzzle_folder)
        print("Puzzles deleted.")

    print(f"Book '{book_name}' created successfully.")


if __name__ == '__main__':
    main()
