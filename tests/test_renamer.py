"""renamer 模块的单元测试。"""

import os
import tempfile
import unittest

from organizer import renamer


class RenamerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = self.tmp.name
        for name in ["20230101_张三_高数作业.pdf", "20230202_李四_英语作业.docx"]:
            with open(os.path.join(self.folder, name), "w", encoding="utf-8") as f:
                f.write("x")

    def tearDown(self):
        self.tmp.cleanup()

    def _touch(self, name):
        with open(os.path.join(self.folder, name), "w", encoding="utf-8") as f:
            f.write("x")

    def test_parse_rule_rejects_unknown_token(self):
        with self.assertRaises(ValueError):
            renamer.parse_rule("学号_姓名_作业名", "作业名_课程")

    def test_parse_rule_rejects_duplicate_token(self):
        with self.assertRaises(ValueError):
            renamer.parse_rule("学号_学号_作业名", "作业名_学号")

    def test_plan_and_apply(self):
        plans = renamer.plan_renames(self.folder, "学号_姓名_作业名", "作业名_学号")
        targets = {p["old"]: p["new"] for p in plans}
        self.assertEqual(targets["20230101_张三_高数作业.pdf"], "高数作业_20230101.pdf")
        self.assertEqual(targets["20230202_李四_英语作业.docx"], "英语作业_20230202.docx")

        done, _ = renamer.apply_renames(self.folder, plans)
        self.assertEqual(done, 2)
        self.assertTrue(os.path.exists(os.path.join(self.folder, "高数作业_20230101.pdf")))
        # 操作日志已记录，可供撤销
        self.assertEqual(len(renamer.oplog.load(self.folder)), 1)

    def test_conflict_skip_by_default(self):
        self._touch("高数作业_20230101.pdf")  # 预先放一个同名目标文件
        plans = renamer.plan_renames(self.folder, "学号_姓名_作业名", "作业名_学号")
        conflicted = [p for p in plans if p["old"] == "20230101_张三_高数作业.pdf"][0]
        self.assertIsNone(conflicted["new"])
        self.assertIn("已存在", conflicted["reason"])
        # 原文件不能被覆盖
        self.assertTrue(os.path.exists(os.path.join(self.folder, "20230101_张三_高数作业.pdf")))

    def test_conflict_suffix(self):
        self._touch("高数作业_20230101.pdf")
        plans = renamer.plan_renames(
            self.folder, "学号_姓名_作业名", "作业名_学号", on_conflict="suffix")
        conflicted = [p for p in plans if p["old"] == "20230101_张三_高数作业.pdf"][0]
        self.assertEqual(conflicted["new"], "高数作业_20230101-1.pdf")

    def test_wrong_segment_count_skipped(self):
        self._touch("只有一个名字.pdf")
        plans = renamer.plan_renames(self.folder, "学号_姓名_作业名", "作业名_学号")
        bad = [p for p in plans if p["old"] == "只有一个名字.pdf"][0]
        self.assertIsNone(bad["new"])
        self.assertIn("段", bad["reason"])

    def test_target_format_file_is_skipped(self):
        # 已经是目标格式的文件段数与新规则不符，应被跳过且原样保留
        self._touch("高数作业_20230101.pdf")
        plans = renamer.plan_renames(self.folder, "学号_姓名_作业名", "作业名_学号")
        ok = [p for p in plans if p["old"] == "高数作业_20230101.pdf"][0]
        self.assertIsNone(ok["new"])
        self.assertIn("段", ok["reason"])
        self.assertTrue(os.path.exists(os.path.join(self.folder, "高数作业_20230101.pdf")))


if __name__ == "__main__":
    unittest.main()
