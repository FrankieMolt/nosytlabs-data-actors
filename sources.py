#!/usr/bin/env python3
"""OMA-AI live data sources — direct, free, no Apify dependency.

Each feed pulls REAL data from the primary free public API for that domain.
If a source fails it returns {"error": "..."} rather than empty, so the
monitoring layer can alert instead of silently serving zeros.

This is the always-live layer. The Apify actors (server.ACTORS) are a
separate paid wrapper that only works once the Apify plan is upgraded
— they are NOT required for the feed to be real.
"""
import json, time, urllib.request, urllib.error

UA = {"User-Agent": "OMA-AI/1.0 (+https://lethometry.com)"}
TIMEOUT = 20

def _get(url, headers=None, raw=False, data=None, method="GET"):
    h = dict(UA); 
    if headers: h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        b = r.read()
    return b if raw else json.loads(b)

# ---- individual real fetchers ------------------------------------------------

def coingecko():
    g = _get("https://api.coingecko.com/api/v3/global")["data"]
    mkt = _get("https://api.coingecko.com/api/v3/coins/markets"
                "?vs_currency=usd&order=market_cap_desc&per_page=10&page=1")
    return {
        "global_mcap_usd": g["total_market_cap"]["usd"],
        "btc_dominance": g["market_cap_percentage"].get("btc"),
        "eth_dominance": g["market_cap_percentage"].get("eth"),
        "total_volume_usd": g["total_volume"]["usd"],
        "active_cryptos": g.get("active_cryptocurrencies"),
        "top_coins": [{"symbol": c["symbol"].upper(), "name": c["name"],
                       "price": c["current_price"], "mcap": c["market_cap"],
                       "chg24h": c["price_change_percentage_24h"]} for c in mkt],
    }

def fear_greed():
    d = _get("https://api.alternative.me/fng/?limit=1")["data"][0]
    return {"value": int(d["value"]), "classification": d["value_classification"]}

def news():
    # Cointelegraph RSS (no key). First <title> is the channel title; skip it.
    import re
    xml = _get("https://cointelegraph.com/rss", raw=True,
                headers={"User-Agent": "Mozilla/5.0"})
    titles = re.findall(r"<title>([^<]+)</title>", xml.decode("utf-8", "ignore"))
    chan = titles[0] if titles else ""
    headlines = [t.strip() for t in titles[1:] if t.strip() and t.strip() != chan][:5]
    return {"headlines": headlines}

def mempool():
    # Base pending + latest block via public Base RPC
    def rpc(url, method):
        body = json.dumps({"jsonrpc": "2.0", "method": method,
                           "params": [], "id": 1}).encode()
        r = _get(url, headers={"Content-Type": "application/json"},
                 data=body, method="POST")
        return int(r["result"], 16)
    gas = rpc("https://mainnet.base.org", "eth_gasPrice")
    blk = rpc("https://mainnet.base.org", "eth_blockNumber")
    return {"chain": "base", "gas_gwei": round(gas / 1e9, 4),
            "latest_block": blk}

def defi_yields():
    d = _get("https://yields.llama.fi/pools?limit=200")["data"]
    # real, sensible yields: TVL > $1M, APY in a sane 1–1000% band
    # (excludes 900k% outlier garbage pools)
    real = [p for p in d if (p.get("tvlUsd") or 0) > 1_000_000
            and 1 <= (p.get("apy") or 0) <= 1000]
    top = sorted(real, key=lambda x: x.get("apy") or 0, reverse=True)[:10]
    return {"top_yields": [{"chain": p["chain"], "project": p["project"],
                            "symbol": p["symbol"], "apy": round(p.get("apy") or 0, 2),
                            "tvl_usd": p.get("tvlUsd")} for p in top]}

def defi_tvl():
    chains = _get("https://api.llama.fi/v2/chains")
    top = sorted(chains, key=lambda x: x.get("tvl", 0), reverse=True)[:10]
    return {"total_tvl_usd": sum(c.get("tvl", 0) for c in chains),
            "top_chains": [{"name": c["name"], "tvl_usd": c["tvl"]} for c in top]}

def gas():
    def rpc(url, method):
        body = json.dumps({"jsonrpc": "2.0", "method": method,
                           "params": [], "id": 1}).encode()
        r = _get(url, headers={"Content-Type": "application/json"},
                 data=body, method="POST")
        return int(r["result"], 16) / 1e9
    return {"eth_gwei": round(rpc("https://ethereum-rpc.publicnode.com", "eth_gasPrice"), 3),
            "base_gwei": round(rpc("https://mainnet.base.org", "eth_gasPrice"), 3)}

def polymarket():
    m = _get("https://gamma-api.polymarket.com/markets"
              "?limit=8&order=volume&ascending=false")
    return {"top_markets": [{"question": x["question"],
                             "volume": x.get("volume"),
                             "liquidity": x.get("liquidity"),
                             "slug": x.get("slug")} for x in m]}

# ---- dispatch ----------------------------------------------------------------

FEEDS = {
    "coingecko-market-data": coingecko,
    "crypto-fear-greed-index": fear_greed,
    "crypto-news-aggregator": news,
    "base-mempool-monitor": mempool,
    "defi-llama-yields": defi_yields,
    "defi-tvl-monitor": defi_tvl,
    "ethereum-gas-tracker": gas,
    "polymarket-data": polymarket,
}

def fetch_all():
    out, ok, fail = {}, 0, 0
    for slug, fn in FEEDS.items():
        try:
            out[slug] = fn()
            ok += 1
        except Exception as e:
            out[slug] = {"error": f"{type(e).__name__}: {e}"[:160]}
            fail += 1
    return {"ok": ok, "failed": fail, "generated_at": int(time.time()), "feeds": out}

if __name__ == "__main__":
    print(json.dumps(fetch_all(), indent=1)[:2000])
