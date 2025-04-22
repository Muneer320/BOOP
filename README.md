# BOOP – Book Of Organized Puzzles

Welcome to **BOOP**, a fully automated solution to generate your personalized puzzle book. From title pages to solution pages, everything is crafted seamlessly. Just provide the words, and it’ll do the magic!

## 🔧 Features
- Automatically generates a full-fledged puzzle book (PDF format).
- Includes:
  - **Title Page**
  - **Index Page**
  - **Puzzle Pages** (unique identifiers for each page).
  - **Solution Pages**.
- Puzzles are categorized **Topic-wise** and further divided into:
  - **Normal Mode**: 10 puzzles.
  - **Hard Mode**: 5 puzzles.
  - **Bonus Mode**: 2 puzzles.

## 🗂 Project Structure
```plaintext
Assets/              # Includes backgrounds, title page templates, etc.
  ├── Cover.png            # Cover image
  ├── pageBackground.png   # Page background image
Words/               # Folder for word input and processing
  ├── rawWordToJSON.py     # Converts words.txt to JSON
  ├── words.json           # Processed JSON of words
  ├── words.txt            # Input file (your word list, atleast 200 words per topic)
appendImage.py       # Handles adding images to pages
generatePuzzle.py    # Core puzzle generation logic
index.py             # Creates the index page
main.py              # The main driver script
README.md            # Documentation
```

## 🚀 Getting Started

### Prerequisites

*   Python 3.8+
*   Rust toolchain (including `cargo`)
*   `maturin` (can be installed via pip)

### Building and Running

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd BOOP
    ```

2.  **Create and activate a Python virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Build the Rust extension:**
    Navigate to the Rust project directory and build the extension using Maturin. This compiles the Rust code and makes it available to your Python environment.
    ```bash
    cd wordgrid_solver/wordgrid_solver
    maturin develop
    cd ../..  # Return to the root directory
    ```

5.  **Run the FastAPI server:**
    ```bash
    python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
    ```
    The API will be available at `http://localhost:8000`.

6.  **(Optional) Generate a standalone puzzle book PDF (Original CLI functionality):**
    *   Place your word list in `Words/words.txt` (ensure sufficient words per topic as per original instructions).
    *   Run the script:
        ```bash
        python main_arg.py  # Assuming main_arg.py is the entry point for PDF generation
        ```
    *   Your puzzle book PDF will be generated.

## 📖 How It Works

*   **API (`api.py`)**: Provides endpoints (`/generate`, `/status/{job_id}`) to request puzzle generation and check job status. Uses background tasks for non-blocking generation.
*   **Rust Extension (`wordgrid_solver`)**: Handles the computationally intensive task of finding word placements in the grid, optimized for performance.
*   **Puzzle Generation (`generatePuzzle.py`)**: Orchestrates the puzzle creation using the Rust solver and generates SVG output.
*   **PDF Generation (`main_arg.py`, `index.py`, `appendImage.py`)**: Contains the original logic for creating a complete PDF book (if using the CLI approach).

## 📖 Puzzle Types
- **Normal Puzzle**: A 13x13 word search.
- **Hard Puzzle**: A 17x17 word search with more complexity.
- **Bonus Puzzle**: Special patterns and challenges.

## ❓ FAQ
### What happens if I don’t provide enough words?
The program will still generate puzzles but will warn you about missing words.

### Can I add more topics?
Absolutely! Just add your words in the `Words/words.txt` and rerun the `main.py` script.

## 🧑‍💻 Contributions
Feel free to fork this repository and make a pull request.
