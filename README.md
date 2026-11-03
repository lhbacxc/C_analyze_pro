# C_analyze_pro

对 `storage-analyzer`（C 盘 / 整机只读存储分析 skill）的**补全与优化**版本。

原版技能只下发了 `SKILL.md`，其中引用的 `scripts/`（扫描、报告、服务端）与
`references/` 全部缺失，实际无法运行。本仓库补上了整套实现，并按真实机器跑通验证。

## 能力

一条链路解决问题：**只读扫描 → 规则分级 → 交互式 HTML 报告 → 网页一键清理**。

- 只读扫描全盘，找出占空间大户；跳过 junction / 符号链接，避免重复计数
- 每个目录按 🟢 可自动清理 / 🟡 需人工判断 / 🔴 谨慎清理 三级给出处置方案
- 报告：磁盘分段进度条、Top 6 排行、优先级清单、可折叠卡片、命令一键复制
- 服务模式可在网页上「移到回收站 / 直接删除 / 在资源管理器定位」，带三套白名单 +
  token + `$HOME` 路径校验；静态模式输出可分享的单文件 HTML（无按钮）

## 目录结构

```
skill/
├── SKILL.md                    技能入口（流程、铁律、安全模型、坑位）
├── scripts/
│   ├── scan.py                 只读扫描 → scan.json
│   ├── probe.py                下钻探查 / 大文件清单
│   ├── analyze.py              规则引擎：scan.json → analysis.json
│   ├── rules_win.py            Windows 绿灯规则表
│   ├── rules_extra.py          黄灯 / 红灯规则、长期建议、macOS 规则
│   ├── ui.py + theme.py        HTML 报告渲染（深色主题）
│   ├── server.py               服务模式（127.0.0.1 + token + 白名单）
│   └── build_report.py         静态报告
└── references/
    ├── windows.md              Windows 数据布局、统计陷阱、神秘目录线索
    ├── analysis-schema.md      analysis.json 全字段说明
    └── macos.md                macOS 布局（未真机实测）

examples/
├── scan.sample.json             扫描产物样例
├── analysis.sample.json         分级产物样例
└── report.sample.html           静态报告样例（浏览器直接打开）
```

## 快速开始

依赖：Python 3（标准库即可，**无需 pip install**）。

```bash
python skill/scripts/scan.py scan.json          # 1. 扫描（C 盘约 1 分钟）
python skill/scripts/probe.py "C:\Users\me\AppData\Local\某目录"   # 2. 按需下钻
python skill/scripts/analyze.py scan.json analysis.json           # 3. 自动分级
python skill/scripts/server.py analysis.json                     # 4. 起服务看报告
```

服务模式会自动打开浏览器并打印地址（同时写入 `analysis.json` 同级的 `server_url.txt`，
方便在后台任务里取端口）。只需一份可分享的报告时：

```bash
python skill/scripts/build_report.py analysis.json report.html
```

> Windows 上命令里的 `python` 按本机实际解释器替换；macOS 用 `python3`。

## 引擎做了什么

`analyze.py` 是可选的一层自动化，不是判断的替代品：

1. 按规则表实测路径体积，套用文案模板生成三灯（`rules_win.py` / `rules_extra.py`）
2. 未命中任何规则的大目录 → 自动归「需人工判断」，并提示先下钻确认归属
3. 同一软件出现多个版本目录（如 `AndroidStudio2025.1.2` vs `2026.1.3`）→ 自动归红灯
4. 计算 Top 6 与进度条分段比例

生成后 **agent 必须复核**：改写文案为本机实际情况、确认 `trash_paths` 只包含核实过的
安全路径、把神秘大目录补进正确灯级。字段规范见 `references/analysis-schema.md`。

## 安全模型

| 接口 | 允许的路径 |
|---|---|
| `/api/rm` 直接删除 | 仅绿灯 `trash_paths` |
| `/api/trash` 移回收站 | 绿灯 + 黄灯 `trash_paths`（橙灯永不直删） |
| `/api/open` 定位 | 上述全部 + 黄灯 `path` + 红灯 `app_paths` |

外加：`realpath` 校验、必须位于 `$HOME` 内、`X-Token` 校验、`Host` 校验、
浏览器每次点击先 `confirm`。Windows 入回收站走 `SHFileOperationW + FOF_ALLOWUNDO`。
系统路径（`C:\Windows\...` 等）即使写进白名单也不会生效，只能用 `openable: false`
+ 命令让用户以管理员身份自行执行。

## 已验证

Windows 10/11 实测（2026-10）：

- 扫描 C 盘 300 GB / 200 万+ 文件约 40–60 秒
- 分级：绿灯 10 项 / 黄灯 17 项 / 红灯 2 项，共 29 张卡
- 服务模式页面 200，移回收站 11 个按钮、直删 10 个、定位 27 个
- 无 token 请求被拒，伪造 `Host` 返回 403
- 静态报告 47 KB，`rm` / `trash` 按钮数为 0

修复过的真实缺陷见 [CHANGELOG.md](./CHANGELOG.md)。

## 平台状态

- **Windows**：完整实测（扫描 / 分级 / 服务模式 / 移回收站 / 白名单拦截）
- **macOS**：`du` 扫描分支与规则表已实现，**未在真机实测**；首次运行需核对
  `~/Library/Containers` 归属判断与访达自动化授权

## 许可

仅供个人使用与学习。原版 skill 版权归原作者。
