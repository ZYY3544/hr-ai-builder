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
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import requests                                    # noqa: E402
from scan_liepin_company import (UA, C_AI, C_HR, FetchFailed, T_AI, T_HR,   # noqa: E402
                                 is_hr_job, listing, parse_job)


def company_of(page: str):
    """从职位页取公司 id —— 扫的过程中顺手把新公司收进来。"""
    m = re.search(r'"compId"\s*:\s*"?(\d+)"?', page) or re.search(r"/company/(\d+)/", page)
    return m.group(1) if m else None


def scan_one(s, cid: str, pages: int, found: dict = None) -> list:
    """扫一家公司。found 非空时，把沿途职位页上出现的**其他**公司 id 也记下来——
    公司发现不能只靠一个种子滚一圈：那样推荐算法给什么就只看见什么，
    阿里/腾讯/华为/快手这些压根不会进视野（第一轮 47 家就是这么来的）。"""
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
        if found is not None:
            ncid = company_of(r.text)
            if ncid and ncid != cid:
                found.setdefault(ncid, parse_job(r.text, url).get("company") or "?")
        d = parse_job(r.text, url)
        if not d["desc"] or not is_hr_job(d["title"] or t, d["full"]):
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

    found = {}                       # 沿途新发现的公司：id → 名
    state.setdefault("discovered", [])
    i = 0
    while i < len(comps):
        c = comps[i]; i += 1
        name, cid = c["name"], c["id"]
        if cid in state["done"] or name in a.skip:
            continue
        print(f"\n[{i}/{len(comps)}] {name}（{cid}）")
        # 取数失败要退避重试，不能当成「这家没岗位」。猎聘连着扫十来家就开始限流，
        # 第一版没区分这两者，41 家静静地报了 0 命中，差点当真数用。
        hits, err = None, ""
        for attempt, backoff in enumerate((0, 60, 180), 1):
            if backoff:
                print(f"  等 {backoff}s 后重试（第 {attempt} 次）…")
                time.sleep(backoff)
            try:
                hits = scan_one(s, cid, a.pages, found)
                break
            except FetchFailed as e:
                err = str(e)
            except Exception as e:
                err = str(e)
                break
        if hits is None:
            print(f"  取数失败（非「无岗位」）：{err}")
            state["errors"].append({"id": cid, "name": name, "err": err})
            json.dump(state, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            continue
        for h in hits:
            # ⚠️ 公司页里混着别家公司的推荐职位（实测用友名下混进美团/字节/嘉楠，
            #    联想名下混进字节）。归属一律以**职位页自报的公司名**为准，
            #    名录名只留作「从哪一次扫描来的」线索，不能当归属用。
            h["_scanned_under"] = name
            h["company"] = h.get("company") or name
            print(f"     ✓ {h['company'][:10]:12s} {h['title'][:28]:30s} "
                  f"{h['city'][:9]:11s} {h['salary']:12s} AI在{h['where']}")
        state["hits"].extend(hits)
        state["done"].append(cid)
        json.dump(state, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"  本家 {len(hits)} 条 · 累计 {len(state['hits'])} 条（已落盘）")
        # 沿途遇到的其他公司只记录、**不自动入队**——公司名单必须是人定的。
        # 自动入队等于又变回滚雪球：名单由算法决定，阿里/腾讯/华为这类不在推荐圈里的
        # 永远进不来，而且两次跑的路径不同，没法定期刷新对比。
        known = {x["id"] for x in comps}
        for ncid, nname in list(found.items()):
            if ncid not in known:
                state["discovered"].append({"id": ncid, "name": nname})
        found.clear()
        if state["discovered"]:
            print(f"  （沿途记下 {len(state['discovered'])} 家公司备选，需人工确认后才加进名单）")
        time.sleep(8)          # 公司之间多喘一口，降低被限流概率

    print(f"\n完成 {len(state['done'])} 家，候选共 {len(state['hits'])} 条，失败 {len(state['errors'])} 家。")
    print("下一步：逐条读 JD 判收不收（四条排除规则见 scan_liepin_company.py 注释）。")


if __name__ == "__main__":
    main()
