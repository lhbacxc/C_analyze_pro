# macOS 数据布局与判读参考

> 状态：扫描用的 `du -sk` 分支与规则表已实现，但**未在真机实测**（本机为 Windows）。
> 首次在 Mac 上跑完请核对：`~/Library/Containers` 的 UUID 归属、`du` 耗时、
> 「移到废纸篓」是否触发访达自动化授权提示。

## 1. 体积都藏在哪

| 位置 | 典型内容 | 默认归属 |
|---|---|---|
| `~/Library/Caches` | 应用缓存（Chrome、Slack、npm 等） | 多数绿灯 |
| `~/Library/Containers` | 沙盒应用数据，**UUID 命名** | 需逐个追查归属 |
| `~/Library/Group Containers` | 同一开发者的多 App 共享数据（如微信/QQ） | 黄灯 |
| `~/Library/Application Support` | 应用配置与真实数据 | 黄灯 |
| `~/Library/Developer/Xcode/DerivedData` | 构建中间产物 | 绿灯 |
| `~/Library/Developer/CoreSimulator/Devices` | 模拟器镜像 | 黄灯，`xcrun simctl delete unavailable` |
| `~/Library/Developer/Xcode/iOS DeviceSupport` | 各版本调试符号 | 绿灯，旧版本可删 |
| `/Applications` | 应用本体 | 红灯（走启动台/AppCleaner 卸载） |
| `~/.Trash` | 废纸篓 | 黄灯 |
| `/private/var/vm` | swapfile | 蓝灯，重启可释放 |

## 2. 陷阱

1. **UUID 容器**：`~/Library/Containers/<UUID>` 无法从名字判断归属。用
   `probe.py <该目录>` 看内部文件名（例如出现 `*.mp4` + `bangumi` → B 站离线缓存）；
   或 `mdls -name kMDItemFSName` 之类元数据线索。仍是只读。
2. **APFS 本地快照**：`tmutil listlocalsnapshots /` 能看到，会算进「已用」但
   属于「可清除空间」，系统在需要时自动回收——不要当垃圾报给用户。
3. **符号链接与 firmlinks**：`/System/Volumes/Data` 与 `/` 是同一个卷的两面，
   不要重复相加。
4. `du` 遇到权限拒绝会少算，报告里要标注「这部分未计入」。

## 3. 判断口径

与 Windows 一致：能自动重建的进绿灯；含用户内容或需要挑拣的进黄灯；
你可能想动但不建议手删的进红灯；纯系统文件归蓝灯并把技巧写进 `long_term`
（重启释 swap、Time Machine 快照策略、系统设置里的「优化储存空间」）。

## 4. macOS 特有执行注意

- 移入废纸篓用 `osascript` 或 `SHFileOperationW` 的等价实现；首次会弹
  「终端/某 App 想要控制访达」授权，点允许即可。
- 静态报告用 `build_report.py`；想要网页一键删除必须用 `server.py`，
  因为 `file://` 页面碰不到文件系统。
- 命令里路径含空格要加引号；`brew cleanup -s --prune=all` 比手删更安全。
