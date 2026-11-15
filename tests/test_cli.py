# -*- coding: utf-8 -*-
import contextlib
import io
import unittest

from memearchive.cli import main


def run(*argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        code = main(list(argv))
    return code, buf.getvalue()


class TestCLI(unittest.TestCase):
    def test_no_args_shows_help(self):
        code, out = run()
        self.assertEqual(code, 0)
        self.assertIn("usage: meme", out)

    def test_stats(self):
        code, out = run("stats")
        self.assertEqual(code, 0)
        self.assertIn("共 382 条", out)

    def test_search_hit(self):
        code, out = run("search", "破防")
        self.assertEqual(code, 0)
        self.assertIn("破防", out)

    def test_search_miss(self):
        code, _ = run("search", "zzzz-not-found")
        self.assertEqual(code, 1)

    def test_show_by_id(self):
        code, out = run("show", "A01")
        self.assertEqual(code, 0)
        self.assertIn("内卷", out)

    def test_show_miss(self):
        code, _ = run("show", "不存在的梗xyz")
        self.assertEqual(code, 1)

    def test_list_json(self):
        code, out = run("list", "--cat", "G", "-n", "2", "--json")
        self.assertEqual(code, 0)
        self.assertTrue(out.strip().startswith("["))

    def test_pinyin_search(self):
        code, out = run("search", "neijuan")
        self.assertEqual(code, 0)
        self.assertIn("内卷", out)

    def test_sources(self):
        code, out = run("sources", "--type", "film")
        self.assertEqual(code, 0)
        self.assertIn("让子弹飞", out)

    def test_random(self):
        code, out = run("random", "-n", "2", "--cat", "H")
        self.assertEqual(code, 0)
        self.assertGreaterEqual(len(out.strip().splitlines()), 6)

    def test_fortune(self):
        code, out = run("fortune", "-n", "3")
        self.assertEqual(code, 0)
        self.assertEqual(len([line for line in out.splitlines() if line.strip()]), 3)


if __name__ == "__main__":
    unittest.main()
