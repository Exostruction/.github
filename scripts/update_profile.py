#!/usr/bin/env python3
"""Update the marked sections in profile/README.md with the latest pushes
and recently active repositories of the organization.

Public data only. Standard library only.
Environment: ORG (required), GITHUB_TOKEN (optional, raises the rate limit).
"""
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone

ORG = os.environ.get("ORG") or os.environ.get("GITHUB_REPOSITORY_OWNER")
TOKEN = os.environ.get("GITHUB_TOKEN")
README = os.environ.get("README_PATH", "profile/README.md")
MAX_PUSHES = 8
MAX_REPOS = 5
SKIP_REPOS = {".github"}

if not ORG:
    sys.exit("ORG is missing")


def api(path):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "org-profile-updater",
            **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def ago(iso):
    t = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    s = int((datetime.now(timezone.utc) - t).total_seconds())
    if s < 3600:
        return f"{max(s // 60, 1)} min ago"
    if s < 86400:
        return f"{s // 3600} h ago"
    d = s // 86400
    return "yesterday" if d == 1 else f"{d} days ago"


def clean(text, limit=70):
    text = re.sub(r"\s+", " ", text.splitlines()[0] if text else "").strip()
    text = text.replace("|", "\\|").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"([\[\]`*_])", r"\\\1", text)
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def pushes():
    rows, seen = [], set()
    for ev in api(f"/orgs/{ORG}/events?per_page=100"):
        if ev.get("type") != "PushEvent":
            continue
        repo = ev["repo"]["name"].split("/", 1)[-1]
        if repo in SKIP_REPOS:
            continue
        p = ev["payload"]
        commits = p.get("commits") or []
        if not commits:
            continue
        sha = commits[-1]["sha"]
        if sha in seen:
            continue
        seen.add(sha)
        branch = p.get("ref", "").replace("refs/heads/", "")
        msg = clean(commits[-1]["message"])
        rows.append(
            f"| [`{repo}`](https://github.com/{ORG}/{repo}) | `{clean(branch, 24)}` "
            f"| [{msg}](https://github.com/{ORG}/{repo}/commit/{sha}) | {ago(ev['created_at'])} |"
        )
        if len(rows) >= MAX_PUSHES:
            break
    if not rows:
        return "No recent public pushes."
    return "| Repo | Branch | Commit | When |\n|---|---|---|---|\n" + "\n".join(rows)


def repos():
    data = api(f"/orgs/{ORG}/repos?type=public&sort=pushed&direction=desc&per_page=30")
    rows = []
    for r in data:
        if r["name"] in SKIP_REPOS or r.get("archived") or r.get("fork"):
            continue
        desc = clean(r.get("description") or "", 90)
        lang = r.get("language") or ""
        rows.append(
            f"| [**{r['name']}**]({r['html_url']}) | {desc} | {lang} | {ago(r['pushed_at'])} |"
        )
        if len(rows) >= MAX_REPOS:
            break
    if not rows:
        return "No public repositories yet."
    return "| Repo | Description | Language | Last push |\n|---|---|---|---|\n" + "\n".join(rows)


def replace(text, name, body):
    pat = re.compile(rf"(<!--{name}:START-->)(.*?)(<!--{name}:END-->)", re.S)
    if not pat.search(text):
        sys.exit(f"Marker {name} is missing in {README}")
    return pat.sub(lambda m: f"{m.group(1)}\n{body}\n{m.group(3)}", text)


with open(README, encoding="utf-8") as f:
    content = f.read()

content = replace(content, "ACTIVITY", pushes())
content = replace(content, "REPOS", repos())

with open(README, "w", encoding="utf-8") as f:
    f.write(content)
print("README updated")
