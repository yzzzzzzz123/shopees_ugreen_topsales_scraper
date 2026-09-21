# UGREEN Top Sales 标准执行任务书

执行者：当前宿主 Agent。按本任务书完成本轮任务，不把目录准备或单页可读当作全量成功。
本任务书是可直接下发的版本化 Markdown，不依赖前任 Agent 的聊天记忆。

## 1. 任务参数

先读取 Skill 和本任务书，在宿主上下文填妥以下绑定；**不修改本文件、不另外保存任务书
副本**。`--plan` 给出意图，`--prepare` 回执给出实际已核验的日期路径和执行程序。

| 参数符号 | 来源 / 默认值 | 使用规则 |
| --- | --- | --- |
| `MODE` | 用户请求；默认 `full_store_top_sales` | 只有明确抽测/只文字/既有表分析才缩小 |
| `ROOT` | plan/prepare 的 `project_root` | 当前 Skill 所属主 Git 仓库绝对路径 |
| `ROOT_RUNNER` | ROOT 下 `skills/shopee-ugreen-topsales/scripts/run_scrape.py` | 计划、规范检查、准备入口 |
| `STORE_URL` | plan 的 `store_url` | 默认 PH UGREEN 第 0 页 Top Sales，店铺 64922227、PHP |
| `STARTED_AT` | 开始本轮时实际带时区 ISO 时间 | 转上海日与 prepare 的 date 一致，跨午夜不变 |
| `RUN_DATE` | prepare 的 `date`，与 plan 的 run_date 核对 | `YYYY-MM-DD`，上海启动日 |
| `DAILY` / `BRANCH` | prepare 的 `worktree` / `branch` | 日期目录和分支，不能自行猜路径 |
| `PYTHON` / `DAILY_RUNNER` | prepare 的 `python` / `runner` | 发布调用这两个实际回执路径 |
| `OUTPUT` | prepare 的 `output` | `DAILY/result/ugreen_topsales.xlsx` |
| `SOURCE_HEAD` | prepare 的 `source_head/worktree_head` | 两者必须一致，运行期不能漂移 |
| `PAGE` | 已有工具中原 Chrome 的实际目标页引用 | 先读工具文档取得，不新建替代浏览器/标签 |
| `READ_ROUTE` | 用户选择与当前工具能力 | `playwright` 为普通 Playwright 接管原 Chrome；`cua_devtools` 为电脑操作 CUA 接管原 Chrome；不是 CLI 参数 |

若计划后跨过上海午夜且尚未 prepare，重新计划并绑定新的启动时间；一旦 prepare 完成，
本轮继续已绑定日期，不在中途再次 prepare 新日期。用户指定其他店铺/国家时先报告
当前 PH 发布合同的限制，不把 SG 数据按 PHP 输出。参数未解析或来源冲突时禁止运行，
不能把本表符号、示例日期或模板占位符作为实参传入。

## 2. 目标与不做的事

默认目标：现场读取当前 PH UGREEN 全部 Top Sales 列表，按首次出现顺序去重，逐个进入
所有唯一商品详情，取得完整 model/SKU、主副图库与所需字段，输出并验证完整四表 Excel。

只使用当前环境已有工具操作原 Chrome；不复制 profile/Cookie/Storage、不另启
Chrome/context/采集标签，不擅自开放调试端口或重启浏览器，不修改系统代理。
A 为普通 Playwright，B 为电脑操作 CUA；均接管人工已打开的原 Chrome，见 Skill 第 4～5 节。
两条路线均不做指纹配置、地区探测或环境修改脚本注入。只读 DOM/当前商品 JSON 不属于
环境修改。A 按真实 URL `page.goto`，使用主 Skill 第 4 节的滚轮辅助函数检查正常页、
分段浏览，再以最终一次 `page.content()` 取得的完整 DOM 离线解析；滚动前另读的 DOM
仅用于安全检查。只读可见性/焦点检查用于前台保护，检测到失焦即暂停，不抢回焦点。
不以 locator/click/evaluate 逐项操控，不用 JS 滚动。新的未验证方法
先做隔离最小实验，不改正式项目试错。单路串行，每次页/商品
导航前独立随机取 2～3 秒间隔；每完成 50 件额外随机冷却 3～5 分钟，页面自身加载耗时
可额外增加实际间隔。不承诺必然成功或无人值守。
每完成 50 件唯一商品详情累计保存进度 Excel；列表读取完成、停止/挑战/异常和结束时
补存当前全部已验收数据。遇挑战先断开浏览器再保存，不等用户回复才写表。
长期规则及绑定 `CheckpointSaver`/`BrowserHandoff.on_handoff` 的方式见主 Skill 第 8 节。

只现场取数，不能用历史 Excel、访问记录、旧 URL 清单、网上另找的图片补齐。本轮明确
抽测时只交文字，不创建日期目录、不给部分表挂“全量”标签；既有表分析不启动浏览器。

## 3. 必读参考与目录

全量执行前完整读取：

1. [worktree.md](../references/worktree.md)：日期身份、完整目录树、Git/产物权限。
2. [excel-output.md](../references/excel-output.md)：四表、逐列类型和语义、17 项核验。
3. [capture-protocol.md](../references/capture-protocol.md)：现场内存数据对象、完整性、stdin 发布。

需要备用读取路线时，另完整读取
[cua-fallback.md](../references/cua-fallback.md)。它只替换 S2～S4 的页面读取方法，
不改变范围、日期身份、字段合同或 S5～S6 发布门禁。

抽测也需读取后两份，确保“缺字段”与“取得完整字段”使用同一口径；不因此创建正式结果。
规范表 [ugreen_topsales.xlsx](ugreen_topsales.xlsx) 只读 schema，不读取其中旧商品作为种子。

```text
ROOT/skills/shopee-ugreen-topsales/        # 自包含 Skill：唯一标准与执行资源
├── SKILL.md                             # 规范索引与入口
├── assets/
│   ├── run_prompt_template.md           # 本标准任务书
│   └── ugreen_topsales.xlsx             # 只读内容规范
├── references/                          # Excel / worktree / 现场协议
└── scripts/                             # 确定性准备、交接、导出、校验
ROOT/worktrees/YYYYMMDD_ugreen_topsales/   # 同 HEAD 的实际日期 Git 快照
├── skills/shopee-ugreen-topsales/         # 同版本完整 Skill，规范只读、代码从此执行
└── result/
    ├── ugreen_topsales.xlsx              # 唯一全量正式产物
    └── ugreen_topsales_progress.xlsx     # 每 50 件及停止尾批的累计进度，不附 raw/JSON/截图
```

## 4. 阶段执行树

```text
S0 读取规范、绑定参数、检查合同
├── 明确抽测/分析 → 按范围执行 → 只交对应结论，不走全量发布
└── 默认全量
    └── S1 准备本日 Git worktree，验收 clean / 同 HEAD / 固定路径
        └── S2 A：普通 Playwright / B：电脑操作 CUA，均接管人工已打开的原 Chrome
            └── S3 全部分页 → 完整商品卡 → 现场身份去重
                └── S4 每个唯一详情 → 全部 model/SKU → 完整商品图库
                    └── S5 本轮内存载荷 → 严格校验 → 候选 Excel → 原子发布
                        └── S6 独立文件验收 → 交付固定路径与实际计数
任一网页阶段出现登录/验证/错误：立即断开自动化 → 保存已有数据和尾批 → 用户接管 → 明确回复继续 → 重新附着验收
任一完整性/路径/Git/模板校验失败：不发布、不回填、不自动清理；报告具体缺口
```

## 5. S0：规范与执行前检查

**输入：** 用户任务、当前 Skill、Skill 内规范、实际工具文档。

**动作：** 在主根执行以下只读入口；此处相对路径以 ROOT 为 cwd。

```bash
.venv/bin/python skills/shopee-ugreen-topsales/scripts/run_scrape.py --plan
.venv/bin/python skills/shopee-ugreen-topsales/scripts/run_scrape.py --check-contract
```

核对计划范围、参数、规范文件存在及 Excel schema。确认当前宿主可以使用用户原 Chrome
目标页，知道实际读取能力，不臆造 API。确认未有另一全量任务占用此页/项目。
按所选路线读取实际技能和工具文档：A 读取 Playwright，B 读取 CUA 工具文档与
cua-fallback.md；显式 B 不再测试 A。缺少工具时报告，不把 Python 依赖或旧路径当作
技能已安装。区分原会话读取能力与旧私有浏览器启动代码。
同时确认宿主具有从内存以 direct argv / stdin 交接完整载荷的能力；不等全量采完才
发现无法安全发布，不以保存原始 JSON 文件作为绕行办法。

**输出：** 已绑定的内存任务参数和规范检查回执。

**验收：** `awaiting_browser_collection` 与 `contract_checked` 分别正确；二者均不代表
已取数。规范或本地必需程序缺失时停止说明；Playwright 工具不可用先检查受支持的
CUA 备用能力（用户明确只用 A 时不自动切换），主备均不可用再停止，不自行启动旧浏览器路线。

## 6. S1：准备日期快照

**输入：** 当前全量请求、上海启动日、clean 的已提交主根。

**动作：** 从主根调用：

```bash
.venv/bin/python skills/shopee-ugreen-topsales/scripts/run_scrape.py --prepare
```

绑定回执路径/分支/解释器/HEAD，并完整读取 DAILY 内同版本的 Skill、任务书及规范。
显式日期只允许上海本日：`--prepare --date YYYY-MM-DD`，不得拿它创建历史测试数据。

**输出：** `created` 或 `reused` 回执，正确注册的 DAILY；不写业务文件。

**验收：** 主根与 DAILY clean、同 HEAD、分支正确、规范哈希可一致读取。脏状态/冲突
不得自行提交、清理或覆盖；报告冲突并等待用户处理。具体边界以 worktree.md 为准。

## 7. S2：原页面与能力确认

**输入：** 已有工具的原 Chrome 页面引用、STORE_URL、日期参数。

**动作：** 遵循主 Skill 第 4～5 节：A 用普通 Playwright 连接原 Chrome，绑定唯一目标标签，
不新增环境配置或初始化脚本。使用实际可用的接管接口，不以旧私有浏览器启动器代替。
用户选择 B，或 A 工具不可用且原页正常时，读取 cua-fallback.md 用电脑操作接管原页。
随后读取真实当前页面，确认 PH、UGREEN、店铺身份与 Top Sales；A 按真实 URL 导航，
核对正常页后分段滚轮浏览，再从最终完整 DOM 离线找字段，不点击分页、图库、缩略图或规格。先读列表
URL/标题/当前价格/月销及分页，再从本轮列表取一条真实
商品链接进入详情，核验完整 model ID/规格映射、主图/副图绝对 URL 的读取能力。
SKU 不要求出现在列表页；截图可见也不等于已取得完整结构化数据。
若 Playwright 连接能力不可用而原页正常，依 cua-fallback.md 使用 B（用户明确只用 A 时不自动切换），
不能把浏览器连接修复或重启当成继续取数的必要前提。

**输出：** 实际 A/B 路线、读取能力/缺口、当前页面身份、排序和字段能力；证据仅在本轮工具结果/内存。

**验收 / 失败：** 登录、验证码、challenge、page unavailable 或主备工具均不可用，立即停止
采集并断开自动化附着连接，保留原页交用户；A 的导航、读取、解析和循环须由主 Skill
第 4 节的 `BrowserHandoff.run` 保护。先断开再通知，不等截图/日志/冷却，不关闭 Chrome。
等待期间不轮询或自动重连；只有用户明确回复继续才重新附着并验收，不能把“好了”当验收。
不刷屏重试、不切身份/代理、不自动解验证码。
必需能力缺失则指明缺失字段，不能因为没有独立新 runner 就先另起开发工程。

## 8. S3：完整列表

**输入：** 现场 Top Sales 第 0 页，capture-protocol.md 的 pages/cards schema。

**动作：** 单路从第 0 页读到现场真实末页，逐页等内容完成更新后记录实际 URL、当前/
总页数、next 状态及完整卡片。每卡记录实际 PDP URL、标题、明确列表价格与月销原文。
保持出现顺序；每次翻页前重新随机等待 2～3 秒，再按完整 next URL 正常导航。列表页
和卡片不计入详情阶段的 50 件批次冷却。实时数页数，不照抄规范表的历史总页数。

**输出：** 内存 pages 数组；按 `(shop_id,item_id)` 去重的本轮详情待办集合。
列表完成时先保存一份累计进度 Excel，再进入详情阶段。

**验收 / 失败：** 页码连续、总页数一致、非末页 30 卡/末页 1–30 卡、next 状态正确；
单页无重复，每页有新身份，跨页真实重复保留首次位置并计数。内容未更新、分页漂移、
卡片缺失、价格/月销语义不明时不能跳过/凑数/以历史列表顶替，需停下核对。

## 9. S4：逐个完整详情

**输入：** 本轮唯一 PDP 集合；capture-protocol.md 的 details/skus schema。

**动作：** 按列表首次出现顺序，串行正常进入每个详情，逐件核对 URL/可见身份，读取
当前详情标题、全部真实 model 及规格/图片映射、完整商品图库。区分图与视频、商品图与
评论/推荐图；主图为真实图库首图，余图按原序。每次详情导航前重新随机等待 2～3 秒，
详情阶段每完成 50 个商品先原子更新累计进度 Excel，再随机冷却 3～5 分钟。
备用路线须核对内嵌数据属于当前商品；站内跳转残留 `ShopPage` 数据时，只在页面正常
且无挑战时按已取得的详情完整链接正常加载一次，再核验。B 可按实际界面打开图片查看器；
视频封面不是主图。A 不打开查看器或选择规格，只从完整 DOM 与当前商品内嵌数据解析。
以下是每轮固定兜底口径：

- 图片已有合规完整 URL 时原样保留。权威 `product_images.images`、model/extinfo 或 tier
  图片字段只有图片 ID，且同一完整 DOM 没有该 ID 的绝对原图 URL 时，仅对这个缺失项
  生成 `https://down-ph.img.susercontent.com/file/<图片ID>`；不得覆盖已有 URL、改变图片
  顺序、去缩略后缀或给非权威字符串套域名，生成后仍按 capture-protocol.md 校验。
- SKU 图优先采用具体 model/extinfo 的 `sku_image/image/image_id`；仅当这些直接字段全空时，
  才按 `tier_index` 使用 tier 图片。直接字段内部冲突或所选后备内部冲突仍停止，不随取一个。
- 仅当商品恰有一个真实 model、恰有一层规格，且 tier 名称、唯一 option、model 名称均为空
  时，`sku_props` 写 `{"规格":"单规格"}`。多个 model、非空真实规格或结构解析失败不得套用。

详见 capture-protocol.md；B 的操作细节另见 cua-fallback.md。

**输出：** 内存 details 数组，每个本轮唯一商品恰好一条。

**验收 / 失败：** 不缺商品、不增商品、不重复身份；全部 model ID、非空规格映射、
主副图实际完整 URL 已取得。不能用可见选项笛卡尔积或单个 model 充当全集；图片没取得
不能谎报没有。`models_complete/gallery_complete=true` 必须基于当前完整读取，而非为
通过校验手填。任一缺失未解决不进入发布，不能为部分商品写正式表。出现 traffic error/
验证时立即断开自动化连接、原页交用户，再保存已有数据（含不足 50 件的尾批）；
等待用户明确回复继续后才重新附着验收并正常
续跑一次，仍异常则立即再次断开。不能把冷却结束或验证码消失当作自动继续信号。

## 10. S5：确定性交接与原子发布

**输入：** 本轮完整 pages/details、STARTED_AT、实际 captured_at、已绑定路径。

**动作：** 按 capture-protocol.md 构造仅内存 JSON，用支持 stdin 的进程工具 direct argv
调用下列参数；这里的大写符号须替换为回执值，不是命令字面量，不拼接 shell：

```text
[PYTHON, DAILY_RUNNER, "--publish-stdin", "--project-root", ROOT, "--worktree", DAILY]
cwd = DAILY
stdin = 本轮完整 UTF-8 JSON 对象
```

脚本重算排名、计数与核验，检查 Git/路径/规范哈希，候选表经独立重开验证后才原子发布。
不直接调用宽松导出函数绕过门禁，不把 audit、旧表路径或凭据塞入 payload。

**输出：** OUTPUT 和 stdout 发布回执，不保存载荷文件或回执 sidecar。

**验收 / 失败：** 退出 0、输出路径精确匹配、模式 `full_topsales`、核验 `通过`；有失败
不覆盖已有有效表，不交付旧表充当本次结果。完整性和数量不能仅靠模型自报。

## 11. S6：独立验收与交付

**输入：** 本次发布回执、同一 ROOT/DAILY。

**动作：** 独立只读运行：

```text
[PYTHON, DAILY_RUNNER, "--validate", "--project-root", ROOT, "--worktree", DAILY]
cwd = DAILY
```

核对唯一路径、四表、17 项核验、商品/SKU/主副图数与发布回执相同，并检查日期源码
Git clean、result 只含正式 Excel 及可选的规定进度表。验证失败时不能删文件或改审计来凑通过。

**交付：** 给出 OUTPUT 的可访问文件链接、实际列表页数/商品数/SKU 数、核验状态。
如通讯渠道无法接收本地路径，使用现有可用附件渠道传文件；没有附件能力则明确说明，
不能声称已送达。按用户要求简洁反馈，不另加报告文件、截图或网页日志包。

## 12. 最终自检与停止条件

- [ ] 参数来自本轮计划和准备回执，上海启动日/快照/发布路径一致。
- [ ] 原 Chrome 的实际现场列表完整遍历，所有唯一详情完整读过，无历史回填。
- [ ] 每个 model、规格和图库有实际本轮证据，不是完整性勾选替代证据。
- [ ] ID 为文本、价格为列表价、月销未展示为空而非零、图片为实际 URL。
- [ ] 发布回执和独立验收都通过，四表及 17 项核验相互一致，Git clean。
- [ ] 未更改规范表、其他日期、登录资料或系统代理；A/B 均未修改原浏览器环境，除规定进度 Excel 外未留下原始/部分产物。
- [ ] 结论区分真实全量、抽测、只读验证或阻塞，不把本地脚本测试说成网站成功。

正式交付后结束；等待必要人工输入、缺必需字段或基础设施冲突时明确暂停，不空转。
持续执行时用中文简短说明任务清单、当前页/商品、刚完成结果和下一步；完成或已暂停后
不继续发送空转提醒。不要关闭/清理用户原 Chrome 页面。

**开始执行：先绑定本轮任务参数，执行 S0；按门禁逐阶段推进，不跳过现场验收。**
