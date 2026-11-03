# -*- coding: utf-8 -*-
"""规则引擎：scan.json -> analysis.json（三灯分级 + 命令 + trash_paths + Top5 + 摘要）。

用法:
    python analyze.py scan.json analysis.json

产物可继续手工微调（字段见 references/analysis-schema.md）：
引擎只给「基线」，神秘大目录的归属、业务判断和措辞由 agent 复核。
"""
import datetime
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from scan import dir_size  # noqa: E402
from rules_win import GREEN_WIN  # noqa: E402
from rules_extra import (GREEN_MAC, LONG_TERM_WIN, RED_WIN, YELLOW_MAC,  # noqa: E402
                         YELLOW_WIN)

GB = 1024.0 ** 3
HOME = os.path.realpath(os.path.expanduser("~"))


def gb(n):
    return "约 %.1f GB" % (n / GB) if n >= 0.1 * GB else "约 %d MB" % round(n / 1024.0 / 1024)


def expand(pat):
    p = os.path.expandvars(os.path.expanduser(pat))
    if any(c in p for c in "*?["):
        return sorted(os.path.normpath(x) for x in glob.glob(p) if os.path.exists(x))
    return [os.path.normpath(p)] if os.path.exists(p) else []


def expand_all(pats):
    out = []
    for p in pats:
        for x in expand(p):
            if x not in out:
                out.append(x)
    return out


def measure(paths):
    total = 0
    for p in paths:
        try:
            total += os.path.getsize(p) if os.path.isfile(p) else dir_size(p)[0]
        except OSError:
            pass
    return total


def inside_home(p):
    rp = os.path.realpath(p)
    return rp == HOME or rp.lower().startswith(HOME.lower() + os.sep)


def ps_rm(paths):
    return ("Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "
            + ", ".join('"%s"' % p for p in paths))


def show_path(paths, title):
    if len(paths) == 1:
        return os.path.normpath(paths[0])
    base = os.path.dirname(os.path.normpath(paths[0])) or paths[0]
    return "%s 等 %d 个位置" % (base, len(paths))


# ------------------------------------------------------------------ 绿灯
def build_green(rules):
    items, used = [], []
    for r in rules:
        paths = expand_all(r["patterns"])
        if not paths:
            continue
        size = measure(paths)
        if size < r.get("min_gb", 0.2) * GB:
            continue
        trash = [] if r.get("no_trash") else list(paths)
        cmds = [{"label": r["cmd"][0], "cmd": r["cmd"][1]}] if r.get("cmd") else \
               [{"label": "PowerShell（复制后粘贴到终端）", "cmd": ps_rm(paths)}]
        items.append({
            "title": r["title"], "size": gb(size), "path": show_path(paths, r["title"]),
            "type": r["type"], "desc": r["desc"], "close": r.get("close", ""),
            "risk": r.get("risk", ""), "commands": cmds, "trash_paths": trash,
            "openable": inside_home(paths[0]), "_bytes": size, "_paths": paths,
            "_why": ("纯缓存，删掉会自动重建，不影响功能与个人数据。"
                     if "缓存" in r["type"] or "临时" in r["type"]
                     else "可再生文件，清完不影响已有数据。"),
        })
        used.extend(paths)
    return items, used


# ------------------------------------------------------------------ 黄灯
def build_yellow(rules, scan, green_paths):
    items, used, hidden = [], [], set()
    for r in rules:
        paths = expand_all(r["match"])
        if not paths:
            continue
        batches = [[p] for p in paths] if r.get("split") else [paths]
        for grp in batches:
            size = measure(grp)
            if size < r.get("min_gb", 0.5) * GB:
                continue
            trash = [p for p in expand_all(r.get("trash_globs", [])) if p not in grp]
            open_path = grp[0] if r.get("split") else (r.get("open_path") or grp[0])
            title = os.path.basename(grp[0]) if r.get("split") else r["title"]
            items.append({
                "title": title, "size": gb(size), "path": show_path(grp, title),
                "type": r["type"], "desc": r["desc"], "risk": r.get("risk", ""),
                "steps": r.get("steps", []), "commands": r.get("commands", []),
                "open_path": open_path, "open_note": r.get("open_note", ""),
                "openable": r.get("openable", True) and inside_home(open_path),
                "trash_paths": trash, "_bytes": size, "_paths": grp,
                "_why": r["desc"].split("。")[0] + "。",
            })
            used.extend(grp)
        hidden.update(tuple(x) for x in r.get("hide", []))
    return items, used, hidden


AUTO_SKIP = {"Microsoft", "Windows", "Packages", "Temp", "Programs", "AppData",
             "ConnectedDevicesPlatform", "PlaceholderTileLogoFolder", "OEM",
             "Local Settings", "Application Data"}
GROUP_LABEL = {"user_profile": "用户目录", "appdata_local": "AppData\\Local",
               "appdata_roaming": "AppData\\Roaming", "programdata": "ProgramData",
               "program_files": "Program Files", "downloads": "下载文件夹"}


def auto_yellow(scan, covered, hidden, limit=8, min_gb=1.0):
    """未命中任何规则的大目录 → 通用「需人工判断」卡片。"""
    cands = []
    for gkey in ("user_profile", "appdata_local", "appdata_roaming", "programdata"):
        for c in scan["groups"].get(gkey, []):
            if c["kind"] != "dir" or c["size"] < min_gb * GB:
                continue
            if (gkey, c["name"]) in hidden or c["name"] in AUTO_SKIP:
                continue
            if any(os.path.realpath(c["path"]).startswith(os.path.realpath(p))
                   for p in covered):
                continue
            cands.append((c["size"], gkey, c))
    cands.sort(reverse=True)
    out = []
    for size, gkey, c in cands[:limit]:
        out.append({
            "title": c["name"], "size": gb(size), "path": c["path"], "type": "待判断",
            "desc": "位于%s下的一级目录，%s。扫描时没有命中任何已知缓存规则，"
                    "多半是某个应用的数据、素材或你自己的文件，需要打开看一眼再决定。"
                    % (GROUP_LABEL.get(gkey, gkey), gb(size)),
            "risk": "不清楚内容前不要整目录删除，可能包含个人数据或应用运行必需的文件。",
            "steps": ["在资源管理器打开，按「大小」排序看清楚里面是什么（图片/视频/安装包/数据库）。",
                      "能对应到具体应用的，优先用应用内的「清理缓存 / 更改存储位置」功能。",
                      "确认是纯素材且不常用，剪到其他盘归档，而不是删除。"],
            "open_path": c["path"], "openable": True, "commands": [],
            "trash_paths": [], "_bytes": size, "_paths": [c["path"]],
            "_why": "体积不小但用途不明，需要先确认内容。",
        })
    return out


# ------------------------------------------------------------------ 红灯
def build_red(rules, scan, covered, size_map):
    items = []
    for r in rules:
        paths = expand_all(r["match"])
        if not paths:
            continue
        size = measure(paths)
        if size < r.get("min_gb", 0.5) * GB:
            continue
        items.append({
            "title": r["title"], "size": gb(size), "path": show_path(paths, r["title"]),
            "type": r["type"], "desc": r["desc"], "risk": r.get("risk", ""),
            "indirect_release": r.get("indirect_release", []),
            "commands": r.get("commands", []),
            "openable": r.get("openable", True) and inside_home(paths[0]),
            "app_paths": [paths[0]] if inside_home(paths[0]) else [],
            "_bytes": size,
        })
    items += auto_red_versions(scan, size_map)
    return items


VER_RE = re.compile(r"^(.*?)(\d{4}\.\d+(?:\.\d+)?)$")


VER_ROOTS = ["%LOCALAPPDATA%", "%LOCALAPPDATA%/Google", "%LOCALAPPDATA%/Programs",
             "%APPDATA%", "%PROGRAMFILES%"]


def auto_red_versions(scan, size_map):
    """识别同一软件的多个版本目录，旧版本 → 红灯（别手删，走正规清理）。"""
    groups = {}
    for root in VER_ROOTS:
        for child in glob.glob(os.path.join(os.path.expandvars(root), "*")):
            if not os.path.isdir(child):
                continue
            m = VER_RE.match(os.path.basename(child))
            if not m:
                continue
            groups.setdefault(m.group(1), []).append((m.group(2), child))
    out = []
    for prefix, lst in groups.items():
        if len(lst) < 2:
            continue
        lst.sort(key=lambda x: [int(n) for n in x[0].split(".")], reverse=True)
        newest = lst[0][0]
        olds = lst[1:]
        sizes = [(size_map.get(os.path.realpath(p)) or measure([p]), p) for _, p in olds]
        size = sum(s for s, _ in sizes)
        if size < 0.3 * GB:
            continue
        first = sizes[0][1]
        out.append({
            "title": "%s 旧版本配置（%s）" % (prefix, "、".join(v for v, _ in olds)),
            "size": gb(size), "path": first, "type": "应用残留",
            "desc": "本机已装更新的 %s 版本，这里还留着旧版本的配置与索引缓存。" % newest,
            "risk": "若还会回到旧版本打开工程，删掉后需要重建索引（耗时但不丢工程）。",
            "indirect_release": ["确认只用新版后，直接删掉旧版本配置目录即可"
                                 "（配置不在程序目录里，不影响已装 IDE）。",
                                 "更稳妥：先重命名为 .bak，用几天没问题再删。",
                                 "只想清索引又想保留配置：只删该目录下的 caches / index 子目录。"],
            "commands": [], "app_paths": [first],
            "openable": inside_home(first),
            "open_label": "在资源管理器打开",
            "open_hint": "打开的是旧版配置目录本身，确认后可直接删除该文件夹（不影响已安装的新版）。",
            "_bytes": size,
        })
    return out


# ------------------------------------------------------------------ Top5 / 摘要
FRIENDLY = {
    "pagefile.sys": ("pagefile.sys（虚拟内存）", "系统文件"),
    "hiberfil.sys": ("hiberfil.sys（休眠文件）", "系统文件"),
    "$Recycle.Bin": ("回收站 $Recycle.Bin", "回收站"),
    "Windows": ("Windows 系统目录", "系统资产"),
    "Users": ("用户目录（含 AppData）", "用户数据"),
    "Program Files": ("已安装程序", "应用本体"),
    "Program Files (x86)": ("已安装程序（32 位）", "应用本体"),
    "ProgramData": ("程序共享数据", "应用数据"),
    "Recovery": ("恢复分区文件", "系统资产"),
    "AppData": ("AppData（应用数据与缓存）", "应用数据"),
    ".android": (".android（模拟器镜像）", "虚拟机镜像"),
    ".cache": (".cache（开发缓存）", "开发缓存"),
}


def build_top(scan, limit=6):
    rows = []
    for c in scan["groups"].get("c_root") or scan["groups"].get("root", []):
        if c.get("kind") == "reparse":
            continue
        name, typ = FRIENDLY.get(c["name"], (c["name"], "系统及其他"))
        rows.append({"name": name, "size": gb(c["size"]), "type": typ,
                     "path": c["path"], "note": "", "_bytes": c["size"], "_skip": False})
    kids = {c["name"]: c for c in scan["groups"].get("user_profile", [])}
    appdata = kids.get("AppData")
    if appdata:
        for r in rows:
            if r["name"].startswith("用户目录"):
                r["_skip"] = True
    if appdata:
        top3 = scan["groups"].get("appdata_local", [])[:3]
        note = "含 " + "、".join("%s %s" % (c["name"], gb(c["size"])) for c in top3)
        rows.append({"name": "AppData（应用数据与缓存）", "size": gb(appdata["size"]),
                     "type": "应用数据", "path": appdata["path"], "note": note,
                     "_bytes": appdata["size"]})
    for key in (".android", ".cache"):
        c = kids.get(key)
        if c and c["size"] >= 5 * GB:
            name, typ = FRIENDLY[key]
            rows.append({"name": name, "size": gb(c["size"]), "type": typ,
                         "path": c["path"], "note": "", "_bytes": c["size"]})
    rows = [r for r in rows if not r.pop("_skip", False)]
    rows.sort(key=lambda r: -r["_bytes"])
    seen, out = set(), []
    for r in rows:
        if r["path"] in seen:
            continue
        seen.add(r["path"])
        r.pop("_bytes")
        out.append(r)
    return out[:limit]


def build_summary(scan, green, yellow, red, top):
    md = scan["system"]["main_disk"]
    total, used = md["total"], md["used"]
    g = sum(i["_bytes"] for i in green)
    y = sum(i["_bytes"] for i in yellow)
    r = sum(i["_bytes"] for i in red)
    pct = used / total * 100 if total else 0
    first = top[0] if top else {"name": "未知", "size": "—"}
    overview = ("%s 已用 %s / %s（%.0f%%），最大占用是 %s（%s）。"
                "绿灯 %d 项共 %s 可以立刻清掉、不碰任何个人文件；连黄灯一起处理最多 %s。"
                % (scan["system"].get("disk_name", "C:"), gb(used), gb(total), pct,
                   first["name"], first["size"], len(green), gb(g), gb(g + y)))

    prio = []
    for i in sorted(green, key=lambda x: -x["_bytes"])[:3]:
        prio.append("先清 <b>%s %s</b>：%s" % (i["title"], i["size"], i["_why"]))
    for i in sorted(yellow, key=lambda x: -x["_bytes"])[:2]:
        prio.append("<b>%s %s</b>：%s" % (i["title"], i["size"], i["_why"]))
    sysfiles = [x for x in top if "hiberfil" in x["name"] or "pagefile" in x["name"]]
    if sysfiles:
        prio.append("系统文件也能回收：不常用休眠执行 <b>powercfg /h off</b> 可省下与内存等大的 "
                    "hiberfil.sys；虚拟内存可在系统属性里迁到数据盘。")
    prio.append("长期方案：把模拟器镜像、素材、下载文件与项目环境迁到数据盘，系统盘只留系统与常用程序。")
    return {"overview": overview,
            "priority": prio,
            "tier_stats": {"green": gb(g), "yellow": gb(y), "red": gb(r)},
            "long_term": LONG_TERM_WIN}


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if len(sys.argv) < 3:
        print("usage: python analyze.py scan.json analysis.json")
        return 2
    with open(sys.argv[1], encoding="utf-8") as f:
        scan = json.load(f)
    win = scan["system"]["os"] == "windows"
    green, used = build_green(GREEN_WIN if win else GREEN_MAC)
    size_map = {}
    for items_ in scan["groups"].values():
        for c in items_:
            size_map[os.path.realpath(c["path"])] = c["size"]
    green_hide = [tuple(x) for r in (GREEN_WIN if win else GREEN_MAC)
                  for x in r.get("hide", [])]
    yellow, yused, hidden = build_yellow(YELLOW_WIN if win else YELLOW_MAC, scan, used)
    hidden.update(green_hide)
    yellow += auto_yellow(scan, used + yused, hidden)
    red = build_red(RED_WIN if win else [], scan, used, size_map)
    top = build_top(scan)
    summ = build_summary(scan, green, yellow, red, top)
    for i in green + yellow + red:
        for k in ("_bytes", "_paths", "_why", "path_internal"):
            i.pop(k, None)

    analysis = {
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "system": {"disk_name": scan["system"].get("disk_name", "C:"),
                   "hostname": scan["system"].get("hostname", ""),
                   "user": scan["system"].get("user", "")},
        "disk": {k: scan["system"]["main_disk"].get(k, 0) for k in ("total", "used", "free")},
        "summary": summ,
        "top5": top,
        "tiers": {"green": green, "yellow": yellow, "red": red},
    }
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump(analysis, f, ensure_ascii=False, indent=1)
    print("green %d / yellow %d / red %d -> %s"
          % (len(green), len(yellow), len(red), sys.argv[2]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
