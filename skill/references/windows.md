# Windows 数据布局与判读参考

## 1. 体积都藏在哪

| 位置 | 典型内容 | 默认归属 |
|---|---|---|
| `C:\Users\<user>\AppData\Local` | 应用数据 + 缓存（uv/npm/pip、浏览器、IDE、剪映） | 逐项判断，多数是绿灯 |
| `C:\Users\<user>\AppData\Roaming` | 应用配置与部分数据（微信、编辑器、全局 npm） | 多为黄灯 |
| `C:\Users\<user>\AppData\LocalLow` | 低完整性应用（IE 遗留、部分国产软件） | 一般不出现大项 |
| `C:\Windows\WinSxS` | 组件存储，硬链接计数偏大 | 蓝灯；只走 DISM 清理 |
| `C:\Windows\Installer` | MSI/MSP 补丁缓存 | 🔴 绝不手删 |
| `C:\Windows\System32` / `SysWOW64` | 系统二进制 | 蓝灯 |
| `C:\pagefile.sys` | 虚拟内存 | 蓝灯；建议迁移或设固定值 |
| `C:\hiberfil.sys` | 休眠 + 快速启动 | 蓝灯；`powercfg /h off` 可整块回收 |
| `C:\$Recycle.Bin` | 回收站（按 SID 分子目录） | 🟡 需用户确认 |
| `C:\ProgramData` | 程序共享数据（NVIDIA 驱动包、Adobe、安装缓存） | 多为黄灯 |
| `C:\Program Files*` | 已安装程序本体 | 🔴（要卸载就别手删） |
| `C:\Recovery`、`C:\$SysReset` | 恢复分区与重置残留 | 蓝灯 |

## 2. 必须避开的三个统计陷阱

1. **junction 重复计数**：`C:\Users\<user>\Local Settings` 与 `Application Data` 是
   指向 `AppData\Local` / `AppData\Roaming` 的 junction。若跟进会凭空多出几十 GB。
   `scan.py` 已按 `FILE_ATTRIBUTE_REPARSE_POINT` 跳过，`kind` 标记为 `reparse`；
   自行写脚本时必须同样处理。
2. **权限拒绝**：`C:\Windows\Temp`、部分 `ProgramData` 子目录、个别回收站条目
   在非管理员下读不到。`dir_size` 返回 `denied` 计数，报告里要说明「这部分未计入」，
   不要假装总和等于已用量。
3. **硬链接**：`WinSxS` 与 `System32` 之间存在硬链接，两者相加会大于实际占用。
   只作参考，不要拿它们算「可释放空间」。

## 3. 常见「神秘大目录」的归属线索

| 路径特征 | 通常是什么 | 处置 |
|---|---|---|
| `AppData\Local\uv\cache\archive-v0` | uv 的 wheel/sdist 归档 | 绿灯，`uv cache clean` |
| `AppData\Local\npm-cache\_cacache` | npm 包归档 | 绿灯，`npm cache clean --force` |
| `AppData\Local\Google\Chrome\User Data\OptGuideOnDeviceModel` | Chrome 端侧 AI 模型 | 绿灯，自动重下 |
| `AppData\Local\Microsoft\Edge\User Data\Default\Service Worker` | 站点离线数据 | 绿灯，最多重新同步 |
| `...\Default\IndexedDB`、`Extensions` | 站点数据库、扩展本体 | 🟡 走浏览器内清理 |
| `AppData\Local\com.github.<作者>\<应用>` | 第三方桌面应用的导入文件 | 🟡 应用内删除或迁移 |
| `AppData\Local\JianyingPro\Apps` | 剪映多版本程序本体 | 🔴 别手删 |
| `.android\avd\<设备>.avd\userdata-qemu.img.qcow2` | 模拟器数据盘 | 🟡 可删快照、Wipe Data |
| `AppData\Local\NVIDIA\DXCache` | 着色器缓存 | 绿灯 |
| `ProgramData\NVIDIA Corporation\NVIDIA app\UpdateFramework` | 驱动更新包 | 🟡 需管理员 |
| `AppData\Roaming\<编辑器>\CachedExtensionVSIXs` | 扩展安装包副本 | 绿灯 |

## 4. 判断口径

- **绿灯只放「删掉会自动重建」的东西**：缓存、临时文件、安装包残留。判断句：
  「删了之后应用会不会自己再生成？」会 → 绿灯。
- **黄灯是有决策成本的**：含用户内容（聊天记录、草稿、导入素材、截图）或需要挑拣。
  能给「核实过的安全子路径」（如 AVD 的 `snapshots`）就给 `trash_paths`，只准移回收站。
- **红灯是「你可能想动但不建议手删」**：`Windows\Installer`、程序本体、旧版本配置。
  给正规卸载/清理路径，绝不给删除按钮。
- **纯系统文件不进红灯**：`WinSxS`、`pagefile.sys`、`hiberfil.sys`、`System32`
  没有「要不要删」的决策，归蓝色「系统及其他」，技巧写进 `summary.long_term`。
- 体积 ≤ 0.1 GB 且无可操作性的项直接不列，避免报告变成流水账。

## 5. Windows 特有的执行注意

- 报告里给的命令是 PowerShell；复制到终端时若路径含空格要保留引号。
- `Clear-RecycleBin -DriveLetter C -Force` 只清 C 盘，比「清空回收站」更精确。
- `powercfg /h off` 会同时关掉快速启动与休眠，回收的体积约等于物理内存。
- 迁移大文件优先迁到非系统盘（`scan.py` 的 `system.disks` 里能看到各盘剩余量）。
- 中文卷标/路径：扫描与报告全程 UTF-8，不要用 PowerShell 的 `>` 重定向去中转 JSON。
