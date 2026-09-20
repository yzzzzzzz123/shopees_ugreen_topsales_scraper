# 日期 worktree 与文件规范

## 1. 身份与参数

正式任务固定使用上海启动日，不能按代理国家或抓取结束时刻改日期。

| 项目 | 固定规则 |
| --- | --- |
| 主项目根 | 从当前 Skill 所在 Git common dir 解析，不能指向其他仓库 |
| 业务日期 | `started_at` 转为 `Asia/Shanghai` 后的日期 |
| 日期目录 | `worktrees/YYYYMMDD_ugreen_topsales` |
| 日期分支 | `daily/YYYYMMDD-ugreen-topsales` |
| 正式结果 | 该日期目录下 `result/ugreen_topsales.xlsx` |
| 规范工作簿 | 主根与日期快照中的 `skills/shopee-ugreen-topsales/assets/ugreen_topsales.xlsx`，均只读且哈希一致 |
| 执行源码 | 发布时必须调用目标日期目录内的 `skills/shopee-ugreen-topsales/scripts/run_scrape.py` |
| Python | 使用 `--prepare` 回执中的 `python`，当前实现为主根 `.venv/bin/python` |

不生成 `run-001` 等序号，不把输出写回主根 `result/`，不使用当前工作目录猜结果路径。
跨午夜继续原日期身份；新的任务才重新绑定上海日期。仅只读历史验收可明确选择旧日期。

## 2. 固定目录树

```text
shopees_ugreen_topsales_scraper/
├── AGENTS.md
├── README.md
├── pyproject.toml
├── skills/shopee-ugreen-topsales/         # 自包含的唯一规范与执行资源
│   ├── SKILL.md                         # 规范索引及入口
│   ├── agents/openai.yaml
│   ├── assets/
│   │   ├── run_prompt_template.md       # 通用任务书，不写入本次参数
│   │   └── ugreen_topsales.xlsx          # 只读内容规范，非运行结果
│   ├── references/
│   │   ├── excel-output.md              # 四表内容合同
│   │   ├── worktree.md                  # 本文件：目录与生命周期
│   │   ├── capture-protocol.md          # 现场内存数据协议
│   │   ├── extraction_contract.md       # 兼容路由，无第二份规范
│   │   └── verified_access.md           # 历史证据，不是执行指令
│   └── scripts/                         # 确定性准备、交接、导出、校验等
└── worktrees/
    └── YYYYMMDD_ugreen_topsales/          # Git 注册的日期快照，不是普通拷贝
        ├── .git                         # linked worktree 的 Git 文件
        ├── AGENTS.md / README.md / pyproject.toml
        ├── skills/shopee-ugreen-topsales/ # 同提交的完整 Skill；assets/references 只读
        ├── …                            # 其余已跟踪源文件按 Git 快照保留
        └── result/
            └── ugreen_topsales.xlsx      # 唯一正式交付文件，Git ignored
```

日期快照完整保留已跟踪源码；上图不是允许删除其他源码的白名单。运行产物则严格只有
上述 Excel。不生成任务书副本、原始 HTML/JSON、截图、响应、trace、manifest、部分表、
会话资料或 token 文件。本次任务参数绑定在宿主上下文，不改写快照中的任务书。

## 3. 准备门禁

1. 正常全量请求允许通过 `run_scrape.py --prepare` 创建或安全复用上海本日目录。
   只读计划/规范检查和抽测不创建 worktree。`--date YYYY-MM-DD` 仅用于 `--prepare`，
   且仍必须为上海本日，不能用它补造过去或未来任务。
2. 主根已跟踪与未跟踪改动均须为空，Python 环境与入口已存在。缺环境只报告具体缺口，
   不临时改机器、猜依赖或用旧日期源码顶替。
3. 已注册日期目录必须属于本仓库、分支正确、Git clean、与主根同一已提交 HEAD。
   新目录从此 HEAD 建立；已有同名分支只能安全复用同 HEAD，不能强制移动分支。
4. 拒绝符号链接、越界路径、未注册的同名目录、异仓库、不同 HEAD 或未知结果文件。
   失败时报告实际冲突，不自行 `commit/stash/reset/clean`、删除目录或分支。
5. 准备回执中的 `date/project_root/worktree/branch/python/runner/output/source_head`
   作为参数绑定依据；与计划不一致则先停止核对，不能混用两轮参数。

## 4. 并发与发布

宿主仅运行一个全量任务，列表和详情均串行，页/商品访问间至少 10 秒。确定性脚本分别
用 `.git/ugreen_daily.lock` 保护准备、`.git/ugreen_daily_run.lock` 保护发布；这些是控制锁，
不是结果或业务数据。当前锁并不覆盖宿主浏览器取数全过程，因此不能宣称已实现跨宿主
全生命周期互斥；发现另一采集任务时停止，不并发争用同一原 Chrome 会话。

发布要求主根/日期目录仍 clean、同 HEAD、规范已跟踪且 SHA-256 相同，并在发布前再次
复核。发布模块只在目标 `result/` 创建自身唯一临时候选 `.xlsx`，完整重开校验后原子
替换正式文件；退出时清理该候选。发布期间的受控临时文件不是额外交付物。

- 同日完整重跑可以在全部验收后替换同日结果；不修改其他日期，也不改规范工作簿。
- 发布前失败保留已有正式文件；不能把它当作失败本轮的新结果交付。
- `result/` 有未知文件时拒绝；不自动清除或扩大忽略列表。
- 不在日期快照热修补代码或规范。修复在主根完成，经用户审阅/提交后才进入新快照；
  同日快照与新 HEAD 不一致时需报告，不暗中同步或重建。
- Git 提交、推送、拉取、清理、删除日期或分支均非正常采集的隐含步骤，须另有明确请求。

## 5. 完成与中断

正式结果在 ignored `result/`，结束时日期源码保持 Git clean。用明确的根和日期参数
独立验收，不回退主根、规范表或另一日期。回执走 stdout，不另写 JSON 文件。

挑战页或必要人工输入时保留原页面；用户处理后重读身份和字段再继续。同一宿主仍保有
本轮内存时，可接着未完成的页/商品；内存丢失或无法证明数据属于本轮时重新现场采集，
不借旧 Excel、日志或历史访问记录“恢复”。不得承诺不存在的持久化断点或 resume 服务。
