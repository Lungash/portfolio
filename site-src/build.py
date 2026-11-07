#!/usr/bin/env python3
"""Static generator for luntech.work (stdlib only).

    python3 site-src/build.py            # real tools only (what goes to main)
    python3 site-src/build.py --mock     # also add site-src/tools.mock.json placeholders (preview only)

Reads tools.json, writes into site/:
  tools/index.html, tools/<slug>/index.html, the featured block + CSS/JS links in index.html,
  fingerprinted style.<hash>.css and tools.<hash>.js, sitemap.xml, _headers.
Old fingerprinted copies are removed.
"""
import hashlib, html, json, pathlib, re, sys

SRC = pathlib.Path(__file__).resolve().parent
OUT = SRC.parent / "site"
SITE = "https://lungash.luntech.work"
STATUSES = {"released", "in-progress", "private"}
MOCK = "--mock" in sys.argv
esc = lambda s: html.escape(str(s), quote=True)

def fingerprint(src, stem, ext):
    data = (SRC / src).read_bytes()
    h = hashlib.sha256(data).hexdigest()[:8]
    for old in OUT.glob(f"{stem}.*.{ext}"):
        old.unlink()
    (OUT / f"{stem}.{h}.{ext}").write_bytes(data)
    return h, data

css_h, css_data = fingerprint("style.css", "style", "css")
js_h, _ = fingerprint("tools.js", "tools", "js")
CSS = f"/style.{css_h}.css"
JS = f"/tools.{js_h}.js"

def load():
    tools = json.load(open(SRC / "tools.json"))["tools"]
    if MOCK:
        tools += json.load(open(SRC / "tools.mock.json"))["tools"]
    seen = set()
    for t in tools:
        assert re.fullmatch(r"[a-z0-9-]+", t["slug"]), f"bad slug {t['slug']}"
        assert t["slug"] not in seen, f"duplicate slug {t['slug']}"
        seen.add(t["slug"])
        assert t["status"] in STATUSES, f"{t['slug']}: status must be one of {STATUSES}"
        for k in ("name", "tagline", "tags"):
            assert t.get(k), f"{t['slug']}: missing {k}"
        d = t.get("download")
        if d:
            p = OUT / d["file"]
            assert p.is_file(), f"{t['slug']}: download file {d['file']} not found in site/"
            b = p.read_bytes()
            d["_size"] = f"{len(b) / 1048576:.1f} MiB"
            d["_sha"] = hashlib.sha256(b).hexdigest()
    return tools

def head(title, desc, path, extra="", robots=False):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="theme-color" content="#f2eee5" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#16140f" media="(prefers-color-scheme: dark)">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE}{path}">
<link rel="canonical" href="{SITE}{path}">
{'<meta name="robots" content="noindex">' if robots else ''}
<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32x32.png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="manifest" href="/assets/site.webmanifest">
<link rel="stylesheet" href="{CSS}">
{extra}</head>
"""

FOOT = """<footer>
  <span>&copy; 2026 Lungash</span>
</footer>
</div>
"""

def card(t):
    ph = t.get("placeholder")
    st = "placeholder" if ph else t["status"]
    text = " ".join([t["name"], t["tagline"], " ".join(t["tags"]), t.get("stack", ""), t["status"]]).lower()
    dl = '<span class="dl">&darr; download</span>' if t.get("download") else ""
    return (f'<li class="card{" ph" if ph else ""}" data-tags="{esc(" ".join(t["tags"]))}" data-text="{esc(text)}">\n'
            f'  <p class="meta"><span class="badge st-{st}">{esc(st)}</span><span>{esc(t.get("stack", ""))}</span>{dl}</p>\n'
            f'  <h3><a href="/tools/{t["slug"]}/">{esc(t["name"])}</a></h3>\n'
            f'  <p>{esc(t["tagline"])}</p>\n'
            f'  <ul class="chips" aria-label="Tags">{"".join(f"<li>{esc(g)}</li>" for g in t["tags"])}</ul>\n'
            f'</li>')

def cards(ts, list_id=""):
    idattr = f' id="{list_id}"' if list_id else ""
    return f'<ul class="tools"{idattr}>\n' + "\n".join(card(t) for t in ts) + "\n</ul>"

def tool_page(t):
    ph = t.get("placeholder")
    st = "placeholder" if ph else t["status"]
    title = f'{t["name"]} — Lungash'
    out = head(title, t["tagline"], f'/tools/{t["slug"]}/', robots=bool(ph))
    ver = f' &middot; {esc(t["version"])}' if t.get("version") else ""
    out += f"""<body class="tool-page">
<a class="skip" href="#main">Skip to content</a>
<div class="sheet">
<header>
  <div class="titleblock">
    <a href="/">&larr; Lungash</a>
    <a href="/tools/">All tools</a>
    <span>{esc(t.get("stack", ""))}</span>
  </div>
  <h1 class="tool">{esc(t["name"])}</h1>
  <div class="tool-head"><span class="badge st-{st}">{esc(st)}</span><span>{esc(t["status"]) if ph else ""}{ver}</span></div>
  <p class="lede">{esc(t["tagline"])}</p>
</header>
<main id="main">
"""
    if ph:
        out += '<p class="ph-banner">Placeholder. This is not a real tool; it exists only to preview how the tools section scales.</p>\n'
    out += '<div class="body">\n'
    if t.get("body"):
        out += (SRC / t["body"]).read_text()
    else:
        out += "".join(f"<p>{esc(p)}</p>\n" for p in t.get("description", []))
        if t.get("specs"):
            out += '<dl class="spec">\n' + "".join(
                f'<div><dt>{esc(s["k"])}</dt><dd>{esc(s["v"])}</dd></div>\n' for s in t["specs"]) + "</dl>\n"
    d = t.get("download")
    if d:
        v = f' &middot; {esc(t["version"])}' if t.get("version") else ""
        out += f'<div class="get">\n  <a class="btn" href="/{d["file"]}" download>{esc(d["label"])}{v} &middot; {d["_size"]}</a>\n'
        out += "".join(f"  <p>{esc(n)}</p>\n" for n in d.get("notes", []))
        out += f'  <p class="hash">SHA-256 {d["_sha"]}</p>\n</div>\n'
    links = [f'<a href="{esc(l["url"])}">{esc(l["label"])}</a>' for l in t.get("links", [])]
    note = [f'<span>{esc(t["note"])}</span>'] if t.get("note") else []
    if links or note:
        out += '<p class="links">' + " <span>&middot;</span> ".join(links + note) + "</p>\n"
    out += '</div>\n<ul class="tag-links" aria-label="Tags">' + "".join(
        f'<li><a href="/tools/?tag={esc(g)}">#{esc(g)}</a></li>' for g in t["tags"]) + "</ul>\n</main>\n" + FOOT + "</body>\n</html>\n"
    return out

def index_page(ts):
    n = len(ts)
    out = head("Tools — Lungash", "Everything I've built: Rust, networking, cryptography and Android tools.", "/tools/")
    out += f"""<body class="tool-page">
<a class="skip" href="#main">Skip to content</a>
<div class="sheet">
<header>
  <div class="titleblock">
    <a href="/">&larr; Lungash</a>
    <span>Tools</span>
    <span>{n} entries</span>
  </div>
  <h1 class="tool">Tools</h1>
  <p class="lede">Everything I&rsquo;ve built.</p>
</header>
<main id="main">
{cards(ts, "tool-list")}
</main>
{FOOT}<script src="{JS}" defer></script>
</body>
</html>
"""
    return out

def write(path, text):
    p = OUT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)

tools = load()
# clear previously generated tool pages so removed tools don't linger
import shutil
if (OUT / "tools").exists():
    shutil.rmtree(OUT / "tools")
write("tools/index.html", index_page(tools))
for t in tools:
    write(f'tools/{t["slug"]}/index.html', tool_page(t))

# home page: featured block + asset link
home = (OUT / "index.html").read_text()
feat = [t for t in tools if t.get("featured")][:4]
block = (f'<!--tools:start-->\n{cards(feat)}\n'
         f'<p class="more"><a href="/tools/">View all {len(tools)} tools &rarr;</a></p>\n<!--tools:end-->')
home = re.sub(r"<!--tools:start-->.*?<!--tools:end-->", lambda m: block, home, flags=re.S)
home = re.sub(r'href="/style(\.[0-9a-f]{8})?\.css"', f'href="{CSS}"', home)
(OUT / "index.html").write_text(home)

# sitemap (placeholders never listed)
urls = ["/", "/tools/"] + [f'/tools/{t["slug"]}/' for t in tools if not t.get("placeholder")]
(OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    "".join(f"  <url><loc>{SITE}{u}</loc></url>\n" for u in urls) + "</urlset>\n")

# cache rules for Cloudflare Pages
(OUT / "_headers").write_text("""/
  Cache-Control: public, max-age=0, must-revalidate
/index.html
  Cache-Control: public, max-age=0, must-revalidate
/tools/*
  Cache-Control: public, max-age=0, must-revalidate
/sitemap.xml
  Cache-Control: public, max-age=0, must-revalidate
/robots.txt
  Cache-Control: public, max-age=0, must-revalidate
/assets/site.webmanifest
  Cache-Control: public, max-age=0, must-revalidate
/style.*.css
  Cache-Control: public, max-age=31536000, immutable
/tools.*.js
  Cache-Control: public, max-age=31536000, immutable
/downloads/*
  Cache-Control: public, max-age=31536000, immutable
/assets/*
  Cache-Control: public, max-age=86400
""")
print(f"built {len(tools)} tools ({'with' if MOCK else 'no'} placeholders); css {css_h} js {js_h}")
