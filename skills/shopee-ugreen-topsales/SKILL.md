---
name: shopee-ugreen-topsales
description: 接管人工已打开的原 Chrome，采集 PH UGREEN 全店 Top Sales，在日期 Git worktree 发布四表 Excel 和每日 PDF 分析，覆盖月销/价格变化、7/30日趋势、新出现链接、价格段与动销。A 使用普通 Playwright，B 使用电脑操作 CUA；也支持抽测或既有表分析。
---

# Shopee UGREEN Top Sales

## 1. 两条网页路线，同一业务链路

- **A：普通 Playwright，接管人工已打开的原 Chrome。**
- **B：电脑操作 CUA，接管人工已打开的原 Chrome。** 必要时通过原页面 DevTools
  执行只读表达式，读取 DOM 和商品内嵌 JSON。

默认 A；用户指定 B，或 A 工具不可用且原页正常时使用 B。用户指定路线时遵从，
不重复本轮不需要的备用路线。网站挑战不是切换工具重试的理由。

两条路线均沿用原浏览器和登录状态，不做指纹伪装、地区查询、初始化脚本注入，
不覆盖 UA、语言、时区、GPU、屏幕或其他浏览器属性。指纹整套实现已按用户要求删除。
读取 DOM/当前商品 JSON 的只读表达式是取数，不是修改浏览器环境。

不复制 Cookie/Storage/profile，不启动替代 Chrome/context/采集标签，不重启 Chrome，
不擅自开放调试端口、安装扩展或修改系统代理。按用户 2026-09-23 的要求，A 绑定已打开且
指定用于采集的原标签集合；某页风控后保留原页，保存并接管下一个原标签，不操作账号登录切换。
单页或全部不可用时立即断开、保存并等用户明确继续后重新验收。普通超时、加载或解析失败由宿主自动
诊断恢复，不要求用户回复“继续”；不将工具时限或 Page Unavailable 冒充验证码。

```text
读规范与参数 → 全量任务准备日期 worktree
  → A 普通 Playwright / B 电脑操作 CUA：接管原 Chrome
  → 全部列表 → 全部唯一详情（每 50 件保存累计进度 Excel，停止时补存尾批）→ 内存载荷
  → stdin 严格发布 → Excel 独立验收 → 每日分析 → 报告验收 → 四表 Excel + PDF
```

## 2. 范围和规范入口

默认地址 `https://shopee.ph/ugreen.ph?page=0&sortBy=sales&tab=0`；店铺 `64922227`，
国家 PH，币种 PHP。当前发布代码不支持其他店铺/国家，不将其他站点数据塞入 PH 合同。

| 用户请求 | 执行范围 |
| --- | --- |
| 跑一遍、完整执行、刷新全店 | 本轮全部列表、全部唯一详情、完整四表、每日 PDF 分析与独立验收 |
| 明确抽测几页/几件、试字段、只文字 | 按约定数量；没给数量则少量代表性样本，不创建 worktree、不发布部分表 |
| 分析既有 Excel | 只读指定源表和合格历史；要求输出时生成指定日期分析 PDF，不访问网页或改写源表 |
| 整理 Skill、解释脚本 | 仅维护/解释，不因此启动采集或创建日期运行 |

先完整读取 [标准任务书](assets/run_prompt_template.md)，再按任务读取：

| 文件 | 用途 |
| --- | --- |
| [worktree.md](references/worktree.md) | 全量必读：日期身份、Git 边界、目录和生命周期 |
| [capture-protocol.md](references/capture-protocol.md) | 全量和抽测必读：现场字段、类型和内存交接 |
| [excel-output.md](references/excel-output.md) | 全量和抽测必读：四表逐列口径及 17 项验收 |
| [daily-analysis.md](references/daily-analysis.md) | 全量交付/既有表分析必读：每日变化、7/30 日趋势、新出现链接、金额代理、价格段与动销 |
| [cua-fallback.md](references/cua-fallback.md) | 使用 B 前必读：DevTools 只读采集、分块回传和验收 |
| [ugreen_topsales.xlsx](assets/ugreen_topsales.xlsx) | 只读内容规范，不是业务数据种子 |
| [verified_access.md](references/verified_access.md) | 已发生的验证与历史证据，不覆盖当前流程 |

不另建平行 spec，不修改冻结任务书或另存任务书副本。完整任务不能因字段难取而
自动缩减为抽测，不从其他轮次 Excel/历史 URL/网上另找图片补齐本轮事实。
明确续跑时可按第 8 节恢复本轮已保存的累计进度，不把已采数据当作必须重抓的历史种子。

## 3. 本地入口与日期准备

公开入口 `scripts/run_scrape.py` 只负责计划、准备、stdin 进度保存/发布和独立验收，不自动操作
浏览器。主项目解释器为 `.venv/bin/python`；依赖见 `pyproject.toml`。

```text
.venv/bin/python skills/shopee-ugreen-topsales/scripts/run_scrape.py --plan
.venv/bin/python skills/shopee-ugreen-topsales/scripts/run_scrape.py --check-contract
```

无参数等同 --plan；awaiting_browser_collection 不是已经采集。--check-contract 检查
所列规范路径和模板 schema/哈希，不证明浏览器连通，也不替代完整阅读必需文档。

全量经 --prepare 自动提交现有改动并创建/更新上海本日 worktree；抽测跳过。绑定回执的
project_root/worktree/branch/python/runner/output/source_head/worktree_head。
不以脏状态或 HEAD 不同阻断采集和发布；日期分支保持正确，Python 来自主根，发布 runner 来自
目标日期目录。prepare 后沿用启动日，跨午夜不重建另一轮身份。

正式结果：`worktrees/YYYYMMDD_ugreen_topsales/result/ugreen_topsales.xlsx`，
以及同目录 `ugreen_topsales_analysis.pdf` 每日分析报告。
采集中累计进度表：同目录 `ugreen_topsales_progress.xlsx`，与全量正式结果区分。
日期工作区包含完整 Skill/源码；任务准备自动提交主项目和本日工作区的现有改动，
再快进或正常合并主项目版本，不重复请求授权。模板、规范在采集中只读；保留已有
改动和结果，不 stash/reset/clean、不删除冲突文件或改其他日期。实际 Git 失败或合并
冲突才报告处理，具体流程见 worktree.md。

## 4. S2-A：普通 Playwright 接管原 Chrome

1. 阅读当前可用的 Playwright Skill/工具文档，定位用户指定用于采集的已打开原标签，
   按稳定顺序绑定唯一页面对象集合，核对店铺身份、Top Sales 和当前页；只有一页也适用。
   不盲用 contexts[0].pages[0]，不将空白页、无关店铺或账号管理页纳入。只读 URL 枚举不是
   页面可用性证明；每次接管候选页仍先检查当前 URL/DOM。不得自动扩充集合或新建页面。
2. 使用已有原会话连接能力，不调用 launch、launch_persistent_context、new_context
   或新建采集页。连接不可用时报告具体缺口；需用户开启调试/授权时交用户，不自行改设置。
   只允许持续长连接：同一轮初始化、能力检查、列表与详情采集和进度保存
   复用持续附着连接和已绑定原标签，同一时刻只操作其中一页。检查成功后直接沿用，不做“短连检查即断开”，
   不按工具调用、页面或批次重建 Playwright，不因保存或失焦重连。远程调试已经
   允许后不重复点击或触发授权；仅结束、用户停止、全部标签不可用或连接实际损坏时释放。
   已打开的其他 Chrome 窗口若不在当前连接内，只能使用其已有且已获授权的连接地址；
   看不到就如实报告，不自动开放端口、读取 profile 或声称已接管所有窗口。
3. 本机 Python Playwright 1.63.0 已验证可用
   `chromium.connect_over_cdp("chrome", no_defaults=True)` 附着用户已开启远程调试的 Chrome。
   no_defaults 避免默认上下文覆盖；不额外设置浏览器环境或 init script。
   它不是所有机器的通用保证，也不证明此前外部修改已恢复。
4. **默认完整 DOM 直读，不发送鼠标移动或滚轮。** 这是用户在 2026-09-22 确认沿用的
   现场办法，不必先尝试旧滚轮路线或等它超时才直读。每次导航前随机等待 2～3 秒，
   读取当前完整 DOM 并执行 `check_html(html,page.url)`，确认没有验证页且身份正常后，
   才按本轮真实链接 `page.goto(url, wait_until="domcontentloaded", timeout=30000)`。
   导航后随机驻留 2～4 秒，再 `page.content()` 取得完整 DOM；先检查实际 URL、
   挑战和页面完整性，再将这次 DOM 交给离线解析器。详情需核对 shop/item、当前 PDP、
   全部 model 和图库，不因直读省略验收；导航前的 DOM 不作下一件商品的数据。
   DOM 单次读取上限沿用现场 20 秒，导航自身上限 30 秒（宿主外层保护 35 秒）；
   记录超时发生的具体操作，按第 7 项恢复。不要给整段采集或写表套 20/35 秒总时限。
   驻留示例：`time.sleep(rng.uniform(2, 4))`，使用最终秒数、不再缩放，随后完整读页与检查；
   所有取数仅留内存。当前已验证的宿主长进程可跨工具调用保留 pages/details/待办与保存器，
   后续轮询只查看宿主进度，不因此重连、重新导航或重复读取网页。
   页面后台或 `hasFocus=false` 本身不是暂停条件，也不因此切换标签或抢回焦点；仅在诊断
   必要时通过 `evaluate` 只读 `document.visibilityState/document.hasFocus()`。
   [page_browse.py](scripts/page_browse.py) 的 `read_page_after_browsing` 保留为显式滚轮浏览
   的可选辅助函数，不属于默认采集步骤。需要使用时先核对原页内容视口落点，事件返回
   不代表实测滚动完成，不用它处理验证或在完整 DOM 已可读时反复尝试输入。
   不以 locator/click/evaluate 打开图库、选择规格或逐项读取，不执行 JS 滚动或环境注入；
   不读取 Cookie/密码/Storage、整份账号状态或隐藏网络接口。
   结束只断开附着连接，不关闭用户 page/context/Chrome。
5. 统一采用完整 DOM 直读、单路串行：导航前随机 2～3 秒，加载后驻留 2～4 秒，
   普通重读退避 5/10 秒。以上均为最终秒数，由宿主直接使用，不重复缩放。
   每完成 50 件累计保存进度，
   保存成功后继续，不再额外冷却。用户在 2026-09-22 后续要求取消每 50 件暂停，保存频率不变。
   旧 2.5/5 倍执行规则已替换。本次按用户要求只整理 Skill 和配套执行说明，不修改生产脚本；
   [pacing.py](scripts/pacing.py) 和 `--plan` 的节奏元数据仍为旧值，不能据此覆盖本节。
   不把上述最终秒数传入旧缩放函数。默认不操作滚轮；可选滚轮的旧内部等待也不代表本节节奏。
   多标签不增加并发，不因接管下一页减少等待或重置恢复预算。
   加载/操作超时上限、重试次数、每 50 件保存及所有身份/完整性检查不缩减。
   该节奏是保守的实测选择，尚无足够对照证明最优吞吐或最低验证率，不承诺免验证码。
   调速不解除全部标签不可用后的暂停，仍须用户明确继续后才重新附着。
6. 宿主按用户指定的原标签集合维护内存状态 `ready / blocked / closed`，同时只接管一页。
   集合大小按实际已打开且可连接的标签数，不硬编码为 4；四页时按本规则依次接管，
   一页时保持原交接。当前有明确正常的目标页时优先从该页开始，再沿绑定顺序使用其余页。
   账号名称不参与选择，不读取、核实或更改 Google/Shopee 登录身份。
   按第 8 节绑定保存器后，外层继续使用原有交接器：

   ```python
   control = BrowserHandoff(pw.stop, on_handoff=lambda: saver.maybe_save(force=True))
   control.run(采集循环)
   ```

   多标签顺序接管由宿主的**单件读取层**负责，生产 CLI 和现有 `BrowserHandoff` 不自动枚举或
   切页。捕获单件的挑战后，先检查是否还有候选；有候选时在外层交接器收到异常之前处理，
   无候选才将异常继续抛给外层，避免第一张受限页就断开整条连接。
   单件函数先检查当前页，再导航、有限恢复、完整验收；仅成功返回后提交记录与推进保存计数。
   URL/DOM 只有实际验证码/人工验证/访问限制才抛 `page_browse.CaptchaDetected`。
   当前页立即停止操作并标记 blocked，保存尾批成功后，顺序接管下一个已绑定原标签；
   先核验该页再进入当前待办，同轮按身份求差续采，不重抓已完成详情、不重置普通重试预算。
   不点击浏览器账号、不读取账号凭据、不登录退出、不切代理、不新建页、不自动解验证码。
   同一标签受限后本轮不再回访、读取或刷新，也不因它自行恢复自动启用；不循环到第一页。
   原标签已关闭可标记 closed 并跳过，不能把关闭或普通加载错误说成风控。
   因关闭而无可用候选时，宿主显式断开、保存并停止，报告关闭原因，不伪抛挑战异常。
   只有一页或全部候选不可用时，沿用 `BrowserHandoff` 先断开、保存再交用户；用户主动
   停止也立即释放。普通异常仍在当前页有限恢复，不切页、不锁定 `waiting_for_user`。
   切页前保存失败由宿主显式断开并锁定停止状态，保留内存和上一份有效表，不访问下一页；
   不能仅抛出普通保存异常后又自动恢复采集。
   断开回调只释放本采集器持有的附着连接（同一个 Playwright 为 `pw.stop()`），
   不用 `browser/context/page.close()`，保留原页。全部停止后锁定等待用户。
   断开失败须报“连接状态未确认”，不能宣称已脱离；仍尝试保存数据，不因断连异常丢弃尾批。
   等待期间不读取/轮询页面、不自动重连；验证码消失或计时结束都不是续跑信号。
   只有用户明确回复继续后才重新附着、绑定新控制器，重新核验指定原标签；仍受限的页
   标记后跳过，全部不可用再次断开。B 沿用原单页人工交接，不以网站挑战为理由改用 B。
   断开只释放本采集器的连接，不声称清除了此前接管影响或其他客户端连接；现有检查
   触发即处理，不承诺验证码出现后毫秒级检测。
7. 普通错误恢复：优先沿用当前连接，先读取当前 URL/完整 DOM 检查验证码，再按身份和
   字段验收。`goto` 超时先读当前 DOM，若已完整则继续解析，不把超时本身当失败或验证码。
   空白/加载中页面、缺少当前 PDP、残留 ShopPage 或内嵌 JSON 截断时，先离线检查已有 DOM；
   正常无挑战的页面最多追加两次完整读取，常规循环内仅允许一次同一本轮详情 URL 的正常重载，
   其余读取前退避 5/10 秒。仍未恢复时，宿主离线诊断确认确属普通加载问题后可用第二次、也是
   最后一次正常重载；同一商品不得通过重开循环重置重试预算。不得补齐/猜测截断 JSON，
   每次取得新 DOM 后重新核对身份和完整字段，通过后才加入 details 并推进保存计数。
   普通异常先补存尾批再自动诊断，不要求用户回复继续；耗尽有限恢复仍缺必需字段时保留
   为未完成并说明具体缺口。若显式滚轮操作超时而新 DOM 完整，可直接验收继续，不谎报滚动成功。
   仅连接实际失效才释放旧附着并自动接回原标签；工具持续不可用且原页正常时可按 B
   恢复。仍无法取得的必需字段保留为未完成，保存进度并说明具体结果，不补造数据。
   登录和网站访问限制不能绕过，不能借普通错误恢复自动解验证或循环刷新网站阻断页。

直接读取已在真实环境抽测成功，见第 9 节。新的未验证实现仍先做隔离最小实验，
成功后再最小接入项目并回归；离线测试不代替真实链路证据。

## 5. S2-B：电脑操作接管原 Chrome

完整读取 [CUA 方法](references/cua-fallback.md)。绑定人工已打开的原窗口/标签，
正常操作页面；必要时打开原 DevTools Console 只读取得商品 DOM/内嵌 JSON。
只用实际支持的 API 和最新界面状态，不根据截图猜字段，不将输入回显或截断预览
当结果。分块返回须核验本次 tag、连续索引、完整文本和商品身份，结果仅保留在内存。

B 不配置浏览器环境；它是 CUA，不应声称为 Playwright。两条路线共用字段、节流、
网站挑战处理、日期和完整性要求，不为 B 另建一套表或降低范围。

## 6. S3：实时全部列表

1. 从 page=0 / 可见第 1 页 Top Sales 开始，限定 `.shop-search-result-view a.contents`，
   排除推荐区。匹配零项须核查选择器/页面，不能当作零商品。
2. 取实际 a.href 与 shop/item 身份；标题取商品 img.alt，排除 custom-overlay、
   flag-label、rating-star。当前列表价必须明确唯一，不用折扣、划线价、分期金额替代。
3. 月销取完整 N Sold/Month 原文；确实未展示才 null，真实 0 保留，累计 Sold 不作月销。
   当前价格/月销来自列表，不扩张为每个 SKU 的价格或销量。
4. 读当前页、总页和下一页实际禁用状态，等卡片更新后收录。非末页 30 卡，末页 1～30；
   页码连续、总页数一致、不凑数、不硬编码历史页数。
5. pages 保留各页顺序；按 (shop_id,item_id) 首次出现顺序去重生成详情待办。同页重复
   拒绝，跨页真实重复计数，每个后续页须有新身份。

list_html.parse_list_html 可解析内存 HTML，其大小/挑战检查仍须核验；不能为复用
解析器启动复制 profile 的浏览器，HTML 不落盘。

## 7. S4：详情、真实 SKU 和图库

每个列表唯一商品恰有一条详情。按本轮真实链接进入，核对 URL、shop/item 身份，
canonical/og 存在也核对。当前页面常见数据路径：

```text
script[type="text/mfe-initial-data"] JSON
└── initialState.DOMAIN_PDP.data.PDP_BFF_DATA
    ├── currentKey
    └── cachedMap[currentKey]
        ├── item：shop_id/item_id、title/name、models[]、tier_variations[]
        └── product_images.images[]
```

有 currentKey 必须绑定该项并匹配身份；没有时仅接受唯一匹配候选。SPA 跳转后初始
数据仍是 ShopPage，仅在页面正常无挑战时，在原标签完整加载同一本轮详情 URL 一次
再验收；不循环刷新、不改抓隐藏接口。

- 标题取当前详情标题，不沿用列表/历史标题代替。
- 完整真实 models 的 ID 为纯数字文本、查重、保留实际顺序。用 extinfo.tier_index
  或 tier_index 映射每层 tier_variations.options，校验维数、整数边界和非空规格名。
  不用单个 display_model_id、选项笛卡尔积或 {"SKU": model_id} 占位；仍公开的禁用
  model 不能漏掉。普通选项文字是规格值，不是图片 ID。唯一例外：恰有一个真实 model、
  恰有一层规格，且 tier 名称、唯一 option、model 名称均为空时，写
  `{"规格":"单规格"}`；多个 model 或解析失败不得套用。
- SKU 图先核对具体 model/extinfo 的 `sku_image/image/image_id`；仅当这些直接字段全空时，
  才按 tier_index 使用 tier 图片。空字符串不是有效候选；同一优先级内部冲突仍停止，
  只有确认无专属图才 null，未取到不等于无图。
- 图库取 product_images.images 或已验证完整的 item.images；单个 item.image 不证明
  副图完整。A 从完整 DOM/内嵌数据读取，不打开查看器；排除视频封面、评论、推荐和覆盖图。
- URL 优先使用当前 DOM/页面数据中的实际完整值，并用图片 ID 精确对应有序图库。只有
  权威图库/model/tier 字段给出图片 ID、同一完整 DOM 又没有该 ID 的绝对原图 URL 时，
  才对这个缺失项生成 `https://down-ph.img.susercontent.com/file/<图片ID>`；不得覆盖已有
  URL、去缩略后缀、改变顺序或给非权威字符串套域名。首张为主图，余图按原序去重；
  SKU 可共享真实映射图。允许域名和最终 URL 形状见 capture-protocol.md。

models_complete/gallery_complete 只有完整现场证据才设 true；声明和结构检查不是
来源证明。任一未解决缺失不能发布全量正式表，但必须按第 8 节保存已取得的进度。

## 8. S5～S7：内存发布、独立验收与每日分析

### 采集中与停止时保存（长期默认规则）

- “50 条”指 50 件已完成并验收的唯一商品详情，不是 SKU 行、图片行或列表卡。
  在累计第 50、100、150…件后，进入下一件之前保存；保存成功后继续，不额外冷却。列表读取完成也保存一次。
  停止、验证码、异常、正常结束时补存当前全部数据，包括不足 50 件的尾批。
- 同一轮累计、原子更新 `result/ugreen_topsales_progress.xlsx`，不生成每批独立文件。
  保存已取得的全部列表记录及已完成详情；未采集详情明确标注，字段不补零或占位 SKU。
  即使全部详情已取得，进度表仍不是全量验收通过的正式结果。四表进度口径见
  [excel-output.md 第 7 节](references/excel-output.md#7-累计进度-excel)。
- 宿主用 `checkpoint_result.CheckpointSaver(snapshot_factory, save, saved_count=已成功保存详情数)`，
  每件详情加入内存后调用 `saver.maybe_save()`；停止/结束调用 `saver.maybe_save(force=True)`。
  `snapshot_factory` 每次返回本轮当前载荷，`save` 调用 `write_snapshot` 或下述 stdin 入口。
  仅保存成功、回读核对通过才推进保存计数；续跑从 58 件开始，下次仍在 100 件保存。
- 从主根入口执行 `ROOT_RUNNER --checkpoint-stdin --project-root ROOT --worktree DAILY`，
  stdin 结构沿用下方载荷；仅进度入口允许连续的已取得列表前缀与详情子集。
  `captured_at` 在进度表中标为保存时间，不伪称此时重新读取过页面。JSON 仅走内存/管道。
  开始新增采集前确认写表所需的 Node 和运行时 `@oai/artifact-tool` 可用；渲染器读取
  `UGREEN_ARTIFACT_NODE_MODULES`，未设置时使用 Codex 运行时依赖缓存，不改依赖目录。
- 进度写入保留日期注册、启动日、路径与字段检查；允许主根有维护改动时先保存已有数据，
  不要求为了保全数据先提交 Git，不热补日期源码。正式发布也不检查 clean/同 HEAD。
- 多页风控先停止操作受限页、保存尾批再接管下一页；单页、全部不可用或停止时先断开再保存。
  保存失败保留上一份有效进度表、内存和暂停状态，报告失败，
  不继续采集。未知文件、其他轮次或会丢失已保存身份/详情的覆盖必须拒绝。

### 进程重启后的断点续采

- 每次累计保存同时在同一个进度 `.xlsx` 内写入带版本和校验值的恢复部件，保存完整
  pages/details/启动时间；四张可见表不增列、不增表，也不另存 JSON/HTML 或浏览器会话。
  候选文件的恢复部件和全部业务单元格都回读通过后才原子替换，因此数据与断点一起提交。
- “继续”先沿用原启动日，调用主根 `--resume-checkpoint --project-root ROOT --worktree DAILY`
  只读验证；不重新 `--prepare`、不重建当天目录、不从第 1 件重抓。宿主调用
  `checkpoint_resume.load_checkpoint(ROOT, DAILY)` 取得 `payload/pending_cards/saved_count/origin`，
  用保存的 started_at/pages/details 重新绑定内存和保存器。待办按 shop/item 身份集合求差，
  不用 `列表[已完成数量:]` 猜位置。680 件恢复后的下次保存点仍是 700，而不是 730。
  仅恢复未必已读完的列表前缀时，还需继续原分页，再完成全部详情。
- 无内嵌恢复部件的旧版表不能静默降级。用户明确授权迁移这份本轮文件时，先核对 SHA-256，
  将其传给 CLI 的 `--legacy-checkpoint-sha256` 或 `load_checkpoint(..., legacy_sha256=...)`。
  旧版迁移必须逐业务单元格往返一致、ID/链接/计数/日期完整，并保留 origin 的限制说明：
  已完成商品只剩详情标题，列表页 URL 规范化，规格仅从未转义展示值拆解；不宣称还原原始
  DOM、原列表标题或未保存字段边界。跨页重复信息丢失或规格不能安全拆解时拒绝迁移，
  不猜造；部件存在但损坏时也不能退回旧版解析。新保存将内嵌完整恢复对象，后续不再拆展示文本。
- 验证恢复只读磁盘、不接触浏览器；没有伪造“重新现场读取”。已保存详情继续保留，
  新详情仍按当前页面取数和验收。验证码暂停仍需用户明确继续后核验原页，恢复文件不解除它。
- 恢复部件与可见表不一致、来源/日期不符、文件被编辑破坏或保存失败，保留原文件并报告
  具体缺口；不得覆盖成较少的数据，也不得自动重抓全店。普通恢复故障先自主诊断。

### 完整结果发布

依 capture-protocol.md 构造精确字段的内存对象：

```text
payload: schema_version、store_url、started_at、captured_at、pages、details
pages[]: page_index、total_pages、url、next_enabled、cards
cards[]: product_url、title、price_php、monthly_sales_text
details[]: product_url、title、skus、main_image_url、secondary_image_urls、
           models_complete、gallery_complete
skus[]: model_id、sku_props、sku_image_url
```

不附加路线、账号、凭据、capture_tag、audit、历史表路径或模型自填排名。
使用 prepare 回执中的解释器、日期 runner 和路径，以 direct argv/stdin 交接：

```text
argv = [PYTHON, DAILY_RUNNER, "--publish-stdin", "--project-root", ROOT, "--worktree", DAILY]
cwd = DAILY
stdin = 本轮完整 UTF-8 JSON
```

不拼接 shell、不保存载荷、不直接调用 write_excel 绕过门禁。发布层严格转换、
重算排名/审计，检查日期/路径/模板，锁内构建受控候选，回读和独立校验后原子
替换正式文件。替换前失败保留旧结果，不能交旧表冒充本次成功。

四表固定为商品汇总、SKU明细、图片明细、抓取核验；表头第 6 行、数据第 7 行起，
ID 为文本、价格为数值、未展示月销为空、外部文字不得生成公式。图片是链接，不是
内嵌图片。逐列、顺序、冻结窗格与 17 项核验以 excel-output.md 为准。

发布退出 0 后先生成分析报告（内部独立重开验收 Excel），再运行最终独立验收：

```text
argv = [PYTHON, ROOT_RUNNER, "--analyze", "--project-root", ROOT, "--worktree", DAILY]
argv = [PYTHON, ROOT_RUNNER, "--validate", "--project-root", ROOT, "--worktree", DAILY]
argv = [PYTHON, ROOT_RUNNER, "--archive", "--project-root", ROOT, "--worktree", DAILY]
cwd = DAILY
```

核对 collection_mode=full_topsales、audit_status=通过、计数一致、
result 只含正式表、规定分析 PDF 及可选进度表。Excel 验收只证明内部一致，必须结合本轮全部现场覆盖。

### 每日分析与共同交付

全量任务在正式 Excel 发布后继续读取 [每日分析合同](references/daily-analysis.md)，执行
`ROOT_RUNNER --analyze --project-root ROOT --worktree DAILY`（分析器先验收源表），再执行同一入口的 `--validate`。
报告回执和独立验收中的 `analysis.analysis_status` 均须为“通过”；随后 `--archive` 成对提交 Excel/PDF 到日期分支，回读哈希通过后交付。

报告必须覆盖每个产品月销及价格的日变化值/变化率、7/30 日趋势，店铺月销上涨/下滑链接数、
新出现链接与 30 日趋势、可观测总月销、估算月销额、每个产品单件价格/客单价代理、固定价格段
销量占比与链接动销。月销是滚动展示下界，不能由差值反推当天订单；真实订单客单价和上架时间
没有来源时不编造。历史不足照样交付基线报告，缺口明确留空，不补零、不造趋势。
只读取验收通过的完整历史 Excel，按店铺/商品 ID 关联，不改 Excel 内容、不增加工作表。
补分析明确指定的旧日期时用主根新入口，不热补历史源码或重新采集。结果固定为
`DAILY/result/ugreen_topsales_analysis.pdf`，完整定义、默认价格段、来源和复算验收见上述合同。

## 9. 实现边界、证据与交付

| 文件 | 当前作用 |
| --- | --- |
| run_scrape.py / prepare_daily_worktree.py | 计划、规范检查、日期准备、stdin 分派 |
| publish_result.py / excel.py / validate_result.py | 严格转换、门禁、四表发布与独立验收 |
| analysis_pdf.py / snapshot_history.py | PDF 确定性排版与中文字体、日期分支成对归档、按采集时间回读 Git 历史 |
| analysis_report.py | 只读每日完整快照，计算跨日指标和 7/30 日趋势，发布及复算验收 PDF |
| checkpoint_result.py / checkpoint_excel.mjs | 每 50 件与停止尾批的累计进度 Excel、原子替换和逐单元格回读；不联网 |
| checkpoint_resume.py / checkpoint_state.py | 同轮进度的冷启动恢复、身份待办差集和工作簿内恢复部件；不操作浏览器 |
| list_html.py | 只在内存解析列表 HTML |
| page_browse.py | 验证码交接及可选滚轮浏览；默认由宿主完整 DOM 直读，普通错误自动恢复，不连接/启动浏览器 |
| pacing.py | 保留旧 2.5 倍换算；宿主按第 4.5 项直接使用最终等待秒数，不套用旧倍率 |
| scraper.py / capture_list_page.cjs | 业务解析与内部遗留编排；旧私有 profile 启动不是 A 接管器，公开 CLI 不调用它 |

旧解析器的无条件占位 SKU、无条件拼 CDN、单图回退和旧标题优先级不能直接用于正式事实；
只有第 7 节定义且已绑定当前完整 DOM 的“单规格”和缺失图片 ID 兜底可以使用。
旧历史清单入口不能替代实时列表。依赖存在、本地测试或历史成功不是本轮采集证明。

2026-09-20 直接 Playwright 抽测：原 Chrome 列表第 1/27 页取得 30 个唯一商品；
首件取得 6 个真实 SKU、规格/SKU 图映射、1 主图 + 8 副图。第二件读到 12 个 model
与两层规格，完整图片验收尚未结束时用户停止；不写成两件全部通过。
2026-09-21～22 的同一轮已用原 Chrome 长连接、无滚轮完整 DOM 直读取得全部 27 页、
808 个唯一待办，并完成至少 600 件详情、1,871 个 SKU；累计进度表已回读核对。
普通加载/内嵌 JSON 截断通过有限同 URL 重载现场恢复；实际验证页已断开交用户。
这些是当前默认方法的真实可行性证据，不是全量完成或未来免验证码的保证；新一轮仍实时数页数和商品。
此前 B 取得过 27 页/810 个唯一商品链接、两件的 6/12 SKU 和各 9 张图库原图。
均不是今日全店全部详情/最终 Excel 完成的证明，也不是以后运行的固定数量。

字段/身份/模板验收失败报告具体缺口，不补造全量结果；已验收数据按第 8 节保存进度。
内存丢失后先按第 8 节从本轮累计进度恢复，不从其他轮次或规范模板回填。
恢复能力覆盖保存成功的断点；上次保存之后尚未落盘的尾部需要重新现场读取。
不落盘 HTML/JSON/截图/trace/响应/会话；允许规定 Excel、每日分析 PDF 及各自受控候选。

正式交付为日期 result/ugreen_topsales.xlsx 和 result/ugreen_topsales_analysis.pdf，报告真实路线、
列表/商品/SKU/主副图数量、历史覆盖与独立验收，给两份可用链接或附件；不以本地路径冒充已发送到手机，不声称图片已内嵌。
持续执行按要求发送中文进度；完成或交还用户后不空转。
