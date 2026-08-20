# Security Policy

## No Secrets in Repository
This repository contains **zero API keys, tokens, or credentials**. All data sources are public and keyless:

- **Solana RPC:** `https://api.mainnet-beta.solana.com` (public, no key)
- **DeFiLlama / CoinGecko:** public REST, no key
- **Dune:** cache-first (`data/dune_cache.json`); live refresh only if `DUNE_API_KEY` env is set (never committed)
- **Social RSS:** keyless RSS cascade (Nitter → GitHub Atom)

Environment overrides (`SOLANA_RPC_URL`, `SOLANA_RPC_URLS`, `DUNE_API_KEY`, `DUNE_QUERY_ID`) are read from `os.environ` and **never** written to disk or committed.

## Reporting a Vulnerability
Please open a GitHub issue or contact the maintainers. Do not include secrets in issues or PRs.

## Dependency Surface
- **Python:** stdlib only (`urllib`, `json`, `sqlite3`, `gzip`, `http.client`) — no `pip install`, no supply-chain risk
- **Frontend:** `Chart.js` via CDN + Google Fonts, no build step, no `npm`

## GitHub Actions
Workflows use `permissions: contents: write, pages: write, id-token: write` scoped to the auto-refresh job only. Pages deployment uses `actions/deploy-pages@v4` with the official `actions/*` actions.

## If You Fork
- Do **not** commit `.env`, `*.key`, or `.vercel` — they are `.gitignore`d.
- Rotate any PAT after pasting it in a shell (shell history may retain it). Create PATs with minimal scopes: `repo` + `workflow` only for pushes that touch `.github/workflows/`.
