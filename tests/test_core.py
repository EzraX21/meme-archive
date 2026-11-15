# -*- coding: utf-8 -*-
import unittest

from memearchive import Archive


class TestArchive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = Archive.load()

    def test_total(self):
        self.assertEqual(len(self.a.items), 382)

    def test_categories(self):
        ids = [c.id for c in self.a.categories]
        self.assertEqual(ids, list("ABCDEFGHIJ"))

    def test_unique_ids_and_terms(self):
        ids = [m.id for m in self.a.items]
        terms = [m.term for m in self.a.items]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(terms), len(set(terms)))

    def test_fields(self):
        for m in self.a.items:
            with self.subTest(term=m.term):
                self.assertTrue(m.term and m.meaning and m.origin and m.example)
                self.assertTrue(1 <= m.heat <= 5)
                self.assertIn(m.cat, [c.id for c in self.a.categories])

    def test_get(self):
        self.assertEqual(self.a.get("A01").term, "内卷")
        self.assertEqual(self.a.get("内卷").id, "A01")
        self.assertIsNone(self.a.get("不存在的梗"))

    def test_search(self):
        hits = self.a.search("破防")
        self.assertTrue(hits)
        self.assertEqual(hits[0].term, "破防")

    def test_select(self):
        self.assertEqual(len(self.a.select(cat="A")), 60)
        self.assertEqual(len(self.a.select(cat="A,J")), 92)
        self.assertEqual(len(self.a.select(min_heat=5)), 61)

    def test_random(self):
        picked = self.a.random(3, cat="H")
        self.assertEqual(len(picked), 3)
        self.assertTrue(all(m.cat == "H" for m in picked))

    def test_sources(self):
        ids = {s.id for s in self.a.sources}
        self.assertGreater(len(ids), 50)
        for m in self.a.items:
            self.assertIn(m.source, ids)
        self.assertEqual(sum(n for _, n in self.a.source_counts()), 382)

    def test_source_filter(self):
        self.assertEqual(len(self.a.select(source="zhenhuan")), 4)
        self.assertEqual(len(self.a.select(source="甄嬛传")), 4)

    def test_pinyin(self):
        self.assertEqual(self.a.search("neijuan")[0].id, "A01")
        self.assertEqual(self.a.get("pofang").id, "A06")
        self.assertIn("内卷", [m.term for m in self.a.match_pinyin("nj")])
        self.assertEqual(len(self.a.pinyin), 382)

    def test_stats(self):
        s = self.a.stats()
        self.assertEqual(s["total"], 382)
        self.assertEqual(sum(s["categories"].values()), 382)
        self.assertEqual(sum(s["eras"].values()), 382)


if __name__ == "__main__":
    unittest.main()
