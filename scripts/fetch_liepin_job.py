#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""取单条猎聘职位的官方 JD 原文，打印可直接入库的字段。

解析逻辑不在这里——统一放在 crawl_liepin_hr_ai.py，这里只是薄壳。
（第一版把同一套抽取正则抄了两份，结果修了爬虫那份、漏了这份，
  两边行为悄悄分叉。同一件事只留一份实现。）

用法：
    python3 scripts/fetch_liepin_job.py https://www.liepin.com/job/1983987041.shtml
"""
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from crawl_liepin_hr_ai import UA, parse   # noqa: E402


def main():
    if len(sys.argv) < 2:
        sys.exit("用法：python3 scripts/fetch_liepin_job.py <猎聘职位链接>")
    url = sys.argv[1]
    r = requests.get(url, headers={"User-Agent": UA}, timeout=25, allow_redirects=True)
    r.raise_for_status()
    d = parse(r.text, url)
    if not d["desc"]:
        sys.exit("没抠到 JD 正文——猎聘可能又换了模板，先人工看一眼页面再改 START/SPLIT/END。")

    print(f"公司：{d['company'] or '?'} · 标题：{d['title'] or '?'} · 薪资：{d['salary'] or '未标'}")
    print(f"JD 长度：{len(d['full'])} 字 · 指纹 {d['sha']}")
    print("\n" + "─" * 60)
    print(d["full"])
    print("─" * 60)
    print(f'\n入库时填：  "jd_kind": "full", "jd_sha": "{d["sha"]}", "source": "liepin",')
    print(f'            "apply_url": "{url}",')


if __name__ == "__main__":
    main()
