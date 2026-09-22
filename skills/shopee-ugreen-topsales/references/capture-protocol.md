# 现场数据交接协议 v1.0

宿主 Agent 使用当前环境已有浏览器工具读取**本轮原 Chrome 页面**，将数据保留在内存，
通过 stdin 的单个 UTF-8 JSON 对象交给 `run_scrape.py --publish-stdin`。
本协议不是 HTTP 接口，不要求新建浏览器连接或保存 JSON 文件。

普通 Playwright 接管人工已打开的原 Chrome；用户指定 CUA，或 Playwright 工具不可用
且原页正常时，可按 [cua-fallback.md](cua-fallback.md) 用电脑操作接管同一原 Chrome，
读取详情 DOM/商品内嵌 JSON；用户明确只用 A 时不自动切换。两条路线都不做环境注入，提交本协议的相同载荷；
控制台回传使用的读取标记、分块包装、诊断字段不得进入最终 pages/cards/details。
普通 Playwright 只允许持续长连接：初始化、检查、采集、进度保存及冷却复用同一附着
连接和原 `page`，不短连检查即断开，不频繁重连或重复触发远程调试授权；连接生命周期
与验证码交接、普通错误自动恢复遵循主 Skill 第 4 节。
普通 Playwright 路线默认完整 DOM 直读，不发送鼠标移动或滚轮。导航前读当前 DOM 检查
挑战，再按真实 URL 导航；随机驻留后用 `page.content()` 取得完整 DOM，核对当前 URL、
挑战及完整性后离线解析。导航前的 DOM 仅用于安全检查，不作下一件商品的数据。
普通恢复的操作时限与有限重试见主 Skill 第 4 节。不通过 locator/click/evaluate 逐项操控页面。
只读可见性/焦点状态仅作诊断；后台或 `hasFocus=false` 本身不暂停、不报错、不断开，
也不自动抢回焦点。普通超时/加载/解析失败由宿主自动恢复；输入超时后重新读取的
完整 DOM 经身份与字段验收可继续采集，不要求用户确认。只有现场验证码/人工验证
抛 `CaptchaDetected` 并交用户；不绕过登录或访问限制。

`--publish-stdin` 只接受完整 PH UGREEN 全量载荷，不提供历史清单回填分支。
`--checkpoint-stdin` 用相同字段保存本轮进度：pages 可为真实连续前缀（保留现场 total_pages/
next_enabled），details 可为已完成并验收的子集；不伪造剩余详情。保存频率及停止尾批
见主 Skill 第 8 节，进度表口径见 [excel-output.md 第 7 节](excel-output.md#7-累计进度-excel)。
每层对象字段须恰好匹配下表；缺字段、额外字段、重复 JSON 键、NaN/Infinity 均拒绝。
`null` 仅用于下述明确允许的字段，不能用来跳过未知的必需数据。

## 1. 根对象

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| `schema_version` | string | 固定 `1.0` |
| `store_url` | string | 本轮 PH UGREEN 第 0 页 Top Sales URL |
| `started_at` | string | 任务启动的带时区 ISO 时间；上海日期必须等于目标 worktree 日期 |
| `captured_at` | string | 完成现场取数的带时区 ISO 时间，不能早于 started_at，可跨午夜 |
| `pages` | array | 按 page_index 从 0 连续排列的全部列表页，非空 |
| `details` | array | 本轮列表全部唯一商品的详情，恰好一商品一条，不多不少 |

## 2. pages[] 与 cards[]

| 页对象字段 | 类型 | 约束 |
| --- | --- | --- |
| `page_index` | integer | 0 起，严格等于数组位置 |
| `total_pages` | integer | 每页一致，等于 pages 长度，来自本轮实际分页 |
| `url` | string | 本轮实际该页 URL，page 参数等于 page_index |
| `next_enabled` | boolean | 非末页 true，末页 false；必须现场确认按钮状态 |
| `cards` | array | 非末页恰好 30 卡；末页 1–30 卡；按现场卡片顺序 |

| 卡片对象字段 | 类型 | 约束 |
| --- | --- | --- |
| `product_url` | string | 现场完整 PH UGREEN PDP URL |
| `title` | string | 本轮非空列表标题，供现场身份核对；正式标题使用详情标题 |
| `price_php` | number | 明确的当前列表价，非负有限数；不是布尔值、区间文字或估值 |
| `monthly_sales_text` | string / null | 完整 `N Sold/Month` 原文；只有确实未展示月销才 null |

月销支持整数、千位逗号、K/M 和 `+`，如 `766 Sold/Month`、`5K+ Sold/Month`、
`1.2M Sold/Month`、`0 Sold/Month`。无 K/M 时不接受小数；换算后必须为可精确保存的
非负整数。`Sold` 累计销量不能冒充月销。发布模块换算下界，不由 Agent 心算回填。

单页不能重复同身份；允许真实跨页重复并保留首次出现位置，但每个后续页必须有新身份，
不能把未更新页面复制多次当遍历。页数/布局改变或分页证据不成立时停止核对，不凑 30 卡。

## 3. details[] 与 skus[]

| 详情对象字段 | 类型 | 约束 |
| --- | --- | --- |
| `product_url` | string | 本轮实际详情 URL，身份必须在列表内 |
| `title` | string | 当前详情的非空标题 |
| `skus` | array | 完整非空真实 model 集合，保留当前页面数据顺序 |
| `main_image_url` | string | 完整详情商品图库首图 URL |
| `secondary_image_urls` | array[string] | 其余商品图按图库顺序，确实无副图时可空 |
| `models_complete` | boolean | 只有当前页面完整 model 集合已实际读取、核对才 true |
| `gallery_complete` | boolean | 只有当前页面完整商品图库已实际读取、核对才 true |

| SKU 对象字段 | 类型 | 约束 |
| --- | --- | --- |
| `model_id` | string | 纯数字文本；同商品内按数值身份唯一，不能靠前导 0 制造不同 model |
| `sku_props` | object | 非空的“非空规格名称 → 非空规格选项文本”映射，必须对应真实 model；下述严格单规格空字段情形固定写 `{"规格":"单规格"}` |
| `sku_image_url` | string / null | 当前真实专属图映射；确认没有专属图可 null，未取到不能装作没有 |

不得从可见选项生成笛卡尔组合、用 query 的单个 model 代表全部 SKU、根据历史 SKU 数
补行、或用主图替补 SKU 图。仅当商品恰有一个真实 model、恰有一层规格，且 tier 名称、
唯一 option、model 名称均为空时，固定用 `{"规格":"单规格"}` 表示页面的无规格事实；
多个 model、存在真实规格或结构解析失败不能套用，也不能改用 model ID 占位。
SKU 图先使用具体 model/extinfo 的 `sku_image/image/image_id`；这些直接字段全空时才使用
该 model 的 tier_index 对应 tier 图片。同一优先级内多个非空引用冲突时拒绝，不跨层随取。
两个 complete 标志是**宿主对实际读取结果的声明，不是证明机制**。仅截图/可访问性文字
无法取得 model ID 和完整 URL 时，必须报告“未取得/未验证”，不能设置 true 来通过校验。

## 4. URL 与文本边界

- URL 使用无凭据、无显式端口、无 fragment 的 HTTPS；不得含空白、反斜杠或登录 token。
- 列表域 `shopee.ph`，路径 `/ugreen.ph`，参数须有 `page=<0起页码>`、
  `sortBy=sales`、`tab=0`；可有 `shop=64922227`，不能绑定另一店铺。
- PDP 域 `shopee.ph`，身份路径为 `/product/64922227/<item_id>` 或当前实际
  `…-i.64922227.<item_id>`（亦支持 `/i.64922227.<item_id>`）；item_id 为正整数。
  商品/店铺 ID 从 URL 重算，不另接收 Agent 提交的身份字段。
- 当前图片校验支持 `down-ph.img.susercontent.com` 或 `cf.shopee.ph` 的
  `/file/<标识>` 原图 URL；不带 query，不收 `_tn` / `_t` 缩略路径。主副图库不能重复。
  已有合规完整 URL 必须原样保留。只有权威 `product_images.images`、model/extinfo 或 tier
  图片字段给出合法图片 ID，且同一完整 DOM 没有该 ID 的绝对原图 URL 时，才对这个缺失项
  生成 `https://down-ph.img.susercontent.com/file/<图片ID>`，并重新通过本条 URL 校验；
  不得覆盖已有 URL、去缩略后缀、改变图片顺序或给其他字符串套域名。实际完整 URL 若
  超出支持范围，说明兼容缺口，不能猜换域名或篡改路径。
- 文本不超过 Excel 单元格 32767 字符，不含不可写入单元格的控制字符。
- 数值须有限且不超过 `2**53-1`，不接受用 true/false 代替整数或价格。

工具明确支持的只读 DOM/当前页面数据可以使用；不凭空发明 API，不读取 Cookie/密码/
Storage 凭据，不直接转向未授权网络接口。所有必需字段仍要绑定实际当前页面和商品。

## 5. 交接与结果

构造数据时按上述对象形状组织内存，不将载荷、HTML、截图落盘；允许已授权的累计进度
Excel。全量发布用支持 stdin
的进程工具调用以下 argv（符号值取自 [标准任务书](../assets/run_prompt_template.md) 参数绑定，不是字面参数）：

```text
[PYTHON, DAILY_RUNNER, "--publish-stdin", "--project-root", ROOT, "--worktree", DAILY]
stdin = JSON.stringify(本轮完整载荷)
cwd = DAILY
```

也可用当前宿主可用语言在内存中 `json.dumps(payload, ensure_ascii=False, allow_nan=False)`
并通过进程的 input/stdin 传入；不拼接 shell 命令或为传参先写 JSON 临时文件。
宿主工具若无法安全传递本轮完整载荷，报告这个交接能力缺口，不改成不受控持久化。

发布模块重算去重、排名、来源页、计数和 17 项核验；不接受 `audit`、外来排名、成功计数
或历史表路径。目标目录/分支和规范哈希检查通过后，候选表独立校验；Git 脏状态或
HEAD 不同不作为阻断条件。
最终原子发布。stdout 回执含 `path/sha256/template_sha256/schema_version/collection_mode/`
`list_page_count/product_count/sku_count/main_image_count/secondary_image_count/audit_status`。

成功条件是进程退出 0、`collection_mode=full_topsales`、`audit_status=通过`，再执行独立
`--validate` 并核对同一路径及数量。失败非 0，保留旧有效结果，不允许删旧表来掩盖失败。
本地协议校验只验证载荷与文件一致性，不会再次联网替宿主证明页面事实。
