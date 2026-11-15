# -*- coding: utf-8 -*-
import unittest

from memearchive import fortune


class TestFortune(unittest.TestCase):
    def test_load(self):
        entries = fortune.load()
        self.assertEqual(len(entries), 60)
        self.assertEqual(len(entries), len(set(entries)))
        for e in entries:
            self.assertTrue(e.strip())

    def test_draw(self):
        got = fortune.draw(5)
        self.assertEqual(len(got), 5)
        self.assertEqual(len(set(got)), 5)

    def test_separator_stripped(self):
        entries = fortune.load()
        self.assertFalse(any(e.startswith("%") for e in entries))


if __name__ == "__main__":
    unittest.main()
