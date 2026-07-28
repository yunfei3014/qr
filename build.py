#!/usr/bin/env python3
"""Regenerate redirect pages and QR images from links.json.

Run:  python3 build.py
Edit links.json to change where a QR code points. The printed QR never changes.
"""

import json
import pathlib
import shutil
from urllib.parse import quote

import segno

ROOT = pathlib.Path(__file__).parent
BASE = "https://yunfei3014.github.io/qr"
CODES = ROOT / "codes"

REDIRECT = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="0; url={url}">
<meta name="robots" content="noindex">
<link rel="canonical" href="{url}">
<title>{label}</title>
<style>
  body {{ margin:0; min-height:100vh; display:grid; place-items:center; padding:24px;
    background:#0b0b0c; color:#f5f5f4; text-align:center;
    font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }}
  a {{ color:#fff; }}
  p {{ color:#a1a1aa; font-size:14px; }}
</style>
<script>location.replace("{url}");</script>
</head>
<body>
  <div>
    <p>Opening {label}&hellip;</p>
    <p><a href="{url}">Continue &rarr;</a></p>
  </div>
</body>
</html>
"""

INDEX_HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>QR links</title>
<style>
  :root { color-scheme: light dark; }
  body { margin:0; padding:48px 24px; background:#fafaf9; color:#18181b;
    font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }
  main { max-width:720px; margin:0 auto; }
  h1 { font-size:22px; font-weight:650; margin:0 0 4px; letter-spacing:-.01em; }
  .sub { color:#71717a; font-size:14px; margin:0 0 40px; }
  .card { display:flex; gap:24px; align-items:center; padding:24px;
    border:1px solid #e4e4e7; border-radius:14px; background:#fff; margin-bottom:16px; }
  .card img { width:120px; height:120px; flex:none; }
  .label { font-weight:600; margin:0 0 6px; }
  code { font:13px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;
    background:#f4f4f5; padding:2px 6px; border-radius:5px; }
  .dest { display:block; margin-top:8px; font-size:13px; color:#71717a;
    word-break:break-all; }
  .dl { font-size:13px; margin-top:10px; }
  @media (prefers-color-scheme: dark) {
    body { background:#0b0b0c; color:#f5f5f4; }
    .card { background:#141416; border-color:#27272a; }
    code { background:#27272a; }
  }
</style>
</head>
<body>
<main>
<h1>QR links</h1>
<p class="sub">Permanent redirects. No expiry, no scan limit. Edit
<code>links.json</code> to repoint any code.</p>
"""

INDEX_CARD = """<div class="card">
  <img src="codes/{slug}.svg" alt="QR code for {slug}">
  <div>
    <p class="label">{label}</p>
    <code>{short}</code>
    <a class="dest" href="{url}">&rarr; {url}</a>
    <p class="dl"><a href="codes/{slug}.svg">SVG</a> &middot;
      <a href="codes/{slug}.png">PNG</a> &middot;
      <a href="codes/{slug}-print.png">Print PNG</a></p>
  </div>
</div>
"""

RAW_CARD = """<div class="card">
  <img src="codes/{slug}.svg" alt="QR code for {slug}">
  <div>
    <p class="label">{label}</p>
    <code>encoded directly &mdash; not repointable</code>
    <a class="dest" href="{url}">&rarr; {url}</a>
    <p class="dl"><a href="codes/{slug}.svg">SVG</a> &middot;
      <a href="codes/{slug}.png">PNG</a> &middot;
      <a href="codes/{slug}-print.png">Print PNG</a></p>
  </div>
</div>
"""


def main() -> None:
    links = json.loads((ROOT / "links.json").read_text())

    if CODES.exists():
        shutil.rmtree(CODES)
    CODES.mkdir()

    cards = []
    for slug, cfg in sorted(links.items()):
        label = cfg.get("label", slug)

        # A "mailto" block is authored as plain text and percent-encoded here,
        # so nobody has to hand-write %20 / %2C in links.json. Implies raw.
        if "mailto" in cfg:
            m = cfg["mailto"]
            parts = [(k, m[k]) for k in ("subject", "body") if m.get(k)]
            query = "&".join(f"{k}={quote(v, safe='')}" for k, v in parts)
            url = "mailto:" + m["to"].strip() + (f"?{query}" if query else "")
            cfg = {**cfg, "raw": True}
        else:
            url = cfg["url"]

        # raw: encode the URI verbatim instead of routing through a redirect page.
        # Needed for non-http schemes (mailto:, tel:, sms:, WIFI:) where scanners
        # offer a native action, and where an https->scheme bounce is unreliable
        # inside in-app browsers. Cost: the code is NOT repointable afterwards.
        raw = bool(cfg.get("raw"))

        if raw:
            encoded = url
            # ECC M, not Q: mailto URIs are long, and Q would push this to a
            # much denser symbol that scans worse across a table.
            ecc = "m"
        else:
            encoded = f"{BASE}/{slug}/"
            # ECC Q = 25% damage tolerance. Deliberately not H: at this URL
            # length H pushes the symbol to v5 (37x37), which some decoders
            # (OpenCV's) fail to read. Q stays at v4 (33x33).
            ecc = "q"
            out = ROOT / slug
            out.mkdir(exist_ok=True)
            (out / "index.html").write_text(REDIRECT.format(url=url, label=label))

        qr = segno.make(encoded, error=ecc)
        qr.save(CODES / f"{slug}.svg", scale=8, border=4)
        qr.save(CODES / f"{slug}.png", scale=10, border=4)
        qr.save(CODES / f"{slug}-print.png", scale=40, border=4)

        tmpl = RAW_CARD if raw else INDEX_CARD
        cards.append(tmpl.format(slug=slug, label=label, short=encoded, url=url))
        mods = qr.symbol_size(scale=1, border=0)[0]
        print(f"{slug:16} -> {url}\n{'':16}    QR encodes "
              f"{'the URI directly' if raw else encoded} "
              f"(v{qr.version}, {mods}x{mods}, ecc {qr.error}, {len(encoded)} chars)")

    (ROOT / "index.html").write_text(
        INDEX_HEAD + "".join(cards) + "</main>\n</body>\n</html>\n"
    )
    print(f"\nBuilt {len(links)} link(s).")


if __name__ == "__main__":
    main()
