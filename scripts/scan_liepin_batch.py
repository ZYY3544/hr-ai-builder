#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按公司名录批量扫猎聘，把所有 AI×HR 候选汇总到一个 json。

跑得久（几十家公司 × 每家几十次请求 × 2 秒间隔），所以：
  · **每家扫完就落盘**——中途断了不用从头再来，重跑会跳过已完成的公司
  · 单家失败不影响整体，记进 errors 继续往下走

输入：liepin_discover_companies.py 产出的公司名录 json
输出：候选岗位 json（含公司/标题/城市/薪资/链接/JD 全文/指纹），供人逐条读后入库

用法：
    python3 scripts/scan_liepin_batch.py companies.json --out cands.json
    python3 scripts/scan_liepin_batch.py companies.json --out cands.json --skip 字节跳动 京东
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import requests                                    # noqa: E402
from scan_liepin_company import (UA, C_AI, C_HR, T_AI, T_HR,      # noqa: E402
                                 listing, parse_job)


def scan_one(s, cid: str, pages: int) -> list:
    items = listing(s, cid, pages)
    cand = [(i, t) for i, t in items if T_HR.search(t) or T_AI.search(t)]
    hits = []
    for jid, t in cand:
        url = f"https://www.liepin.com/job/{jid}.shtml"
        try:
            r = s.get(url, timeout=25)
        except Exception:
            continue
        time.sleep(2.0)
        if r.status_code != 200:
            continue
        d = parse_job(r.text, url)
        if not d["desc"] or not C_HR.search(d["full"] + t):
            continue
        where = [n for n, txt in (("标题", d["title"]), ("职责", d["desc"]), ("要求", d["req"]))
                 if C_AI.search(txt or "")]
        if not where:
            continue
        d["where"] = "+".join(where)
        hits.append(d)
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("registry")
    ap.add_argument("--out", required=True)
    ap.add_argument("--pages", type=int, default=25)
    ap.add_argument("--skip", nargs="*", default=[])
    a = ap.parse_args()

    comps = json.load(open(a.registry, encoding="utf-8"))
    state = {"done": [], "hits": [], "errors": []}
    if os.path.exists(a.out):                       # 断点续跑
        state = json.load(open(a.out, encoding="utf-8"))
        print(f"接着上次跑：已完成 {len(state['done'])} 家，已有候选 {len(state['hits'])} 条")

    s = requests.Session()
    s.headers["User-Agent"] = UA

    for i, c in enumerate(comps, 1):
        name, cid = c["name"], c["id"]
        if cid in state["done"] or name in a.skip:
            continue
        print(f"\n[{i}/{len(comps)}] {name}（{cid}）")
        try:
            hits = scan_one(s, cid, a.pages)
        except Exception as e:
            print(f"  失败：{e}")
            state["errors"].append({"id": cid, "name": name, "err": str(e)})
            continue
        for h in hits:
            h["_company_guess"] = name
            print(f"     ✓ {h['title'][:30]:32s} {h['city'][:9]:11s} "
                  f"{h['salary']:12s} AI在{h['where']}")
        state["hits"].extend(hits)
        state["done"].append(cid)
        json.dump(state, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"  本家 {len(hits)} 条 · 累计 {len(state['hits'])} 条（已落盘）")

    print(f"\n完成 {len(state['done'])} 家，候选共 {len(state['hits'])} 条，失败 {len(state['errors'])} 家。")
    print("下一步：逐条读 JD 判收不收（四条排除规则见 scan_liepin_company.py 注释）。")


if __name__ == "__main__":
    main()
