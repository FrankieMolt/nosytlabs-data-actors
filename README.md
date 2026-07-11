# NosytLabs Data Actors

8 production-grade Apify actors for crypto, DeFi, on-chain, and prediction-market data — live JSON feeds + pay-per-run pricing.

## Actors (click to open in Apify Store)
| Actor | Store | Price/run | Feeds |
|---|---|---|---|
| CoinGecko Market Data | [apify.com/nosytlabs/coingecko-market-data](https://apify.com/nosytlabs/coingecko-market-data) | $0.35 | markets, trending, categories, exchanges, global |
| Crypto Fear & Greed Index | [apify.com/nosytlabs/crypto-fear-greed-index](https://apify.com/nosytlabs/crypto-fear-greed-index) | $0.25 | sentiment 0–100 + history |
| Crypto News Aggregator | [apify.com/nosytlabs/crypto-news-aggregator](https://apify.com/nosytlabs/crypto-news-aggregator) | $0.30 | CoinDesk / Cointelegraph / CryptoSlate |
| Base Mempool Monitor | [apify.com/nosytlabs/base-mempool-monitor](https://apify.com/nosytlabs/base-mempool-monitor) | $0.40 | pending tx, gas, blocks (Base) |
| DeFiLlama Yields | [apify.com/nosytlabs/defi-llama-yields](https://apify.com/nosytlabs/defi-llama-yields) | $0.35 | APY / TVL / risk by pool |
| DeFi TVL Monitor | [apify.com/nosytlabs/defi-tvl-monitor](https://apify.com/nosytlabs/defi-tvl-monitor) | $0.35 | protocol TVL, 24h/7d, chains |
| Ethereum Gas Tracker | [apify.com/nosytlabs/ethereum-gas-tracker](https://apify.com/nosytlabs/ethereum-gas-tracker) | $0.25 | ETH / Base / Arbitrum gwei |
| Polymarket Data | [apify.com/nosytlabs/polymarket-data](https://apify.com/nosytlabs/polymarket-data) | $0.30 | markets, odds, volume, events |

## Live demos (no API key)
- **Landing page:** https://lethometry.com/actors
- **All feeds (aggregated):** https://lethometry.com/actors/api/all
- **Per-actor feed:** `https://lethometry.com/actors/api/<slug>`

Each live feed shows the latest successful run's dataset items — proof the actors work before you buy a run.

## Self-host the feed server
```bash
cd omai_feeds
export APIFY_TOKEN=your_token   # for live Apify pulls
python3 server.py               # serves :8099
```
`server.py` is stdlib-only. It serves the landing page, proxies WordPress, and exposes the live JSON feeds (10-min cache). Run behind a Cloudflare tunnel or reverse proxy.

## OMA-AI consumer
`consume.py` pulls `/actors/api/all` into `snapshot.json` for agent ingestion. Wire it into a cron (e.g. every 30 min).

## Pricing
All actors are **pay per run** — you only pay when the actor runs. No monthly commitment.
