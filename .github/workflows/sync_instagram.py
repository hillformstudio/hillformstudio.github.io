#!/usr/bin/env python3
"""Sync posts for hillform.studio using Meta's Instagram Unified Login.

Runs only on GitHub Actions. Access token stays in the secret environment.
"""
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

IG_ACCOUNT_ID = "17841479898864679"
TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip()
if not TOKEN:
    sys.exit("Missing INSTAGRAM_ACCESS_TOKEN GitHub Actions secret")

# Unified Login / Facebook Graph uses graph.facebook.com and a business IG user ID.
BASE = f"https://graph.facebook.com/v26.0/{IG_ACCOUNT_ID}/media"
query = urlencode({
    "fields": "id,media_type,media_url,thumbnail_url,permalink,caption,timestamp",
    "limit": 12,
})
request = Request(
    BASE + "?" + query,
    headers={
        "Authorization": "Bearer " + TOKEN,
        "Accept": "application/json",
        "User-Agent": "hillform-studio-instagram-sync/1.1",
    },
)
try:
    with urlopen(request, timeout=30) as response:
        payload = json.load(response)
except HTTPError as exc:
    # Never print API error response bodies or secrets into public build logs.
    sys.exit(
        f"Instagram Unified Login API returned HTTP {exc.code}. "
        "Verify Meta token, Instagram account ID, permissions, and app access."
    )
except (URLError, TimeoutError) as exc:
    sys.exit(f"Instagram API connection failed: {type(exc).__name__}")

if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
    sys.exit("Instagram media response missing expected data list")

posts = []
for item in payload["data"]:
    if not isinstance(item, dict):
        continue
    link = str(item.get("permalink") or "")
    if not link.startswith((
        "https://www.instagram.com/p/", "https://www.instagram.com/reel/",
        "https://www.instagram.com/tv/", "https://instagram.com/p/",
        "https://instagram.com/reel/", "https://instagram.com/tv/",
    )):
        continue
    media_type = str(item.get("media_type") or "")
    # Videos display their thumbnail; other posts use the cover image.
    url = str(
        (item.get("thumbnail_url") if media_type == "VIDEO" else item.get("media_url"))
        or item.get("media_url") or ""
    )
    if not url.startswith("https://"):
        continue
    posts.append({
        "id": str(item.get("id") or ""),
        "mediaType": media_type,
        "mediaUrl": url,
        "thumbnailUrl": str(item.get("thumbnail_url") or ""),
        "permalink": link,
        "caption": str(item.get("caption") or "")[:240],
        "timestamp": str(item.get("timestamp") or ""),
    })
if not posts:
    sys.exit("No usable Instagram media returned; keeping existing feed")

posts.sort(key=lambda post: post["timestamp"], reverse=True)
out = Path("data/instagram-feed.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"posts": posts[:6]}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Instagram feed updated: {min(len(posts), 6)} posts; no token stored")
