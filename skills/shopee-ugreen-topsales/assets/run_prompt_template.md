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

若计划后跨过上海午夜且尚未 prepare，重新计划并绑定新的启动时间；一旦 prepare 完成，
本轮继续已绑定日期，不在中途再次 prepare 新日期。用户指定其他店铺/国家时先报告
当前 PH 发布合同的限制，不把 SG 数据按 PHP 输出。参数未解析或来源冲突时禁止运行，
不能把本表符号、示例日期或模板占位符作为实参传入。

## 2. 目标与不做的事

默认目标：现场读取当前 PH UGREEN 全部 Top Sales 列表，按首次出现顺序去重，逐个进入
所有唯一商品详情，取得完整 model/SKU、主副图库与所需字段，输出并验证完整四表 Excel。

只使用当前环境已有工具正常读取原 Chrome；不复制 profile/Cookie/Storage、不另启
Chrome/context/采集标签、不搭 CDP、不要求调试端口或重启浏览器、不修改代理/UA/GPU/
请求头/指纹。单路串行，页与商品访问间至少 10 秒。不给用户承诺必然成功或无人值守。

只现场取数，不能用历史 Excel、访问记录、旧 URL 清单、网上另找的图片补齐。本轮明确
抽测时只交文字，不创建日期目录、不给部分表挂“全量”标签；既有表分析不启动浏览器。

## 3. 必读参考与目录

全量执行前完整读取：

1. [worktree.md](../references/worktree.md)：日期身份、完整目录树、Git/产物权限。
2. [excel-output.md](../references/excel-output.md)：四表、逐列类型和语义、17 项核验。
3. [capture-protocol.md](../references/capture-protocol.md)：现场内存数据对象、完整性、stdin 发布。

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
    └── ugreen_topsales.xlsx              # 唯一最终产物，不附 raw/JSON/截图/任务书副本
```

## 4. 阶段执行树

```text
S0 读取规范、绑定参数、检查合同
├── 明确抽测/分析 → 按范围执行 → 只交对应结论，不走全量发布
└── 默认全量
    └── S1 准备本日 Git worktree，验收 clean / 同 HEAD / 固定路径
        └── S2 读取原 Chrome，确认店铺、排序、工具字段能力
            └── S3 全部分页 → 完整商品卡 → 现场身份去重
                └── S4 每个唯一详情 → 全部 model/SKU → 完整商品图库
                    └── S5 本轮内存载荷 → 严格校验 → 候选 Excel → 原子发布
                        └── S6 独立文件验收 → 交付固定路径与实际计数
任一网页阶段出现登录/验证/错误：原页暂停 → 用户处理 → 重读验收 → 回原阶段
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

**输出：** 已绑定的内存任务参数和规范检查回执。

**验收：** `awaiting_browser_collection` 与 `contract_checked` 分别正确；二者均不代表
已取数。必需程序、工具或规范缺失时停止并说清缺哪一项，不自行启动旧浏览器路线。

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

**动作：** 读取真实当前页面，确认 PH、UGREEN、店铺身份与 Top Sales；通过原页正常
操作定位列表。先确认工具能读取列表 URL/标题/当前价格/月销、分页，以及详情完整
model ID/规格映射、主图/副图绝对 URL，不能把截图可见当完整结构化数据已取得。

**输出：** 当前页面身份、排序和实际字段能力；证据保留在本轮工具结果/内存。

**验收 / 失败：** 登录、验证码、challenge、page unavailable 或工具失联，保留原页
交用户；不刷屏重试、不切身份/代理、不自动解验证码。用户说“好了”后必须重读再验收。
必需能力缺失则指明缺失字段，不能因为没有独立新 runner 就先另起开发工程。

## 8. S3：完整列表

**输入：** 现场 Top Sales 第 0 页，capture-protocol.md 的 pages/cards schema。

**动作：** 单路从第 0 页读到现场真实末页，逐页等内容完成更新后记录实际 URL、当前/
总页数、next 状态及完整卡片。每卡记录实际 PDP URL、标题、明确列表价格与月销原文。
保持出现顺序，至少间隔 10 秒再正常翻页。实时数页数，不照抄规范表的历史总页数。

**输出：** 内存 pages 数组；按 `(shop_id,item_id)` 去重的本轮详情待办集合。

**验收 / 失败：** 页码连续、总页数一致、非末页 30 卡/末页 1–30 卡、next 状态正确；
单页无重复，每页有新身份，跨页真实重复保留首次位置并计数。内容未更新、分页漂移、
卡片缺失、价格/月销语义不明时不能跳过/凑数/以历史列表顶替，需停下核对。

## 9. S4：逐个完整详情

**输入：** 本轮唯一 PDP 集合；capture-protocol.md 的 details/skus schema。

**动作：** 按列表首次出现顺序，串行正常进入每个详情，逐件核对 URL/可见身份，读取
当前详情标题、全部真实 model 及规格/图片映射、完整商品图库。区分图与视频、商品图与
评论/推荐图；主图为真实图库首图，余图按原序。详情间至少 10 秒。

**输出：** 内存 details 数组，每个本轮唯一商品恰好一条。

**验收 / 失败：** 不缺商品、不增商品、不重复身份；全部 model ID、非空规格映射、
主副图实际完整 URL 已取得。不能用可见选项笛卡尔积或单个 model 充当全集；图片没取得
不能谎报没有。`models_complete/gallery_complete=true` 必须基于当前完整读取，而非为
通过校验手填。任一缺失未解决不进入发布，不能为部分商品写正式表。

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
Git clean、result 仅有正式 Excel。验证失败时不能删文件或改审计来凑通过。

**交付：** 给出 OUTPUT 的可访问文件链接、实际列表页数/商品数/SKU 数、核验状态。
如通讯渠道无法接收本地路径，使用现有可用附件渠道传文件；没有附件能力则明确说明，
不能声称已送达。按用户要求简洁反馈，不另加报告文件、截图或网页日志包。

## 12. 最终自检与停止条件

- [ ] 参数来自本轮计划和准备回执，上海启动日/快照/发布路径一致。
- [ ] 原 Chrome 的实际现场列表完整遍历，所有唯一详情完整读过，无历史回填。
- [ ] 每个 model、规格和图库有实际本轮证据，不是完整性勾选替代证据。
- [ ] ID 为文本、价格为列表价、月销未展示为空而非零、图片为实际 URL。
- [ ] 发布回执和独立验收都通过，四表及 17 项核验相互一致，Git clean。
- [ ] 未更改规范表、其他日期、登录资料、代理/指纹；未留下原始/部分产物。
- [ ] 结论区分真实全量、抽测、只读验证或阻塞，不把本地脚本测试说成网站成功。

正式交付后结束；等待必要人工输入、缺必需字段或基础设施冲突时明确暂停，不空转。
持续执行时用中文简短说明任务清单、当前页/商品、刚完成结果和下一步；完成或已暂停后
不继续发送空转提醒。不要关闭/清理用户原 Chrome 页面。

**开始执行：先绑定本轮任务参数，执行 S0；按门禁逐阶段推进，不跳过现场验收。**
