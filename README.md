# portfolio

Personal site for Lungash, served at https://lungash.luntech.work by Cloudflare Pages.
Plain HTML, CSS and a little JS. No framework, no build command on Pages.

- `site/` is what gets deployed (Pages output directory). Generated files live here and are committed.
- `site-src/` is the source: `tools.json`, `content/`, `style.css`, `tools.js` and `build.py`.

## Add a tool

1. Add an entry to `site-src/tools.json` (slug, name, tagline, status `released | in-progress | private`, tags, optional links and download).
2. For a longer write-up put an HTML fragment in `site-src/content/` and point `body` at it; otherwise use `description` and `specs`.
3. Run `python3 site-src/build.py`, review `git diff`, commit, push.

The script regenerates `/tools/`, `/tools/<slug>/`, the home page's featured block (first 4 `featured` tools), the sitemap, `_headers`, and the fingerprinted `style.<hash>.css` / `tools.<hash>.js`.

`python3 site-src/build.py --mock` adds 10 placeholder tools from `tools.mock.json` for layout previews. Never commit a mock build to `main`.

## Caching

Fingerprinted CSS/JS and files under `site/downloads/` are cached for a year (`_headers`), so never overwrite a download: give a new version a new filename. HTML revalidates on every load.

## Cloudflare deploy

Deployed as a Worker with static assets (Workers Builds, connected to this repo). `wrangler.jsonc` points the asset directory at `site/`, and `site/_headers` supplies the cache rules.

- Worker name: `portfolio` (must match `name` in `wrangler.jsonc`)
- Build command: empty. Deploy command: `npx wrangler deploy`. Production branch: `main`.
- Custom domain: `lungash.luntech.work` (Settings, Domains & Routes).
- Once the custom domain works, set `"workers_dev": false` to switch off the `*.workers.dev` URL.

## The old site

The 2024 version of this portfolio is kept on the `v1-2024` branch (and tag). GitHub Pages serves that branch at https://lungash.github.io/portfolio/.
