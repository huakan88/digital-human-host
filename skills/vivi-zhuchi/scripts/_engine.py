#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vivi主持 · 共用 hk-zhuchi 的引擎。

引擎只有一份（`E:\\dsh-agents\\skills\\hk-zhuchi\\scripts`），
「主持」预设只带 persona / 配置 / 素材，通过 HK_PRESET 指回本目录。
所以加第三个主持（梓梓 / V2.0 / 真人克隆…）只要再开一个预设目录。
"""
import os
import pathlib
import runpy
import sys

PRESET = pathlib.Path(__file__).resolve().parent.parent
ENGINE = pathlib.Path(r"E:\dsh-agents\skills\hk-zhuchi\scripts")
os.environ.setdefault("HK_PRESET", str(PRESET))
sys.path.insert(0, str(ENGINE))


def run(entry):
    sys.argv[0] = str(ENGINE / entry)
    runpy.run_path(str(ENGINE / entry), run_name="__main__")
