# BOOP — Book Of Organized Puzzles

> **Archived CLI project.** [BOOP-web](https://github.com/Muneer320/BOOP-web) is the maintained version.

BOOP generates a PDF book of word-search puzzles from a topic-organized word list. This repository preserves the original command-line implementation. It is archived because the web version now carries the active development.

## Run the CLI

Python 3.12 or newer is required. From the repository root:

```bash
python -m pip install -r requirements.txt
python main.py
```

The interactive command reads `Words/words.txt`, generates `Words/words.json`, and writes `Where's Word-o.pdf` and puzzle SVGs in `generated_puzzles/`. Starting from puzzle 1 replaces an existing book with the same name. A later starting number appends to that book.

For command-line options, run `python main_arg.py --help`. For example:

```bash
python main_arg.py --name MyBook --words-file Words/words.txt --json-file output/words.json --output output/puzzles
```

`main_arg.py` replaces an existing PDF with the same name. The default counts per topic are 10 Normal, 5 Hard, 1 Bonus Normal and 1 Bonus Hard puzzle. Normal grids are 13×13; Hard grids are 17×17. Each Normal puzzle needs 10 words of 4–11 characters; each Hard puzzle needs 15 words of 6–15 characters. With the default counts, a topic needs at least 110 Normal-eligible and 90 Hard-eligible words. A word may qualify for both pools.

If a topic lacks enough words, generation stops with an error. A puzzle that cannot be placed is retried; if it still fails, the book is left incomplete and the command reports failure.

## Input format

`Words/words.txt` contains a topic line beginning with `>`, followed by one word or phrase per line. Separate topics with a line of 20 equals signs (`====================`). See the bundled input for an example.

## History and credit

This is the original Python CLI that preceded BOOP-web. Its word-placement routine was adapted from Christian Hill's [Making a word search puzzle in Python](https://scipython.com/blog/making-a-word-search-puzzle-in-python/). The PDF assembly, topic handling and book layout were developed for BOOP.

The legacy PDF dependencies remain pinned for reproducibility. Topic names outside Latin-1 may fail in the title page. Use BOOP-web for current development and support.
