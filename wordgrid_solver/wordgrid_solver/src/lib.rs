use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use rand::seq::{SliceRandom, IteratorRandom}; // Import necessary traits
use rand::thread_rng;
use std::collections::HashMap;

// Represents a position on the grid
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)] // Add PartialEq, Eq, Hash
struct Position {
    row: usize,
    col: usize,
}

// Represents a placed word's location
#[derive(Clone, Debug)]
struct WordPlacement {
    word: String, // The actual word placed
    start: Position,
    end: Position,
}

// Constants
const EMPTY_CELL: char = '\0'; // Using null char for empty
const MASK_CELL: char = '*'; // Or another marker if needed
const ALPHABET: &[char] = &[
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
    'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
];

// --- Helper Functions ---

// Check if a word can be placed at a given position and direction
fn test_candidate(
    grid: &Vec<Vec<char>>,
    nrows: usize,
    ncols: usize,
    word: &str,
    pos: Position,
    dr: isize, // Delta row (-1, 0, 1)
    dc: isize, // Delta col (-1, 0, 1)
) -> bool {
    let mut current_row = pos.row as isize;
    let mut current_col = pos.col as isize;

    for ch in word.chars() {
        // Check bounds
        if current_row < 0 || current_row >= nrows as isize || current_col < 0 || current_col >= ncols as isize {
            return false; // Out of bounds
        }

        let grid_char = grid[current_row as usize][current_col as usize];

        // Check for conflicts or mask
        if grid_char != EMPTY_CELL && grid_char != ch {
            return false; // Conflict with existing letter
        }
        if grid_char == MASK_CELL { // Assuming MASK_CELL means cannot place here
             return false;
        }

        // Move to the next position
        current_row += dr;
        current_col += dc;
    }
    true // Word fits
}

// Place the word onto the grid
fn place_word_on_grid(
    grid: &mut Vec<Vec<char>>,
    word: &str,
    start_pos: Position,
    dr: isize,
    dc: isize,
) -> Position { // Returns the end position
    let mut current_row = start_pos.row as isize;
    let mut current_col = start_pos.col as isize;
    let mut end_pos = start_pos; // Initialize end_pos

    for (i, ch) in word.chars().enumerate() {
         // Bounds check should ideally be done by test_candidate, but double-check is safe
         if current_row >= 0 && current_row < grid.len() as isize &&
            current_col >= 0 && current_col < grid[0].len() as isize {
            grid[current_row as usize][current_col as usize] = ch;
            if i == word.len() - 1 { // Last character determines end position
                end_pos = Position { row: current_row as usize, col: current_col as usize };
            }
         }

        // Move to the next position
        current_row += dr;
        current_col += dc;
    }
    end_pos
}

// --- Core Backtracking Logic ---
fn solve_grid(
    nrows: usize,
    ncols: usize,
    words: &[String], // Use slices for borrowing
    allow_backwards: bool,
    _mask_type: Option<String>, // Mask logic not implemented yet
) -> Option<(Vec<Vec<char>>, HashMap<String, (usize, usize, usize, usize)>)> {
    let mut grid = vec![vec![EMPTY_CELL; ncols]; nrows];
    let mut positions = HashMap::new();
    let mut rng = thread_rng();

    // Define possible directions (delta_row, delta_col)
    let mut directions = vec![
        (0, 1), (1, 0), (1, 1), (0, -1), (-1, 0), (-1, -1), (1, -1), (-1, 1)
    ];
    if !allow_backwards {
        directions.truncate(3); // Keep only right, down, down-right
    }

    // Attempt to place each word
    // Shuffle words for randomness
    let mut words_shuffled = words.to_vec();
    words_shuffled.shuffle(&mut rng);

    for word in &words_shuffled {
        let word_len = word.len();
        if word_len == 0 { continue; } // Skip empty strings

        let mut placed = false;
        // Generate all possible start positions and shuffle them
        let mut possible_starts: Vec<Position> = (0..nrows)
            .flat_map(|r| (0..ncols).map(move |c| Position { row: r, col: c }))
            .collect();
        possible_starts.shuffle(&mut rng);

        'placement_attempts: for start_pos in possible_starts {
            // Shuffle directions for this attempt
            directions.shuffle(&mut rng);

            for &(dr, dc) in &directions {
                 // Check if the word fits within bounds *before* calling test_candidate
                 let end_row = start_pos.row as isize + dr * (word_len as isize - 1);
                 let end_col = start_pos.col as isize + dc * (word_len as isize - 1);

                 if end_row >= 0 && end_row < nrows as isize && end_col >= 0 && end_col < ncols as isize {
                    if test_candidate(&grid, nrows, ncols, word, start_pos, dr, dc) {
                        let end_pos = place_word_on_grid(&mut grid, word, start_pos, dr, dc);
                        // Store position as (start_col, start_row, end_col, end_row) for consistency
                        positions.insert(word.clone(), (start_pos.col, start_pos.row, end_pos.col, end_pos.row));
                        placed = true;
                        break 'placement_attempts; // Word placed, move to the next word
                    }
                 }
            }
        }

        if !placed {
            // If any word cannot be placed, the generation fails
            // println!("Failed to place word: {}", word); // Debugging
            return None;
        }
    }

    // Fill empty cells with random letters
    for r in 0..nrows {
        for c in 0..ncols {
            if grid[r][c] == EMPTY_CELL {
                grid[r][c] = *ALPHABET.choose(&mut rng).unwrap_or(&' '); // Fill with random letter or space
            }
        }
    }

    Some((grid, positions))
}

// --- Python Callable Function ---
#[pyfunction]
#[pyo3(signature = (nrows, ncols, word_list, allow_backwards=true, mask=None))]
fn generate_word_grid_rust(
    py: Python<'_>, // Acquire GIL
    nrows: usize,
    ncols: usize,
    word_list: Bound<'_, PyList>, // Use Bound<PyList> for argument
    allow_backwards: bool,
    mask: Option<String>,
) -> PyResult<PyObject> { // Return PyResult<PyObject> for tuple or None

    // 1. Convert Python word list (Bound<PyList>) to Rust Vec<String>
    let words: Vec<String> = word_list.extract()?;

    // Clean words (uppercase, remove spaces) - important!
    let cleaned_words: Vec<String> = words.iter()
                                        .map(|w| w.replace(" ", "").to_uppercase())
                                        .filter(|w| !w.is_empty())
                                        .collect();

    if cleaned_words.is_empty() {
        // Handle case with no valid words
        let empty_grid = PyList::empty_bound(py);
        let empty_positions = PyDict::new_bound(py);
         return Ok((empty_grid, empty_positions).to_object(py));
    }

    // 2. Call the core Rust solver function
    // Use py.allow_threads to release the GIL while Rust code runs
    // Retry logic (optional, but good for stochastic algorithms)
    const MAX_ATTEMPTS: u32 = 10; // Try a few times before giving up
    let mut result = None;
    for _ in 0..MAX_ATTEMPTS {
         result = py.allow_threads(|| {
            solve_grid(nrows, ncols, &cleaned_words, allow_backwards, mask.clone()) // Clone mask if needed inside thread
        });
         if result.is_some() {
             break; // Found a solution
         }
    }

    // 3. Process the result and convert back to Python objects
    match result {
        Some((grid_vec, positions_map)) => {
            // Convert grid Vec<Vec<char>> to Python list of lists
            let py_grid = PyList::empty_bound(py);
            for row_vec in grid_vec {
                 let py_row = PyList::new_bound(py, row_vec.iter().map(|&c| {
                    if c == EMPTY_CELL { " ".to_string() } else { c.to_string() } // Convert EMPTY_CELL back to space
                }));
                py_grid.append(&py_row)?;
            }

            // Convert positions HashMap<String, (usize, usize, usize, usize)> to Python dict
            let py_positions = PyDict::new_bound(py);
            for (word, pos_tuple) in positions_map {
                py_positions.set_item(word, pos_tuple)?;
            }

            // Return a Python tuple: (grid, positions)
            Ok((py_grid, py_positions).to_object(py))
        }
        None => {
            // Return Python None if the solver failed after attempts
             Ok(py.None())
        }
    }
}

// --- Python Module Definition ---
#[pymodule]
fn wordgrid_solver(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(generate_word_grid_rust, m)?)?;
    Ok(())
}
