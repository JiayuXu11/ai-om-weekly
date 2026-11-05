"""Chinese five-dimension offline dashboard (schema v2)."""
import html
import json
import re
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

SECTION_IDS = ['general', 'applications', 'trending', 'om']
LABELS = {'general': '通用新闻', 'applications': 'AI前沿应用', 'trending': 'AI热门研究', 'om': '运营管理 × AI'}
LABELS['ideas'] = '研究选题'


def esc(value):
    return html.escape(str(value), quote=True)


def instant(value):
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('时间必须包含时区')
    return dt


def safe_url(value):
    parsed = urlparse(value)
    if parsed.scheme not in ('https', 'http') or not parsed.netloc:
        raise ValueError('仅允许HTTP/HTTPS信源链接')
    return esc(value)


def link(url, label, cls='source-link'):
    return f'<a class="{cls}" href="{safe_url(url)}" target="_blank" rel="noopener noreferrer">{esc(label)} <span aria-hidden="true">↗</span></a>'


def paras(values):
    if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
        raise ValueError('正文应为字符串数组')
    return ''.join(f'<p>{esc(v)}</p>' for v in values)


def check_date(item, window):
    start, end = instant(window['start']), instant(window['end'])
    day = datetime.fromisoformat(item['event_date']).date()
    if item['date_precision'] == 'timestamp':
        dt = instant(item['event_at'])
        if not start <= dt < end or dt.astimezone(start.tzinfo).date() != day:
            raise ValueError(f'事件日期或窗口错误: {item["id"]}')
    elif item['date_precision'] == 'day':
        dt = datetime.combine(day, time.min, start.tzinfo)
        if dt < start or dt + timedelta(days=1) > end:
            raise ValueError(f'边界日期需要进一步确认时刻: {item["id"]}')
    else:
        raise ValueError('未知日期精度')


def render(data):
    if data.get('schema_version') != 2:
        raise ValueError('四维仪表板需要schema_version=2')
    instant(data['generated_at'])
    sections = data['sections']
    ids = [s['id'] for s in sections]
    if ids not in (SECTION_IDS, SECTION_IDS + ['ideas']):
        raise ValueError('栏目顺序错误')
    if data.get('edition_type') == 'full':
        if ids != SECTION_IDS + ['ideas']:
            raise ValueError('完整周报必须有五栏')
        for section, count in zip(sections[:4], (10, 10, 5, 5)):
            if len(section['items']) != count:
                raise ValueError('完整周报数量应为10/10/5/5；不足请标记partial')
    for name, days in [('news_window', 7), ('paper_window', 30)]:
        window = data[name]
        if instant(window['end']) - instant(window['start']) != timedelta(days=days):
            raise ValueError(f'{name}应为{days}天')
    if instant(data['news_window']['end']) != instant(data['paper_window']['end']):
        raise ValueError('双窗口截止时间必须一致')
    seen, buttons, rendered = set(), [], []
    for section in sections:
        sid, items = section['id'], section['items']
        if sid == 'ideas':
            if len(items) > 3:
                raise ValueError('研究选题最多3个')
            buttons.append(f'<button type="button" class="tab" data-section="ideas" aria-pressed="false"><span class="tab-icon" aria-hidden="true">✧</span>研究选题<span class="count">{len(items)}</span></button>')
            cards = []
            for rank, item in enumerate(items, 1):
                if not item.get('evidence_ids') or not set(item['evidence_ids']) <= seen:
                    raise ValueError('选题必须引用本期已存在条目')
                if not item.get('sources') or not item.get('paragraphs') or not item.get('target_venues'):
                    raise ValueError('选题缺少论证、来源或目标刊会')
                if item['id'] in seen:
                    raise ValueError('选题ID重复')
                seen.add(item['id'])
                refs = ''.join(link(s['url'], s['title']) for s in item['sources'])
                evidence = ' · '.join(item['evidence_ids'])
                cards.append(f'<article class="card" id="item-{esc(item["id"])}"><div class="card-title"><span class="rank">{rank:02d}</span><h3>{esc(item["title"])}</h3></div><p class="meta">拟投方向：{esc(" / ".join(item["target_venues"]))} · 候选构想，尚待查新与验证</p><div class="body">{paras(item["paragraphs"])}</div><p class="meta">本期依据：{esc(evidence)}</p><div class="sources"><span class="source-label">信源与相近工作</span>{refs}</div></article>')
            content = ''.join(cards) or '<div class="empty">本期未提出达到筛选门槛的选题，保留空栏。</div>'
            rendered.append(f'<section class="dimension" id="section-ideas" data-dimension="ideas"><div class="section-heading"><h2>研究选题</h2><span>{len(items)}个候选</span></div><p class="section-desc">{esc(section["description"])}</p>{content}</section>')
            continue
        window = data['news_window'] if sid in SECTION_IDS[:2] else data['paper_window']
        days = 7 if sid in SECTION_IDS[:2] else 30
        if section['window_days'] != days:
            raise ValueError('板块window_days与双窗口不一致')
        label = LABELS[sid]
        buttons.append(f'<button type="button" class="tab" data-section="{sid}" aria-pressed="false"><span class="tab-icon" aria-hidden="true">{["▤", "◇", "▥", "◎"][SECTION_IDS.index(sid)]}</span>{esc(label)}<span class="count">{len(items)}</span></button>')
        cards = []
        last_likes = float('inf')
        for rank, item in enumerate(items, 1):
            if item['id'] in seen or not item['id']:
                raise ValueError('条目ID必须全局唯一且非空')
            seen.add(item['id'])
            check_date(item, window)
            if not item['date_basis'] or not item['summary'] or not item['sources']:
                raise ValueError('卡片缺少日期依据、摘要或信源')
            sources = []
            for source in item['sources']:
                instant(source['accessed_at'])
                caption = source['publisher'] + ' · ' + source['title']
                if source.get('published_date'):
                    caption += ' · ' + source['published_date']
                sources.append(link(source['url'], caption))
            metadata = [item['event_date']]
            likes_badge = ''
            if item.get('research_type'):
                metadata.append(item['research_type'])
            if item.get('status'):
                metadata.append(item['status'])
            if sid == 'trending':
                m = item['metrics']
                if m['platform'] != 'alphaxiv' or m['basis'] != 'current_total_for_recent_papers' or m['field'] != 'metrics.public_total_votes':
                    raise ValueError('AlphaXiv点赞口径错误')
                if not isinstance(m['likes'], int) or isinstance(m['likes'], bool) or m['likes'] < 0 or m['rank'] != rank or m['likes'] > last_likes:
                    raise ValueError('AlphaXiv点赞/名次顺序错误')
                last_likes = m['likes']
                instant(m['captured_at'])
                safe_url(m['feed_url'])
                likes_badge = f'<span class="likes-badge" aria-label="AlphaXiv公开点赞数">♥ {m["likes"]:,}</span>'
                captured = instant(m['captured_at']).astimezone(timezone(timedelta(hours=8)))
                metadata.append('点赞采集 ' + captured.strftime('%m月%d日 %H:%M') + '（香港）')
            elif item.get('heat_label'):
                metadata.append(item['heat_label'])
            original = f'<p class="original">{esc(item["original_title"])}</p>' if item.get('original_title') else ''
            authors = '<p class="authors">' + esc(' · '.join(item['authors'])) + '</p>' if item.get('authors') else ''
            primary = safe_url(item['sources'][0]['url'])
            deep = '<details class="deep"><summary>展开方法深读</summary>' + paras(item['deep_dive']) + '</details>' if item.get('deep_dive') else ''
            evidence = [item['date_basis']]
            if item.get('uncertainty'):
                evidence.append(item['uncertainty'])
            if item.get('ranking_reason'):
                evidence.append('入选说明：' + item['ranking_reason'])
            detail = '<details class="evidence"><summary>研究与证据说明</summary>' + paras(evidence) + '</details>'
            code = link(item['code_url'], '代码仓库') if item.get('code_url') else ''
            cards.append(f'<article class="card" id="item-{esc(item["id"])}"><div class="card-title"><span class="rank">{rank:02d}</span><h3>{esc(item["title"])}</h3>{likes_badge}<a class="external" href="{primary}" target="_blank" rel="noopener noreferrer" aria-label="打开原始信源">↗</a></div>{original}{authors}<p class="meta">{esc(" · ".join(metadata))}</p><div class="body">{paras(item["summary"])}</div><div class="sources" aria-label="信源链接"><span class="source-label">信源</span>{"".join(sources)}{code}</div>{deep}{detail}</article>')
        if sid == 'trending' and len(items) not in (0, 5):
            raise ValueError('热门研究应为5篇；来源不足时使用空栏并说明')
        content = ''.join(cards) or '<div class="empty">本栏暂无已核实条目。' + esc(section['description']) + '</div>'
        rendered.append(f'<section class="dimension" id="section-{sid}" data-dimension="{sid}"><div class="section-heading"><h2>{esc(label)}</h2><span>近{days}天 · {len(items)}条</span></div><p class="section-desc">{esc(section["description"])}</p>{content}</section>')
    coverage = paras(data['coverage'])
    watch = ''.join(f'<li><strong>{esc(w["name"])}</strong> · {esc(w["status"])} {link(w["url"], "跟踪入口") if w.get("url") else ""}</li>' for w in data.get('watchlist_status', []))
    ideas = ''.join('<article class="card"><h3>' + esc(i['title']) + '</h3>' + paras(i['paragraphs']) + '</article>' for i in data.get('ideas', []))
    idea_block = '<section class="ideas"><h2>可讨论的研究问题</h2>' + ideas + '</section>' if ideas else ''
    css = (Path(__file__).resolve().parent.parent / 'assets' / 'dashboard.css').read_text(encoding='utf-8')
    end = instant(data['news_window']['end']).strftime('%Y.%m.%d')
    note = '<aside class="edition-note">' + esc(data['edition_note']) + '</aside>' if data.get('edition_note') else ''
    overview = '<details class="overview"><summary>本期导读</summary>' + paras(data['overview']) + '</details>' if data.get('overview') else ''
    windows = '新闻 / 应用：' + data['news_window']['start'][:10] + '—' + data['news_window']['end'][:10] + ' · 研究：' + data['paper_window']['start'][:10] + '—' + data['paper_window']['end'][:10]
    script = """
const controls=[...document.querySelectorAll('[data-section]')];
const search=document.querySelector('#search');
let active='all';
function update(){
 const q=search.value.trim().toLocaleLowerCase();let matches=0;
 document.querySelectorAll('[data-dimension]').forEach(section=>{
  const selected=active==='all'||section.dataset.dimension===active;
  section.hidden=!selected;
  section.querySelectorAll('.card').forEach(card=>{card.hidden=!!q&&!card.textContent.toLocaleLowerCase().includes(q);if(selected&&!card.hidden)matches++;});
 });
 controls.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.section===active)));
 document.querySelector('#search-status').textContent=q?'找到 '+matches+' 条相关内容':'';
 document.querySelector('#no-results').hidden=!q||matches>0;
}
controls.forEach(b=>b.addEventListener('click',()=>{active=b.dataset.section;update();}));
search.addEventListener('input',update);update();
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&document.activeElement===search){search.value='';update();}});
"""
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(data['title'])}</title><style>{css}</style></head><body><header class="masthead"><a class="brand" href="#top"><span class="brand-mark">简</span>AI × 运营管理<span class="brand-sub">研究周报</span></a><div class="header-actions"><span>{end}</span><a href="#coverage">信源与范围</a><button type="button" onclick="window.print()">打印</button></div></header><main id="top"><div class="issue"><div><span class="eyebrow">每周观察 / 五个维度</span><h1>{esc(data['title'])}</h1><p>{esc(windows)} · 香港时间</p></div></div>{note}<div class="toolbar"><nav class="tabs" aria-label="内容分类">{''.join(buttons)}</nav><div class="search-row"><button type="button" class="all-button" data-section="all" aria-pressed="true">显示全部</button><label for="search" class="sr-only">搜索标题、正文和作者</label><input id="search" type="search" placeholder="搜索标题、正文、作者…"><span id="search-status" role="status"></span></div></div>{overview}<div id="no-results" class="empty" hidden>没有匹配内容，试试其他关键词。</div>{''.join(rendered)}{idea_block}<section class="coverage" id="coverage"><details><summary>信源覆盖与检索范围</summary>{coverage}<ul>{watch}</ul><p>生成时间：{esc(data['generated_at'])}。各时间窗左闭右开，热度为标明采集时刻的快照。</p></details></section></main><footer>AI × 运营管理 · 中文周报 · 原始信源始终可见</footer><script>{script}</script></body></html>"""
