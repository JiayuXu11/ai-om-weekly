# AI × 运营管理周报

面向研究生和课题组的中文研究周报Skill。手动触发，生成可离线阅读、搜索和打印的深蓝卡片式HTML。

| 栏目 | 时间范围 | 数量 |
|---|---|---:|
| 通用新闻 | 最近7个完整自然日 | 10 |
| AI前沿应用 | 最近7个完整自然日 | 10 |
| AlphaXiv热门研究 | 最近30天首发，累计公开Likes排序 | 5 |
| 运营管理 × AI论文 | 最近30个完整自然日 | 5 |
| 研究选题 | 基于本期材料，附相近工作与验证方案 | 0–3 |

重点跟踪沈作军、辛林威、彭一杰、京东和阿里。重点对象不足时扩大到其他作者的arXiv、SSRN等公开工作论文；不要求已正式发表。每张卡片直接显示信源，热门研究突出显示点赞数及采集时刻。

## 安装和使用

将本仓库复制到Codex的skills目录，文件夹名为`ai-om-weekly`，确保`SKILL.md`位于该文件夹根目录。Windows默认位置为`%USERPROFILE%\.codex\skills\ai-om-weekly`。重启或刷新技能列表后，输入：

> 使用 $ai-om-weekly 生成本期中文周报。

Codex按Skill中的编辑规则调用可用网页检索工具、核对原文并编写`report.json`和`research-log.md`。本仓库不是无需模型参与的全自动新闻爬虫；公开榜单采集与HTML渲染是可单独运行的Python脚本。Python 3.9+，仅用标准库。

```text
python -X utf8 scripts/fetch_alphaxiv.py --limit 5 --output output/alphaxiv-snapshot.json
python -X utf8 scripts/render_report.py examples/report.json --output output/report.html
python -m unittest discover -s tests -v
```

`examples/report.json`和`examples/report.html`是2026-11-05的一次采集示例，之后不会自动更新。原始榜单快照保存在示例目录，便于复核点赞。页面不依赖CDN、在线字体或脚本服务。

## 时间、证据与选题

默认香港时间当天00:00截止，明确不含当天。AlphaXiv接口采用采集时滚动30天，需核对入选研究是否同时位于报告窗口。Likes是当前累计公开点赞，**不是过去30天新增点赞**。博客与预印本分开标注。搜索摘要只作发现线索，不能冒充读过正文；访问受限要保留缺口。

研究选题是待查新、待证明的候选。目标MS、OR、MSOM或AI顶会仅表示研究路径，不构成创新性或录用判断。没有可信机制时留空。

完整周报使用`edition_type: full`，渲染器检查10/10/5/5与0–3选题；来源不足用`partial`并披露原因，不能编造补齐。结构检查与浏览器检查不等于事实核验。

详细规则见[SKILL.md](SKILL.md)、[数据结构](references/report-schema.md)和[选题规则](references/idea-generation.md)。
