"""Regenerate languages.svg from public repo language stats."""

import json
import os
import urllib.request
from html import escape

USER = os.environ.get("GH_USER", "Mysticz0")
TOKEN = os.environ.get("GITHUB_TOKEN")
OUTPUT = "languages.svg"
COLORS_URL = "https://raw.githubusercontent.com/ozh/github-colors/master/colors.json"
FALLBACK_COLOR = "#8b949e"

FONT_SIZE = 14
CHAR_WIDTH = 8.4  # approx advance of a 14px monospace glyph
ROW_HEIGHT = 24
BAR_WIDTH = 320
BAR_HEIGHT = 12
PAD = 16


def fetch(url, auth=False):
    req = urllib.request.Request(url)
    if auth:
        req.add_header("Accept", "application/vnd.github+json")
        if TOKEN:
            req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def language_totals():
    totals = {}
    page = 1
    while True:
        repos = fetch(f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}", auth=True)
        if not repos:
            break
        for repo in repos:
            if repo["fork"]:
                continue
            langs = fetch(f"https://api.github.com/repos/{USER}/{repo['name']}/languages", auth=True)
            for lang, size in langs.items():
                totals[lang] = totals.get(lang, 0) + size
        page += 1
    return dict(sorted(totals.items(), key=lambda kv: kv[1], reverse=True))


def language_colors():
    try:
        return {lang: info.get("color") for lang, info in fetch(COLORS_URL).items()}
    except Exception:
        return {}


def render(totals, colors):
    total = sum(totals.values())
    name_width = max(len(lang) for lang in totals) * CHAR_WIDTH
    bar_x = PAD + name_width + 2 * CHAR_WIDTH
    pct_x = bar_x + BAR_WIDTH + 7 * CHAR_WIDTH
    width = pct_x + PAD
    first_row = PAD + ROW_HEIGHT * 2
    height = first_row + ROW_HEIGHT * (len(totals) - 1) + PAD

    rows = []
    for i, (lang, size) in enumerate(totals.items()):
        share = size / total
        y = first_row + i * ROW_HEIGHT
        bar_y = y - BAR_HEIGHT + 2
        fill = colors.get(lang) or FALLBACK_COLOR
        rows.append(
            f'<text x="{PAD}" y="{y}">{escape(lang)}</text>'
            f'<rect class="track" x="{bar_x:.1f}" y="{bar_y}" width="{BAR_WIDTH}" height="{BAR_HEIGHT}"/>'
            f'<rect x="{bar_x:.1f}" y="{bar_y}" width="{max(share * BAR_WIDTH, 2):.1f}" height="{BAR_HEIGHT}" fill="{fill}"/>'
            f'<text x="{pct_x:.1f}" y="{y}" text-anchor="end">{share * 100:.1f}%</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height}" viewBox="0 0 {width:.0f} {height}">
<style>
text {{ font: {FONT_SIZE}px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; fill: #1f2328; }}
.track {{ fill: #1f2328; fill-opacity: 0.08; }}
@media (prefers-color-scheme: dark) {{
  text {{ fill: #e6edf3; }}
  .track {{ fill: #e6edf3; }}
}}
</style>
<text x="{PAD}" y="{PAD + ROW_HEIGHT - 8}">Languages</text>
{chr(10).join(rows)}
</svg>
"""


def main():
    totals = language_totals()
    if not totals:
        return
    with open(OUTPUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(render(totals, language_colors()))


if __name__ == "__main__":
    main()
