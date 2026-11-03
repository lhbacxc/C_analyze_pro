# CHANGELOG

## v1.0.0 — 2026-11-03

### 背景

原版 `storage-analyzer` 技能只下发了 `SKILL.md`（约 12 KB）。其中引用但实际不存在的文件：

| 被引用 | 状态 |
|---|---|
| `scripts/scan.py` | 缺失 |
| `scripts/build_report.py` | 缺失 |
| `scripts/server.py` | 缺失 |
| `references/windows.md` | 缺失（SKILL.md 要求「Windows 读 references/windows.md」） |
| `references/macos.md` | 缺失 |

即按照原 SKILL.md 的描述**无法执行任何一步**。本次按文档描述的产出（scan.json 结构、
analysis JSON 字段、三套白名单、报告阅读流）重新实现，并在真实机器上跑通。

### 新增

- `scripts/scan.py`：`os.scandir` 递归 + 线程池并行；`system.disks` 走
  `GetDiskFreeSpaceExW`（Windows）/ `statvfs`（macOS）；输出 UTF-8 JSON
- `scripts/probe.py`：单目录下钻 + `FILES:` 大文件清单，用于判断神秘大目录归属
- `scripts/analyze.py` + `rules_win.py` + `rules_extra.py`：规则引擎（详见下）
- `scripts/ui.py` + `scripts/theme.py`：深色报告渲染（分段进度条、可折叠卡片、命令复制）
- `scripts/server.py`：`127.0.0.1` + 随机端口 + 随机 token，三套白名单接口
- `scripts/build_report.py`：静态报告（原文档提到但从未存在）
- `references/`：`windows.md`、`analysis-schema.md`、`macos.md`

### 设计取舍

- **用规则引擎替代硬编码脚本**：第一版分析是手写的、路径写死在代码里，换台机器就废。
  现改为声明式规则表（`patterns` 支持环境变量与通配，`split` 可逐项拆卡），
  体积实测后套模板；未命中规则的大目录自动归黄灯；同软件多版本目录自动归红灯。
- **保留人工复核环节**：引擎只给基线，`SKILL.md` 明确要求 agent 复核文案与
  `trash_paths`，把判断留给人（本 skill 的价值在判断，不在脚本）。
- **命令与路径同源**：`cmd` 留空时命令由实测路径自动生成，避免「报告里写的路径」
  与「命令里删的路径」不一致。

### 修复的真实缺陷

1. **磁盘容量读成剩余空间**（严重）：`GetDiskFreeSpaceExW` 的第 3、4 个参数都被传成了
   同一个 `c_ulonglong` 变量，`total` 被 `totalFree` 覆盖 → 报告显示
   「总容量 74.8 GB / 已用 0 B / 100%」。改为 `avail` / `total` / `total_free` 三个
   独立变量后恢复正常（300.0 / 225.3 / 74.7 GB）。
2. **junction 重复计数**：`C:\Users\<user>\Local Settings` 与 `Application Data` 是指向
   `AppData\Local` / `AppData\Roaming` 的 junction，被当普通目录跟进去后 AppData 虚高到
   74.2 GB（实际 70.6 GB）。现按 `FILE_ATTRIBUTE_REPARSE_POINT` 跳过。
3. **报告按钮出现在不该出现的地方**：`C:\Windows\Installer`、`ProgramData` 等
   `$HOME` 之外的路径也渲染了「在资源管理器打开」，点击必然 403。改为路径超出
   `$HOME` 时置 `openable: false`，并补 `open_label` / `open_hint` 覆盖按钮文案。
4. **长命令被「复制」按钮压住**：命令块右侧留白从 84px 调到 96px。
5. **大数值标签缺间距**：KPI 里的百分比与数值粘连（`225.3 GB75%`），补 `margin-left`。

### 验证

- 扫描：C 盘 300 GB，40–60 秒
- 分级：绿灯 10 / 黄灯 17 / 红灯 2（29 张卡），体积分别为 28.9 / 47.3 / 3.8 GB
- 静态报告 47 KB：`rm` / `trash` 调用数 0
- 服务模式：页面 200，11 个移回收站、10 个直删、27 个定位按钮；无 token → 拒绝，
  伪造 `Host` → 403

### 已知限制

- macOS 分支未真机实测（`du -sk` 扫描 + 规则表已就绪）
- `C:\Windows\Temp`、部分 `ProgramData` 子目录、个别回收站条目在非管理员下读不到，
  报告需说明「这部分未计入」
- 体积为扫描时刻估算值：硬链接、卷影副本会造成少量偏差

### 移除

- 首版手写的 `analysis.py`（写死本机路径、无法复用），由规则引擎取代
