"""scanner 模块的单元测试。"""

import os
import tempfile
import unittest

from organizer import scanner


class ScannerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = self.tmp.name
        # 准备测试文件：两个目标扩展名 + 一个干扰文件
        for name, content in [
            ("作业1.docx", "a" * 100),
            ("作业2.pdf", "b" * 2000),
            ("notes.txt", "c"),
            (".hidden", "x"),
        ]:
            with open(os.path.join(self.folder, name), "w", encoding="utf-8") as f:
                f.write(content)

    def tearDown(self):
        self.tmp.cleanup()

    def test_scan_all(self):
        items = scanner.scan_files(self.folder)
        names = {i["name"] for i in items}
        # .hidden 应被默认忽略
        self.assertEqual(names, {"作业1.docx", "作业2.pdf", "notes.txt"})

    def test_scan_filter_by_ext(self):
        items = scanner.scan_files(self.folder, exts=["docx", "pdf"])
        names = {i["name"] for i in items}
        self.assertEqual(names, {"作业1.docx", "作业2.pdf"})

    def test_normalize_exts(self):
        self.assertEqual(scanner.normalize_exts([".PDF", "Docx"]), {"pdf", "docx"})
        self.assertIsNone(scanner.normalize_exts(None))

    def test_recursive(self):
        sub = os.path.join(self.folder, "sub")
        os.makedirs(sub)
        with open(os.path.join(sub, "深层.docx"), "w", encoding="utf-8") as f:
            f.write("deep")
        items = scanner.scan_files(self.folder, exts=["docx"], recursive=True)
        self.assertEqual(len(items), 2)

    def test_human_size(self):
        self.assertEqual(scanner.human_size(500), "500 B")
        self.assertEqual(scanner.human_size(2048), "2.0 KB")
        self.assertEqual(scanner.human_size(3 * 1024 * 1024), "3.0 MB")


if __name__ == "__main__":
    unittest.main()
