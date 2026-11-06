import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

SPEC = importlib.util.spec_from_file_location(
    "fetch", Path(__file__).resolve().parents[1] / "scripts" / "fetch.py"
)
fetch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fetch)


class FetchTests(unittest.TestCase):
    def test_save_and_reject_malformed_responses(self):
        dept = {"id": "CI", "name": "資電學院"}
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(fetch, "ROOT", Path(tmp)),
            patch.object(fetch, "post") as post,
        ):
            path = Path(tmp) / "115" / "1151-1-CI.json"
            post.return_value = {"total": 1, "items": [{"scr_selcode": "1"}]}
            self.assertEqual(fetch.fetch_dept(None, 115, "1", "1", dept), 1)
            original = path.read_bytes()
            for response in (None, [], {}, {"total": 1, "items": []}):
                post.return_value = response
                self.assertIsNone(fetch.fetch_dept(None, 115, "1", "1", dept))
                self.assertEqual(path.read_bytes(), original)

    def test_failed_list_and_partial_fetch_fail_the_year(self):
        with patch.object(fetch, "post", return_value=None):
            with self.assertRaises(RuntimeError):
                fetch.fetch_year(None, 115)
        with (
            patch.object(fetch, "post", return_value=[{"id": "CI", "name": "資電"}]),
            patch.object(fetch, "fetch_dept", return_value=None),
        ):
            with self.assertRaises(RuntimeError):
                fetch.fetch_year(None, 115)

    def test_empty_semesters_are_valid(self):
        with patch.object(fetch, "post", return_value=[]):
            self.assertEqual(fetch.fetch_year(None, 115), 0)

    def test_main_does_not_build_after_partial_failure(self):
        with (
            patch("sys.argv", ["fetch.py", "-y", "115"]),
            patch.object(fetch, "make_session", return_value=Mock()),
            patch.object(fetch, "fetch_year", side_effect=RuntimeError("partial")),
            patch.object(fetch.subprocess, "run") as build,
        ):
            self.assertEqual(fetch.main(), 1)
            build.assert_not_called()


if __name__ == "__main__":
    unittest.main()
