"""Regenerate the color-coded language chart in README.md from public repo language stats."""

import json
import os
import re
import urllib.request

USER = os.environ.get("GH_USER", "Mysticz0")
TOKEN = os.environ.get("GITHUB_TOKEN")
README = "README.md"
COLORS_URL = "https://raw.githubusercontent.com/ozh/github-colors/master/colors.json"
FALLBACK_COLOR = "#8b949e"
BAR_EM = 15  # width of a 100% bar
START, END = "<!--LANGS:START-->", "<!--LANGS:END-->"


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


def tex_escape(text):
    return re.sub(r"([#$%&_{}])", r"\\\1", text)


def render(totals, colors):
    total = sum(totals.values())
    rows = [r"\texttt{Languages} & & \\"]
    for lang, size in totals.items():
        share = size / total
        color = colors.get(lang) or FALLBACK_COLOR
        bar = max(share * BAR_EM, 0.1)
        rows.append(
            rf"\texttt{{{tex_escape(lang)}}} & "
            rf"\color{{{color}}}{{\rule{{{bar:.2f}em}}{{0.6em}}}} & "
            rf"\texttt{{{share * 100:.1f}\%}} \\"
        )
    return "\n".join(["```math", r"\begin{array}{llr}", *rows, r"\end{array}", "```"])


def main():
    totals = language_totals()
    if not totals:
        return
    with open(README, encoding="utf-8") as f:
        readme = f.read()
    block = f"{START}\n{render(totals, language_colors())}\n{END}"
    updated = re.sub(f"{re.escape(START)}.*?{re.escape(END)}", lambda _: block, readme, flags=re.S)
    with open(README, "w", encoding="utf-8", newline="\n") as f:
        f.write(updated)


if __name__ == "__main__":
    main()
