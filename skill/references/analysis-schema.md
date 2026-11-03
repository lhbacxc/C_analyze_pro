# analysis.json 字段说明

`analyze.py` 产出的是**基线**：它按规则表实测路径体积、套模板文案生成三灯。
agent 拿到 JSON 后应当复核并手工增删卡片（尤其「神秘大目录」的归属、行业/业务判断、
措辞），改完直接喂给 `server.py` / `build_report.py`，不需要重新扫描。

## 顶层

```json
{
  "generated_at": "2026-10-20 20:52",
  "system": {"disk_name": "C:", "hostname": "PC", "user": "lhbac"},
  "disk": {"total": 322138271744, "used": 258191130624, "free": 63947141120},
  "summary": {...},
  "top5": [...],
  "tiers": {"green": [...], "yellow": [...], "red": [...]}
}
```

`disk` 三个值单位为字节，直接来自 `GetDiskFreeSpaceEx`，用来画总览卡片与分段进度条。

## summary

| 字段 | 说明 |
|---|---|
| `overview` | 一句话洞察，渲染在「执行建议」开头。写「最大占用是什么 + 能释放多少」，**不要**重复总/已用/可用数字（卡片大数字里已有）。 |
| `priority` | 有序清单，可含 `<b>` 内联标签，渲染成带序号的建议列表。 |
| `tier_stats` | `{"green": "约 26.9 GB", "yellow": "约 42.2 GB", "red": "约 3.8 GB"}`。**必须以 GB 数字开头**，模板从中解析后画进度条分段；蓝色段与「系统及其他」pill 由模板用「已用 − 绿 − 橙 − 红」自动算余量。 |
| `long_term` | 字符串数组，渲染成两栏长期建议。 |

## tiers.green（🟢 可自动清理）

| 字段 | 必填 | 说明 |
|---|---|---|
| `title` / `size` / `path` | ✓ | `size` 写成「约 11.3 GB」，不要再加「（估算）」。 |
| `type` | | 卡片小标签：开发缓存 / 应用缓存 / 临时文件 / 安装包残留。 |
| `desc` | | 这里面是什么、为什么可以删。 |
| `close` | | 清理前需要关闭的进程。 |
| `risk` | | 删了会有什么代价（重新下载、离线失效等）。 |
| `commands` | | `[{"label": "...", "cmd": "..."}]`，一键复制。官方清理命令优先（`uv cache clean`），否则由引擎生成 `Remove-Item`。 |
| `trash_paths` | ✓ | 可直接删除的绝对路径数组。**漏了就没有网页按钮**。 |
| `openable` | | 默认 true；路径在用户目录之外时置 false（服务端只允许 $HOME 内的路径）。 |

## tiers.yellow（🟡 需人工判断）

除 `title/size/path/desc/risk` 外：

| 字段 | 说明 |
|---|---|
| `steps` | 至少 3 条可照做的处置路径（应用内清理 / 系统工具 / 手动审查）。 |
| `open_path` | 「在资源管理器打开」的目标；缺省用 `path`。 |
| `open_note` | 客观说明「为什么这不方便手动挑」（如回收站内部命名）。 |
| `trash_paths` | **仅当**存在核实过、删了不破坏应用的安全子路径时才给（如 AVD 的 `snapshots`）。橙灯只允许移回收站。 |
| `commands` | 可选，如清空回收站的 `Clear-RecycleBin`。 |

App 托管又没有安全子路径的（微信、浏览器站点数据）只给打开按钮，不给 `trash_paths`。

## tiers.red（🔴 谨慎清理）

| 字段 | 说明 |
|---|---|
| `risk` | 为什么不能手删——要具体（「Office 无法修复/卸载」比「有风险」有用）。 |
| `indirect_release` | 正规释放步骤：自带卸载器、官方清理工具、迁移方案。要可照做。 |
| `app_paths` | 真实应用/目录绝对路径数组 → 渲染「在资源管理器打开（去卸载）」。 |
| `open_label` / `open_hint` | 可选，覆盖按钮文案与说明。 |
| `openable` | 路径在 $HOME 外（`C:\Windows\...`）置 false，不给按钮。 |

红灯**永远不给删除/卸载按钮**：后台代删应用不稳妥。

## 安全约束（服务端会强制校验）

1. `trash` 接口：只接受绿灯 + 黄灯 `trash_paths`；`rm` 接口：只接受绿灯 `trash_paths`；
   `open` 接口：接受前三者 + 黄灯 `path` + 红灯 `app_paths`。
2. 所有路径 `realpath` 后必须位于 `$HOME` 内，否则 403。
3. 每个请求校验 `X-Token` 与 `Host`，浏览器端每次点击先 `confirm`。

因此：`C:\Windows\Installer`、`C:\ProgramData\...` 这类系统路径即使写进
`trash_paths` 也不会生效——正确做法是 `openable: false` + 命令靠用户自己以管理员身份执行。

## 手工微调示例

```python
import json
a = json.load(open("analysis.json", encoding="utf-8"))
a["tiers"]["yellow"].insert(0, {
    "title": "B 站离线视频", "size": "约 42 GB",
    "path": r"C:\Users\me\AppData\Local\bilibili\Downloads",
    "type": "离线内容", "desc": "客户端缓存的离线视频，按 UP 主分目录。",
    "risk": "删掉后需要重新下载才能离线观看。",
    "steps": ["客户端里「我的 → 离线缓存」按 UP 主删除。", "或在资源管理器打开 Downloads 目录手动挑。", "只想腾空间不想删：把 Downloads 目录剪切到数据盘。"],
    "open_path": r"C:\Users\me\AppData\Local\bilibili\Downloads",
    "trash_paths": [r"C:\Users\me\AppData\Local\bilibili\Downloads"],
})
json.dump(a, open("analysis.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
```

改完重启 `server.py` 生效（白名单在启动时构建）。
