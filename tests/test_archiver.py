"""archiver 模块的单元测试。"""

import os
import tempfile
import unittest

from organizer import archiver, oplog


class ArchiverTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = self.tmp.name
        for name in ["高数作业.pdf", "成绩表.xlsx", "答辩.pptx", "头像.png"]:
            with open(os.path.join(self.folder, name), "w", encoding="utf-8") as f:
                f.write("x")

    def tearDown(self):
        self.tmp.cleanup()

    def _touch(self, name):
        with open(os.path.join(self.folder, name), "w", encoding="utf-8") as f:
            f.write("x")

    def test_category_plan_and_apply(self):
        moves = archiver.plan_archive(self.folder, by="category")
        subs = {m["name"]: m["sub"] for m in moves}
        self.assertEqual(subs["高数作业.pdf"], "文档")
        self.assertEqual(subs["成绩表.xlsx"], "表格")
        self.assertEqual(subs["答辩.pptx"], "演示")
        self.assertEqual(subs["头像.png"], "图片")

        done, _ = archiver.apply_archive(self.folder, moves)
        self.assertEqual(done, 4)
        self.assertTrue(os.path.exists(os.path.join(self.folder, "文档", "高数作业.pdf")))
        self.assertFalse(os.path.exists(os.path.join(self.folder, "高数作业.pdf")))
        # 报告由 write_report 单独生成，且操作已记录可撤销
        report_path = archiver.write_report(self.folder, "category", moves, done)
        self.assertTrue(os.path.exists(report_path))
        self.assertEqual(len(oplog.load(self.folder)), 1)

    def test_semester_plan(self):
        moves = archiver.plan_archive(self.folder, by="semester")
        for m in moves:
            self.assertRegex(m["sub"], r"^\d{4}[春秋]$")

    def test_conflict_not_overwritten(self):
        os.makedirs(os.path.join(self.folder, "文档"))
        self._touch(os.path.join("文档", "高数作业.pdf"))
        moves = archiver.plan_archive(self.folder, by="category")
        bad = [m for m in moves if m["name"] == "高数作业.pdf"][0]
        self.assertIn("已存在", bad["reason"])
        done, _ = archiver.apply_archive(self.folder, moves)
        self.assertEqual(done, 3)
        self.assertTrue(os.path.exists(os.path.join(self.folder, "文档", "高数作业.pdf")))

    def test_undo_restores_files(self):
        moves = archiver.plan_archive(self.folder, by="category")
        archiver.apply_archive(self.folder, moves)
        result = archiver.undo_last(self.folder)
        self.assertEqual(result["restored"], 4)
        self.assertFalse(result["errors"])
        for name in ["高数作业.pdf", "成绩表.xlsx", "答辩.pptx", "头像.png"]:
            self.assertTrue(os.path.exists(os.path.join(self.folder, name)))
        # 空的类别子文件夹应被清理
        self.assertFalse(os.path.exists(os.path.join(self.folder, "文档")))

    def test_undo_no_active_operation(self):
        self.assertIsNone(archiver.undo_last(self.folder))

    def test_undo_twice_only_once(self):
        moves = archiver.plan_archive(self.folder, by="category")
        archiver.apply_archive(self.folder, moves)
        self.assertIsNotNone(archiver.undo_last(self.folder))
        self.assertIsNone(archiver.undo_last(self.folder))


if __name__ == "__main__":
    unittest.main()
