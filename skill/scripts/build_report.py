# -*- coding: utf-8 -*-
"""静态报告：analysis.json -> 单文件 HTML（无删除按钮，可分享 / 留存）。

用法:
    python build_report.py analysis.json <输出.html>
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ui import build_html  # noqa: E402


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if len(sys.argv) < 3:
        print("usage: python build_report.py analysis.json out.html")
        return 2
    with open(sys.argv[1], encoding="utf-8") as f:
        analysis = json.load(f)
    # token 为空 -> 渲染器不输出任何操作按钮（file:// 页面本来也碰不到文件系统）
    html = build_html(analysis, "")
    out = os.path.abspath(sys.argv[2])
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print("静态报告: %s (%.0f KB)" % (out, os.path.getsize(out) / 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
