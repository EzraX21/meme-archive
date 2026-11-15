# -*- coding: utf-8 -*-
import json
import threading
import unittest
import urllib.error
import urllib.request

from memearchive import Archive
from memearchive.server import create_server


class TestServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = Archive.load()
        cls.httpd = create_server(cls.archive, "127.0.0.1", 0, quiet=True)
        cls.port = cls.httpd.server_port
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=3)

    def get(self, path):
        url = f"http://127.0.0.1:{self.port}{path}"
        with urllib.request.urlopen(url, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))

    def get_error(self, path, method="GET"):
        url = f"http://127.0.0.1:{self.port}{path}"
        req = urllib.request.Request(url, method=method)
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=5)
        err = ctx.exception
        try:
            body = err.read().decode("utf-8")
        finally:
            err.close()
        return err.code, json.loads(body)

    def test_health(self):
        status, data = self.get("/health")
        self.assertEqual(status, 200)
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["total"], 382)

    def test_index(self):
        status, data = self.get("/")
        self.assertEqual(status, 200)
        self.assertIn("endpoints", data)

    def test_memes_pagination(self):
        _, page1 = self.get("/memes?limit=5&offset=0")
        _, page2 = self.get("/memes?limit=5&offset=5")
        self.assertEqual(page1["total"], 382)
        self.assertEqual(page1["count"], 5)
        self.assertEqual(len(page1["items"]), 5)
        self.assertNotEqual(page1["items"][0]["id"], page2["items"][0]["id"])

    def test_meme_by_id(self):
        _, data = self.get("/memes/A01")
        self.assertEqual(data["term"], "内卷")
        self.assertEqual(data["category_name"], "流行语·社会情绪")

    def test_search(self):
        _, data = self.get("/memes?q=pofang")
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["items"][0]["term"], "破防")

    def test_source_filter(self):
        _, data = self.get("/memes?source=zhenhuan")
        self.assertEqual(data["total"], 4)
        self.assertTrue(all(m["source"] == "zhenhuan" for m in data["items"]))

    def test_sources(self):
        _, data = self.get("/sources?type=game&limit=3")
        self.assertEqual(data["total"], 15)
        self.assertTrue(all(s["type"] == "game" for s in data["items"]))

    def test_source_detail(self):
        _, data = self.get("/sources/zhenhuan")
        self.assertEqual(data["name"], "甄嬛传")
        self.assertEqual(data["total"], 4)

    def test_categories(self):
        _, data = self.get("/categories")
        self.assertEqual(len(data["items"]), 10)
        self.assertEqual(data["items"][0]["total"], 60)

    def test_stats(self):
        _, data = self.get("/stats")
        self.assertEqual(data["total"], 382)
        self.assertEqual(sum(data["by_category"].values()), 382)

    def test_fortune(self):
        _, data = self.get("/fortune?n=3")
        self.assertEqual(len(data["items"]), 3)

    def test_404(self):
        code, data = self.get_error("/nope")
        self.assertEqual(code, 404)
        self.assertEqual(data["error"]["code"], "not_found")

    def test_405(self):
        code, data = self.get_error("/memes", method="POST")
        self.assertEqual(code, 405)
        self.assertEqual(data["error"]["code"], "method_not_allowed")

    def test_bad_limit(self):
        code, data = self.get_error("/memes?limit=abc")
        self.assertEqual(code, 400)
        self.assertEqual(data["error"]["code"], "invalid_param")


if __name__ == "__main__":
    unittest.main()
