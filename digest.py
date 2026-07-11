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
    fg = feeds.get("crypto-fear-greed-index", {})
    if "error" not in fg and "value" in fg:
        out["signals"].append({
            "signal": "fear_greed", "value": fg["value"], "label": fg["classification"],
            "note": f"Sentiment: {fg['value']} ({fg['classification']})"
        })

    # Gas
    g = feeds.get("ethereum-gas-tracker", {})
    if "error" not in g and "eth_gwei" in g:
        out["signals"].append({
            "signal": "gas", "eth": g["eth_gwei"], "base": g["base_gwei"],
            "note": f"Gas gwei — ETH:{g['eth_gwei']} BAS:{g['base_gwei']}"
        })

    # CoinGecko global
    cg = feeds.get("coingecko-market-data", {})
    if "error" not in cg and "global_mcap_usd" in cg:
        out["signals"].append({
            "signal": "global_mcap_usd", "value": cg["global_mcap_usd"],
            "btc_dom": cg.get("btc_dominance"),
            "note": f"Total crypto mcap: ${cg['global_mcap_usd']/1e9:.1f}B  BTC-dom {cg.get('btc_dominance'):.1f}%"
        })

    # Polymarket top markets by volume
    pm = feeds.get("polymarket-data", {})
    if "error" not in pm and "top_markets" in pm:
        top = pm["top_markets"][:3]
        out["signals"].append({
            "signal": "polymarket_top",
            "markets": [{"q": m["question"], "vol": m["volume"]} for m in top],
            "note": "Top Polymarket: " + ", ".join(m["question"][:40] for m in top)
        })

    # DeFi TVL total
    tvl = feeds.get("defi-tvl-monitor", {})
    if "error" not in tvl and "total_tvl_usd" in tvl:
        out["signals"].append({
            "signal": "defi_tvl", "total_usd": tvl["total_tvl_usd"],
            "top_chain": tvl["top_chains"][0]["name"],
            "note": f"DeFi TVL: ${tvl['total_tvl_usd']/1e9:.1f}B  top={tvl['top_chains'][0]['name']}"
        })

    # DeFi yields top
    y = feeds.get("defi-llama-yields", {})
    if "error" not in y and "top_yields" in y:
        t = y["top_yields"][0]
        out["signals"].append({
            "signal": "defi_yield_top",
            "note": f"Top yield: {t['project']} ({t['chain']}) {t['apy']}% APY"
        })

    # News headlines
    news = feeds.get("crypto-news-aggregator", {})
    if "error" not in news and "headlines" in news:
        hl = news["headlines"][:5]
        out["signals"].append({
            "signal": "news", "headlines": hl,
            "note": f"{len(hl)} headlines; top: " + (hl[0] if hl else "n/a")
        })

    # Mempool (Base gas/block)
    mp = feeds.get("base-mempool-monitor", {})
    if "error" not in mp and "gas_gwei" in mp:
        out["signals"].append({
            "signal": "base_mempool", "gas": mp["gas_gwei"], "block": mp["latest_block"],
            "note": f"Base: gas {mp['gas_gwei']} gwei, block {mp['latest_block']}"
        })

    out["feed_counts"] = {k: ("error" if "error" in v else "ok")
                           for k, v in feeds.items()}
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
