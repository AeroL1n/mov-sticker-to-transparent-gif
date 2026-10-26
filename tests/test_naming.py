"""Naming and exclusive-copy tests. No user MOV media is needed or altered."""
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sticker_converter", ROOT / "scripts/convert_stickers.py")
converter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(converter)


class NamingTests(unittest.TestCase):
    def test_version_and_folders(self):
        self.assertEqual(converter.VERSION, "2.3.0")
        self.assertEqual([converter.size_folder(s) for s in converter.SIZES],
                         ["120gif", "220gif", "330gif"])

    def test_chinese_names(self):
        with tempfile.TemporaryDirectory() as d:
            used = set()
            self.assertEqual(converter.pick_name("比心", used, Path(d)), "比心")
            self.assertEqual(converter.pick_name("比心", used, Path(d)), "比心_2")
            self.assertEqual(converter.pick_name("比心", used, Path(d)), "比心_3")

    def test_casefold_names(self):
        with tempfile.TemporaryDirectory() as d:
            used = set()
            self.assertEqual(converter.pick_name("Face", used, Path(d)), "Face")
            self.assertEqual(converter.pick_name("face", used, Path(d)), "face_2")

    def test_all_eighteen_legacy_and_new_conflicts(self):
        for size in converter.SIZES:
            for folder in (f"{size}gif", f"{size}x{size}", f"{size}x{size}gif"):
                for name in ("比心.gif", f"比心_{size}x{size}.gif"):
                    with self.subTest(folder=folder, name=name), tempfile.TemporaryDirectory() as d:
                        root = Path(d)
                        target = root / folder / name
                        target.parent.mkdir()
                        target.write_bytes(b"existing-file")
                        before = hashlib.sha256(target.read_bytes()).digest()
                        self.assertEqual(converter.pick_name("比心", set(), root), "比心_2")
                        self.assertEqual(hashlib.sha256(target.read_bytes()).digest(), before)

    def test_unsafe_characters(self):
        self.assertEqual(converter.safe_name('比/心:好?'), '比_心_好_')
        for invalid in ("", " . ", ".."):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                converter.safe_name(invalid)

    def test_exclusive_copy(self):
        with tempfile.TemporaryDirectory() as d:
            src, dst = Path(d)/"source", Path(d)/"target"
            src.write_bytes(b"source-data")
            converter.copy_exclusive(src, dst)
            self.assertEqual(dst.read_bytes(), b"source-data")
            src.write_bytes(b"new-data")
            with self.assertRaises(FileExistsError):
                converter.copy_exclusive(src, dst)
            self.assertEqual(dst.read_bytes(), b"source-data")


if __name__ == "__main__":
    unittest.main()
