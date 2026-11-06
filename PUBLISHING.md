# Publishing Thoroughbred Ascot on Cloudflare (free)

The game is plain files, so Cloudflare serves it for free. Every push to `main` republishes it automatically.

## One-off setup (in the Cloudflare dashboard)

1. Sign up for a free account at dash.cloudflare.com.
2. Go to **Workers & Pages** → **Create** → **Import a repository**, connect GitHub and pick `thoroughbreddigitalgame`
   (you can give Cloudflare access to this one private repo only).
3. Settings:
   - **Project name:** `thoroughbred-ascot`
   - **Build command:** `python3 game/tools/stage.py dist`
   - **Deploy command:** `npx wrangler deploy` (the default)
   - **Branch:** `main`
4. Save and deploy. The game appears at `https://thoroughbred-ascot.<your-subdomain>.workers.dev`.

## How it works

- `game/tools/stage.py` gathers the 243 files the game needs (about 33 MB) into `dist/`.
- `wrangler.jsonc` tells Cloudflare to serve `dist/` as it is.
- Free-plan limits that matter: 20,000 files and 25 MiB per file. The largest file is about 7 MB.
