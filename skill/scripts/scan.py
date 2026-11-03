# -*- coding: utf-8 -*-
"""只读存储扫描器。全程只读取元信息与统计大小，不做任何写/删操作。

用法:
    python scan.py <输出JSON路径> [--min-mb 50]

输出结构:
    system: os / platform / hostname / user / home / disk_name / disks / main_disk
    groups: 各扫描组的子目录列表（已按体积降序、过滤小项、标记 denied）
"""
import ctypes
import json
import os
import socket
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

FILE_ATTRIBUTE_REPARSE_POINT = 0x400
WINDOWS = sys.platform == "win32"
MACOS = sys.platform == "darwin"

MIN_SIZE = 50 * 1024 * 1024


def reconfigure_stdout():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


# ---------------------------------------------------------------- 大小统计
def dir_size_win(path):
    """递归统计目录大小（字节），返回 (size, denied_count)。跳过 reparse point。"""
    total = 0
    denied = 0
    stack = [path]
    while stack:
        cur = stack.pop()
        try:
            with os.scandir(cur) as it:
                for e in it:
                    try:
                        st = e.stat(follow_symlinks=False)
                    except OSError:
                        denied += 1
                        continue
                    attrs = getattr(st, "st_file_attributes", 0)
                    try:
                        is_dir = e.is_dir(follow_symlinks=False)
                    except OSError:
                        is_dir = False
                    if is_dir:
                        # junction / symlink 不跟进，避免 Local Settings 这类重复计数
                        if attrs & FILE_ATTRIBUTE_REPARSE_POINT:
                            continue
                        stack.append(e.path)
                    else:
                        total += st.st_size
        except (PermissionError, OSError):
            denied += 1
    return total, denied


def dir_size_du(path):
    """macOS / POSIX：用 du -sk 统计（KB），返回 (size, denied)。"""
    try:
        out = subprocess.run(["du", "-sk", path], capture_output=True, text=True, timeout=1800)
        if out.returncode == 0 and out.stdout.strip():
            return int(out.stdout.split()[0]) * 1024, 0
        return 0, 1
    except Exception:
        return 0, 1


def dir_size(path):
    return dir_size_win(path) if WINDOWS else dir_size_du(path)


def scan_children(root, min_size=MIN_SIZE):
    """列出 root 每个一级子项的大小，降序。"""
    out = []
    if not root or not os.path.isdir(root):
        return out
    try:
        entries = list(os.scandir(root))
    except OSError:
        return out

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
        if is_dir:
            if attrs & FILE_ATTRIBUTE_REPARSE_POINT:
                return {"name": e.name, "path": e.path, "size": 0, "denied": 0,
                        "kind": "reparse"}
            size, denied = dir_size(e.path)
            return {"name": e.name, "path": e.path, "size": size,
                    "denied": denied, "kind": "dir"}
        if attrs & FILE_ATTRIBUTE_REPARSE_POINT:
            return None
        return {"name": e.name, "path": e.path, "size": st.st_size,
                "denied": 0, "kind": "file"}

    with ThreadPoolExecutor(max_workers=12) as ex:
        for r in ex.map(one, entries):
            if r and r["size"] >= min_size:
                out.append(r)
    out.sort(key=lambda x: -x["size"])
    return out


# ---------------------------------------------------------------- 磁盘信息
def get_disks_win():
    drives = []
    k32 = ctypes.windll.kernel32
    mask = k32.GetLogicalDrives()
    for i in range(26):
        if not (mask >> i) & 1:
            continue
        root = chr(ord("A") + i) + ":\\"
        if not os.path.exists(root):
            continue
        try:
            avail = ctypes.c_ulonglong(0)
            total = ctypes.c_ulonglong(0)
            total_free = ctypes.c_ulonglong(0)
            ok = k32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(root), ctypes.byref(avail),
                                         ctypes.byref(total), ctypes.byref(total_free))
            if not ok:
                continue
            buf = ctypes.create_unicode_buffer(261)
            vol = ""
            if k32.GetVolumeInformationW(ctypes.c_wchar_p(root), buf, 261,
                                          None, None, None, None, 0):
                vol = buf.value
            drives.append({"mount": root, "name": vol or root,
                           "total": total.value, "free": avail.value,
                           "used": total.value - avail.value})
        except Exception:
            continue
    return drives


def get_disks_posix():
    drives = []
    for mount in ("/", "/System/Volumes/Data"):
        try:
            st = os.statvfs(mount)
        except OSError:
            continue
        total = st.f_blocks * st.f_frsize
        free = st.f_bavail * st.f_frsize
        drives.append({"mount": mount, "name": "Macintosh HD" if mount == "/" else mount,
                       "total": total, "free": free, "used": total - free})
        break
    return drives


# ---------------------------------------------------------------- 主流程
def scan_windows(home, min_size):
    local = os.environ.get("LOCALAPPDATA", os.path.join(home, "AppData", "Local"))
    roaming = os.environ.get("APPDATA", os.path.join(home, "AppData", "Roaming"))
    targets = {
        "user_profile": home,
        "appdata_local": local,
        "appdata_roaming": roaming,
        "temp": os.environ.get("TEMP", os.path.join(local, "Temp")),
        "downloads": os.path.join(home, "Downloads"),
        "program_files": r"C:\Program Files",
        "program_files_x86": r"C:\Program Files (x86)",
        "programdata": r"C:\ProgramData",
        "c_root": "C:\\",
    }
    dev_paths = [os.path.join(home, p) for p in
                 (".cache", ".conda", ".gradle", ".m2", ".cargo", ".nuget", ".docker")]
    dev_paths += [os.path.join(local, "pip", "Cache"), os.path.join(local, "npm-cache"),
                  os.path.join(local, "uv")]
    return targets, dev_paths


def scan_macos(home, min_size):
    lib = os.path.join(home, "Library")
    targets = {
        "user_profile": home,
        "library": lib,
        "caches": os.path.join(lib, "Caches"),
        "containers": os.path.join(lib, "Containers"),
        "group_containers": os.path.join(lib, "Group Containers"),
        "app_support": os.path.join(lib, "Application Support"),
        "applications": "/Applications",
        "downloads": os.path.join(home, "Downloads"),
        "root": "/",
    }
    dev_paths = [os.path.join(home, p) for p in
                 (".npm", ".cache", ".gradle", ".m2", ".cargo", ".docker",
                  "Library/Developer/Xcode/DerivedData",
                  "Library/Developer/CoreSimulator/Devices")]
    return targets, dev_paths


def main():
    reconfigure_stdout()
    args = [a for a in sys.argv[1:]]
    min_size = MIN_SIZE
    if "--min-mb" in args:
        i = args.index("--min-mb")
        min_size = int(float(args[i + 1]) * 1024 * 1024)
        del args[i:i + 2]
    if not args:
        print("usage: python scan.py <out.json> [--min-mb 50]")
        return 2
    out_path = args[0]

    home = os.path.expanduser("~")
    if WINDOWS:
        os_name = "windows"
        targets, dev_paths = scan_windows(home, min_size)
        disks = get_disks_win()
    elif MACOS:
        os_name = "macos"
        targets, dev_paths = scan_macos(home, min_size)
        disks = get_disks_posix()
    else:
        os_name = "posix"
        targets, dev_paths = {"user_profile": home, "root": "/"}, []
        disks = get_disks_posix()

    groups = {}
    for key, root in targets.items():
        sys.stderr.write("scanning %s ...\n" % root)
        sys.stderr.flush()
        if key == "temp":
            size, denied = dir_size(root)
            groups[key] = ([{"name": os.path.basename(root) or root, "path": root,
                             "size": size, "denied": denied, "kind": "dir"}]
                           if size >= min_size else [])
            continue
        groups[key] = scan_children(root, min_size)

    dev = []
    for p in dev_paths:
        if os.path.isdir(p):
            size, denied = dir_size(p)
            dev.append({"name": os.path.basename(p.rstrip("\\/")) or p, "path": p,
                        "size": size, "denied": denied, "kind": "dir"})
    dev.sort(key=lambda x: -x["size"])
    groups["dev_caches"] = [d for d in dev if d["size"] >= min_size]

    main_disk = next((d for d in disks if d["mount"].upper().startswith("C:")),
                     disks[0] if disks else {})
    try:
        hostname = socket.gethostname()
    except Exception:
        hostname = ""
    result = {
        "system": {
            "os": os_name, "platform": sys.platform,
            "hostname": hostname,
            "user": os.environ.get("USERNAME") or os.environ.get("USER", ""),
            "home": home,
            "disk_name": (main_disk.get("mount") or "/").rstrip("\\/") or "/",
            "disks": disks, "main_disk": main_disk,
            "min_size_bytes": min_size,
        },
        "groups": groups,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    sys.stderr.write("done -> %s\n" % out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
