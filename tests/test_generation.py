import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import generatePuzzle
from Words.rawWordToJSON import word_to_json


class GenerationTests(unittest.TestCase):
    def test_json_output_path_is_used(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "words.txt"
            target = Path(directory) / "nested" / "words.json"
            source.write_text("> TOPIC\nALPHA\nBRAVO\nCHARLIE\nDELTA\nECHO\nFOXTROT\nGOLF\nHOTEL\nINDIA\nJULIET\n")
            word_to_json(source, target, num_normal=1, num_hard=0,
                         bonus_normal=0, bonus_hard=0)
            self.assertEqual(len(json.loads(target.read_text())["TOPIC"]["Normal"]), 1)

    def test_failures_keep_full_filename_and_bonus_size(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = {
                f"Topic {n}": {"Normal": [], "Hard": [],
                               "Bonus": {"Normal": [["ALPHA"]], "Hard": [["BRAVO"]]}}
                for n in range(1, 11)
            }
            source = root / "words.json"
            source.write_text(json.dumps(data))
            output = root / "puzzles"
            with patch.object(generatePuzzle, "create_transition_svg"), patch.object(
                generatePuzzle, "create_puzzle_and_solution", side_effect=lambda filename, *a, **kw: filename
            ) as create:
                failures = generatePuzzle.create_all_puzzles(source, None, output)
                self.assertEqual(len(failures), 20)
                self.assertEqual(failures[-2][4], "10BN1")
                self.assertEqual(failures[-2][2], 13)
                self.assertEqual(failures[-1][2], 17)
                create.side_effect = lambda *a, **kw: None
                self.assertEqual(generatePuzzle.create_individual_puzzle(failures, output, None), [])
                self.assertEqual(create.call_args.kwargs["page_number"], "10BH1")


if __name__ == "__main__":
    unittest.main()
