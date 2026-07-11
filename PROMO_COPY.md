# NosytLabs Apify Actors — Social + Repo Copy

## X / Twitter (post 1 — main)
NosytLabs just shipped 8 production-grade crypto/data actors on @apify.

Live market data, on-chain signals, and prediction markets — all pay-per-run, no API keys to babysit.

Browse + run: https://lethometry.com/actors

#crypto #web3 #data #automation

## X / Twitter (post 2 — thread reply, feature detail)
What's inside:
• CoinGecko market data (21+ global markets)
• Crypto Fear & Greed Index (real-time sentiment)
• Polymarket prediction markets
• Base mempool monitor (pending tx + gas)
• DeFiLlama yields + TVL
• Ethereum gas tracker (ETH/Base/Arbitrum)
• Crypto news aggregator

One endpoint each, JSON, ready for your pipeline.

## X / Twitter (post 3 — for devs / OMA-AI)
Building an agent? Every actor has a live JSON feed:
https://lethometry.com/actors/api/<actor>

Drop it into n8n, a cron, or your own model. OMA-AI pulls these directly.

## GitHub repo description (if you push the feed server)
"NosytLabs OMA-AI data layer — Cloudflare-tunneled Apify actor landing page + live JSON feeds for crypto/on-chain/prediction-market data."

## GitHub README snippet
# NosytLabs Data Actors
Public landing page + live JSON feeds for 8 Apify actors (crypto, DeFi, on-chain, prediction markets).

- Landing: https://lethometry.com/actors
- Feeds: https://lethometry.com/actors/api/<actor>  (e.g. /actors/api/coingecko-market-data)
- Aggregated: https://lethometry.com/actors/api/all
- Source: omai_feeds/server.py (stdlib-only, systemd-managed on oldpc)

Self-host: `python3 server.py` (needs APIFY_TOKEN in env for live pulls).
