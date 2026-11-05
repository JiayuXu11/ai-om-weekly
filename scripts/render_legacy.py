"""Render an evidence-backed weekly report using only Python's standard library."""
import argparse
import html
import json
import sys
from datetime import datetime, timedelta, time
from pathlib import Path
from urllib.parse import urlparse


def esc(value):
    return html.escape(str(value), quote=True)


def paragraphs(values):
    if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
        raise ValueError('正文须为字符串数组')
    return ''.join(f'<p>{esc(v)}</p>' for v in values)


def instant(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('时间须包含时区')
    return result


def render(data):
    start, end = instant(data['window_start']), instant(data['window_end'])
    if start >= end:
        raise ValueError('时间窗口顺序错误')
    instant(data['generated_at'])
    items = data['items']
    if not 15 <= len(items) <= 20:
        print(f'编辑提醒：本期 {len(items)} 条，目标15–20条', file=sys.stderr)
    deep_count = sum(bool(x['deep_dive']) for x in items)
    if not 2 <= deep_count <= 3:
        print(f'编辑提醒：深读 {deep_count} 篇，目标2–3篇', file=sys.stderr)
    seen, cards, nav = set(), [], []
    for index, item in enumerate(items, 1):
        if not item['id'] or item['id'] in seen:
            raise ValueError('事件id为空或重复')
        seen.add(item['id'])
        day = datetime.fromisoformat(item['event_date']).date()
        if item['date_precision'] == 'timestamp':
            event = instant(item['event_at'])
            if not start <= event < end:
                raise ValueError(f'事件超出窗口：{item["id"]}')
            if event.astimezone(start.tzinfo).date() != day:
                raise ValueError('event_date须为窗口时区的事件日期')
        elif item['date_precision'] == 'day':
            day_start = datetime.combine(day, time.min, start.tzinfo)
            if day_start < start or day_start + timedelta(days=1) > end:
                raise ValueError(f'日期处于窗口边界，需核实时刻：{item["id"]}')
        else:
            raise ValueError('未知日期精度')
        if not item['date_basis'] or not item['sources']:
            raise ValueError('缺少日期依据或来源')
        source_links = []
        for source in item['sources']:
            url = source['url']
            parsed = urlparse(url)
            if parsed.scheme not in ('http', 'https') or not parsed.netloc:
                raise ValueError('来源URL必须为HTTP/HTTPS地址')
            instant(source['accessed_at'])
            source_links.append(f'<li><a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(source["title"])}</a> · {esc(source["publisher"])} · {esc(source["type"])} · 发布 {esc(source["published_date"] or "日期未确认")}</li>')
        scores = item['scores']
        weights = {'freshness': .30, 'heat': .25, 'impact': .30, 'relevance': .15}
        available = []
        for name, weight in weights.items():
            value = scores[name]
            if value is None and name == 'heat':
                continue
            if not isinstance(value, (int, float)) or not 0 <= value <= 5:
                raise ValueError('编辑分须为0–5，只有热度可未知')
            available.append((value, weight))
        expected = sum(v*w for v, w in available) / sum(w for _, w in available)
        if abs(scores['total'] - expected) > .02:
            raise ValueError('编辑总分与权重不一致')
        anchor = f'event-{index}'
        title = esc(item['title'])
        nav.append(f'<li><a href="#{anchor}">{index:02d} {title}</a></li>')
        deep = ('<section class="deep"><h3>方法深读</h3>' + paragraphs(item['deep_dive']) + '</section>') if item['deep_dive'] else ''
        uncertainty = f'<p class="note">证据与范围：{esc(item["uncertainty"])}</p>' if item['uncertainty'] else ''
        cards.append(f'<article id="{anchor}"><div class="meta">{index:02d} / {esc(item["category"])} · {esc(item["event_date"])}</div><h2>{title}</h2>{paragraphs(item["summary"])}{deep}{uncertainty}<details><summary>来源与排序依据</summary><p>{esc(item["date_basis"])}</p><p>热度：{esc(item["heat"])}</p><p>编辑排序：{esc(item["ranking_reason"])}</p><ul>{"".join(source_links)}</ul></details></article>')
    ideas = ''.join(f'<article><h2>{esc(x["title"])}</h2>{paragraphs(x["paragraphs"])}</article>' for x in data['ideas'])
    ideas_section = '<section id="ideas"><h2 class="section-title">可讨论的研究问题 · 编辑设想</h2>' + ideas + '</section>' if ideas else ''
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(data['title'])}</title>
<style>
:root{{color-scheme:light;--ink:#192b35;--muted:#526571;--accent:#096e70;--paper:#f3f5f3}}*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.85 "Microsoft YaHei",system-ui,sans-serif}}header,main,footer{{max-width:1060px;margin:auto;padding:36px 26px}}header{{padding-top:56px}}.eyebrow,.meta{{color:var(--accent);font-size:13px;font-weight:650}}h1{{font-size:clamp(28px,4vw,44px);line-height:1.3;margin:12px 0}}h2{{font-size:23px;line-height:1.5;margin:12px 0}}h3{{font-size:18px}}p{{margin:12px 0}}a{{color:var(--accent);overflow-wrap:anywhere}}.sub,.note{{color:var(--muted);font-size:14px}}.layout{{display:grid;grid-template-columns:235px minmax(0,1fr);gap:28px}}nav{{align-self:start;position:sticky;top:20px;font-size:13px;max-height:90vh;overflow:auto}}nav ol{{list-style:none;padding:0}}nav li{{margin:0 0 12px}}nav a{{text-decoration:none}}article,.overview,.coverage{{background:white;border:1px solid #dce4e1;border-radius:12px;padding:26px;margin-bottom:20px;overflow-wrap:anywhere}}article{{scroll-margin-top:20px}}.deep{{border-left:3px solid var(--accent);padding-left:20px;margin-top:24px}}details{{font-size:13px;color:var(--muted);border-top:1px solid #e3e8e5;padding-top:14px;margin-top:20px}}summary{{cursor:pointer;color:var(--accent)}}.section-title{{margin:32px 0 20px}}footer{{font-size:12px;color:var(--muted)}}@media(max-width:760px){{.layout{{display:block}}nav{{position:static;max-height:none}}header,main,footer{{padding:24px 18px}}article{{padding:20px}}}}@media print{{body{{background:white;font-size:11pt}}nav{{display:none}}.layout{{display:block}}header,main,footer{{max-width:none;padding:10px}}article{{border-radius:0;break-inside:auto}}h2,h3{{break-after:avoid}}details{{display:block}}details>*{{display:block}}a{{color:#164b59}}}}
</style></head><body><header><div class="eyebrow">AI × OPERATIONS / WEEKLY BRIEF</div><h1>{esc(data['title'])}</h1><p class="sub">窗口：{esc(data['window_start'])} 至 {esc(data['window_end'])}（左闭右开）<br>{len(items)} 条动态 · {deep_count} 篇方法深读 · 生成于 {esc(data['generated_at'])}</p></header><main><section class="overview"><h2>本周重点</h2>{paragraphs(data['overview'])}</section><div class="layout"><nav aria-label="周报目录"><strong>本期目录</strong><ol>{''.join(nav)}</ol>{'<a href="#ideas">研究讨论</a>' if ideas else ''}<p><a href="#coverage">来源覆盖</a></p></nav><div>{''.join(cards)}{ideas_section}<section id="coverage" class="coverage"><h2>来源覆盖与缺口</h2>{paragraphs(data['coverage'])}</section></div></div></main><footer>本报告保留来源链接。企业自报、编辑解读与候选研究问题须按正文标识理解。</footer></body></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding='utf-8-sig'))
    result = render(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result, encoding='utf-8')
    print(f'HTML已生成：{args.output.resolve()}')


if __name__ == '__main__':
    main()
