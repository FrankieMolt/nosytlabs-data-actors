# NosytLabs — Crypto Data Feeds

Free, live JSON feeds for crypto markets, DeFi, on-chain activity, and
prediction-market data. Powered by **direct public APIs** — no API key,
no account, no rate-limit wall.

## Live feeds (free, no key required)

- **Landing page:** https://lethometry.com/actors
- **All feeds (aggregated):** https://lethometry.com/actors/api/all
- **Per feed:** `https://lethometry.com/actors/api/<slug>`

Feeds (slug): `coingecko-market-data`, `crypto-fear-greed-index`,
`crypto-news-aggregator`, `base-mempool-monitor`, `defi-llama-yields`,
`defi-tvl-monitor`, `ethereum-gas-tracker`, `polymarket-data`.

Each feed returns **real data** pulled directly from its primary public
source and cached for 2 hours:

| Feed | Source |
|------|--------|
| coingecko-market-data | CoinGecko API |
| crypto-fear-greed-index | alternative.me |
| crypto-news-aggregator | Cointelegraph RSS |
| base-mempool-monitor | Base public RPC |
| defi-llama-yields | DeFiLlama yields API |
| defi-tvl-monitor | DeFiLlama TVL API |
| ethereum-gas-tracker | ETH + Base public RPC |
| polymarket-data | Polymarket gamma API |

## Architecture

- `sources.py` — one real fetcher per feed (direct APIs, with fallbacks)
- `server.py` — stdlib HTTP server on `:8099`; serves the landing page
  and `/actors/api/*`, proxies WordPress (`:8081`) for `/`
- `consume.py` — writes `snapshot.json` for agent ingestion
- `digest.py` — generates `digest.md` / `digest.json` (OMA-AI brief)
- `run_pipeline.py` — cron entry (every 2 hours); silent on success,
  alerts on failure / stale snapshot
- `omai-feeds.service` — systemd unit (in repo + `/etc/systemd/system`)

## Apify actors (optional paid wrapper)

8 `nosytlabs/*` actors on Apify mirror these feeds as pay-per-run actors
($0.25–$0.40/run). They are a **separate monetization layer** and are
**NOT required** for the live feeds above.

> ⚠️ The Apify account is currently on the **FREE plan**, which blocks
> paid runs (`403 Monthly usage hard limit exceeded`, `PAID_ACTORS`
> feature disabled). Paid runs require upgrading the Apify plan
> (e.g. Starter). The free live feeds work regardless of Apify status.

## Self-host

```bash
cd omai_feeds
python3 server.py            # serves :8099 — no token needed
```
Run behind a Cloudflare tunnel or reverse proxy. The feed needs no
external credentials.

## OMA-AI consumer

`consume.py` pulls `/actors/api/all` into `snapshot.json`. Wire it into a
cron (every 2 hours) via `run_pipeline.py`.
