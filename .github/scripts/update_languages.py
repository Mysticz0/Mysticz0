"""Regenerate the language chart in README.md from public repo language stats."""

import json
import os
import re
import urllib.request

USER = os.environ.get("GH_USER", "Mysticz0")
TOKEN = os.environ.get("GITHUB_TOKEN")
README = "README.md"
BAR_WIDTH = 40

PREFIX = "+"
START, END = "<!--LANGS:START-->", "<!--LANGS:END-->"


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github+json")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def language_totals():
    totals = {}
    page = 1
    while True:
        repos = api(f"/users/{USER}/repos?per_page=100&page={page}")
        if not repos:
            break
        for repo in repos:
            if repo["fork"]:
                continue
            for lang, size in api(f"/repos/{USER}/{repo['name']}/languages").items():
                totals[lang] = totals.get(lang, 0) + size
        page += 1
    return dict(sorted(totals.items(), key=lambda kv: kv[1], reverse=True))


def render(totals):
    total = sum(totals.values())
    name_width = max(len(lang) for lang in totals)
    lines = ["```", "  Language Usage", ""]
    for i, (lang, size) in enumerate(totals.items()):
        share = size / total
        halves = round(share * BAR_WIDTH * 2)
        bar = "█" * (halves // 2) + ("▌" if halves % 2 else "")
        lines.append(f"{PREFIX} {lang:<{name_width}}  {bar:<{BAR_WIDTH}}  {share * 100:5.1f}%")
    lines.append("```")
    return "\n".join(lines)


def main():
    totals = language_totals()
    if not totals:
        return
    with open(README, encoding="utf-8") as f:
        readme = f.read()
    block = f"{START}\n{render(totals)}\n{END}"
    updated = re.sub(f"{re.escape(START)}.*?{re.escape(END)}", lambda _: block, readme, flags=re.S)
    with open(README, "w", encoding="utf-8", newline="\n") as f:
        f.write(updated)


if __name__ == "__main__":
    main()
