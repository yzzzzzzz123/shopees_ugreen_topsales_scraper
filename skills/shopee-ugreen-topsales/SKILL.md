---
name: shopee-ugreen-topsales
description: 通过现有浏览器工具读取用户原 Chrome 中的 PH UGREEN Top Sales 全店列表与商品详情，在日期 Git worktree 输出符合固定内容规范的四表 Excel；也支持用户明确限定的现场抽测或既有表分析。
---

# Shopee UGREEN Top Sales

## 执行入口与唯一规范

本 Skill 自包含任务书、业务规范、参考工作簿及执行脚本；本文件就是规范索引，
项目根不另设规范目录或平行标准。新增/修改规则同步维护下列文件，不依赖聊天记忆。

先完整读取 [标准任务书](assets/run_prompt_template.md)，再按其中路由读取各阶段规范。
任务参数来自计划/准备回执，在宿主上下文绑定；不改写冻结任务书，不创建任务书副本，
未解析的参数符号不得当作实参运行。

| 文件 | 何时读取 | 负责的内容 |
| --- | --- | --- |
| [assets/run_prompt_template.md](assets/run_prompt_template.md) | 每次执行先完整读取 | 可直接下发的任务书、参数绑定、阶段及验收 |
| [references/worktree.md](references/worktree.md) | 准备、发布或验收前 | 日期身份、目录树、Git 边界与生命周期 |
| [references/excel-output.md](references/excel-output.md) | 采集字段及导出前 | 四表内容、字段顺序、行粒度、类型、17 项核验 |
| [references/capture-protocol.md](references/capture-protocol.md) | 现场取数及发布前 | 内存数据、stdin 交接、严格字段校验 |
| [assets/ugreen_topsales.xlsx](assets/ugreen_topsales.xlsx) | 只读检查 schema 时 | 对应的工作簿结构/版式；不是历史数据种子 |

## 默认任务与架构

正常“跑一遍 / 完整执行 / 刷新全店”就是本轮全部 Top Sales 列表 → 每个唯一详情 →
完整 model/SKU 与图库 → 确定性交接、发布、独立验收 → 日期 Excel。默认店铺
`64922227`、PH、PHP，地址 `https://shopee.ph/ugreen.ph?page=0&sortBy=sales&tab=0`。
不按代理地区切国家，不把过去一次抽测要求永久当默认。

| 用户请求 | 范围与交付 |
| --- | --- |
| 跑一遍、完整执行、刷新全店 | 本轮全部列表和唯一详情，日期 worktree 下完整四表 Excel |
| 明确抽测、几页、几件、只文字 | 按范围现场读取，中文文字说明已取得/未取得/未验证；不建 worktree、不调用全量发布 |
| 分析既有 Excel | 只读指定文件并给分析结论；不自动访问网页或改写文件 |
| 其他国家或店铺 | 先说明当前发布合同只支持 PH UGREEN，不把其他站数据塞进 PHP 合同 |

没有给抽测数量时，只做少量代表性抽测，不自动扩成全店。已知清单刷新不是实时列表
失败的自动回退；规范表和历史访问记录不得补齐本轮商品、URL、价格、月销、SKU 或图片。

```text
用户任务
└── 宿主 Agent：读取 Skill → 绑定任务书 → 已有工具读取原 Chrome
    ├── 人工接管：用户在原页完成登录/验证 → Agent 重读验收
    └── 本轮完整数据（仅内存）
        └── run_scrape.py --publish-stdin
            └── publish_result.py → excel.py → 独立校验 → 原子发布
                └── run_scrape.py --validate → 日期 worktree 中唯一 Excel
```

这是“宿主 Agent 执行任务书 + 确定性本地脚本”的单执行者串行流程；不另起模型服务、
多 Agent 总控或 LangChain/LangGraph 应用。脚本负责准备、转换、校验及导出，不自行
访问网页。`--plan` 只生成计划；已有工具能完整取数即可交接，不必先另造采集运行时。

## 现场工具与边界

宿主按任务书使用**当前已有工具直接读取原 Chrome 页面**，先读实际工具文档，
只用其明确支持的能力，不发明 API。无必需字段时说清实际缺口。

不复制 profile/Cookie/Storage，不启动替代浏览器/context/标签，不另搭 CDP、调试端口，
不重启 Chrome，不修改代理/指纹/UA/GPU/header。单路串行，页/商品间至少 10 秒。
登录、验证码、挑战、无效页面或工具失联时保留原页交用户；处理后重读验收，
“好了”本身不代表通过。不关闭原窗口，不刷新冲击，不自动解验证或切身份。

可见选项不是完整 model 集合，截图/相对路径不是完整图片 URL；缺字段不能靠设置
`models_complete/gallery_complete=true` 自证。工具返回的当前 DOM/页面数据也须绑定
商品身份；不读登录凭据或擅自转向网络接口。

## 发布与输出门禁

- 只读 `assets/ugreen_topsales.xlsx` 的 schema，不使用旧业务行作为本轮种子或补值。
- 数据仅在内存，通过 `--publish-stdin` 交接；按现场协议由代码重算排名、计数与核验。
- 唯一结果是 `worktrees/YYYYMMDD_ugreen_topsales/result/ugreen_topsales.xlsx`，
  上海启动日跨午夜不变。主根与日期快照 clean、同一已提交 HEAD、规范哈希相同。
- 正常全量允许受控 `--prepare` 创建/安全复用本日 worktree；日期内源码、任务书和
  规范只读，不热修补。不自动提交、推送、拉取、清理、强制同步或删除分支/其他日期。
- 完整现场覆盖、载荷校验、原子发布和独立 `--validate` 都通过才交付完整四表。
  失败保留既有结果但不能充当本轮输出；不发布部分表，不持久化 raw HTML/JSON/截图/
  trace/会话/token。只允许发布模块管理并清理自己的受控临时候选工作簿。
- 未知文件、脏状态、字段缺失、路径或合同漂移停止报告，不放宽校验制造成功。

## 状态与证据用语

| 状态 / 结果 | 可以说明什么 | 不代表什么 |
| --- | --- | --- |
| `awaiting_browser_collection` | 任务计划已生成 | 现场采集已完成 |
| `created/reused` | 日期 worktree 已准备 | 网站可访问、字段已取得 |
| `contract_checked` | 本地规范结构通过检查 | 本轮数据完整 |
| 发布与独立验收通过 | 载荷和工作簿内部契约一致 | 自动证明网页已完整读取 |

只有另有本轮全部现场覆盖证据才能声明全量完成。离线测试、历史成功和完整性勾选不能
代替本轮证据，也不保证无人值守或长期稳定。持续执行按系统要求用中文反馈任务清单、
当前页/商品、已完成结果和下一步；完成或等待必要人工输入后不空转提醒。

只有解释旧实现或访问故障历史时才读
[历史访问记录](references/verified_access.md)。旧复制 profile、注入和旧 runner 命令
不是操作步骤；维护用纯解析/导出代码可保留复用，不能静默恢复旧浏览器/清单路线。
[旧契约入口](references/extraction_contract.md) 仅为旧链接保留兼容路由，不维护第二份规范。
