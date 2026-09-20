---
name: shopee-ugreen-topsales
description: 组织 PH UGREEN 全店 Top Sales 列表与商品详情采集，在日期 Git worktree 交付固定四表 Excel。说明 Playwright 原 Chrome 加指纹/JS 的主路线、CUA 回退、现有脚本职责与验证门槛；也支持明确限定的抽测或既有表分析。
---

# Shopee UGREEN Top Sales：完整链路与脚本对照

## 1. 一条业务链路，只有两套网页操作方式

用户确认的目标是：

- **A 主路线：Playwright 连接用户已经打开的原 Chrome，按本轮代理地区绑定指纹，
  使用完整 proxy-access.js，再采集列表和详情。**
- **B 回退路线：A 的工具能力不可用、原页正常时，CUA 操作同一个原 Chrome，
  通过 DevTools 只读取得列表和详情数据。**

指纹属于 A 的一部分，不是第三条路线。两者共用任务书、现场字段协议、日期 worktree、
Excel 导出和验收。所有项目文件保留；某文件未被当前入口调用，不等于无用或可以删除。

### 1.1 必须先分清“确认的目标”“代码已有能力”“已实测结果”

| 层次 | 当前事实 |
| --- | --- |
| 确认的目标 | A 包含原 Chrome、Playwright、代理地区、指纹和完整 JS；B 是 CUA 回退 |
| 已有配置代码 | 地区解析、八套配置、版本组合、单轮冻结、JS 渲染与探针均存在 |
| 已有浏览器启动代码 | scraper.py / capture_list_page.cjs 仍创建私有 profile/context；不是原 Chrome 连接器 |
| 当前公开 CLI | run_scrape.py 负责计划、准备、stdin 发布、独立验收、规范检查；不自动操作浏览器 |
| 已验证的备用方法 | CUA + 原 Chrome DevTools 取得过完整列表链接及少量详情的 SKU/图库，见第 11 节 |
| 尚未证明 | 在原 Chrome 中完成整套配置、注入、跨页保持和结束清理；以及这条主路线的全店成功 |

**可行性门槛：** 原 Chrome 注入适配尚未验证，不能因本文件列出流程就当作已经接通。
开发这部分时，先在隔离临时目录/最小实验中验证，保护原成功会话；真实环境验证成功后
再最小接入项目并回归。不能先改正式脚本、Skill 或配置来试错。本文对该部分是目标与
实现说明，**不是授权跳过实验直接在用户日常会话反复注入**。

当前主路线未满足门槛时，如实说明；原页正常且没有未处理的配置副作用，才按 B 执行。
不能把 CUA 结果说成 Playwright 加 JS 的成功结果。

### 1.2 总流程

```text
用户任务
└── S0 读 Skill/任务书/字段合同，绑定上海启动日，检查本地入口
    └── S1 全量任务准备日期 Git worktree；抽测不创建
        └── S2 网页方式选择
            ├── A：Playwright 原 Chrome
            │   ├── 验证原会话连接与目标页配置能力
            │   ├── 确认代理地区观测 + 正在运行的 Chrome 版本
            │   ├── 八套设备配置选择一次，绑定本轮参数
            │   ├── 配套 UA/地区/尺寸设置 + 完整 JS 注入
            │   └── 实际探针核对；未验证适配不可冒充已完成
            └── B：A 工具能力不足且原页正常 → CUA + 原 DevTools 只读
                ↓
            S3 全部列表页 → 商品卡/分页证据 → 首次出现顺序去重
                ↓
            S4 全部唯一详情 → 真实 model/SKU → 规格/图片映射 → 完整图库
                ↓
            S5 完整内存 JSON → stdin → 严格校验 → 四表 Excel → 原子发布
                ↓
            S6 独立验收 → 日期 worktree 下唯一正式 Excel

网站登录/验证码/挑战/Page Unavailable → 原页交用户 → 重读验收
字段/身份/Git/模板门禁失败 → 停止，不补造、不发布部分结果
```

## 2. 范围、任务书和标准文件

默认地址：`https://shopee.ph/ugreen.ph?page=0&sortBy=sales&tab=0`。
店铺 ID `64922227`、国家 PH、币种 PHP。代理地区不决定店铺国家、币种或业务日期。
当前发布代码不支持其他店铺/国家，不能把 SG 商品塞进 PH/PHP 合同。

| 用户请求 | 执行范围 |
| --- | --- |
| 跑一遍、完整执行、刷新全店 | 本轮全部列表、全部唯一详情、完整四表和独立验收 |
| 明确抽测几页/几件、只文字 | 按约定数量现场读取并文字说明；没给数量则少量代表性抽测；不建 worktree、不发布部分表 |
| 分析既有 Excel | 只读指定文件，不自动访问网页或修改文件 |
| 整理 Skill、解释脚本 | 只维护/解释文档，不因此启动浏览器、注入或创建日期运行 |

先完整读取 [标准任务书](assets/run_prompt_template.md)，再按阶段读取：

| 文件 | 用途 |
| --- | --- |
| [assets/run_prompt_template.md](assets/run_prompt_template.md) | 本轮参数绑定、S0～S6 输入输出、验收和执行树 |
| [references/worktree.md](references/worktree.md) | 日期身份、目录树、Git 边界、发布及中断 |
| [references/capture-protocol.md](references/capture-protocol.md) | pages/details 的精确字段、类型、stdin 交接 |
| [references/excel-output.md](references/excel-output.md) | 四表逐列内容、类型、顺序及 17 项核验 |
| [references/cua-fallback.md](references/cua-fallback.md) | 进入 B 时必读：DevTools 读取、身份验证、分块回传 |
| [assets/ugreen_topsales.xlsx](assets/ugreen_topsales.xlsx) | 只读内容规范，不是历史商品清单或业务种子 |
| [references/verified_access.md](references/verified_access.md) | 历史证据；其中旧命令不覆盖当前 A/B 规范 |

标准全部留在本 Skill 内，不在项目根另建 spec/。任务参数绑定在宿主上下文，
不修改冻结任务书，不另存任务书副本。完整执行不能因字段难取而自动缩减为抽测。

## 3. scripts 每个文件的作用和调用关系

| 文件 | 主要函数/内容 | 在整条链路中的作用 |
| --- | --- | --- |
| [run_scrape.py](scripts/run_scrape.py) | main、_plan、_read_capture_payload | 对外本地入口，分派计划/准备/发布/验收，不爬网页 |
| [prepare_daily_worktree.py](scripts/prepare_daily_worktree.py) | prepare、_prepare_locked | 创建/安全复用日期 Git worktree，返回路径、HEAD、解释器 |
| [browser_region.py](scripts/browser_region.py) | BrowserRegion、region_from_payload、detect_browser_region | 解析地区与语言/时区；现有检测函数会新开空白 Chrome，需要原会话适配 |
| [browser-profiles.json](scripts/browser-profiles.json) | 八套配置目录 | OS、platform、GPU、线程/内存、屏幕等完整套装，不是登录 profile |
| [browser_fingerprint.py](scripts/browser_fingerprint.py) | choose_profile_id、load_fingerprint | 校验八套配置，组合地区和浏览器版本，生成完整参数 |
| [proxy-access.js](scripts/proxy-access.js) | __UGREEN_FINGERPRINT__ 模板 | A 的完整 JS 来源，不自行查代理、选配置或启动 Chrome |
| [capture_list_page.cjs](scripts/capture_list_page.cjs) | capture、AccessWatch、STEALTH_PROBE | Node 列表 HTML 快照、探针、访问状态；启动部分仍要求临时 profile |
| [list_html.py](scripts/list_html.py) | parse_list_html | 内存 HTML → 卡片/分页/挑战诊断；不联网、不写文件 |
| [scraper.py](scripts/scraper.py) | 配置绑定、列表校验、DETAIL_PAGE_SCRIPT、_parse_detail、scrape_all | 现有浏览器编排与解析实现；复制启动和宽松解析不能直接冒充原 Chrome 正式链路 |
| [publish_result.py](scripts/publish_result.py) | _convert、_gates、publish | 严格转换事实、重算排名/审计、Git/模板门禁、原子发布 |
| [excel.py](scripts/excel.py) | write_excel、validate_excel | 重建四表、写入、回读、跨表关联和审计核验 |
| [validate_result.py](scripts/validate_result.py) | _target_workbook、main | 只读指定日期注册 worktree 的结果，不回退其他文件 |

`tests/` 是已有回归用例；`agents/openai.yaml` 是 Skill 元数据；`pyproject.toml` 是依赖合同；
assets/references 是执行资源。全部保留，不因本次整理删脚本、测试、环境或历史目录。

当前依赖声明为 Python >=3.10，Playwright 1.63.0、openpyxl 3.1.5、lxml 6.1.3。
依赖声明不证明当前宿主有可操作原 Chrome 的 Playwright 工具或 Skill。

## 4. S0～S1：准备执行环境和日期 worktree

### 4.1 只读计划与规范检查

主根使用已有解释器执行：

```text
.venv/bin/python skills/shopee-ugreen-topsales/scripts/run_scrape.py --plan
.venv/bin/python skills/shopee-ugreen-topsales/scripts/run_scrape.py --check-contract
```

1. --plan（无参数同义）给出固定店铺、上海日期、任务书、预计 worktree/输出路径和步骤。
   状态 awaiting_browser_collection，不会访问网页。
2. --check-contract 检查所列规范文件安全存在，核对模板四表名称/顺序、第 6 行表头和 SHA。
   它不是完整 Skill 语义验证、浏览器连通性检查或真实采集证明。
   当前代码的 CONTRACT_DOCUMENTS 未列 cua-fallback.md；使用 B 前仍须单独确认并完整读取，
   不能以 contract_checked 证明这份备用文档已被程序检查。
3. 核对全量/抽测范围、上海启动时间，确认宿主可安全使用内存和 direct argv/stdin 交接。
4. 确认没有其他任务占用原目标页。当前代码没有锁住宿主浏览器整个生命周期。
5. 实际查找并完整读取 Playwright Skill 和工具文档；没找到要说明，不使用已失效旧路径。
   2026-09-20 本次检查的项目/本机技能目录没有找到独立 playwright-cli Skill；
   不把 Python playwright 包说成这个 Skill 已安装，不擅自安装补齐。

### 4.2 全量准备；抽测跳过

1. 经公开入口 run_scrape.py --prepare 创建/复用上海本日。
   --date 仅用于 --prepare，公开入口只接受上海今天。
2. 准备器取得 .git/ugreen_daily.lock，检查主根 tracked/untracked clean、
   主根 .venv/bin/python 和 runner 存在。
3. 日期目录固定 worktrees/YYYYMMDD_ugreen_topsales，分支 daily/YYYYMMDD-ugreen-topsales。
4. 已有目录必须注册在本仓库、分支正确、clean、与主根同 HEAD；否则拒绝。
   新建使用主根已提交 HEAD，不自动 commit、reset、删目录或移动分支。
5. 绑定 prepare 回执 project_root/worktree/branch/python/runner/output/source_head/worktree_head。
   读取日期内同版本 Skill/任务书，后续源码和规范只读。
6. **实际 Python 是回执中的主根 .venv/bin/python**，不是日期目录独立 venv。
   发布脚本则必须位于目标日期 worktree。不要套用其他项目的环境合同。

```text
worktrees/YYYYMMDD_ugreen_topsales/
├── .git                                  # Git linked worktree 注册文件
├── skills/shopee-ugreen-topsales/          # 同提交的完整 Skill/脚本/规范
└── result/
    └── ugreen_topsales.xlsx               # 唯一正式结果，Git ignored
```

主根文档改动也会使 clean 门禁失败。修复在主根完成、经另行授权提交后进入新快照；
不能为继续任务擅自提交/同步/重建当天 worktree。跨午夜沿用启动日，不重建第二轮身份。

## 5. S2-A：主路线的配置、指纹和完整 JS

本节把现有代码逻辑与原 Chrome 适配要求逐项对齐。原会话适配未通过最小真实实验前，
不把以下待接通步骤宣称为可直接执行的成熟采集器，也不修改正式代码试错。

### A1. 连接原 Chrome，不换成复制 profile 的浏览器

1. 读取实际 Playwright Skill / 工具文档，选择原 Chrome 的目标标签，绑定实际页面引用。
2. 确认既能读取/正常导航，也支持目标范围内的配置、初始化脚本、探针和内存回传。
3. 只具有 DOM 读取，不代表能够设置完整 UA/时区/尺寸并注入；缺项要具体说明。
4. 原会话连接不能靠调用 launch、新建 context、复制 Cookie/Storage/profile 代替；
   不重启原 Chrome，不擅自开放调试端口，不影响其他标签/账号。
5. 现有 scraper._launch_context 和 Node installPersistentLaunchShim 不满足这条连接要求。
   其配置代码有复用价值，启动部分必须单独验证适配，文件不删除。

### A2. 代理地区：观测、解析、验证，不修改代理

现有 browser_region.py 的实际行为：

1. detect_browser_region 在空白临时 Chrome 中访问固定 ipwho.is 查询，仅取
   success、country_code、timezone.id；清除继承的 HTTP/HTTPS/ALL_PROXY 环境变量，
   不设置显式代理，沿用浏览器系统网络配置。
2. 查询/启动/读取共用 20 秒预算；关闭 context/Playwright 分别有 5 秒预算。
   HTTP、来源、JSON 类型、大小、国家/时区等不符合要求则失败，不静默选固定国家。
3. region_from_payload 将国家映射为 locale，languages=[locale, 基础语言]；
   时区取响应的 IANA 值，并可由浏览器规范化别名。
4. 例如 US → en-US/en，SG → en-SG/en，PH → en-PH/en。
   同一国家可能多时区，不能只按国家猜时区。
5. 原 Chrome 路线应通过已验证的原会话适配取得本轮观测，再复用解析器。
   **现有空白临时 Chrome 查询不是原会话检测，不能直接执行后宣称已符合 A。**
6. 系统代理/PAC 可能按域分流，ipwho.is 出口不保证 Shopee 出口相同。
   不记录代理凭据，不用语言/GPU/店铺域名反推真实出口，不在项目里自动切代理。

### A3. 八套设备配置：每轮选择一次，而非每页换一次

1. browser_fingerprint._read_catalog 校验 JSON 大小、重复键、schema、批准 ID 和字段集合。
2. _validate_profile 检查 OS 与 UA platform/navigator.platform 配对，GPU 字段成套，
   线程/内存/尺寸/触点/PDF 类型和值域正确。
3. choose_profile_id 使用 secrets.choice 独立抽一套；允许连续两轮抽到相同 ID。
   它没有顺序轮换、去重抽签、失败换号或每页变化逻辑。
4. load_fingerprint(profile_id, chrome_version, region) 合成完整参数。
   UA 用真实 Chrome 主版本加 .0.0.0，完整四段版本另存；不写死 122 或 153。
5. scraper._prepare_browser_config 在缺地区时检测、缺版本时读取、auto 时选一次。
   _require_fingerprint 将组合序列化为 _fingerprint_json，本轮固定。
6. 列表、详情、重试、人工恢复复用冻结值；列表重试显式继承快照，不重选。
   配置已冻结后修改地区/ID/版本会报错。
7. 安装二进制 --version 不一定等于正在运行的旧 Chrome 实例版本；
   原会话适配还需核验正在连接的实例，不能只读被注入的 chrome.runtime 版本值。

| 配置 ID | platform | GPU 组合 | 线程 / 内存声明 | 屏幕 |
| --- | --- | --- | --- | --- |
| windows-intel | Win32 | Intel UHD 620 / ANGLE D3D11 | 8 / 8 GB | 1366×768 |
| windows-nvidia | Win32 | NVIDIA GTX 1660 / ANGLE D3D11 | 16 / 8 GB | 1920×1080 |
| windows-amd | Win32 | AMD RX 6600 / ANGLE D3D11 | 12 / 8 GB | 2560×1440 |
| macos-intel | MacIntel | Intel Iris Plus 655 / OpenGL | 8 / 8 GB | 1440×900 |
| macos-amd | MacIntel | AMD Radeon Pro 560X / OpenGL | 12 / 8 GB | 1680×1050 |
| linux-intel | Linux x86_64 | Intel UHD 620 / Mesa | 4 / 4 GB | 1600×900 |
| linux-nvidia | Linux x86_64 | NVIDIA GTX 1660 / OpenGL | 16 / 8 GB | 1920×1200 |
| linux-amd | Linux x86_64 | AMD RX 6600 / radeonsi | 12 / 8 GB | 2560×1440 |

表格是当前目录的说明，唯一配置来源仍是 browser-profiles.json。
Windows UA 中 Win64; x64 与 navigator.platform=Win32 不冲突。
地区决定语言/时区，设备套装决定硬件声明，没有“新加坡显卡”或“菲律宾 Win32”。

代理中途变化时暂停核对，不自动热切指纹或将不同配置混为本轮。
“动态”在当前实现中准确含义是：**每轮依据输入生成，再整轮冻结**，不是持续监听系统代理。

### A4. proxy-access.js：哪些由 JS 做，哪些不是

模板第一行接收 __UGREEN_FINGERPRINT__；自己不检测代理、不挑选套装、不读 Chrome 版本。
scraper._stealth_template 校验文件 SHA，_stealth_script 检查占位符恰有一个后替换。
Node validatedInitScript 同样核验模板与序列化参数。不得擅自删减模板块。

| JS 区块 | 实际行为 |
| --- | --- |
| webdriver | 覆写为 undefined |
| 属性枚举/标记 | 包装 Object.getOwnPropertyNames 过滤特定前缀；尝试删除 window 对应标记 |
| chrome 对象 | 替换 runtime、loadTimes、csi、app、webstore 等兼容占位对象 |
| permissions | 特判通知查询，其余调用原方法 |
| plugins | 返回固定五项插件数组 |
| 语言/平台 | 按参数返回 language、languages、vendor、platform |
| 硬件/PDF | 按参数返回触点、线程、内存和 PDF 字段 |
| screen/outer | 屏幕/外框尺寸取参数；availWidth/Height 取 innerWidth/Height |
| WebGL | 包装 WebGL1/2 getParameter，替换 vendor/renderer 对应两个参数的返回 |

**UA、locale、timezone、viewport/screen 的浏览器层设置不是只靠这个 JS。**
现有 Python/Node 启动器还通过新 context 参数设置它们。原 Chrome 适配必须证明有
受支持、作用域可控的等价能力；只执行 JS 不能算整套配置完成。

模板有不可配置属性，不保证重复注入幂等、热更新或通用 undo。
注册初始化脚本不代表已作用于当前文档；在同一文档反复执行可能报错或留下部分修改。
因此原会话最小实验必须验证：目标范围、配置顺序、新文档注入、跨页保持、失败清理、
结束撤销注册且不影响其他标签。不能拿正常用户页面直接循环试注入。

### A5. 页面探针是有限验证，不是全层身份保证

1. 核对实际目标文档的 UA、语言、platform/vendor、线程/内存、触点、PDF、时区、
   屏幕、WebGL、插件数等与本轮参数一致。
2. 现有 _valid_stealth_probe 检查这些列明字段；user_agent_data 虽采集却不在通过条件内。
   不能把探针通过扩张为 UA-CH、Worker、网络层全部一致。
3. chrome.runtime.getManifest().version 来自模板赋值，不能当独立版本证据。
4. plugins 普通数组、permissions 普通对象、替换 chrome 等兼容性局限仍存在；
   八套参数化不等于原生 API 语义缺陷已修复。
5. 模板哈希一致、初始化注册成功、离线测试通过都不等于网页可访问，更不等于全量成功。

部分配置/注入成功但探针失败或不能撤销时，暂停说明，不能直接切 B 隐藏副作用。
本轮适配尚未开始且工具能力不足、或失败状态已安全解除，原页正常时才回退 B。

## 6. S2-B：CUA 回退的实际操作

进入前完整读 [cua-fallback.md](references/cua-fallback.md)。

1. 确认失败是 A 的工具/适配能力问题，不是网站挑战；原目标页仍正常。
2. CUA 操作同一原 Chrome 标签，正常打开 DevTools Console，执行商品范围的只读表达式。
3. B 不重新选指纹，不补注入，不修改代理，不复制会话或另开采集页。
   已成功配置的同一文档可延续读取，但不能改变本轮参数。
4. 列表读 DOM，详情读当前商品内嵌 JSON；必要时正常打开商品图片查看器。
5. 每次返回加新的 capture_tag，与 URL/页码/商品身份绑定。
   长 JSON 分块回传，只解析对应的实际结果数组；核对连续索引、完整字符串、tag 和身份。
6. 不从输入回显、截断预览、旧输出拼数据；不读取账号标签、Cookie/Storage 或完整无关状态。
7. 结果只放宿主内存，去掉标记/分块包装后按同一 capture-protocol 进入 S5/S6。

这是 CUA 操作加 DOM/JSON 读取，不是 GPT 看截图猜字段，也不是 Playwright 成功。
全量范围不因回退而缩成两件；网站验证码始终原页交用户，不靠换工具或身份跨过。

## 7. S3：全部列表页怎么采集

1. 原页确认 PH UGREEN 与 Top Sales，从 page=0 / 可见第 1 页开始。
2. 限定 .shop-search-result-view 内的 a.contents 商品卡，不混顶部推荐或详情推荐区。
   选择器变化须核验，不把匹配零项解释为零商品。
3. 读取每个实际 a.href 和店铺/商品身份；标题取真实商品 img.alt，
   排除 custom-overlay、flag-label、rating-star 等图。
4. 当前列表价必须明确且唯一。现有解析器查同时包含 truncate、text-base/5、
   font-medium 的数值 span；不拿划线价、折扣或分期金额替代。
5. 月销取完整 N Sold/Month 原文。没有展示才 null，真实 0 保留；累计 Sold 不作月销。
6. 读取当前页/总页和 next 状态，等待可见页码、商品卡实际更新；
   URL 更新不等于内容更新，不能重复记录上一页。
7. 单路串行、页/商品导航间至少 10 秒，直到现场真实末页。
   当前合同要求非末页 30 卡、末页 1～30 卡；布局变化报告，不凑数。
8. pages 保留各页卡片；按 (shop_id,item_id) 首次出现顺序生成详情待办。
   同页重复拒绝，真实跨页重复计数，每页要有新身份，排名由发布代码重算。
9. 不固定历史总页数，不以旧表/历史 URL 清单替代实时列表失败。

list_html.parse_list_html 可复用本轮内存 HTML，但它还带历史 HTML 大小下限及挑战标记检查；
返回 errors/challenge 后须进一步验收。不能为了调用解析器而启动复制 profile 浏览器。

## 8. S4：真实详情、SKU、主副图怎么取

### 8.1 当前商品身份

1. 只按本轮列表真实链接进入详情，核对当前 URL、shop/item ID；canonical/og 存在也核对。
2. 读取当前页面 script[type="text/mfe-initial-data"] 的商品范围数据：

```text
initialState.DOMAIN_PDP.data.PDP_BFF_DATA
├── currentKey
└── cachedMap[currentKey]
    ├── item：shop_id/item_id、title/name、models[]、tier_variations[]
    └── product_images.images[]：商品图库
```

3. 有 currentKey 优先使用该项且必须匹配目标；有 currentKey 指错不能随取别项。
   没有 currentKey 时，仅候选身份唯一且匹配时接受。
4. SPA 跳转可能画面已是详情，内嵌数据仍是 ShopPage。页面正常无挑战时，
   在原标签正常完整加载同一本轮详情 URL 一次再核验，不循环刷新或改抓隐藏接口。

### 8.2 model 与 SKU 规格

1. 取完整真实 models 数组，ID 用纯数字文本并查重，保留实际顺序。
2. 将 extinfo.tier_index 或 tier_index 映射到每层 tier_variations.options，
   检查维数、整数索引、边界和规格名称，形成“规格名 → 实际选项”。
3. 不用 URL 中一个 display_model_id 代表全集，不做选项笛卡尔积，不凭数量补行；
   禁用但仍公开的真实 model 也不能随意漏掉。
4. 映射失败报告，不能用 {"SKU": model_id} 占位冒充真实规格。
5. SKU 图核对 model/extinfo 及真实 tier 图片映射；空字符串不是有效候选。
   多层映射含混时正常选择选项核验；确认没有专属图才 null，未取到不等于没有。

### 8.3 完整商品图库

1. 核对 product_images.images 或经验证的 item.images，确认是完整当前商品图库；
   单个 item.image 不能证明副图完整。
2. 正常打开原页面图片查看器，使懒加载图出现；排除视频封面、评论/推荐/覆盖图。
3. 读取本轮 DOM/页面数据中实际完整 URL，以图片 ID 对应有序图库。
   不能拼 CDN 前缀、删除缩略后缀或使用网上/历史图片。
4. 首张真实商品图为主图，余图按原序为副图，去重；SKU 可以共享真实映射图。
5. 当前协议只接受指定 PH CDN 的完整 HTTPS /file/ URL，超出合同须报告兼容缺口；
   不为了过校验修改真实 URL。

每个列表唯一商品恰有一条完整详情。models_complete/gallery_complete 只有真实完整
读取后才 true；布尔声明不是证明机制。任一未解决缺失不能发布正式部分表。

## 9. S5～S6：从内存事实到唯一 Excel

### 9.1 交接对象

精确类型/字段见 capture-protocol.md，不接受多字段或少字段：

```text
payload：schema_version、store_url、started_at、captured_at、pages、details
├── pages[]：page_index、total_pages、url、next_enabled、cards
│   └── cards[]：product_url、title、price_php、monthly_sales_text
└── details[]：product_url、title、skus、main_image_url、secondary_image_urls、
    │          models_complete、gallery_complete
    └── skus[]：model_id、sku_props、sku_image_url
```

指纹、读取路线、capture_tag、账号、凭据、audit、模型自填排名和旧工作簿路径不放入载荷。
配置状态在本轮宿主上下文/进度里说明，不擅自给 Excel 加列或输出 sidecar。

```text
argv = [PYTHON, DAILY_RUNNER, "--publish-stdin", "--project-root", ROOT, "--worktree", DAILY]
cwd = DAILY
stdin = 本轮完整 UTF-8 JSON
```

符号值使用 prepare 回执，使用 direct argv/stdin；不拼接 shell，不先写原始 JSON 文件。

### 9.2 发布的真实顺序

1. run_scrape 拒绝重复 JSON 键、NaN/Infinity 和非对象载荷。
2. publish_result._convert 严查 PH 身份、连续全部分页、卡数/next、详情全集、SKU/图库、
   价格/月销和带时区时间；确定性重算排名、首次页/位置、去重数和审计。
   正式标题使用详情标题，价格/月销保留首次列表卡的本轮值。
3. _gates 检查注册 worktree、上海启动日/日期分支、发布脚本执行位置、主根和日期
   clean/同 HEAD、规范已跟踪且 SHA 一致、result 没有未知文件。
4. 取得 .git/ugreen_daily_run.lock，再次检查相同门禁，创建本次受控候选 .xlsx。
5. excel.write_excel 重建四表，临时写盘、fsync、按内存期望值回读后形成候选。
   不是修改模板旧业务行。
6. 发布层额外调用 excel.validate_excel 独立重开，要求 full_topsales 且核验通过。
7. 算候选 SHA，第三次检查门禁未漂移，os.replace 原子替换正式文件。
8. 正常退出/可捕获失败清理自身候选；强制杀进程可能残留，不能保证绝无临时文件。
   替换前失败保留旧正式结果，不把旧表当本轮成功。

准备锁和发布锁不覆盖宿主浏览器全生命周期。宿主负责单任务串行。
同日完整成功可替换同日结果，当前代码不自动留备份；其他日期不动。

### 9.3 四表内容

| Sheet | 粒度与核心字段 |
| --- | --- |
| 商品汇总 | 每商品一行：排名、页/位置、店铺/商品 ID、详情标题、列表价、月销原文/下界/状态、SKU 数、主图、副图数、链接 |
| SKU明细 | 每真实 model 一行：商品关联、model ID、规格、SKU 图、商品链接；没有 SKU 价格列 |
| 图片明细 | 每张主/副图库图一行：商品关联、类型/序号、实际 URL；不是内嵌图片，不把 SKU 图计入图库 |
| 抓取核验 | 固定 17 项，含范围、分页/去重、详情覆盖/失败、月销空值、SKU/主副图数量和结论 |

表头第 6 行、数据第 7 行起，冻结 F7/E7/E7/A7。
ID 为文本，价格为数值，未展示月销为空非零；外部文本按字面写入，不能生成公式。
四表列名/顺序与 17 项完整名称以 excel-output.md 为准，不增删或改口径。

### 9.4 独立验收和证据边界

```text
argv = [PYTHON, DAILY_RUNNER, "--validate", "--project-root", ROOT, "--worktree", DAILY]
cwd = DAILY
```

1. validate_result 核对明确日期的注册关系、唯一路径、result 只有正式表，再独立验 Excel。
2. 核对 collection_mode=full_topsales、计数与发布回执一致；宿主另查日期源码 Git clean。
3. 此只读验收允许历史日期/跨午夜，本身不重新检查 clean/同 HEAD/分支/发布锁；
   不能描述成重复所有发布门禁。
4. Excel 层不会联网确认图片可访问、真实 SKU 全集或网页覆盖。17 项通过仅证明内部一致，
   必须结合本轮实际现场证据才可说全量完成。
5. 不直接调用 write_excel 绕过 Git/日期/路径/模板和严格载荷门禁。

## 10. 代码保留，但调用时需要分清的差异

以下是同一项目的复用/适配边界，不是第三条采集路线。

| 代码 | 现有行为 | 当前规范下的处理 |
| --- | --- | --- |
| detect_browser_region | 新建空白浏览器观测地区 | 解析可复用；原会话观测能力需先最小验证 |
| _temporary_chrome_profile_base / _clone_detail_profiles | 复制会话建立私有/分片 profile | 保留代码，不作为原 Chrome A/B 执行步骤 |
| _launch_context / installPersistentLaunchShim | 新 context 设置 UA/地区/尺寸并注册 JS | 配置链可参考；不能把该启动方式说成连接原 Chrome |
| Node validateProfile | 要求特定临时目录及会话副本 | 不能直接塞入用户原 profile 路径冒充接管 |
| _capture_list_page_with_profile | 非人工模式默认三次，重启私有浏览器，冻结指纹不换 | 不将旧重启/挑战重试搬成原会话策略；挑战原页交用户 |
| DETAIL_PAGE_SCRIPT | currentKey/URL/商品身份匹配，附带指纹探针 | 商品字段选择可参考；B 不要求指纹探针匹配，不补注入 |
| _parse_detail | 可退为 SKU ID 占位、拼图片 CDN、单图回退；全量标题优先列表卡 | 当前正式合同更严格，不能不加核验直接发布该宽松结果 |
| verify_access / scrape_known_details | 参考表身份抽测或旧清单详情刷新 | 保留，不作为实时列表失败的自动回退或全店成功证明 |
| excel.py 的 known_product_details | 支持旧清单模式与 26 项审计 | 当前 publish_result 只收全量 17 项模式，不混称今日 Top Sales |
| run_scrape 旧参数 | browser-profile、verify-access 等参数会明确拒绝并提示迁移 | 不虚构 CLI 注入开关，不绕过入口恢复复制流程 |

底层 prepare_daily_worktree 可解析非今天日期，但公开 run_scrape --prepare 只接受今天；
不得借底层调用规避正常运行边界。上述差异只是如实说明，不表示本轮已修改这些代码。

## 11. 失败、中断、已验证范围与交付

| 情况 | 动作 |
| --- | --- |
| A 工具/适配能力缺失，原页正常且无半注入 | 说明缺口，按 B 继续同一业务范围 |
| 配置/注入部分生效或无法清理 | 暂停说明影响，不叠加脚本、不隐瞒后换 B |
| 登录/验证码/挑战/Page Unavailable | 原页给用户；处理后重读，不把“好了”当验收 |
| SKU/图库/分页/身份缺失 | 说明具体字段，不历史回填、不发布部分结果 |
| 主根脏、日期不同 HEAD、result 有未知文件 | 报告冲突，不自动 Git 清理或删除 |
| 宿主内存丢失 | 重新现场取得证据，没有持久化 resume 服务，不从旧表补本轮 |
| 发布失败但旧表仍在 | 明确旧表不是本次新结果 |

不落盘 HTML、JSON、截图、trace、会话/token、部分 Excel 或任务书副本；
只允许发布模块管理受控临时候选。标准、脚本、依赖环境、测试、其他日期成果全部保留。

2026-09-20 已验证范围：B 路线取得 27 页/810 个唯一商品链接；两件详情分别取得
6/12 个真实 SKU、各 9 张主副图库原图 URL，并取得 SKU 图片映射。
**当时未完成全部 810 件详情，未生成本轮最终全店 Excel，也没有证明 A 的原 Chrome
注入链已接通。** 历史数量不是以后运行的期望值，更不是可复用业务数据。

正式交付仅为 worktrees/YYYYMMDD_ugreen_topsales/result/ugreen_topsales.xlsx。
报告真实路线、列表页数/商品/SKU/主副图数量及独立验收结果，提供文件链接或可用附件。
没有附件能力时说明，不以本地路径冒充已经发送到手机。不声称图片已经嵌入 Excel。

持续执行按系统要求用中文说明任务清单、正在处理、刚完成和下一步；必要人工输入时明确
暂停，完成/交还后不空转。不关闭原 Chrome，不承诺任何指纹或工具一定访问成功。
