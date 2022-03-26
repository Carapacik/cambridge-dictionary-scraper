import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cambridge_dictionary_scraper.scraper import validate
from cambridge_dictionary_scraper.storage import _replace, write_json, write_lines


class StorageAndValidationTests(unittest.TestCase):
    def temporary_directory(self):
        # Keep test artifacts inside the repository so restricted CI/sandboxes
        # do not need access to the operating system's global temp directory.
        return tempfile.TemporaryDirectory(dir=Path(__file__).parent)

    def test_valid_complete_output(self):
        with self.temporary_directory() as directory:
            root = Path(directory)
            write_lines(root / "words.txt", ["aback", "apple"])
            write_json(root / "word-urls.json", {"aback": "u1", "apple": "u2"})
            write_json(root / "meanings.json", {"aback": "m1", "apple": "m2"})
            write_json(root / "failures.json", {"browse": {}, "meanings": {}})
            write_json(
                root / "checkpoint.json",
                {"completed_letters": list("abcdefghijklmnopqrstuvwxyz")},
            )
            self.assertEqual(validate(root, 5), [])

    def test_failure_accounts_for_missing_meaning(self):
        with self.temporary_directory() as directory:
            root = Path(directory)
            (root / "words.txt").write_text("apple\n", encoding="utf-8")
            (root / "word-urls.json").write_text(json.dumps({"apple": "u"}), encoding="utf-8")
            (root / "meanings.json").write_text("{}", encoding="utf-8")
            (root / "failures.json").write_text(
                json.dumps({"browse": {}, "meanings": {"apple": {"url": "u", "error": "x"}}}),
                encoding="utf-8",
            )
            (root / "checkpoint.json").write_text(
                json.dumps({"completed_letters": list("abcdefghijklmnopqrstuvwxyz")}),
                encoding="utf-8",
            )
            self.assertEqual(validate(root, 5), [])

    def test_atomic_replace_retries_a_brief_windows_lock(self):
        with patch("cambridge_dictionary_scraper.storage.os.replace") as replace, patch(
            "cambridge_dictionary_scraper.storage.time.sleep"
        ):
            replace.side_effect = [PermissionError(), PermissionError(), None]
            _replace("temporary", Path("target"))
            self.assertEqual(replace.call_count, 3)

    def test_accounted_browse_failure_is_valid(self):
        with self.temporary_directory() as directory:
            root = Path(directory)
            write_lines(root / "words.txt", ["apple"])
            write_json(root / "word-urls.json", {"apple": "u"})
            write_json(root / "meanings.json", {"apple": "fruit"})
            write_json(
                root / "failures.json",
                {
                    "browse": {
                        "https://dictionary.cambridge.org/browse/english/g/example/": "403"
                    },
                    "meanings": {},
                },
            )
            write_json(
                root / "checkpoint.json",
                {
                    "completed_letters": [
                        letter for letter in "abcdefghijklmnopqrstuvwxyz" if letter != "g"
                    ]
                },
            )
            self.assertEqual(validate(root, 5), [])


if __name__ == "__main__":
    unittest.main()
