#!/usr/bin/env python3
"""Integration + unit tests for omai_feeds.

Run:  python3 -m unittest test_omai_feeds -v
Requires the live server on 127.0.0.1:8099 (systemd omai-feeds.service).
"""
import json
import os
import time
import unittest
import urllib.error
import urllib.request
from urllib.request import urlopen
from urllib.error import HTTPError

import server          # imports sources, loads TOKEN
import sources         # direct free upstreams

BASE = "http://127.0.0.1:8099"


def get(path, timeout=30):
    """Return (status, headers, body) for any status including 4xx/5xx."""
    req = urllib.request.Request(BASE + path)
    try:
        with urlopen(req, timeout=timeout) as r:
            return r.status, dict(r.getheaders()), r.read().decode("utf-8", "replace")
    except HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")


def get_json(path, timeout=30):
    s, h, b = get(path, timeout)
    return s, h, json.loads(b) if b else None


class TestModuleSanity(unittest.TestCase):
    def test_actor_count(self):
        self.assertEqual(len(server.ACTORS), 8)

    def test_cache_ttl(self):
        self.assertEqual(server.CACHE_TTL, 7200)

    def test_token_loaded(self):
        # TOKEN must be non-empty (loaded from hermes config)
        self.assertTrue(server.TOKEN, "APIFY_TOKEN not loaded from ~/.hermes/config.yaml")

    def test_bind_is_loopback(self):
        # the server must NOT be reachable on a non-loopback external interface.
        # Bind a listener on the LAN IP to confirm 8099 is NOT also open there:
        # if it were bound to 0.0.0.0, connect() to the LAN address would succeed.
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        try:
            # 192.168.2.221 is oldpc's LAN IP; if server were on 0.0.0.0 this
            # would connect. With loopback-only bind it must refuse.
            result = s.connect_ex(("192.168.2.221", 8099))
            self.assertNotEqual(result, 0,
                "server is reachable on LAN IP -> bound to 0.0.0.0 (security regression)")
        finally:
            s.close()
        # and the loopback listener must be present
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:8099/health", timeout=5) as r:
            self.assertEqual(r.status, 200)


class TestLiveEndpoints(unittest.TestCase):
    def test_health(self):
        s, h, j = get_json("/health")
        self.assertEqual(s, 200)
        self.assertTrue(j["ok"])
        self.assertEqual(j["actors"], 8)
        self.assertEqual(h.get("Access-Control-Allow-Origin"), "*")

    def test_actors_directory(self):
        s, h, j = get_json("/actors/api")
        self.assertEqual(s, 200)
        self.assertEqual(len(j), 8)
        for entry in j:
            self.assertIn("slug", entry)
            self.assertIn("store", entry)
            self.assertTrue(entry["store"].startswith("https://apify.com/nosytlabs/"))

    def test_actors_landing_html(self):
        s, h, b = get("/actors")
        self.assertEqual(s, 200)
        self.assertIn("text/html", h.get("Content-Type", ""))
        self.assertGreater(len(b), 1000)

    def test_all_feeds_ok(self):
        s, h, j = get_json("/actors/api/all", timeout=60)
        self.assertEqual(s, 200)
        self.assertEqual(j["ok"], 8, f"failed feeds: {j.get('failed')}")
        self.assertEqual(j["failed"], 0)
        self.assertEqual(len(j["feeds"]), 8)
        for slug, val in j["feeds"].items():
            self.assertNotIn("error", val, f"{slug} errored: {val}")
            self.assertIn("data", val)

    def test_each_feed_endpoint(self):
        for slug in server.ACTORS:
            s, h, j = get_json(f"/actors/api/{slug}", timeout=40)
            self.assertEqual(s, 200, slug)
            self.assertEqual(j["actor"], slug)
            self.assertIn("data", j)

    def test_unknown_actor_404(self):
        s, h, j = get_json("/actors/api/does-not-exist")
        self.assertEqual(s, 404)
        self.assertIn("unknown actor", j.get("error", ""))

    def test_site_content_proxy_no_leak(self):
        # /site/content proxies WP REST; must NOT leak 127.0.0.1 anywhere
        s, h, b = get("/site/content", timeout=30)
        self.assertEqual(s, 200)
        self.assertNotIn("127.0.0.1", b, "leaked internal IP in proxied content")
        # body is a JSON array of post objects (real published content)
        import json as _json
        posts = _json.loads(b)
        self.assertIsInstance(posts, list)
        self.assertGreater(len(posts), 0)
        for p in posts[:3]:
            self.assertNotIn("127.0.0.1", _json.dumps(p))


class TestSourcesLive(unittest.TestCase):
    """Hit the real upstream free APIs (no Apify dependency)."""

    def test_fetch_all_structure(self):
        data = sources.fetch_all()
        self.assertIsInstance(data, dict)
        self.assertEqual(set(data.keys()), {"ok", "failed", "generated_at", "feeds"})
        self.assertEqual(set(data["feeds"].keys()), set(server.ACTORS.keys()))
        self.assertEqual(data["ok"] + data["failed"], 8)

    def test_fetch_all_non_empty(self):
        data = sources.fetch_all()
        for slug, val in data["feeds"].items():
            self.assertIsInstance(val, dict, f"{slug} not a dict: {type(val)}")
            # either real data (no 'error' key) or an explicit error dict
            if "error" in val:
                # tolerate transient upstream throttle in live runs
                if "429" in val["error"] or "Too Many Requests" in val["error"]:
                    self.skipTest(f"{slug}: upstream rate-limited (429) — not an app defect")
                continue
            self.assertTrue(len(val) > 0, f"{slug} returned empty dict")

    def test_coingecko_shape(self):
        try:
            cg = sources.coingecko()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                self.skipTest(f"CoinGecko rate-limited (429) — upstream throttle, not an app defect")
            raise
        self.assertIsInstance(cg, dict)
        self.assertIn("global_mcap_usd", cg)
        self.assertIn("btc_dominance", cg)
        self.assertIn("top_coins", cg)
        self.assertIsInstance(cg["top_coins"], list)

    def test_gas_numeric(self):
        g = sources.gas()
        self.assertIsInstance(g, dict)
        self.assertIn("eth_gwei", g)
        self.assertIn("base_gwei", g)

    def test_non_retryable_error_still_raises(self):
        # A 404 (non-retryable) must raise immediately and not hang in a retry loop
        import urllib.error
        with self.assertRaises(urllib.error.HTTPError):
            sources._get("https://www.python.org/nonexistent-404-page")



if __name__ == "__main__":
    unittest.main(verbosity=2)
