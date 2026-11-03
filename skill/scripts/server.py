# -*- coding: utf-8 -*-
"""报告服务：127.0.0.1 + 随机端口 + token，提供移入回收站 / 直接删除 / 打开位置。

安全模型（三套白名单，权限从严到宽）:
  rm    仅允许绿灯 trash_paths
  trash 允许绿灯 + 黄灯 trash_paths
  open  允许上述全部 + 黄灯 path + 红灯 app_paths
所有请求 realpath 校验且必须位于 $HOME 之内，并校验 token 与 Host。
"""
import json
import os
import random
import secrets
import shutil
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ui import build_html  # noqa: E402

HOME = os.path.realpath(os.environ.get("USERPROFILE", os.path.expanduser("~")))
ANALYSIS = {}
TOKEN = secrets.token_urlsafe(18)
WL_RM, WL_TRASH, WL_OPEN = [], [], []


def _norm(p):
    try:
        return os.path.realpath(os.path.abspath(p))
    except Exception:
        return None


def _inside_home(p):
    return p and (p == HOME or p.lower().startswith(HOME.lower() + os.sep))


def build_whitelists(a):
    rm, trash, op = [], [], []

    def add(lst, p):
        if isinstance(p, str) and p:
            lst.append(p)

    for key in ("green", "yellow"):
        for it in (a.get("tiers") or {}).get(key) or []:
            for p in it.get("trash_paths") or []:
                add(trash, p)
                if key == "green":
                    add(rm, p)
            if key == "yellow":
                add(op, it.get("open_path") or it.get("path"))
            else:
                add(op, it.get("path"))
    for it in (a.get("tiers") or {}).get("red") or []:
        for p in it.get("app_paths") or []:
            add(op, p)
        add(op, it.get("path"))
    return rm, trash, op


def allowed(paths, wl):
    ok = []
    norms = [_norm(x) for x in wl if x]
    for p in paths or []:
        rp = _norm(p)
        if not rp:
            continue
        if not _inside_home(rp):
            continue
        for w in norms:
            if rp == w or rp.lower().startswith(w.lower() + os.sep):
                ok.append(rp)
                break
    return ok


def size_of(paths):
    total = 0
    for p in paths:
        try:
            if os.path.isdir(p):
                for root, dirs, files in os.walk(p):
                    for f in files:
                        try:
                            total += os.path.getsize(os.path.join(root, f))
                        except OSError:
                            pass
            else:
                total += os.path.getsize(p)
        except OSError:
            pass
    return total


def fmt(n):
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or u == "TB":
            return "%.1f %s" % (n, u)
        n /= 1024.0


def trash_windows(paths):
    """SHFileOperationW + FOF_ALLOWUNDO → 移入回收站。"""
    import ctypes
    from ctypes import wintypes

    class SHFILEOPSTRUCTW(ctypes.Structure):
        _fields_ = [("hwnd", wintypes.HWND), ("wFunc", wintypes.UINT),
                    ("pFrom", wintypes.LPCWSTR), ("pTo", wintypes.LPCWSTR),
                    ("fFlags", ctypes.c_uint16), ("fAnyOperationsAborted", wintypes.BOOL),
                    ("hNameMappings", ctypes.c_void_p), ("lpszProgressTitle", wintypes.LPCWSTR)]

    FO_DELETE, FOF_ALLOWUNDO, FOF_NOCONFIRMATION = 3, 0x0040, 0x0010
    FOF_SILENT, FOF_NOERRORUI = 0x0004, 0x0400
    src = "\0".join(paths) + "\0\0"
    op = SHFILEOPSTRUCTW(0, FO_DELETE, src, None,
                         FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT | FOF_NOERRORUI,
                         False, None, None)
    rc = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
    if rc != 0:
        raise OSError("SHFileOperationW 返回 %d" % rc)


def rm_path(p):
    if os.path.isdir(p) and not os.path.islink(p):
        shutil.rmtree(p)
    else:
        os.remove(p)


class Handler(BaseHTTPRequestHandler):
    server_version = "storage-analyzer"

    def log_message(self, *args):
        pass

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _host_ok(self):
        h = (self.headers.get("Host") or "").split(":")[0]
        return h in ("127.0.0.1", "localhost")

    def do_GET(self):
        if not self._host_ok():
            return self._json(403, {"ok": False, "error": "bad host"})
        if self.path.split("?")[0] not in ("/", "/index.html"):
            return self._json(404, {"ok": False, "error": "not found"})
        body = build_html(ANALYSIS, TOKEN).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if not self._host_ok():
            return self._json(403, {"ok": False, "error": "bad host"})
        if self.headers.get("X-Token") != TOKEN:
            return self._json(403, {"ok": False, "error": "token 无效，请刷新页面"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
            data = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return self._json(400, {"ok": False, "error": "bad json"})
        paths = data.get("paths") or []
        if isinstance(paths, str):
            paths = [paths]
        ep = self.path.split("?")[0]

        if ep == "/api/trash":
            ok = allowed(paths, WL_TRASH)
            if not ok:
                return self._json(403, {"ok": False, "error": "路径不在允许清单内"})
            sz = size_of(ok)
            try:
                trash_windows(ok)
            except Exception as ex:
                return self._json(500, {"ok": False, "error": str(ex)})
            return self._json(200, {"ok": True, "count": len(ok), "freed": fmt(sz)})

        if ep == "/api/rm":
            ok = allowed(paths, WL_RM)
            if not ok:
                return self._json(403, {"ok": False, "error": "路径不在允许清单内（仅绿灯缓存可直删）"})
            sz = size_of(ok)
            errs = []
            for p in ok:
                try:
                    rm_path(p)
                except Exception as ex:
                    errs.append("%s: %s" % (p, ex))
            if errs and len(errs) == len(ok):
                return self._json(500, {"ok": False, "error": errs[0]})
            return self._json(200, {"ok": True, "count": len(ok) - len(errs), "freed": fmt(sz),
                                    "warn": errs[:2]})

        if ep == "/api/open":
            ok = allowed(paths, WL_OPEN)
            if not ok:
                return self._json(403, {"ok": False, "error": "路径不在允许清单内"})
            p = ok[0]
            try:
                if os.path.isdir(p):
                    subprocess.Popen(["explorer", p])
                else:
                    subprocess.Popen(["explorer", "/select,", p])
            except Exception as ex:
                return self._json(500, {"ok": False, "error": str(ex)})
            return self._json(200, {"ok": True})

        return self._json(404, {"ok": False, "error": "not found"})


def main():
    global ANALYSIS, WL_RM, WL_TRASH, WL_OPEN
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if len(sys.argv) < 2:
        print("usage: python server.py <analysis.json>")
        return 2
    with open(sys.argv[1], encoding="utf-8") as f:
        ANALYSIS = json.load(f)
    WL_RM, WL_TRASH, WL_OPEN = build_whitelists(ANALYSIS)

    port = random.randint(49152, 60500)
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = "http://127.0.0.1:%d/" % port
    try:
        # 后台运行时 stdout 可能拿不到，把地址落到 analysis.json 同级目录
        url_file = os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), "server_url.txt")
        with open(url_file, "w", encoding="utf-8") as f:
            f.write(url)
    except Exception:
        pass
    print("报告地址: %s" % url, flush=True)
    print("绿灯移除白名单 %d 项 / 橙灯 %d 项 / 打开白名单 %d 项"
          % (len(WL_RM), len(WL_TRASH), len(WL_OPEN)), flush=True)
    threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("已停止", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
