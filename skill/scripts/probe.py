# -*- coding: utf-8 -*-
"""只读下钻探查：列目录构成，或找大文件。用于「神秘大目录」归属判断。

用法:
    python probe.py <目录1> [<目录2> ...]
    python probe.py FILES:<根目录>     # 列出该根下 >1.5GB 的大文件
    python probe.py <目录> --min-mb 200
"""
import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scan import dir_size  # noqa: E402

GB = 1024 ** 3


def children(root, minsz):
    if not os.path.isdir(root):
        print("\n[missing] %s" % root)
        return
    try:
        entries = list(os.scandir(root))
    except OSError as ex:
        print("\n[denied] %s (%s)" % (root, ex))
        return

    def one(e):
        try:
            st = e.stat(follow_symlinks=False)
        except OSError:
            return None
        attrs = getattr(st, "st_file_attributes", 0)
        try:
            is_dir = e.is_dir(follow_symlinks=False)
        except OSError:
            is_dir = False
        if attrs & 0x400:
            return {"n": e.name, "s": 0, "k": "reparse"} if is_dir else None
        if is_dir:
            s, _ = dir_size(e.path)
            return {"n": e.name, "s": s, "k": "dir"}
        return {"n": e.name, "s": st.st_size, "k": "file"}

    with ThreadPoolExecutor(max_workers=12) as ex:
        res = [r for r in ex.map(one, entries) if r and r["s"] >= minsz]
    res.sort(key=lambda x: -x["s"])
    print("\n=== %s ===" % root)
    for r in res:
        print("  %7.2f GB  [%s] %s" % (r["s"] / GB, r["k"], os.path.join(root, r["n"])))


def big_files(root, minsz=1.5 * GB, limit=25):
    print("\n=== 大文件 (>%.1f GB): %s ===" % (minsz / GB, root))
    found = []
    for dp, dns, fns in os.walk(root):
        for f in fns:
            p = os.path.join(dp, f)
            try:
                st = os.stat(p, follow_symlinks=False)
            except OSError:
                continue
            if getattr(st, "st_file_attributes", 0) & 0x400:
                continue
            if st.st_size >= minsz:
                found.append((st.st_size, p))
    found.sort(reverse=True)
    for s, p in found[:limit]:
        print("  %7.2f GB  %s" % (s / GB, p))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    args = sys.argv[1:]
    minsz = 30 * 1024 * 1024
    if "--min-mb" in args:
        i = args.index("--min-mb")
        minsz = int(float(args[i + 1]) * 1024 * 1024)
        del args[i:i + 2]
    if not args:
        print(__doc__)
        sys.exit(2)
    for t in args:
        if t.startswith("FILES:"):
            big_files(t[6:])
        else:
            children(t, minsz)
