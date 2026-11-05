"""Capture AlphaXiv's 30-day Likes feed without a third-party API key."""
import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

API = 'https://api.alphaxiv.org/papers/v3/feed'
FEED = 'https://www.alphaxiv.org/?sort=Likes&interval=30+Days'


def normalize(papers, captured_at, limit):
    end = datetime.fromisoformat(captured_at.replace('Z', '+00:00'))
    start = end - timedelta(days=30)
    found, skipped, seen = [], [], set()
    for item in papers:
        pid = item.get('universal_paper_id')
        title = item.get('title')
        if not isinstance(pid, str) or not pid or not isinstance(title, str) or not title:
            skipped.append({'id': pid, 'reason': 'missing ID/title'})
            continue
        if pid in seen:
            continue
        seen.add(pid)
        likes = (item.get('metrics') or {}).get('public_total_votes')
        date_text = item.get('first_publication_date')
        try:
            first = datetime.fromisoformat(date_text.replace('Z', '+00:00'))
            if first.tzinfo is None:
                raise ValueError('naive date')
        except (ValueError, AttributeError, TypeError):
            skipped.append({'id': pid, 'reason': 'unverified first-publication time'})
            continue
        if not start <= first < end:
            skipped.append({'id': pid, 'reason': 'outside 30-day window'})
            continue
        if not isinstance(likes, int) or isinstance(likes, bool) or likes < 0:
            skipped.append({'id': pid, 'reason': 'missing public_total_votes'})
            continue
        numeric = bool(re.fullmatch(r'\d{4}\.\d{4,5}', pid))
        external = item.get('external_blog') or item.get('external_link') or {}
        external_url = external.get('source_url') if isinstance(external, dict) else None
        paper_url = 'https://arxiv.org/abs/' + pid if numeric else external_url
        if paper_url and (urlparse(paper_url).scheme not in ('http', 'https') or not urlparse(paper_url).netloc):
            paper_url = None
        found.append({
            'paper_id': pid, 'original_title': title,
            'first_publication_at': date_text,
            'alphaxiv_url': 'https://www.alphaxiv.org/abs/' + pid,
            'original_url': paper_url,
            'research_type': '预印本' if numeric else '研究博客/外部研究材料（需核对原文）',
            'authors': item.get('authors', []),
            'abstract': item.get('abstract', ''),
            'github_url': item.get('github_url'),
            'metrics': {'platform': 'alphaxiv', 'likes': likes,
                        'field': 'metrics.public_total_votes',
                        'basis': 'current_total_for_recent_papers',
                        'captured_at': captured_at, 'feed_url': FEED}
        })
    # Python's stable sorting preserves the feed order on ties.
    found.sort(key=lambda x: -x['metrics']['likes'])
    selected = found[:limit]
    for rank, item in enumerate(selected, 1):
        item['metrics']['rank'] = rank
    return {'captured_at': captured_at, 'feed_url': FEED,
            'window_start': start.isoformat(), 'window_end': end.isoformat(),
            'metric_note': '近30天首发研究的当前累计公开点赞，非30天新增点赞；候选原文仍需逐篇核实。',
            'candidate_count': len(found), 'items': selected, 'skipped': skipped}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limit', type=int, default=5)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.limit <= 100:
        parser.error('--limit must be 1–100')
    url = API + '?' + urlencode({'pageNum': 0, 'sort': 'Likes', 'pageSize': 100,
                                'interval': '30 Days', 'linkBlogs': 'true', 'topics': '[]'})
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
    try:
        with urlopen(req, timeout=30) as response:
            raw = json.load(response)
        if not isinstance(raw, dict) or not isinstance(raw.get('papers'), list) or not raw['papers']:
            raise ValueError('AlphaXiv response missing a nonempty papers list')
        if any(not isinstance(x, dict) for x in raw['papers']):
            raise ValueError('Unexpected paper entry')
        captured = datetime.now(timezone.utc).isoformat()
        result = normalize(raw['papers'], captured, args.limit)
        result['request_url'] = url
        result['scope'] = 'AlphaXiv首个100项Likes排序响应；保存原始响应供复核'
        args.output.parent.mkdir(parents=True, exist_ok=True)
        raw_path = args.output.with_name(args.output.stem + '.raw.json')
        raw_path.write_text(json.dumps({'request_url': url, 'captured_at': captured, 'response': raw}, ensure_ascii=False, indent=2), encoding='utf-8')
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        if len(result['items']) < args.limit:
            print(f'采集不足：要求{args.limit}项，已核实元数据{len(result["items"])}项。见快照缺口。', file=sys.stderr)
            return 2
        print(f'已采集{len(result["items"])}项；当前累计公开点赞，非30天增量。快照：{args.output.resolve()}')
        return 0
    except Exception as exc:
        print(f'AlphaXiv采集失败：{type(exc).__name__}: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
