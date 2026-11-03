# -*- coding: utf-8 -*-
"""把 analysis JSON 渲染成交互式 HTML 报告。"""
import html
import re
from theme import CSS, JS


def fmt(n):
    if n is None:
        return "—"
    n = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return ("%.1f %s" % (n, unit)) if unit in ("GB", "TB") else ("%d %s" % (round(n), unit))
        n /= 1024.0


def e(s):
    return html.escape(str(s if s is not None else ""))


def parse_gb(txt):
    if not txt:
        return 0.0
    m = re.search(r"([\d.]+)\s*(TB|GB|MB|KB)", str(txt), re.I)
    if not m:
        return 0.0
    v = float(m.group(1))
    u = m.group(2).upper()
    return v * {"TB": 1024.0, "GB": 1.0, "MB": 1 / 1024.0, "KB": 1 / 1048576.0}[u]


def card_head(title, size, path, tag=None):
    tag_html = '<span class="tag">%s</span>' % e(tag) if tag else ""
    return ('<summary><span class="chev">▶</span><span class="sum-main">'
            '<span class="sum-title">%s%s</span>'
            '<span class="sum-path">%s</span></span>'
            '<span class="sum-size">%s</span></summary>'
            % (e(title), tag_html, e(path), e(size)))


def render_green(it, live):
    parts = ['<details class="item">', card_head(it.get("title"), it.get("size"), it.get("path"), it.get("type")), '<div class="body">']
    if it.get("desc"):
        parts.append("<p>%s</p>" % e(it["desc"]))
    if it.get("close"):
        parts.append('<div class="kv"><span class="k">先关闭</span><span>%s</span></div>' % e(it["close"]))
    if it.get("risk"):
        parts.append('<div class="note info">%s</div>' % e(it["risk"]))
    for c in it.get("commands") or []:
        if c.get("label"):
            parts.append("<p>%s</p>" % e(c["label"]))
        parts.append('<code class="cmd"><button class="cp" onclick="copyCmd(this)">复制</button>'
                     '<span class="txt">%s</span></code>' % e(c["cmd"]))
    btns = []
    if live and it.get("trash_paths"):
        paths = it["trash_paths"]
        btns.append('<button class="act" onclick=\'act("trash",%s,"移入回收站")\'>移到回收站</button>'
                    % e(json_dumps(paths)))
        btns.append('<button class="act r" onclick=\'act("rm",%s,"永久删除")\'>直接删除（立即释放）</button>'
                    % e(json_dumps(paths)))
    if live and it.get("path") and it.get("openable", True):
        btns.append('<button class="act" onclick=\'openPath(%s)\'>在资源管理器打开</button>' % e(json_dumps(it["path"])))
    if btns:
        if not live:
            parts.append('<div class="tip">静态报告模式：不提供一键清理按钮，请复制上面的命令自行执行。</div>')
        parts.append('<div class="btnrow">%s</div>' % "".join(btns))
        if it.get("trash_paths"):
            parts.append('<div class="tip">「移到回收站」可还原，但需清空回收站才真正释放空间；'
                         '「直接删除」立即释放且不可恢复。所有操作单次只作用于上面列出的路径。</div>')
    parts.append("</div></details>")
    return "".join(parts)


def render_yellow(it, live):
    parts = ['<details class="item">', card_head(it.get("title"), it.get("size"), it.get("path"), it.get("type")), '<div class="body">']
    if it.get("desc"):
        parts.append("<p>%s</p>" % e(it["desc"]))
    if it.get("risk"):
        parts.append('<div class="note">%s</div>' % e(it["risk"]))
    if it.get("open_note"):
        parts.append('<div class="note info">%s</div>' % e(it["open_note"]))
    for i, step in enumerate(it.get("steps") or [], 1):
        if i == 1:
            parts.append('<ul class="steps">')
        parts.append("<li>%s</li>" % e(step))
    if it.get("steps"):
        parts.append("</ul>")
    for c in it.get("commands") or []:
        if c.get("label"):
            parts.append("<p>%s</p>" % e(c["label"]))
        parts.append('<code class="cmd"><button class="cp" onclick="copyCmd(this)">复制</button>'
                     '<span class="txt">%s</span></code>' % e(c["cmd"]))
    btns = []
    if live and it.get("openable", True):
        target = it.get("open_path") or it.get("path")
        if target:
            btns.append('<button class="act" onclick=\'openPath(%s)\'>在资源管理器打开</button>' % e(json_dumps(target)))
        if it.get("trash_paths"):
            btns.append('<button class="act" onclick=\'act("trash",%s,"移入回收站")\'>移到回收站</button>'
                        % e(json_dumps(it["trash_paths"])))
    if btns:
        parts.append('<div class="btnrow">%s</div>' % "".join(btns))
        parts.append('<div class="tip">「打开」只定位查看，不会删除任何文件；「移到回收站」可还原，'
                     '需清空回收站才真正释放空间。</div>')
    parts.append("</div></details>")
    return "".join(parts)


def render_red(it, live):
    parts = ['<details class="item">', card_head(it.get("title"), it.get("size"), it.get("path"), it.get("type")), '<div class="body">']
    if it.get("desc"):
        parts.append("<p>%s</p>" % e(it["desc"]))
    if it.get("risk"):
        parts.append('<div class="note">%s</div>' % e(it["risk"]))
    if it.get("indirect_release"):
        parts.append("<p>正确的释放方式：</p><ul class=\"steps\">%s</ul>"
                     % "".join("<li>%s</li>" % e(x) for x in it["indirect_release"]))
    for c in it.get("commands") or []:
        if c.get("label"):
            parts.append("<p>%s</p>" % e(c["label"]))
        parts.append('<code class="cmd"><button class="cp" onclick="copyCmd(this)">复制</button>'
                     '<span class="txt">%s</span></code>' % e(c["cmd"]))
    if live and it.get("openable", True):
        targets = it.get("app_paths") or ([it["path"]] if it.get("path") else [])
        if targets:
            label = it.get("open_label") or "在资源管理器打开（去卸载）"
            parts.append('<div class="btnrow"><button class="act" onclick=\'openPath(%s)\'>%s</button></div>'
                         % (e(json_dumps(targets[0])), e(label)))
            hint = it.get("open_hint") or ("只定位到应用本体，卸载请走上面的正规流程，"
                                           "不要直接删除程序文件夹（会留下注册表与残留项）。")
            parts.append('<div class="tip">%s</div>' % e(hint))
    parts.append("</div></details>")
    return "".join(parts)


def json_dumps(o):
    import json
    return json.dumps(o, ensure_ascii=False)


def build_html(a, token=""):
    s = a.get("system") or {}
    disk = a.get("disk") or {}
    total = float(disk.get("total") or 0)
    used = float(disk.get("used") or 0)
    free = float(disk.get("free") or 0)
    summ = a.get("summary") or {}
    ts = summ.get("tier_stats") or {}
    g, y, r = parse_gb(ts.get("green")), parse_gb(ts.get("yellow")), parse_gb(ts.get("red"))
    gb = 1024.0 ** 3
    used_gb = used / gb if used else 1
    blue = max(0.0, used_gb - g - y - r)
    pct = lambda v: max(0.0, min(100.0, v / used_gb * 100)) if used_gb else 0
    used_pct_total = (used / total * 100) if total else 0
    live = bool(token)

    out = []
    out.append('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
               '<meta name="viewport" content="width=device-width,initial-scale=1">'
               '<title>C 盘空间分析报告</title><style>%s</style></head><body><div class="wrap">' % CSS)

    # 头部
    out.append('<header class="top"><div class="eyebrow">Storage Analysis · Read Only</div>'
               '<h1>%s 盘空间分析</h1><div class="meta">'
               '<span>%s</span><span class="dot"></span><span>%s</span>'
               '<span class="dot"></span><span>%s</span>'
               '<span class="dot"></span><span>扫描仅读取元信息，未修改任何文件</span>'
               '</div></header>'
               % (e(s.get("disk_name", "C:")), e(a.get("generated_at", "")),
                  e(s.get("hostname", "")), e(s.get("user", ""))))

    # 总览
    out.append('<div class="card"><div class="kpis">'
               '<div class="kpi"><div class="lbl">总容量</div><div class="val">%s</div></div>'
               '<div class="kpi"><div class="lbl">已使用</div><div class="val">%s<small>%s</small></div></div>'
               '<div class="kpi"><div class="lbl">可用</div><div class="val">%s</div></div>'
               '<div class="kpi"><div class="lbl">可释放（估算）</div><div class="val" style="color:#66d97a">%s</div></div>'
               '</div>' % (fmt(total), fmt(used), "%.0f%%" % used_pct_total, fmt(free),
                           "%.1f GB" % (g + y)))
    out.append('<div class="bar" title="已用 %.1f GB / 总 %.1f GB">' % (used_gb, total / gb))
    out.append('<div class="g" style="width:%.2f%%"></div>' % pct(g))
    out.append('<div class="y" style="width:%.2f%%"></div>' % pct(y))
    out.append('<div class="r" style="width:%.2f%%"></div>' % pct(r))
    out.append('<div class="b" style="width:%.2f%%"></div>' % pct(blue))
    out.append("</div>")
    out.append('<div class="legend">'
               '<span class="pill"><i style="background:#3fb950"></i>可自动清理 <b>%s</b></span>'
               '<span class="pill"><i style="background:#e3a008"></i>需人工判断 <b>%s</b></span>'
               '<span class="pill"><i style="background:#f85149"></i>谨慎清理 <b>%s</b></span>'
               '<span class="pill"><i style="background:#4c8dff"></i>系统及其他 <b>%.1f GB</b></span>'
               '<span class="pill"><i style="background:#3a4553"></i>可用 <b>%s</b></span>'
               '</div></div>' % (ts.get("green", "—"), ts.get("yellow", "—"), ts.get("red", "—"), blue, fmt(free)))

    # Top5
    top5 = a.get("top5") or []
    if top5:
        mx = max([parse_gb(i.get("size")) for i in top5] + [1])
        out.append('<h2>占用排行 Top %d<span class="num">按单项体量排序</span></h2><div class="card tight"><div class="rank">' % len(top5))
        for i, it in enumerate(top5, 1):
            w = parse_gb(it.get("size")) / mx * 100
            tag = '<span class="tag">%s</span>' % e(it["type"]) if it.get("type") else ""
            out.append('<div class="row"><div class="idx">%02d</div><div><div class="nm">%s%s</div>'
                       '<div class="p">%s</div></div><div class="sz">%s</div></div>'
                       '<div class="track"><i style="width:%.1f%%"></i></div>'
                       % (i, e(it.get("name")), tag, e(it.get("path", "")), e(it.get("size")), w))
        out.append("</div></div>")

    # 执行建议
    out.append('<h2>执行建议</h2><div class="card">')
    if summ.get("overview"):
        out.append('<div class="callout">%s</div>' % e(summ["overview"]))
    pr = summ.get("priority") or []
    if pr:
        out.append('<ol class="prio">%s</ol>' % "".join("<li>%s</li>" % p for p in pr))
    out.append("</div>")

    # 三级
    tiers = a.get("tiers") or {}
    meta = [
        ("green", "g", "可自动清理", "纯缓存与临时文件，删掉会被自动重建，不影响任何功能与个人数据。"),
        ("yellow", "y", "需人工判断", "含用户数据或需要挑拣，建议打开看一眼再决定。"),
        ("red", "r", "谨慎清理", "不建议手删的项，按正规流程卸载/迁移才能真正释放。"),
    ]
    for key, cls, title, desc in meta:
        items = tiers.get(key) or []
        if not items:
            continue
        total_size = ts.get(key, "")
        out.append('<section class="tier %s"><div class="tier-h"><span class="badge">%s</span>'
                   '<h3>%s</h3><span class="sum">%s</span></div><p class="tier-desc">%s</p>'
                   % (cls, {"green": "🟢 自动", "yellow": "🟡 判断", "red": "🔴 谨慎"}[key], title, e(total_size), desc))
        for it in items:
            out.append({"green": render_green, "yellow": render_yellow, "red": render_red}[key](it, live))
        out.append("</section>")

    # 长期建议
    lt = summ.get("long_term") or []
    if lt:
        out.append('<h2>长期优化建议</h2><div class="card"><div class="longterm">%s</div></div>'
                   % "".join("<div>%s</div>" % e(x) for x in lt))

    out.append('<footer>报告由 storage-analyzer 生成 · 所有体积为扫描时刻的估算值（系统文件、'
               '隐藏卷影副本、硬链接可能造成少量偏差）· 删除前请确认路径 · 静态内容不包含任何写操作。</footer>')
    out.append('<div id="toast"></div>')
    out.append("<script>%s</script></div></body></html>" % JS.replace("__TOKEN__", token))
    return "".join(out)
