#!/usr/bin/env python3
"""OMA-AI feed digest — turns snapshot.json into a compact market brief.

Run after consume.py. Produces:
  digest.md     - human-readable brief (also good for Telegram/LLM context)
  digest.json   - machine-readable summary for the OMA-AI brain

Stdlib-only. No external calls (snapshot.json is the source of truth).
"""
import json, os, time

HERE = os.path.dirname(os.path.abspath(__file__))
SNAP = os.path.join(HERE, "snapshot.json")
OUT_MD = os.path.join(HERE, "digest.md")
OUT_JSON = os.path.join(HERE, "digest.json")

def load():
    with open(SNAP) as f:
        return json.load(f)

def summarize(snap):
    feeds = snap.get("feeds", {})
    out = {"generated_at": snap.get("generated_at"), "signals": []}

    # Fear & Greed
    fg = feeds.get("crypto-fear-greed-index", {}).get("data")
    if fg and isinstance(fg, list) and fg:
        v = fg[0]
        val = v.get("value")
        cls = v.get("valueClassification", "")
        out["signals"].append({
            "signal": "fear_greed", "value": val, "label": cls,
            "note": f"Sentiment: {val} ({cls})"
        })

    # Gas (per-chain records — chains depend on what the actor returns)
    gas = feeds.get("ethereum-gas-tracker", {}).get("data")
    if gas and isinstance(gas, list) and gas:
        by = {g.get("chain"): g for g in gas}
        def gw(ch):
            g = by.get(ch)
            return round(g.get("fast_gwei"), 2) if g and g.get("fast_gwei") is not None else None
        parts = []
        for ch in ("ethereum", "base", "arbitrum", "polygon", "optimism"):
            v = gw(ch)
            if v is not None:
                parts.append(f"{ch[:3].upper()}:{v}")
        out["signals"].append({
            "signal": "gas", "chains": {c: gw(c) for c in by},
            "note": "Gas gwei — " + (" ".join(parts) if parts else "no data")
        })

    # CoinGecko global
    cg = feeds.get("coingecko-market-data", {}).get("data")
    if cg and isinstance(cg, list):
        for rec in cg:
            if rec.get("type") == "global_market_data":
                mc = rec.get("total_market_cap", {})
                out["signals"].append({
                    "signal": "global_mcap_usd", "value": mc.get("usd"),
                    "note": f"Total crypto mcap: ${mc.get('usd',0)/1e9:.1f}B"
                })
                break

    # Polymarket top markets by volume
    pm = feeds.get("polymarket-data", {}).get("data")
    if pm and isinstance(pm, list):
        top = sorted(pm, key=lambda x: x.get("volume", 0) or 0, reverse=True)[:3]
        out["signals"].append({
            "signal": "polymarket_top",
            "markets": [{"q": m.get("question"), "vol": m.get("volume")} for m in top],
            "note": "Top Polymarket: " + ", ".join(m.get("question","")[:40] for m in top)
        })

    # DeFi TVL top movers
    tvl = feeds.get("defi-tvl-monitor", {}).get("data")
    if tvl and isinstance(tvl, list):
        out["signals"].append({
            "signal": "defi_tvl_protocols", "count": len(tvl),
            "note": f"DeFi TVL tracked: {len(tvl)} protocols"
        })

    # News headlines
    news = feeds.get("crypto-news-aggregator", {}).get("data")
    if news and isinstance(news, list):
        headlines = [n.get("title") for n in news[:5] if n.get("title")]
        out["signals"].append({
            "signal": "news", "headlines": headlines,
            "note": f"{len(news)} headlines; top: " + (headlines[0] if headlines else "n/a")
        })

    out["feed_counts"] = {k: v.get("count") for k, v in feeds.items()}
    return out

def to_md(s):
    lines = ["# OMA-AI Market Brief", "", f"_Generated: {time.strftime('%Y-%m-%d %H:%M', time.localtime(s.get('generated_at', time.time())))}_", ""]
    for sig in s.get("signals", []):
        lines.append(f"- **{sig['signal']}**: {sig['note']}")
    lines.append("")
    lines.append("## Feed counts")
    for k, v in s.get("feed_counts", {}).items():
        lines.append(f"- {k}: {v}")
    return "\n".join(lines)

def main():
    snap = load()
    s = summarize(snap)
    with open(OUT_MD, "w") as f:
        f.write(to_md(s))
    with open(OUT_JSON, "w") as f:
        json.dump(s, f, indent=1)
    print(f"digest OK signals={len(s['signals'])} -> digest.md + digest.json")

if __name__ == "__main__":
    main()
