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
| 累计进度 | 同目录 `result/ugreen_topsales_progress.xlsx`；每 50 件及停止尾批保存 |
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
│   │   ├── cua-fallback.md              # Playwright 不可用时的原 Chrome 只读备用路线
│   │   ├── extraction_contract.md       # 兼容路由，无第二份规范
│   │   └── verified_access.md           # 历史证据，不是执行指令
│   └── scripts/                         # 确定性准备、交接、导出、校验等
└── worktrees/
    └── YYYYMMDD_ugreen_topsales/          # Git 注册的日期快照，不是普通拷贝
        ├── .git                         # linked worktree 的 Git 文件
        ├── AGENTS.md / README.md / pyproject.toml
        ├── skills/shopee-ugreen-topsales/ # 准备时自动更新的完整 Skill；采集中规范只读
        ├── …                            # 其余已跟踪源文件按 Git 快照保留
        └── result/
            ├── ugreen_topsales.xlsx      # 唯一全量正式交付文件，Git ignored
            └── ugreen_topsales_progress.xlsx # 累计进度，不冒充全量通过
```

日期快照完整保留已跟踪源码；上图不是允许删除其他源码的白名单。运行产物则严格只有
上述正式/累计进度 Excel。不生成任务书副本、原始 HTML/JSON、截图、响应、trace、manifest、
会话资料或 token 文件。本次任务参数绑定在宿主上下文，不改写快照中的任务书。

## 3. 自动准备与提交

1. 正常全量请求允许通过 `run_scrape.py --prepare` 自动提交现有改动、创建或更新上海本日目录。
   只读计划/规范检查和抽测不创建 worktree。`--date YYYY-MM-DD` 仅用于 `--prepare`，
   且仍必须为上海本日，不能用它补造过去或未来任务。
2. 主根有改动时自动 `git add -A -- .` 后提交，包括未忽略的新增文件；无改动不生成空提交。
   Python 环境与入口须已存在。缺环境只报告具体缺口，
   不临时改机器、猜依赖或用旧日期源码顶替。
3. 已注册日期目录属于本仓库、分支正确后，自动提交其中现有改动，再以
   `git merge --no-edit <source_head>` 快进或合并主项目版本；已有同名分支也按此更新。
   新分支从主项目 HEAD 建立。自动提交和本日更新已获授权，不重复确认。
   不要求合并后的 HEAD 等于主项目，独立的日期提交保留。
4. 路径注册、日期归属和未知结果文件检查照常；不以脏状态或 HEAD 不同作为门禁。
   实际提交/合并失败或冲突时报告并保留现场，不 `stash/reset/clean` 或删除目录/分支。
5. 准备回执中的 `date/project_root/worktree/branch/python/runner/output/source_head`
   作为参数绑定依据；与计划不一致则先停止核对，不能混用两轮参数。

## 4. 并发与发布

宿主仅运行一个全量任务，列表和详情均串行；每次页/商品导航前独立随机等待 0.8～1.2 秒，
每完成 50 件额外随机冷却 72～120 秒；所有人为等待统一提速 2.5 倍，详见主 Skill 第 4.5 项。
页面自身加载耗时可额外增加实际间隔。确定性脚本分别
用 `.git/ugreen_daily.lock` 保护准备、`.git/ugreen_daily_run.lock` 保护发布；这些是控制锁，
不是结果或业务数据。当前锁并不覆盖宿主浏览器取数全过程，因此不能宣称已实现跨宿主
全生命周期互斥；发现另一采集任务时停止，不并发争用同一原 Chrome 会话。

发布不检查 Git 脏状态、规范是否已提交或 HEAD 是否相同；仍检查只读规范 SHA-256 相同，
并在发布前再次复核。发布模块只在目标 `result/` 创建自身唯一临时候选 `.xlsx`，完整重开校验后原子
替换正式文件；退出时清理该候选。发布期间的受控临时文件不是额外交付物。

- 同日完整重跑可以在全部验收后替换同日结果；不修改其他日期，也不改规范工作簿。
- 发布前失败保留已有正式文件；不能把它当作失败本轮的新结果交付。
- `result/` 有未知文件时拒绝；不自动清除或扩大忽略列表。
- `ugreen_topsales_progress.xlsx` 是明确允许的累计进度文件，不当作未知文件或正式结果。
  进度保存由主根新入口执行，只核对注册归属、启动日、路径和字段，允许主根维护脏状态时
  先保全已采集数据；保存和发布不因 Git 改动暂停，也不在运行中同步日期源码。
- 修复在主根完成；开始采集前通过准备流程自动提交并更新本日工作区，采集中保持当前
  已加载源码，避免更换正在运行的代码。
- 自动提交及本日工作区更新属于正常任务步骤；不推送、拉取、清理、删除日期或分支。

## 5. 完成与中断

正式结果在 ignored `result/`，不纳入自动提交。用明确的根和日期参数
独立验收，不回退主根、规范表或另一日期。回执走 stdout，不另写 JSON 文件。

只有现场验证码/人工验证才立即断开并保留原页面，再保存已有数据及不足 50 件尾批；
用户明确回复继续后才重新附着、重读身份和字段。同一宿主仍保有
本轮内存时，可接着未完成的页/商品；内存丢失或无法证明数据属于本轮时重新现场采集，
不借旧 Excel、日志或历史访问记录“恢复”。普通超时或加载错误按 Skill 第 4 节自动恢复，
不要求用户回复继续。不得承诺不存在的持久化断点或 resume 服务。
