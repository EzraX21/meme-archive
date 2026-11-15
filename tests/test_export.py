# -*- coding: utf-8 -*-
import importlib.util
import os
import tempfile
import unittest

from memearchive import Archive
from memearchive import export as ex

HAS_XLSX = importlib.util.find_spec("openpyxl") is not None


class TestExport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = Archive.load()

    def test_markdown(self):
        text = ex.to_markdown(self.a)
        self.assertIn("# 互联网梗大全", text)
        self.assertIn("共收录 **382** 条", text)
        self.assertIn("#### A01　内卷", text)
        self.assertIn("**相关作品**：甄嬛传", ex.to_markdown(self.a))

    def test_csv(self):
        text = ex.to_csv_text(self.a)
        head = text.splitlines()[0]
        self.assertEqual(head, "序号,分类,梗,释义,出处 / 来源,出处实体,用法示例,年代,热度")
        self.assertEqual(len(text.splitlines()), 383)

    def test_export_md_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            md = ex.export(self.a, "md", os.path.join(tmp, "out.md"))
            csv_path = ex.export(self.a, "csv", os.path.join(tmp, "out.csv"))
            for f in md + csv_path:
                self.assertTrue(os.path.getsize(f) > 1000)

    @unittest.skipUnless(HAS_XLSX, "需要 openpyxl")
    def test_export_all(self):
        with tempfile.TemporaryDirectory() as tmp:
            files = ex.export(self.a, "all", os.path.join(tmp, "out"))
            self.assertEqual(len(files), 3)

    @unittest.skipUnless(HAS_XLSX, "需要 openpyxl")
    def test_xlsx(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = ex.write_xlsx(self.a, os.path.join(tmp, "t.xlsx"))
            self.assertTrue(os.path.getsize(path) > 10000)

    def test_unknown_format(self):
        with self.assertRaises(ValueError):
            ex.export(self.a, "pdf", "x")


if __name__ == "__main__":
    unittest.main()
