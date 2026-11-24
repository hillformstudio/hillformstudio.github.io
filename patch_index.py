#!/usr/bin/env python3
"""One-time patch for Hillform website index.html, preserving existing grid design."""
from pathlib import Path
p = Path('index.html')
s = p.read_text(encoding='utf-8')
old = "jsonFeedUrl: '' // example format: https://feeds.behold.so/YOUR_FEED_ID"
new = "jsonFeedUrl: './data/instagram-feed.json' // GitHub Actions-generated public feed"
if old not in s:
    raise SystemExit('Expected feed settings not found; index.html unchanged')
s = s.replace(old, new, 1)
old_check = r"if (!/^https:\/\/feeds\.behold\.so\/[A-Za-z0-9_-]+\/?$/.test(raw)) return;"
new_check = "if (raw !== './data/instagram-feed.json') return;"
if old_check not in s:
    raise SystemExit('Expected feed allowlist not found; index.html unchanged')
s = s.replace(old_check, new_check, 1)
p.write_text(s, encoding='utf-8')
print('Updated index.html for local Instagram JSON feed')
