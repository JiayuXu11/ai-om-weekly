# 五栏编辑与来源规则

## 时间
新闻与应用7天；两类研究30天。记录event_date、date_precision、date_basis与源材料发布日期。时间戳用带偏移ISO8601；只有日期的边界日无法判定则暂不入选。OM论文的first_publication、substantive_revision或public_disclosure要明确，不能用抓取时间冒充发布日。期刊接收、online first和工作稿首发分别记录。

## 通用新闻 / 应用
- Mag7：Microsoft、Apple、Alphabet/Google/DeepMind、Amazon/AWS、Meta、NVIDIA、Tesla。
- 应用重点：Google/Gemini；OpenAI/ChatGPT/Codex；Anthropic/Claude。三家逐一看官方博客和更新日志。其他可看DeepSeek、Qwen、Kimi、MiniMax、Mistral、Cursor、Perplexity、Canva、Adobe、Salesforce、JD等。
- 用实际工作流变化选应用，不把参数榜当应用。可用状态、对象、价格与地区仅在来源明确时写。
- 新闻排序为编辑判断：新鲜度、可核实热度、实质影响；不要混加HN分数、X点赞、GitHub累计stars。未知热度留空，不制造小数总分。
- 公司自报效果注明归属和比较基线。诉讼区分指控、程序裁定、终局判决与和解，原文优先，争议辅以独立报道。

## AlphaXiv榜单
入口：https://www.alphaxiv.org/?sort=Likes&interval=30+Days
公开接口：https://api.alphaxiv.org/papers/v3/feed
查询参数：pageNum=0、sort=Likes、pageSize=100、interval=30 Days、linkBlogs=true、topics=[]。参数和字段可能变化，采集脚本失败必须报告。
核验过的公开计数字段为metrics.public_total_votes；不能用metrics.total_votes、views或GitHub stars替代。
口径：近30天首发候选集，当前累计公开Likes降序。真实新增点赞需要历史端点快照；第一次运行无此数据。
保存请求URL、时间、原始响应、研究ID、类型、原文URL、公开点赞字段和榜单名次。点赞相同保留接口顺序。取得不足5条就说明，不能从旧榜凑。
平台可能收录非arXiv研究博客，使用真实外部原文URL；不凭特殊ID构造不存在的arXiv链接。用户提到的Weight-Space Programming作为检索锚点，不固定置顶，也不长期固定入选。

## OM × AI
关注LLM/agents辅助库存采购、定价、供应链规划、服务运营、平台/电商、人机协作、资源调度、仿真优化、决策学习，以及stylized model分析新模式。
重点作者/机构是检索优先级，不是入选配额；无近30天合格稿时明确“未发现可核实新稿”，而非“没有论文”。作者姓名+主页/合作者/机构交叉消歧。
研究类型：working_paper、preprint、technical_report、research_blog、conference、journal。不能因出自名校/大厂就把预印本写成同行评审结论。
京东、阿里按论文实际作者单位/官方团队署名确认，搜索词出现公司名不等于公司论文。企业产品新闻进入应用，只有研究稿进入此栏。

## 卡片与写作
中文标题+具体事实/机制；普通卡片150–250字，热门研究及OM研究250–450字。证据短标签可以保留，一般局限放入正文末句或“研究详情”，不让冗长免责声明压过信息。
信源行永远可见：来源名称+文章标题链接+日期。论文额外显示英文原标题、作者、研究类型及公开状态；指标需采集时刻。深读可折叠，信源不能折叠。


## Quotas and fallback
Full editions require 10 general news, 10 applications, 5 trending studies, 5 OM studies, and 0-3 ideas. If priority OM authors have too few qualified items, expand arXiv/SSRN to other authors without weakening date and relevance checks. Use partial only after documenting remaining gaps.
