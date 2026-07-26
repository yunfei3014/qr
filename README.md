# qr — permanent QR redirects

Static redirect host on GitHub Pages. Free forever, no expiry, no scan limit.
Print the QR once; change where it points whenever you like.

Live: <https://yunfei3014.github.io/qr/>

## How it works

`links.json` maps a slug to a destination. `build.py` generates:

- `<slug>/index.html` — a redirect page (meta refresh + JS, works with JS off)
- `codes/<slug>.svg` / `.png` / `-print.png` — the QR image
- `index.html` — an index of every link with its QR

The QR encodes `https://yunfei3014.github.io/qr/<slug>/` — never the destination.
That indirection is the whole point: the printed code is permanent, the
destination is a one-line edit.

## Change where a QR points

Edit `links.json` on github.com (pencil icon), commit. A GitHub Action rebuilds
and republishes in ~40s. The printed QR is unaffected.

Locally instead:

```bash
pip install segno
python3 build.py
git commit -am "repoint meet" && git push
```

## Add a link

```json
{
  "meet":  { "url": "https://calendly.com/...", "label": "30 min intro" },
  "deck":  { "url": "https://docsend.com/...",  "label": "Seed deck" }
}
```

Then rebuild. New QR lands in `codes/deck.svg`.

## Limits

GitHub Pages soft limits: 100 GB bandwidth/month, 10 builds/hour. A redirect
page is ~1 KB, so the bandwidth ceiling is on the order of 100M scans/month.
No per-scan metering, no trial, no account to keep alive.

## Custom domain (optional)

Add a `CNAME` file with e.g. `qr.example.com`, point a DNS CNAME at
`yunfei3014.github.io`, and enable HTTPS in repo Settings → Pages. Shorter URL,
smaller QR, and the link survives even if the GitHub username changes.

## No analytics here

Static hosting cannot count scans. If scan counts matter, put a counted
redirect in front of this. Deliberate trade: this tier has nothing that can
expire or bill.
