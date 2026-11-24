#!/usr/bin/env python3
"""Create a public, token-free snapshot of a connected Instagram Business account."""
import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

TOKEN = os.environ.get('INSTAGRAM_ACCESS_TOKEN', '').strip()
if not TOKEN:
    sys.exit('Missing INSTAGRAM_ACCESS_TOKEN secret')

fields = 'id,media_type,media_url,thumbnail_url,permalink,caption,timestamp'
params = urllib.parse.urlencode({'fields': fields, 'limit': 12, 'access_token': TOKEN})
url = f'https://graph.instagram.com/v25.0/me/media?{params}'
req = urllib.request.Request(url, headers={'Accept': 'application/json', 'User-Agent': 'hillform-feed/1.0'})
try:
    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.load(response)
except urllib.error.HTTPError as exc:
    sys.exit(f'Instagram API HTTP {exc.code}; confirm token is current and has media-read permission')
except Exception as exc:
    sys.exit(f'Instagram API unavailable: {type(exc).__name__}')

if not isinstance(result, dict) or not isinstance(result.get('data'), list):
    sys.exit('Instagram response lacked media data')

posts = []
for item in result['data']:
    if not isinstance(item, dict):
        continue
    permalink = str(item.get('permalink') or '')
    if not permalink.startswith(('https://www.instagram.com/p/', 'https://www.instagram.com/reel/', 'https://www.instagram.com/tv/', 'https://instagram.com/p/', 'https://instagram.com/reel/')):
        continue
    kind = str(item.get('media_type') or '')
    image = str((item.get('thumbnail_url') if kind == 'VIDEO' else item.get('media_url')) or item.get('media_url') or '')
    if not image.startswith('https://'):
        continue
    posts.append({'id': str(item.get('id') or ''), 'mediaType': kind, 'mediaUrl': image,
                  'thumbnailUrl': str(item.get('thumbnail_url') or ''), 'permalink': permalink,
                  'caption': str(item.get('caption') or '')[:240], 'timestamp': str(item.get('timestamp') or '')})
if not posts:
    sys.exit('No usable Instagram media returned; retaining current feed')

posts.sort(key=lambda x: x['timestamp'], reverse=True)
output = pathlib.Path('data/instagram-feed.json')
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps({'posts': posts[:6]}, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(f'Snapshot prepared: {min(len(posts), 6)} posts; no access token stored')
