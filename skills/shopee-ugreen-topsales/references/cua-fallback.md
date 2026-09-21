# B：电脑操作 CUA 接管原 Chrome

用户选择 B 或 A 工具不可用时读取。本方法使用人工**已打开的原 Chrome 页面**：宿主通过
电脑操作工具 CUA 操作界面，在 DevTools Console 执行只读 JavaScript，读取本轮页面
DOM 和商品内嵌 JSON。不是 Playwright、截图 OCR、直接 HTTP 爬虫或旧 profile runner。

目录、日期快照、四表字段及发布仍分别服从 [worktree.md](worktree.md)、
[excel-output.md](excel-output.md)、[capture-protocol.md](capture-protocol.md)。

## 1. 进入与停止条件

| 现场情况 | 操作 |
| --- | --- |
| 普通 Playwright 能读取原会话且正常 | 默认使用 A；用户指定 B 时按本方法执行 |
| Playwright/扩展取标签或 DOM 超时、入口不可用，但 CUA 能读取正常原页 | 用户未明确限定只用 A 时切到本方法；不要无限重连 |
| 列表能读、列表没有 SKU | 正常现象；先取真实链接，再进详情，不据此宣布无法采集 |
| 登录、验证码、访问挑战、Page Unavailable | 原页交用户；不靠换工具、身份、代理或重复刷新跨过网站限制 |
| CUA 也不可用，或当前环境明确不允许 DevTools 只读执行 | 报告具体能力缺口，暂停，不虚构 API |
| 数据身份冲突、必需字段仍不完整 | 保留现场、不发布，报告缺失字段，不套用历史数据 |

只做受支持的原页面读取。不得复制 Cookie/Storage/profile、启动另一个 Chrome/context/
采集标签、搭建 CDP、修改代理/请求头/指纹、安装扩展或扩大权限。页/商品导航单路串行，
每次导航前独立随机等待 2～3 秒，每完成 50 件额外随机冷却 3～5 分钟；单纯读取界面
不算新一次商品导航，但不得高频刷新冲击页面。

本参考约束 B；A 使用普通 Playwright。两者都不做指纹配置、地区查询或环境脚本注入，
只沿用人工已打开的原浏览器状态。CUA 结果不得声称为 Playwright 验证结果。

只读取商品相关 DOM。不要输出整份 `initialState`、账号信息标签、认证数据或控制台
无关历史。只读表达式不能含 fetch/XHR、新网络接口调用、业务提交或页面状态注入。
DevTools 若要求安全授权、解锁粘贴等，交用户处理，不自动关闭安全保护。

## 2. 工具接入与界面操作

1. 先读当前 CUA 工具文档，绑定用户指定的原 Chrome 窗口/标签并核对 URL。工具名称
   可能不同；不能假设另一台电脑也有同名 API。不要通过外部脚本或浏览器配置文件取数。
2. 从原页面正常打开 DevTools 的 Console。macOS 本次使用 `super+alt+j`；其他环境
   使用工具文档和实际菜单。确认 Console 的执行上下文是目标页面，而非扩展、DevTools
   本身或无关 iframe。不要改变设备模拟、代理或指纹设置。
3. 每次依据最新可访问性树定位 `Console prompt`。本次 CUA 的 `setValue` 能完整写入
   表达式；`typeText` 曾丢失括号/标点，`paste` 曾超时，因此必须核对输入而不是盲按回车。
   只使用当前文档支持的输入方式，不能复用旧可访问性索引、截图坐标。
4. 执行后重读界面，等待**本次表达式**的返回结果。页面可见不证明代码已执行；出现语法
   错误时先检查输入是否完整，不能把输入传输错误误判为网站没有数据。
5. 结果保存在宿主内存；不保存 DevTools 日志、HTML、JSON、截图或临时工作簿。
   原窗口/会话保留，不清空用户控制台、账号或浏览器资料。

CUA 工具只负责操作；字段来自 DOM/页面 JSON，不能说成“GPT 根据图片推测的商品数据”。
`run_scrape.py` 仍只承担准备/交接/发布，不会因本参考文件存在而自动启动本流程。

## 3. 列表页：先取得完整详情链接

确认地址中的 `page`、`sortBy=sales`、`tab=0` 和页面选中的 Top Sales。限定读取实际
搜索结果区域，排除顶部热销推荐、广告或详情页推荐区。以下是本次验证过的 DOM 入口；
每轮仍需确认匹配数量与页面一致，不能将旧选择器匹配不到当作零商品：

| 内容 | 本次验证的入口 / 核对方式 |
| --- | --- |
| 商品卡 | `.shop-search-result-view a.contents`，读取每个 `a.href` 的完整链接 |
| 标题 | 卡片商品 `img.alt`；排除 `custom-overlay`、`flag-label`、`rating-star` |
| 当前列表价格 | 卡片内同时含 `truncate`、`text-base/5`、`font-medium` 类的数值 span；必须唯一，不拿折扣/原价替代 |
| 月销 | 卡片自身文本节点中的完整 `N Sold/Month`；无展示才空，不能拿累计 Sold 顶替 |
| 当前页 / 总页 | `.shopee-mini-page-controller__current` / `__total` |
| 下一页 | `button.shopee-mini-page-controller__next-btn` 的存在及真实禁用状态 |

只读探针示例（字段选择器使用前核对实际 DOM）：

```javascript
(() => ({
  url: location.href,
  current: document.querySelector('.shopee-mini-page-controller__current')?.textContent,
  total: document.querySelector('.shopee-mini-page-controller__total')?.textContent,
  links: Array.from(document.querySelectorAll('.shop-search-result-view a.contents'), a => a.href)
}))()
```

翻页使用原界面的正常控件；地址可能已更新、商品卡尚未更新，需确认显示页码等于
URL `page + 1`、卡片加载完整且有新的商品身份，再收录。非末页 30 卡、末页 1～30 卡
及连续页码仍依原合同核验。按 `(shop_id,item_id)` 保留第一次出现的顺序；保留每页记录
以核算跨页重复。全部页数与数量都来自本轮，不照抄本文件末尾的历史验证数量。

## 4. 详情页：绑定当前商品，再读取内嵌数据

按本轮列表中的完整链接，在原标签进入详情。先正常加载，再检查：

```javascript
(() => Array.from(document.querySelectorAll('script[type="text/mfe-initial-data"]'), n => {
  const p = JSON.parse(n.textContent);
  return {pageName: p.pageName, hasPdp: !!p.initialState?.DOMAIN_PDP};
}))()
```

**本次关键故障：** 从店铺列表点击商品会发生站内跳转，屏幕已经显示详情，但上述标签
仍可能是 `pageName: "ShopPage"` 的旧店铺初始数据。不能把它解析为当前商品，也不能
因此认定 SKU 无法取得。在页面正常且没有挑战时，将**已经现场取得的同一详情完整
链接**在原标签地址栏正常加载一次，再检查；不是反复刷新、另开标签或重启 Chrome。
本次正常完整加载后变成 `pageName: "product"`，出现了匹配的 PDP 数据。

读取路径：

```text
script[type="text/mfe-initial-data"] 的 JSON
└── initialState.DOMAIN_PDP.data.PDP_BFF_DATA
    ├── currentKey
    └── cachedMap[currentKey]
        ├── item：shop_id/item_id（或 shopid/itemid）、title/name
        │   ├── models[]：model_id/modelid、extinfo.tier_index 或 tier_index
        │   └── tier_variations[]：name、options[]、images[]
        └── product_images.images[]（或经核对的 item.images[]）
```

- 优先绑定 `cachedMap[currentKey]`，其商品/店铺身份须与现场链接、当前地址及可见商品
  一致；canonical/og 身份存在时也核对。不能随取缓存第一项或另一个商品的数据。
- 如果没有 `currentKey`，仅当商品候选身份唯一且正好等于本轮待办商品时才可采用；
  有 currentKey 却指向别的商品、含混的候选或无数据时，不降级猜取。
- 标题取本轮详情 `item.title/name`。models 必须非空、ID 为真实纯数字文本且不重复，
  不能用 URL 的单个 `display_model_id` 代表全部 SKU。
- 用每个 model 的 `tier_index` 对应各 `tier_variations[j].options[index]`，形成规格名
  到选项的映射。核对维数、整数索引和边界；不能用选项笛卡尔积补 SKU，也不能退成
  `{"SKU": model_id}` 冒充真实规格。仅当恰有一个真实 model、恰有一层规格，且 tier
  名称、唯一 option、model 名称均为空时固定写 `{"规格":"单规格"}`；其他页面结构
  不同则重新核验，不硬套该路径。
- 旧 `scraper.py` 中 `DETAIL_PAGE_SCRIPT`、`_parse_detail` 仅可参考字段映射；不要因此
  调用旧私有浏览器启动器。其单图回退、占位规格、图片 ID 拼域名等宽松路径不能替代
  当前完整性证据。

## 5. 主副图库与 SKU 图：取得真实 URL

1. 以绑定当前商品的有序图库记录为基准，区分商品图、视频封面、评论图和推荐图。
   只取得单个 `item.image` 不证明完整图库；图库记录本身若含混，先核对，不能静默回退。
2. 页面通常只加载部分缩略图。正常点击主图或真实商品图片缩略图，打开原页面图片
   查看器，显示剩余图库。默认显示视频时，先点击商品图片缩略图，不能把视频封面算主图。
3. 从当前 DOM 中实际图片元素的 `img.src` 读取绝对 URL。此次 `srcset/currentSrc` 可能
   是带 `@resize` 的展示图，而 `src` 是真实原图；以实际观察为准，不删除后缀造原图。
4. 用图库图片 ID 与已观察的原图 URL 精确匹配，覆盖每张图库并保持原序。以下仅做匹配，
   不生成 URL；图片标识必须来自本轮商品数据：

```javascript
(imageId) => {
  const urls = Array.from(document.images, img => img.src).filter(src => {
    try {
      const u = new URL(src);
      return u.protocol === 'https:' && !u.username && !u.password && !u.port &&
        ['down-ph.img.susercontent.com', 'cf.shopee.ph'].includes(u.hostname) &&
        !u.search && !u.hash && u.pathname === '/file/' + imageId;
    } catch { return false; }
  });
  return [...new Set(urls)];
}
```

5. SKU 图先核对具体 model/extinfo 的 `sku_image/image/image_id`；这些直接字段全空时，
   才按已验证的 tier_index 对应 `tier_variations[].images[]`。图片字段可能是空字符串：
   不能只用 `??`，因为 `""` 会阻断后续有效映射。同一优先级内多个非空引用冲突时
   停止核对，不跨层随取第一张。
6. 图片 ID 存在却匹配不到原图 URL时，只要 ID 来自当前商品权威图库/model/tier 字段，
   可仅对该缺失项生成 `https://down-ph.img.susercontent.com/file/<图片ID>` 并按
   capture-protocol.md 重新校验；已有完整 URL 不得覆盖。只有确认该 SKU 没有专属图才
   可 null。禁止用商品主图替代 SKU 图或用历史图片补齐。主副图按图库去重，SKU 可以
   共享同一张真实映射图片。

## 6. 控制台结果回传：不要解析截断预览或旧结果

大结果的 Console 预览和可访问性单节点文本会截断，界面增量 diff 也不保证按新旧顺序
排列。本次发生过：取“最后一个数组”误选旧输出，以及把所有展开数组的行混在一起。
按以下方式回传到宿主内存，既适用于列表也适用于详情：

1. 宿主为**每次读取**生成新 `capture_tag`，并绑定预期 URL/页码/商品身份。
2. 把只读字段表达式的结果包为 `{capture_tag, data}`，`JSON.stringify` 后按约 240 个
   字符分块返回数组。本次分块方式如下；value/tag 是宿主绑定的表达式结果与新标记，
   不是要求在网站 window 上建立缓存：

```javascript
(value, tag) => JSON.stringify({capture_tag: tag, data: value}).match(/.{1,240}/gsu)
```

   `u` 标志避免把 emoji 等字符的代理对切开；单块仍被 UI 截断时缩小块大小并重读，
   不放宽完整性检查。
3. 用新完整可访问性树确认包含该 tag 的**实际数组结果行**已经出现，再正常展开。
   不从代码输入/回显、`The focused UI element is ...` 行、旧输出或含 `…` 的预览取数据。
   只在等待本次结果时做有界读取；结果未出现/执行出错就检查本次输入，不重新导航轰击。
4. 只收该数组的索引叶子行 `0..N-1`：大数组若显示 `[0…99]` 等区间，先正常展开
   同一已绑定数组内的索引分组，不展开原型或混入其他输出。序号连续、数量与数组
   length 一致、每块完整。
   文本转义以实际显示为准，先解码每个字符串，再按序拼接，最后 JSON.parse；不能把
   截断号、换行或引号凭经验补回去。校验 tag 和 data 的 URL/页码/商品身份。
5. 全部核验通过才收录 `data`，剥离 tag 和分块包装；不要把诊断字段放进发布载荷。
   控制台展开项太多时可点 `Collapse all` 折叠以减少界面负担，不清空用户日志或改设置。
6. 宿主工具重置会丢失内存。没有本轮完整内存证据时重新现场采集，不能从旧工作簿恢复；
   也不能为规避这一限制另存原始 JSON。不要让一次长工具调用超时丢掉已采数据。

## 7. 验收与已验证范围

备用路线仍先取得全部列表，再按首次出现顺序完成全部唯一商品详情；能力验证时先进入
少量详情是为了确认方法，不会将全量任务降为两件抽测。每件均核对 models/规格/图映射、
完整图库及链接；只有证据充分才能设置 `models_complete/gallery_complete=true`。
随后按 capture-protocol.md 交接原有 S5/S6，不写第二种 Excel、不发布部分表。

2026-09-20 的现场验证：27 页、810 个唯一商品链接；前两件详情分别读到 6/12 个真实
SKU，均读到 9 张商品主副图原图 URL，SKU 图片映射也已取得。这证明该次备用方法可读到
所需字段；**当时未完成 810 件详情，也未生成全店最终 Excel**。这些数量不是之后任务的
期望值或可复用业务数据，更不是无人值守、所有商品或未来网站版本必然成功的保证。

本参考是主根 Skill 的维护内容；更新不等于同步运行中的日期 worktree。正式运行仍须
冻结包含所用规范的 clean Git snapshot；不得热补日期目录、自动提交或绕过同 HEAD 门禁。
