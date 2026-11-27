# SnapOG

An Open Graph image API prototype built for Cloudflare Workers, with D1 usage records and R2 image caching. This example is intended for local evaluation and deployment to your own account. Hosted-service availability and cache-hit latency have not been verified for this source snapshot.

## Quick Start

Follow [Local Development](#local-development) to start your own instance, then open its `/register` page to create a test API key. The examples below use a local server. References to `snapog.dev` in the prototype's branding are not a verified hosted-service entrypoint.

```bash
curl "http://127.0.0.1:8787/og?title=My+Blog+Post&domain=myblog.com&key=sk_YOUR_KEY" \
  --output og.png
```

## API

```
GET /og
  ?title=Your Page Title     # required, max 120 chars
  &key=sk_your_key           # required
  &description=Subtitle      # optional, max 200 chars
  &domain=yourdomain.com     # optional
  &author=Jane Doe           # optional
  &tag=Tutorial              # optional, shown as pill badge
  &template=default          # default | blog | article
  &theme=dark                # dark | light
```

Returns `image/png`, 1200×630.

Headers:
- `X-Cache: HIT|MISS` — whether served from R2 cache
- `X-SnapOG-Tier: free|pro|business`

## HTML Integration

After deploying your own instance, replace `YOUR_DEPLOYMENT_HOST` and `YOUR_KEY` below. A local address is not reachable by social preview crawlers.

```html
<meta property="og:image"
      content="https://YOUR_DEPLOYMENT_HOST/og?title=YOUR_TITLE&key=YOUR_KEY" />
<meta property="og:image:width"  content="1200" />
<meta property="og:image:height" content="630" />
<meta name="twitter:card"   content="summary_large_image" />
<meta name="twitter:image"  content="https://YOUR_DEPLOYMENT_HOST/og?title=YOUR_TITLE&key=YOUR_KEY" />
```

## Demo Tiers

The prototype displays the following proposed prices and implements per-key monthly request limits. Registration accepts a tier selection without payment verification; there is no implemented subscription checkout. These are demo settings, not purchasable plans.

| Tier | Proposed price (demo only) | Requests/key/month |
|------|-------|-------------|
| Free | $0 | 100 |
| Pro | $19/mo | 10,000 |
| Business | $49/mo | 100,000 |

Cache hits also count toward these limits. Free tier images include a "snapog.dev" watermark as prototype branding.

## Local Development

### Prerequisites
- Node.js 24.11.1 (see `.node-version`; supported development range: 24.11.1–24.x)
- pnpm 12.16.1, matching `packageManager` in `package.json`
- Wrangler 3 is installed locally from the lockfile; no global Wrangler is needed
- A Cloudflare account with Workers access

### Setup

```bash
cd projects/snapog
pnpm install --frozen-lockfile

# 1. Create D1 database
pnpm exec wrangler d1 create snapog-db
# Copy the returned database_id into wrangler.toml [d1_databases]

# 2. Apply migrations locally
pnpm run db:local

# 3. Create R2 bucket (local R2 is simulated)
# No setup needed for local dev — wrangler simulates R2

# 4. Start dev server
pnpm run dev
```

Open http://127.0.0.1:8787

### Test

```bash
# Register a key via browser at http://127.0.0.1:8787/register
# Then test with:
API_KEY=sk_your_key bash sample/smoke-test.sh

# Or direct curl:
curl "http://127.0.0.1:8787/og?title=Hello+World&key=sk_your_key" --output og.png
```

### Typecheck

```bash
pnpm run typecheck
```

## Deployment

Deploy to resources you control after reviewing the prototype's authentication and tier handling. The checked-in D1 database ID is a placeholder; replace it with your own. Deploying this code does not add payment verification or turn the demo prices into subscriptions.

```bash
# 1. Create remote D1 database
pnpm exec wrangler d1 create snapog-db
# Update wrangler.toml with the database_id

# 2. Apply migrations to remote
pnpm run db:remote

# 3. Create R2 bucket
pnpm exec wrangler r2 bucket create snapog-og-cache

# 4. Deploy
pnpm run deploy
```

## Tech Stack

- [Cloudflare Workers](https://workers.cloudflare.com/) — edge compute
- [Hono](https://hono.dev/) — HTTP framework
- [workers-og](https://github.com/nicholasgasior/workers-og) — OG image generation (Satori-based)
- [Cloudflare D1](https://developers.cloudflare.com/d1/) — SQLite for usage tracking
- [Cloudflare R2](https://developers.cloudflare.com/r2/) — image cache storage
