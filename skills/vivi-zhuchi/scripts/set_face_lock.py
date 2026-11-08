#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""切 / 校验 vivi 定妆脸锁。

用法（在技能根目录下）：
    python scripts/set_face_lock.py --check        # 只校验，不改文件
    python scripts/set_face_lock.py locked         # 切到 GitHub HEAD 新锁
    python scripts/set_face_lock.py in_use         # 切回本机旧锁
    python scripts/set_face_lock.py canonical      # 切到历史 720x1280 canonical

规则：一切以 assets/ASSETS-LOCK.json 的 md5 为准；被替换下来的那张自动进
assets/_archive/，不删文件、可回滚。
"""
import hashlib
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOCK = ROOT / "assets" / "ASSETS-LOCK.json"
TARGET = ROOT / "assets" / "host_look.jpg"
ARCHIVE = ROOT / "assets" / "_archive"


def md5(p):
    return hashlib.md5(pathlib.Path(p).read_bytes()).hexdigest()


def load():
    return json.loads(LOCK.read_text(encoding="utf-8"))


def main(argv):
    if not LOCK.exists():
        print("找不到 %s" % LOCK)
        return 2
    data = load()
    locks = data["face_lock"]
    default = locks.get("default", "in_use")

    def is_lock(v):
        return isinstance(v, dict) and "md5" in v and "file" in v

    names = [k for k, v in locks.items() if is_lock(v)]

    if not argv or argv[0] in ("-h", "--help"):
        print("当前 default=%s" % default)
        for name in names:
            v = locks[name]
            print("  %-10s %s  %s  %s" % (name, v["md5"][:12], v.get("size", "?"), v["file"]))
        print("\n用法: python scripts/set_face_lock.py --check|%s" % "|".join(names))
        return 0

    arg = argv[0]
    cur = md5(TARGET) if TARGET.exists() else "-"

    if arg == "--check":
        want = locks[default]["md5"]
        ok = cur == want
        print("现场 assets/host_look.jpg md5 = %s" % cur)
        print("ASSETS-LOCK default(%s) md5 = %s" % (default, want))
        print("结果：%s" % ("一致 ✓" if ok else "不一致 ✗（跑 set_face_lock.py %s 校正）" % default))
        return 0 if ok else 1

    if arg not in names:
        print("未知锁名 %r；可选：%s" % (arg, ", ".join(names)))
        return 2

    src = ROOT / locks[arg]["file"]
    if not src.exists():
        print("源文件不存在：%s" % src)
        return 2
    expect = locks[arg]["md5"]
    if md5(src) != expect:
        print("源文件 md5 对不上（%s != %s），拒绝切换" % (md5(src), expect))
        return 2

    if TARGET.exists():
        ARCHIVE.mkdir(parents=True, exist_ok=True)
        shutil.copy2(TARGET, ARCHIVE / ("host_look-%s.jpg" % cur[:12]))
    shutil.copy2(src, TARGET)
    now = md5(TARGET)
    data["face_lock"]["default"] = arg
    LOCK.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("已切到 %s：%s" % (arg, expect))
    print("现场 md5 = %s %s" % (now, "✓" if now == expect else "✗"))
    print("旧图已存入 %s" % ARCHIVE)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
