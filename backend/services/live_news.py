"""Public news retrieval. Missing paid-provider credentials are not an outage."""
import hashlib
import os
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import httpx

status = {}

RSS_FEEDS = [
    ('BBC Business', 'https://feeds.bbci.co.uk/news/business/rss.xml'),
    ('CNBC Finance', 'https://www.cnbc.com/id/10000664/device/rss/rss.html'),
]


def article(title, description, source, url, published):
    text = re.sub(r'<[^>]*>', ' ', f'{title} {description}').strip()
    if len(text) < 3 or not title or title == '[Removed]':
        return None
    try:
        date = datetime.fromisoformat(published.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        try:
            date = parsedate_to_datetime(published)
        except (ValueError, TypeError):
            date = datetime.now(timezone.utc)
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    return {'id': 'live_' + hashlib.sha256(f'{source}|{url or title}'.encode()).hexdigest()[:24],
            'text': text[:12000], 'headline': title[:400], 'source': source[:200],
            'url': url, 'timestamp': date.astimezone(timezone.utc).isoformat()}


def fetch_articles():
    """Prefer a configured NewsAPI account, then key-free publisher RSS."""
    errors = []
    key = os.getenv('NEWS_API_KEY', '').strip()
    if key:
        try:
            response = httpx.get('https://newsapi.org/v2/everything',
                                 params={'q': 'finance economy', 'language': 'en', 'pageSize': 8},
                                 headers={'X-Api-Key': key}, timeout=5)
            response.raise_for_status()
            records = [article(a.get('title', ''), a.get('description') or '',
                               (a.get('source') or {}).get('name') or 'NewsAPI',
                               a.get('url') or '', a.get('publishedAt'))
                       for a in response.json().get('articles', [])]
            records = [a for a in records if a]
            if records:
                return records, 'NewsAPI'
            errors.append('NewsAPI returned no usable articles')
        except (httpx.HTTPError, ValueError, TypeError, AttributeError):
            errors.append('NewsAPI unavailable or invalid')
    for publisher, url in RSS_FEEDS:
        try:
            response = httpx.get(url, timeout=5, follow_redirects=True,
                                 headers={'User-Agent': 'RiskPulseAI/1.0 (local research prototype)'})
            response.raise_for_status()
            root = ElementTree.fromstring(response.content)
            records = [article(item.findtext('title', ''), item.findtext('description', ''),
                               publisher, item.findtext('link', ''), item.findtext('pubDate'))
                       for item in root.findall('.//item')[:8]]
            records = [a for a in records if a]
            if records:
                return records, publisher
            errors.append(f'{publisher} returned no usable articles')
        except (httpx.HTTPError, ElementTree.ParseError, ValueError, TypeError):
            errors.append(f'{publisher} unavailable or invalid')
    raise RuntimeError('; '.join(errors))
