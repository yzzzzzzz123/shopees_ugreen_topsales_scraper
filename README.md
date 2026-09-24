# shopees_ugreen_topsales_scraper

通过当前已有浏览器工具读取用户原 Chrome 中的 UGREEN Philippines 页面，完整遍历
本轮 Top Sales 列表和每个商品详情，按内容规范输出四表 Excel，再独立验收。
不复制浏览器会话、不另起浏览器。只有两套网页操作方式，共用同一发布链路。

- A：普通 Playwright，持续连接人工已打开的原 Chrome，默认完整 DOM 直读，不操作鼠标或滚轮。
  导航前检查当前页，导航后驻留并读取完整 DOM 与当前商品内嵌 JSON，离线核对身份、SKU 和图库。
- B：电脑操作 CUA，接管人工已打开的原 Chrome，必要时通过原 DevTools 只读取数；
  详见 [CUA 方法](skills/shopee-ugreen-topsales/references/cua-fallback.md)。

两条路线都不配置指纹、不注入环境修改脚本，不覆盖浏览器 UA、语言、时区或尺寸。
默认 A；用户选择 B 或 A 工具不可用且原页正常时用 B，用户明确只用 A 时不自动切换。
网站挑战由用户处理；A 可先接管下一个已打开并指定用于采集的原标签，全部不可用才暂停。
宿主负责原浏览器操作，公开 CLI 负责本地交接，不宣称 CLI 已自动实现两种路线。

[Skill 入口与规范索引](skills/shopee-ugreen-topsales/SKILL.md) ·
[可直接下发的任务书模板](skills/shopee-ugreen-topsales/assets/run_prompt_template.md)

## 正常使用

```text
使用 $shopee-ugreen-topsales 完整跑一遍：通过现有工具读取我原 Chrome 的 UGREEN PH 页面，
采集本轮全店 Top Sales 列表和每个商品详情，按该 Skill 内的内容规范生成并验收当日四表 Excel。
遇到验证码或访问限制，保留原页，保存后接管下一个我已打开的采集标签；全部不可用再暂停。
只有一个采集标签时，按原逻辑断开、保存并等我处理后继续。
```

“跑一遍”“完整走 Skill”默认就是上述全量交付。只有明确要求“抽测几页/只文字”，
才缩小到现场字段覆盖报告；只分析既有表则不启动网页采集。

默认店铺 ID `64922227`，币种 PHP。统一按 Skill 使用导航前随机 2～3 秒、加载后驻留
2～4 秒、普通重读退避 5/10 秒，单路串行。每完成 50 件详情保存，成功后继续，不额外冷却。
页面加载/解析/写表耗时、超时上限及完整性检查不缩减；此节奏不保证避免验证。
本次只整理 Skill 和执行说明，生产脚本版本保持不变；`pacing.py` / `--plan` 仍含旧节奏值，
宿主以 Skill 第 4.5 项最终秒数执行，不重复缩放。
Playwright 对每个已授权原 Chrome 连接只附着一次，能力确认、列表、详情和进度保存均复用
持续连接和已绑定原标签集合，禁止短连检查后断开、频繁重连或反复触发远程调试授权。
页面后台或失焦时，只要仍可正常读取且身份、完整性通过就继续，不因此暂停、断开或
重连，也不自动抢回焦点。普通读页/输入超时或解析失败由宿主自动恢复，不要求用户确认。
宿主在单件读取层捕获现场验证/访问限制，立即停止操作该页，保存尾批后顺序接管下一张
已绑定原标签，重做当前未完成待办。受限标签本轮不回访，不操作账号登录切换，不新建标签。
标签数按实际可连接的用户指定页面确定，不硬编码为四页；单页或全部不可用时，沿用
断开、保存、等待用户明确继续的流程。`BrowserHandoff` 仍是单页交接器，CLI 不自动切页；
多标签顺序接管由宿主按 Skill 执行。普通异常在当前页有限恢复，不占用其他标签。
原窗口、标签和登录状态全程保留。缺少 model、SKU 映射或图库证据不能用旧值补齐。

## 规范与结果分开

- [assets/ugreen_topsales.xlsx](skills/shopee-ugreen-topsales/assets/ugreen_topsales.xlsx) 是只读的 Excel **内容规范**：
  四表、字段、口径、类型、粒度及核验要求，不只是配色，也不是数据种子。
  规则解释见 [excel-output.md](skills/shopee-ugreen-topsales/references/excel-output.md)，规范中的历史业务值不复用。
- 现场数据协议见 [capture-protocol.md](skills/shopee-ugreen-topsales/references/capture-protocol.md)。商品链接、身份、
  排名、价格、月销、SKU 和图片均须来自本轮；完整性声明由实际页面证据支撑，
  JSON 结构检查或 URL 白名单不能独立证明网站 SKU/图库全集。
- 正式 Excel 为 `worktrees/YYYYMMDD_ugreen_topsales/result/ugreen_topsales.xlsx`，
  包含 `商品汇总`、`SKU明细`、`图片明细`、`抓取核验`。日期固定为上海启动日。
  规范和其他日期结果不动，失败不覆盖有效正式结果。
- 每日同时交付同目录 `ugreen_topsales_analysis.pdf`：逐链接月销/价格日变化、7/30 日趋势、
  店铺新出现链接、月销与金额估算、价格段销量占比和动销。缺历史明确留空，月销滚动展示值
  不当成当天订单，客单价只给列表价代理。详细定义见 Skill 的 `references/daily-analysis.md`。
  正式 Excel 发布后执行主根 `run_scrape.py --analyze --project-root ROOT --worktree DAILY`（内部先独立验收源表），
  再执行 `--validate`、`--archive`，确认分析通过及日期分支归档 commit；既有日期补分析也使用这三个入口，不重新采集。
- 长期默认每完成 50 件唯一商品详情累计更新同目录 `ugreen_topsales_progress.xlsx`；
  列表完成、停止/挑战/异常和结束时补存尾批。进度表标明未完成，绝不冒充全量通过。
  工作簿内同时保存完整恢复状态，进程重启后先恢复已采数据、只采剩余身份；沿用原日期，
  不重新 prepare。旧版表迁移需明确授权并绑定 SHA-256，详见 Skill 第 8 节。
- 全量准备会自动提交现有改动，并创建或更新本日 worktree，无需再次确认；采集和发布
  不以脏状态或 HEAD 不同阻断。现有结果、其他日期及历史提交保留；见 [worktree.md](skills/shopee-ugreen-topsales/references/worktree.md)。

## 本地命令入口

在主项目根目录使用已有 Python 环境：

```sh
.venv/bin/python skills/shopee-ugreen-topsales/scripts/run_scrape.py --plan
.venv/bin/python skills/shopee-ugreen-topsales/scripts/run_scrape.py --check-contract
```

无参数等同 `--plan`：只读返回任务书、规范、上海当日身份、目标路径和必需步骤，
状态是 `awaiting_browser_collection`，不会自动采集或写 Excel。

| 参数 | 实际能力 |
| --- | --- |
| `--prepare` | 委托每日目录准备器，仅创建/安全复用上海本日；可显式给同一天的 `--date YYYY-MM-DD` |
| `--publish-stdin --project-root ROOT --worktree DAILY` | 接收现场协议的 stdin JSON 对象，确定性转换、完整性审计、原子发布 |
| `--analyze --project-root ROOT --worktree DAILY` | 只读完整快照，生成同目录 PDF 分析 |
| `--archive --project-root ROOT --worktree DAILY` | 将验收后的 Excel/PDF 成对提交到日期分支；同日历史保留在 Git |
| `--validate --project-root ROOT --worktree DAILY` | 对指定日期结果进行独立只读验收，不回退其他文件 |
| `--resume-checkpoint --project-root ROOT --worktree DAILY` | 只读核验累计进度并报告可恢复计数与下一保存点；宿主用 `checkpoint_resume.load_checkpoint` 取得内存对象和待办 |
| `--check-contract` | 只读检查 Skill 内文档及规范工作簿 schema，不是网站采集成功证明 |

`ROOT`、`DAILY` 使用明确绝对路径。现场 JSON 仅内存/管道交接，不保存原始响应、
截图或 JSON；允许上述累计进度 Excel，主根入口 `--checkpoint-stdin` 接收本轮已采集载荷。
完整命令和阻断处理见 [任务书模板](skills/shopee-ugreen-topsales/assets/run_prompt_template.md)。

## 实现状态与历史边界

宿主 Agent 负责原浏览器现场读取；Python 入口负责计划、目录准备、数据发布和独立验收。
它不再启动浏览器，也不会复制 profile。无需因缺少新浏览器 runner 而一律先开发采集器；
工具能取得完整数据时可复用现有纯解析、转换及导出模块。

旧 `--verify-access`、`--refresh-known-products`、浏览器配置和人工 PTY 参数会明确提示
迁移到当前任务书，不静默启动旧复制流程。指纹配置、地区查询与环境注入实现及其
专用测试已删除；现有内部复制 profile 启动函数仍不是原 Chrome 连接器，不用于 A/B。
业务字段、发布与验收逻辑保留。新方案仍须先隔离验证，再最小接入项目。

2026-09-20 已现场验证普通 Playwright 直接读取原 Chrome：列表第 1/27 页 30 件；
首件详情取得 6 个真实 SKU、完整规格/SKU 图映射和 1 主图 + 8 副图。只证明抽测能力，
不是全店完成，也不证明所有商品结构都已适配。

本地测试和规范验收不等于真实全店采集已成功，也不证明未来无人值守稳定。
未实际取得的字段必须如实报告；没有完整现场证据就不发布正式四表结果。

## 目录维护

| 位置 | 用途与保留规则 |
| --- | --- |
| `skills/shopee-ugreen-topsales/` | 完整业务 Skill；任务书与规范模板在 assets，详细规范在 references，执行代码在 scripts |
| `tests/` | 已有回归用例；不是采集产物，不作为缓存清理 |
| `worktrees/` | 日期运行快照及正式结果；不得按普通缓存删除 |
| `.venv/` | 本机 Python 环境；不进入 Git，普通整理时保留 |
| `.local-browser-profiles/` | 历史本机会话资料，可能含登录信息；当前入口不用，未经明确要求不读取或删除 |
| `*.egg-info/`、`__pycache__/`、`.DS_Store` | 可再生安装元数据、Python 缓存、Finder 信息；已由 Git 忽略，本次保留 |

`egg-info` 由 setuptools 安装或构建时生成，不是源码或任务数据，后续安装可能再次生成。
本次删除仅限用户明确要求的指纹整套及其调用、专用测试；历史日期快照和结果不动。
以后清理仍须有明确范围，不因“未被入口调用”或“可再生”自动删除其他资料。
