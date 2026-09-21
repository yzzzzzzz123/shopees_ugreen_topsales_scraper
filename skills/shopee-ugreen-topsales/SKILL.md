---
name: shopee-ugreen-topsales
description: 接管人工已打开的原 Chrome，采集 PH UGREEN 全店 Top Sales 列表与商品详情，在日期 Git worktree 发布并验收四表 Excel。A 使用普通 Playwright，B 使用电脑操作 CUA；也支持明确限定的抽测或既有表分析。
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
不擅自开放调试端口、安装扩展或修改系统代理。只有现场验证码/人工验证才立即断开、
保留原页交用户，并等用户明确继续后重新验收。普通超时、加载或解析失败由宿主自动
诊断恢复，不要求用户回复“继续”；不将工具时限或 Page Unavailable 冒充验证码。

```text
读规范与参数 → 全量任务准备日期 worktree
  → A 普通 Playwright / B 电脑操作 CUA：接管原 Chrome
  → 全部列表 → 全部唯一详情（每 50 件保存累计进度 Excel，停止时补存尾批）→ 内存载荷
  → stdin 严格发布 → 独立验收 → 唯一四表 Excel
```

## 2. 范围和规范入口

默认地址 `https://shopee.ph/ugreen.ph?page=0&sortBy=sales&tab=0`；店铺 `64922227`，
国家 PH，币种 PHP。当前发布代码不支持其他店铺/国家，不将其他站点数据塞入 PH 合同。

| 用户请求 | 执行范围 |
| --- | --- |
| 跑一遍、完整执行、刷新全店 | 本轮全部列表、全部唯一详情、完整四表与独立验收 |
| 明确抽测几页/几件、试字段、只文字 | 按约定数量；没给数量则少量代表性样本，不创建 worktree、不发布部分表 |
| 分析既有 Excel | 只读指定文件，不自动访问网页或修改文件 |
| 整理 Skill、解释脚本 | 仅维护/解释，不因此启动采集或创建日期运行 |

先完整读取 [标准任务书](assets/run_prompt_template.md)，再按任务读取：

| 文件 | 用途 |
| --- | --- |
| [worktree.md](references/worktree.md) | 全量必读：日期身份、Git 边界、目录和生命周期 |
| [capture-protocol.md](references/capture-protocol.md) | 全量和抽测必读：现场字段、类型和内存交接 |
| [excel-output.md](references/excel-output.md) | 全量和抽测必读：四表逐列口径及 17 项验收 |
| [cua-fallback.md](references/cua-fallback.md) | 使用 B 前必读：DevTools 只读采集、分块回传和验收 |
| [ugreen_topsales.xlsx](assets/ugreen_topsales.xlsx) | 只读内容规范，不是业务数据种子 |
| [verified_access.md](references/verified_access.md) | 已发生的验证与历史证据，不覆盖当前流程 |

不另建平行 spec，不修改冻结任务书或另存任务书副本。完整任务不能因字段难取而
自动缩减为抽测，不从旧 Excel/历史 URL/网上另找图片补齐本轮事实。

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

正式结果：`worktrees/YYYYMMDD_ugreen_topsales/result/ugreen_topsales.xlsx`。
采集中累计进度表：同目录 `ugreen_topsales_progress.xlsx`，与全量正式结果区分。
日期工作区包含完整 Skill/源码；任务准备自动提交主项目和本日工作区的现有改动，
再快进或正常合并主项目版本，不重复请求授权。模板、规范在采集中只读；保留已有
改动和结果，不 stash/reset/clean、不删除冲突文件或改其他日期。实际 Git 失败或合并
冲突才报告处理，具体流程见 worktree.md。

## 4. S2-A：普通 Playwright 接管原 Chrome

1. 阅读当前可用的 Playwright Skill/工具文档，定位用户给定 URL 的原标签，确认唯一性、
   店铺身份、Top Sales 和当前页。不能盲用 contexts[0].pages[0] 或操作无关账号标签。
2. 使用已有原会话连接能力，不调用 launch、launch_persistent_context、new_context
   或新建采集页。连接不可用时报告具体缺口；需用户开启调试/授权时交用户，不自行改设置。
   只允许持续长连接：同一轮初始化、能力检查、列表与详情采集、进度保存及批次冷却
   复用同一附着连接和已绑定的原 `page`。检查成功后直接沿用，不做“短连检查即断开”，
   不按工具调用、页面或批次重建 Playwright，不因保存、冷却或失焦重连。远程调试已经
   允许后不重复点击或触发授权；仅结束、用户停止、验证码交接或连接实际损坏时释放。
3. 本机 Python Playwright 1.63.0 已验证可用
   `chromium.connect_over_cdp("chrome", no_defaults=True)` 附着用户已开启远程调试的 Chrome。
   no_defaults 避免默认上下文覆盖；不额外设置浏览器环境或 init script。
   它不是所有机器的通用保证，也不证明此前外部修改已恢复。
4. 按真实链接 `page.goto`，正常页使用
   [page_browse.py](scripts/page_browse.py) 的 `read_page_after_browsing` 分段滚轮浏览，
   再从返回的最终完整 DOM 离线解析。宿主传入已绑定的原 `page`、根据当前内容视口
   核对的 `wheel_origin=(x,y)` 和检测到挑战/不完整页面即抛异常的 `check_html(html,url)`；
   不硬编码其他窗口的坐标。辅助函数不负责连接或导航，也不保存数据。
   加载后随机停留 2～4 秒，先读 DOM 检查页面；随后 `mouse.move` 到已核对的落点，
   用 `mouse.wheel` 分 3～5 次向下滚动，每次 280～560 像素并停留 0.9～2.4 秒。
   约 35% 的页面插入一次 100～220 像素的短回滚并停留 1～2 秒，最后再等 1.2～2.5 秒，
   取得最终 DOM 并重新检查。滚轮事件返回不代表滚动已经结束，保留事件后的等待。
   滚动前的 DOM 只用于安全检查，业务解析只接收滚动后的 DOM；每步检查原页身份，
   关闭或身份改变先停止本次输入并自动核对恢复；验证码按第 6 项交接，不用滚轮处理验证。
   输入步长不宣称为实测滚动距离。
   仅额外用 `evaluate` 只读 `document.visibilityState/document.hasFocus()` 作为诊断；
   页面在后台或 `hasFocus=false` 本身不是暂停、报错或断开条件，也不自动切换标签或
   抢回焦点。只要原页仍可正常读取、身份与完整性检查通过，就保持当前连接继续采集。
   焦点状态不保证已发出的 `mouse.wheel` 会及时返回。记录读页、mouse.move、mouse.wheel
   等具体步骤的耗时，普通超时不交给用户；按第 6 项自动恢复，不盲目反复输入。
   这替换固定驻留，不保证避免验证码，也不改变导航间隔、批次冷却或字段口径。
   不以 locator/click/evaluate 打开图库、选择规格或逐项读取，不执行 JS 滚动或环境注入；
   不读取 Cookie/密码/Storage、整份账号状态或隐藏网络接口。
   结束只断开附着连接，不关闭用户 page/context/Chrome。
5. 单路串行；每次页/商品导航前独立随机取 2～3 秒间隔，每完成 50 件额外随机冷却
   3～5 分钟，页面加载耗时可额外增加实际间隔。核对内容实际更新。发现挑战按下一项
   立即断开交用户，不循环刷新、切身份/代理或切工具绕过人工验证。
6. 按第 8 节绑定累计保存器后，附着成功时绑定
   `control = BrowserHandoff(pw.stop, on_handoff=lambda: saver.maybe_save(force=True))`，
   用 `control.run(采集函数, …)`
   包住导航、滚动、DOM 检查、离线验收及外层采集循环。URL/DOM 检查只有实际检测到
   验证码/人工验证才抛 `page_browse.CaptchaDetected`；该异常先断开再保存并交用户，
   不等批次结束、截图或冷却。用户主动停止也释放连接。普通异常直接传给宿主恢复，
   不断开、不锁定 `waiting_for_user`，不要求用户确认；单独失焦不算异常。
   回调只用当前附着的 `pw.stop()`，不用 `browser/context/page.close()`，保留原页和内存数据。
   控制器随即锁定等待用户，禁止后续采集；先执行断开，再离线保存已取得数据。
   断开失败须报“连接状态未确认”，不能宣称已脱离；仍尝试保存数据，不因断连异常丢弃尾批。
   等待期间不读取/轮询页面、不自动重连；验证码消失或计时结束都不是续跑信号。
   只有用户明确回复继续后才重新附着、绑定新控制器，先验收原页，再正常续跑一次；
   若仍有验证码立即再次断开。B 在验证码出现时立即停止电脑输入，不换工具继续读页。
   断开只释放本采集器的连接，不声称清除了此前接管影响或其他客户端连接；现有检查
   触发即处理，不承诺验证码出现后毫秒级检测。
7. 普通错误恢复：优先沿用当前连接，先读取当前 URL/完整 DOM 检查验证码，再按身份和
   字段验收。滚轮或鼠标输入超时但当前 DOM 完整可读时，可用这次重新读取的完整 DOM
   继续；记录浏览输入未确认，不谎报完成了滚动。加载未完成时退避后最多重试两次正常
   读取/导航，解析失败先离线检查当前 DOM。避免把整段人工设置时限当作页面失败证据。
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

## 8. S5～S6：内存发布与独立验收

### 采集中与停止时保存（长期默认规则）

- “50 条”指 50 件已完成并验收的唯一商品详情，不是 SKU 行、图片行或列表卡。
  在累计第 50、100、150…件后，进入下一件或批次冷却之前保存；列表读取完成也保存一次。
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
- 先断开浏览器再保存尾批；保存失败保留上一份有效进度表、内存和暂停状态，报告失败，
  不继续采集。未知文件、其他轮次或会丢失已保存身份/详情的覆盖必须拒绝。

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

发布退出 0 后独立运行：

```text
argv = [PYTHON, DAILY_RUNNER, "--validate", "--project-root", ROOT, "--worktree", DAILY]
cwd = DAILY
```

核对 collection_mode=full_topsales、audit_status=通过、计数一致、
result 只含正式表及可选的规定进度表。Excel 验收只证明内部一致，必须结合本轮全部现场覆盖才算全量完成。

## 9. 实现边界、证据与交付

| 文件 | 当前作用 |
| --- | --- |
| run_scrape.py / prepare_daily_worktree.py | 计划、规范检查、日期准备、stdin 分派 |
| publish_result.py / excel.py / validate_result.py | 严格转换、门禁、四表发布与独立验收 |
| checkpoint_result.py / checkpoint_excel.mjs | 每 50 件与停止尾批的累计进度 Excel、原子替换和逐单元格回读；不联网 |
| list_html.py | 只在内存解析列表 HTML |
| page_browse.py | 原页滚轮浏览、DOM 检查及验证码交接；普通错误交宿主自动恢复，不连接/启动浏览器 |
| scraper.py / capture_list_page.cjs | 业务解析与内部遗留编排；旧私有 profile 启动不是 A 接管器，公开 CLI 不调用它 |

旧解析器的无条件占位 SKU、无条件拼 CDN、单图回退和旧标题优先级不能直接用于正式事实；
只有第 7 节定义且已绑定当前完整 DOM 的“单规格”和缺失图片 ID 兜底可以使用。
旧历史清单入口不能替代实时列表。依赖存在、本地测试或历史成功不是本轮采集证明。

2026-09-20 直接 Playwright 抽测：原 Chrome 列表第 1/27 页取得 30 个唯一商品；
首件取得 6 个真实 SKU、规格/SKU 图映射、1 主图 + 8 副图。第二件读到 12 个 model
与两层规格，完整图片验收尚未结束时用户停止；不写成两件全部通过。
此前 B 取得过 27 页/810 个唯一商品链接、两件的 6/12 SKU 和各 9 张图库原图。
均不是今日全店全部详情/最终 Excel 完成的证明，也不是以后运行的固定数量。

字段/身份/模板验收失败报告具体缺口，不补造全量结果；已验收数据按第 8 节保存进度。
内存丢失后重新现场取数，不从旧表恢复，不承诺不存在的持久化 resume 服务。
不落盘 HTML/JSON/截图/trace/响应/会话；允许累计进度 Excel 和写表模块受控候选。

正式交付仅为日期 result/ugreen_topsales.xlsx，报告真实路线、列表/商品/SKU/主副图
数量和独立验收，给可用链接或附件；不以本地路径冒充已发送到手机，不声称图片已内嵌。
持续执行按要求发送中文进度；完成或交还用户后不空转。
