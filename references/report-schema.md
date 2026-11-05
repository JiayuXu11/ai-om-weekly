# 数据结构 v2
UTF-8 JSON，纯文本字符串，不嵌入任意HTML/Markdown。所有来源url必须http/https。

根对象：
- schema_version: 2
- title：中文标题；generated_at：带时区ISO时间。
- news_window、paper_window：分别含start、end（带时区ISO，7天与30天）；共同截止时间。
- edition_note：可选说明；预览明确标注“设计预览，不是本周完整采集”。
- overview：中文字符串数组。
- sections：固定五个对象，id依次general、applications、trending、om、ideas（兼容旧四栏数据）；每项含title（中文）、description、window_days、items。
- coverage：字符串数组，来源覆盖和缺口。
- watchlist_status：数组，每项name、status、url（可选）；需区分实际检索状态与仅配置。
- edition_type：full / partial / preview。full强制10/10/5/5及第五栏。
- ideas板块items：0–3个，每项id、title、target_venues（数组）、evidence_ids（本期前四栏ID数组）、paragraphs（论证段落）、sources（title/url）。不使用新闻日期字段。旧根对象ideas仅为旧报告兼容，新报告不要使用。

每条item：
- id：全报告唯一；title：中文。
- event_date：YYYY-MM-DD；date_precision：day/timestamp；时间精度timestamp时event_at必填。
- date_basis：所据事件/首发/实质修订/公开披露的依据说明。
- summary：中文段落数组。
- sources：至少一项，每项title、url、publisher、type、published_date（不知则null）、accessed_at（带时区）。
- 可选original_title、authors（数组）、research_type、status（均为中文展示文本）、paper_id、code_url。
- deep_dive：段落数组或[]；uncertainty：字符串或空。
- 可选heat_label、ranking_reason。
- trending必填metrics：platform=alphaxiv、likes（非负整数）、basis=current_total_for_recent_papers、field=metrics.public_total_votes、captured_at、rank（1–5）、feed_url。只表示累计Likes，不能声称30天新增。AlphaXiv地址列入sources。
- trending若无可靠点赞/排名不放假卡片，items=[]，在description/coverage说明。
- OM可选watchlist_matches（重点对象名称数组）；status如“工作论文 / 未正式发表”依据来源填写。

打印输出全部板块。普通页面有五个中文分类按钮、全文搜索、显示全部。每条信源可见，无需展开。details只放方法深读和证据细节。新生成的周报使用v2；旧数据保留原始版本。
