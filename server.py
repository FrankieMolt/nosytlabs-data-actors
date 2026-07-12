#!/usr/bin/env python3
"""omai_feeds - NosytLabs Apify actor landing + OMA-AI data-feed proxy.
Stdlib-only HTTP server. Serves:
  /                -> actors landing page (links to Apify Store, drives traffic)
  /api/<slug>      -> latest succeeded run dataset items for an actor (OMA-AI feed)
  /api             -> actor directory JSON
  /health          -> ok
Run: python3 server.py  (listens :8099)
"""
import json, os, re, time, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import sources  # direct free live sources (no Apify dependency)

# Load APIFY_TOKEN from hermes config
_CFG = os.path.expanduser("~/.hermes/config.yaml")
TOKEN = ""
try:
    TOKEN = re.search(r"APIFY_TOKEN:\s*(\S+)", open(_CFG).read()).group(1)
except Exception:
    pass

ACTORS = {
    "coingecko-market-data": ("mJQwWzfhYiKTHM8FX", "CoinGecko Market Data Scraper",
        "Live CoinGecko market cap, trending, categories, exchange volumes & global metrics.", 0.35),
    "crypto-fear-greed-index": ("IQKMfHXaUqJ5wEQau", "Crypto Fear & Greed Index Scraper",
        "Real-time & historical Crypto Fear & Greed Index (0-100) from alternative.me.", 0.25),
    "crypto-news-aggregator": ("EMbIWhOacp0q0YJMI", "Crypto News Aggregator",
        "Aggregates crypto news from CoinDesk, Cointelegraph & CryptoSlate RSS, deduplicated.", 0.30),
    "base-mempool-monitor": ("or2qRXWQR4T6T2YZP", "Base Mempool Monitor",
        "Monitor Base mempool via QuickNode RPC: pending tx, gas, block activity.", 0.40),
    "defi-llama-yields": ("luOMdtiraTCwZ38ID", "DeFiLlama Yields Scraper",
        "DeFiLlama yield pools across chains: APY, TVL, protocol & risk tier.", 0.35),
    "defi-tvl-monitor": ("OPbUn6gNess2bQDCF", "DeFi TVL Monitor",
        "DeFi protocol TVL, 24h/7d changes & chain distribution from DeFiLlama.", 0.35),
    "ethereum-gas-tracker": ("EKqGYCov3g5QjlHw3", "Ethereum Gas Tracker",
        "Real-time ETH/Base/Arbitrum gas via Etherscan. Slow/standard/fast gwei.", 0.25),
    "polymarket-data": ("dcdMpgL8uIIU0ewIa", "Polymarket Data Scraper",
        "Polymarket markets, odds, volume & events for prediction-market dashboards.", 0.30),
}

CACHE = {}
CACHE_TTL = 7200  # 2 hours
CACHE_LOCK = threading.Lock()

STORE = "https://apify.com/nosytlabs/"

def _api(path):
    req = Request("https://api.apify.com/v2" + path,
                  headers={"Authorization": f"Bearer {TOKEN}"})
    with urlopen(req, timeout=25) as r:
        return json.loads(r.read())

def get_feed(slug):
    """Return (data, error) for a feed slug.

    Live data comes from direct free sources (sources.FEEDS). This is
    always real and costs nothing. The Apify actors are a separate paid
    wrapper and are NOT required for the feed to function.

    Results are cached per-feed (CACHE_TTL) so we don't hammer the
    free upstreams on every page load / poll.
    """
    if slug not in sources.FEEDS:
        return None, "unknown feed slug"
    with CACHE_LOCK:
        if slug in CACHE and time.time() - CACHE[slug][1] < CACHE_TTL:
            return CACHE[slug][0], None
    try:
        data = sources.FEEDS[slug]()
        with CACHE_LOCK:
            CACHE[slug] = (data, time.time())
        return data, None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"[:160]

class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)
    WP = "http://127.0.0.1:8081"

    def _proxy_wp(self, internal_path=None):
        # proxy to WordPress on 8081, preserving Host so WP generates
        # correct absolute URLs (its siteurl is http://127.0.0.1)
        url = self.WP + (internal_path if internal_path else self.path)
        fwd = {k: v for k, v in self.headers.items()
               if k.lower() not in ("connection",)}
        fwd["Host"] = "lethometry.com"
        try:
            req = Request(url, headers=fwd)
            with urlopen(req, timeout=20) as r:
                body = r.read()
                self.send_response(r.status)
                for k, v in r.getheaders():
                    if k.lower() in ("transfer-encoding", "connection", "location"):
                        continue
                    self.send_header(k, v)
                loc = r.headers.get("Location")
                if loc:
                    self.send_header("Location", loc.replace("http://127.0.0.1", "https://lethometry.com").replace("http://127.0.0.1:8081", "https://lethometry.com"))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body)
        except HTTPError as e:
            body = e.read()
            self.send_response(e.code)
            for k, v in e.headers.items():
                if k.lower() in ("transfer-encoding", "connection", "location"):
                    continue
                self.send_header(k, v)
            loc = e.headers.get("Location")
            if loc:
                self.send_header("Location", loc.replace("http://127.0.0.1", "https://lethometry.com"))
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(body[:500])
        except Exception as e:
            self._send(502, json.dumps({"error": f"wp proxy: {e}"}))

    def do_GET(self):
        p = self.path.split("?")[0].rstrip("/")
        if p in ("", "/"):
            return self._proxy_wp()
        if p == "/health":
            self._send(200, json.dumps({"ok": True, "actors": len(ACTORS)}))
            return
        if p == "/site/content":
            # expose the site's real published content (WP REST posts)
            return self._proxy_wp(
                "/wp-json/wp/v2/posts?per_page=20&_fields=id,date,link,title,excerpt,categories")
        if p.startswith("/actors"):
            if p in ("/actors", "/actors/"):
                try:
                    html = open(os.path.join(os.path.dirname(__file__), "actors.html")).read()
                    self._send(200, html, "text/html")
                except Exception as e:
                    self._send(500, json.dumps({"error": str(e)}))
                return
            if p == "/actors/api":
                dir_ = [{"slug": s, "id": v[0], "name": v[1], "price": v[3],
                         "store": STORE + s} for s, v in ACTORS.items()]
                self._send(200, json.dumps(dir_, indent=1))
                return
            if p == "/actors/api/all":
                out = {}
                ok, fail = 0, 0
                for s in ACTORS:
                    data, err = get_feed(s)
                    if err:
                        out[s] = {"error": err}
                        fail += 1
                    else:
                        out[s] = {"count": len(data) if isinstance(data, list) else 1,
                                  "data": data}
                        ok += 1
                self._send(200, json.dumps({"ok": ok, "failed": fail,
                                            "generated_at": int(time.time()),
                                            "feeds": out}))
                return
            if p.startswith("/actors/api/"):
                slug = p[len("/actors/api/"):]
                if slug not in ACTORS:
                    self._send(404, json.dumps({"error": "unknown actor", "known": list(ACTORS)}))
                    return
                data, err = get_feed(slug)
                if err:
                    self._send(502, json.dumps({"error": err}))
                else:
                    self._send(200, json.dumps({"actor": slug,
                        "count": len(data) if isinstance(data, list) else 1,
                        "data": data}))
                return
            self._send(404, json.dumps({"error": "not found under /actors"}))
            return
        return self._proxy_wp()

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 8099))
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), H)
    print(f"omai_feeds on :{PORT}  token={'set' if TOKEN else 'MISSING'}")
    srv.serve_forever()
