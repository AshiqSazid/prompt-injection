"""Citation inventory; optional free public-page metadata checks (no paid APIs).

Metadata agreement is NOT claim-to-citation or novelty verification. Those
review statuses remain explicit until the cited passages are actually checked.
"""
import _root  # noqa: F401
import argparse
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.request


def field(block, name):
    match = re.search(r'\b' + name + r'\s*=\s*\{', block, re.I)
    if not match:
        return None
    start = match.end()
    depth = 1
    for i in range(start, len(block)):
        if block[i] == '{' and block[i-1] != '\\': depth += 1
        if block[i] == '}' and block[i-1] != '\\': depth -= 1
        if depth == 0: return block[start:i]
    raise ValueError(f'unclosed bibliography field {name}')


def clean(value):
    return re.sub(r'\s+', ' ', (value or '').replace('{', '').replace('}', '')).strip()


class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = {}
        self.in_title = False
        self.title = ''

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            key = attrs.get('name') or attrs.get('property')
            if key and attrs.get('content'):
                self.values.setdefault(key.lower(), []).append(attrs['content'])
        if tag == 'title': self.in_title = True

    def handle_endtag(self, tag):
        if tag == 'title': self.in_title = False

    def handle_data(self, data):
        if self.in_title: self.title += data


def verify(entry):
    if not entry['url']:
        return entry
    try:
        request = urllib.request.Request(entry['url'], headers={'User-Agent': 'Research-artifact-bibliography-audit/1.0'})
        with urllib.request.urlopen(request, timeout=25) as response:
            html = response.read(3_000_000).decode('utf-8', errors='replace')
            entry['resolved_url'] = response.url
        parser = Metadata()
        parser.feed(html)
        title = parser.values.get('citation_title', parser.values.get('og:title', [parser.title]))[0]
        normalize = lambda x: re.sub('[^a-z0-9]', '', clean(x).lower())
        entry.update(observed_title=title, metadata=parser.values,
                     metadata_status='title_matches' if normalize(title) == normalize(entry['title']) else 'manual_review_title_difference')
        # Record authoritative authors/year for comparison, never silently
        # replace publication year with an earlier preprint submission year.
    except Exception as exc:
        entry.update(metadata_status='unverified_fetch_failed', error=f'{type(exc).__name__}: {exc}')
    return entry


def build(online=False):
    bibliography = Path('usenix_paper/refs.bib').read_text()
    manuscript = Path('usenix_paper/main.tex').read_text()
    entries = []
    starts = list(re.finditer(r'^@\w+\{([^,]+),', bibliography, re.M))
    for index, match in enumerate(starts):
        block = bibliography[match.end():starts[index+1].start() if index+1 < len(starts) else len(bibliography)]
        key = match.group(1)
        eprint = field(block, 'eprint')
        urls = re.findall(r'https?://[^\s}]+', block)
        url = 'https://arxiv.org/abs/' + eprint if eprint else urls[0] if urls else None
        if key == 'carlini2021extracting':
            url = 'https://www.usenix.org/conference/usenixsecurity21/presentation/carlini-extracting'
        mentions = [m for m in re.finditer(r'\\cite\w*\{([^}]+)\}', manuscript) if key in m.group(1).split(',')]
        entries.append(dict(key=key, title=clean(field(block, 'title')), author=clean(field(block, 'author')),
                            year=field(block, 'year'), url=url, metadata_status='not_checked',
                            claim_review='pending passage-level verification',
                            contexts=[manuscript[max(0,m.start()-200):m.end()+200] for m in mentions]))
    if online:
        with ThreadPoolExecutor(max_workers=3) as pool:
            entries = list(pool.map(verify, entries))
    keys = [e['key'] for e in entries]
    cited = {k for match in re.finditer(r'\\cite\w*\{([^}]+)\}', manuscript) for k in match.group(1).split(',')}
    return dict(schema_version=1, checked_on='2026-09-28', online=online,
                missing_keys=sorted(cited-set(keys)), duplicate_keys=sorted({k for k in keys if keys.count(k)>1}),
                entries=entries,
                limitation='Metadata reachability/title checking does not establish all authors, venue, date, or claim support. See publication checklist.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-online', action='store_true')
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    result = build(args.verify_online)
    text = json.dumps(result, indent=2, ensure_ascii=False) + '\n'
    if args.write:
        Path('data/bibliography_audit.json').write_text(text)
        print(f"audited {len(result['entries'])} bibliography entries; claim verification remains separate")
    else:
        print(text)
