---
name: storage-analyzer
author: Lhbacxc
description: >
  macOS / Windows 只读存储分析助手（自动识别系统）。扫描整机磁盘占用，找出
  占空间大户，把每一项分成 🟢可自动清理 / 🟡需人工判断 / 🔴谨慎清理 三级并给出
  可执行处置方案，生成排版精美、可折叠、命令可一键复制的交互式 HTML 报告，并可
  起本地服务在网页上一键删除（移废纸篓/直接删）。扫描全程只读。务必在以下场景
  使用：用户说"存储分析""磁盘满了""C盘/硬盘满了""空间不够""清理空间"
  "清理磁盘""占空间""哪些东西占地方""帮我看看存储""看一下电脑存储/空间"
  "存储空间""电脑空间不够""内存满了/不够/不足""看下内存/存储"（中文口语里
  "内存"常指存储空间）"storage analysis""disk cleanup""清缓存""磁盘清理"；
  或用户抱怨电脑没空间、想知道什么东西吃硬盘、想要清理建议时。注意：若用户明确
  指运行内存/RAM（如"哪个进程吃内存""内存占用高"想看活动监视器），那是 RAM
  不是存储，不属于本 skill。
---

# Storage Analyzer

只读扫描 → 规则引擎分级 → 生成交互式 HTML 报告（可网页一键移回收站/删除）。

## 铁律

- **全程只读。** 扫描只跑统计、列目录、读元信息。禁止 rm / mv / del / 清空回收站 / 改权限。
- **删除只由用户点击触发。** 报告里的命令供用户自己复制执行；即使用户在对话里说
  「帮我删」，也先停下确认，不要代跑。
- **估算要说清楚。** 「可释放空间」一律标注为估算；权限拒绝读不到的目录要在报告里
  说明「这部分未计入」，不要让总和假装等于已用量。
- **路径与命令保留原文**，不翻译、不改写、不美化。

## 依赖

全部脚本为 **Python 3 标准库**，零第三方依赖，不要 pip install。

| 平台 | 解释器 | 说明 |
|---|---|---|
| Windows | `python` 或 `py -3`（命令示例里的 `python3` 换成它） | 本机若无 PATH 可用已知绝对路径，如 `D:\Software\Miniconda\python.exe` |
| macOS | `python3` | 自带 |

Windows 编码：脚本内部已 `reconfigure(encoding="utf-8")` 直写 UTF-8 JSON。
**不要**用 PowerShell 的 `>` / `Out-File` 中转扫描 JSON（会写坏中文卷标并混入 BOM）。

## 执行流程

### Step 1 扫描（只读，C 盘约 2-4 分钟）

```bash
python scripts/scan.py scan.json            # 可用 --min-mb 200 提高过滤阈值
```

产物 `scan.json`：`system`（os/hostname/home/disk_name/disks/main_disk）+
`groups`（user_profile、appdata_local、appdata_roaming、temp、downloads、
program_files、programdata、c_root、dev_caches）。子项已降序、过滤小于 50MB 的项，
权限拒绝的目录带 `denied` 计数，junction 标 `kind: "reparse"`（体积记 0，不跟进）。

### Step 2 下钻（按需，只读）

遇到体积大但看不出归属的目录，先探一层再看：

```bash
python scripts/probe.py "C:\Users\me\AppData\Local\某目录"
python scripts/probe.py FILES:"C:\Users\me"      # 列出 >1.5GB 的大文件
```

判读线索查 `references/windows.md`（或 `references/macos.md`）。

### Step 3 规则引擎生成分级

```bash
python scripts/analyze.py scan.json analysis.json
```

引擎做四件事：按 `scripts/rules_win.py` / `rules_extra.py` 实测路径体积并套模板文案；
未命中任何规则的大目录自动生成「需人工判断」卡；同一软件多版本目录自动识别为红灯；
计算 Top6 与 `tier_stats`。

**这一步只是基线，agent 必须复核**（本 skill 的价值在判断，不在脚本）：

1. 读一遍 `tiers`，把 `desc` / `steps` / `risk` 改成本机实际情况，不要留模板空话。
2. 处理引擎认不出的「神秘大目录」：按 Step 2 下钻确认归属，补进对应灯级。
3. 检查 `trash_paths`：只放**核实过**、删了不影响功能与个人数据的绝对路径。
4. 确认 `summary.overview` 是一句洞察（最大占用 + 能释放多少），不是数字复读。
5. 字段含义与写法约束见 `references/analysis-schema.md`。

### Step 4 生成报告并打开

默认用服务模式（有删除/移回收站按钮）：

```bash
python scripts/server.py analysis.json      # 自动开浏览器，Ctrl+C 停
```

- 绑 `127.0.0.1` + 随机端口 + 随机 token；同时把 URL 写入 `server_url.txt`。
- 只有需要「可分享/留存的只读文件」时才用静态模式：
  `python scripts/build_report.py analysis.json report.html`（无按钮，因为 `file://`
  页面碰不到文件系统）。

### Step 5 对话里给摘要

结论先行，一段话讲完：总可释放估算 → 最该先清的 2-3 项 → 风险最高的一项 →
一句提醒（读不到的系统目录未计入 / 体积为扫描时刻估算）。细节留给网页。

## 报告结构（固定阅读流）

磁盘总览卡片（容量 + 三色分段进度条 + pills + 系统信息）→ 占用排行 Top6 →
执行建议（overview + 优先级清单）→ 🟢🟡🔴 三级可折叠卡片（命令一键复制）→
长期优化建议。即：现状 → 诊断 → 处方 → 操作 → 预防。

进度条把「已用」拆成 绿 + 橙 + 红（`tier_stats` 解析）+ 蓝（模板算余量 =
已用 − 绿 − 橙 − 红），剩余为可用。所以 `tier_stats` 三个值必须以 GB 数字开头。

## 安全模型（server.py 强制）

三套白名单，权限从严到宽：

| 接口 | 允许的路径 |
|---|---|
| `POST /api/rm`（直接删除） | 仅绿灯 `trash_paths` |
| `POST /api/trash`（移回收站） | 绿灯 + 黄灯 `trash_paths`（橙灯永远不能直删） |
| `POST /api/open`（资源管理器定位） | 上述全部 + 黄灯 `path` + 红灯 `app_paths` |

额外约束：`realpath` 校验 + 必须在 `$HOME` 内 + `X-Token` + `Host` 校验，
浏览器每次点击先 `confirm`。Windows 入回收站走 `SHFileOperationW + FOF_ALLOWUNDO`。
所以 `C:\Windows\...`、`C:\ProgramData\...` 这类系统路径写进 `trash_paths` 也不会生效，
正确做法是 `openable: false` + 给命令让用户用管理员身份自己执行。

## 扩展规则表

`scripts/rules_win.py`（绿灯，字段：`patterns` / `min_gb` / `desc` / `close` / `risk` /
`cmd` / `hide`）、`scripts/rules_extra.py`（黄灯 `match`+`steps`、红灯 `match`+
`indirect_release`、长期建议、macOS 规则）。

- 加绿灯：给 `patterns`（支持环境变量与 `*`），`cmd` 留空则引擎自动生成
  `Remove-Item` 命令（基于实测路径，保证和卡片一致）。
- 加黄灯：给 `match` 与至少 3 条 `steps`；确有待核实的安全子路径才加 `trash_globs`；
  `split: true` 表示每个匹配项单独出一张卡。
- 加红灯：给 `indirect_release`（正规卸载/清理步骤），不给删除按钮。

## 常见坑

- **网页上没按钮**：① 开的是静态报告（改用 `server.py`）；② 绿灯项漏了 `trash_paths`；
  ③ 路径在 `$HOME` 之外被白名单拒掉。改完 `analysis.json` 要**重启服务**（白名单启动时构建）。
- **Bash 后台拿不到 stdout**：所以 `server.py` 把 URL 写进 `server_url.txt`，从文件读端口。
- **体积会和 `scan.json` 不一致**：`analyze.py` 是实时测量，用户中途清过东西时数字会变小，
  这是对的，不要当 bug 去「修正」。
- **PowerShell 里 `$Recycle.Bin`**：路径带 `$`，Bash 下要用**单引号**，否则变量被吞成 `C:Recycle.Bin`。
- **junction**：`Local Settings` / `Application Data` 会让统计翻倍，新写扫描逻辑必须跳过 reparse point。

## 平台状态

- **Windows**：完整实测（扫描 / 分级 / 服务模式 / 移回收站 / 白名单拦截均验证过）。
- **macOS**：`du` 扫描分支与规则表已实现，**未在真机实测**；首次运行需核对
  `~/Library/Containers` 归属判断、`du` 耗时与访达自动化授权。
