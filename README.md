# NosytLabs Data Actors

Public landing page + live JSON feeds for 8 production-grade Apify actors covering crypto, DeFi, on-chain, and prediction-market data.

## Live
- **Landing page:** https://lethometry.com/actors
- **Actor directory (JSON):** https://lethometry.com/actors/api
- **All feeds (aggregated):** https://lethometry.com/actors/api/all
- **Per-actor feed:** `https://lethometry.com/actors/api/<slug>`

## Actors
| Actor | Price/run | Feeds |
|---|---|---|
| CoinGecko Market Data | $0.35 | markets, trending, categories, exchanges, global |
| Crypto Fear & Greed Index | $0.25 | sentiment 0–100 + history |
| Crypto News Aggregator | $0.30 | CoinDesk / Cointelegraph / CryptoSlate |
| Base Mempool Monitor | $0.40 | pending tx, gas, blocks (Base) |
| DeFiLlama Yields | $0.35 | APY / TVL / risk by pool |
| DeFi TVL Monitor | $0.35 | protocol TVL, 24h/7d, chains |
| Ethereum Gas Tracker | $0.25 | ETH / Base / Arbitrum gwei |
| Polymarket Data | $0.30 | markets, odds, volume, events |

## Self-host the feed server
```bash
cd omai_feeds
export APIFY_TOKEN=your_token   # for live Apify pulls
python3 server.py               # serves :8099
```
`server.py` is stdlib-only. It serves the landing page, proxies WordPress, and exposes the live JSON feeds (10-min cache). Run it behind a Cloudflare tunnel or reverse proxy.

## OMA-AI consumer
`consume.py` pulls `/actors/api/all` into `snapshot.json` for agent ingestion. Wire it into a cron (e.g. every 30 min).
