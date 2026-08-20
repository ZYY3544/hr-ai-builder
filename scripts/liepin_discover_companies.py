#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""发现「在招 AI×HR 岗位」的公司，产出 公司名 → 猎聘公司 id 名录。

分工（两步，别混）：
  ① 本脚本＝**发现**。顺着职位页的「猜你喜欢」走，把出现过的公司和它的猎聘 id 收集起来。
     推荐是算法给的，天然偏向同类岗位，用来找「还有谁在招这种岗」正合适。
  ② scan_liepin_company.py＝**完备**。拿到公司 id 之后，按公司翻完整在招列表，
     不漏、且下次能重跑对比出新增/下架。

为什么不用猎聘的公司搜索：/companys/?key= 是 JS 渲染的，匿名请求拿到的是一份
固定占位列表——搜「美团」「腾讯」「阿里巴巴」返回结果一模一样（全是昆山某自动化公司）。
只看「有返回」会被骗，必须看返回内容是不是随关键词变。

礼貌抓取：串行、每次请求间隔 2 秒、页数设上限。

用法：
    python3 scripts/liepin_discover_companies.py <种子职位链接> --max 80
"""
import argparse
import html
import json
import re
import sys
import time

import requests

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
GAP = 2.0

T_HR = re.compile(r"HR|人力|人事|人才|招聘|组织|薪酬|绩效|员工|培训|干部|"
                  r"HRBP|HRIS|SSC|COE|假勤|考勤|雇主|职级|背调|劳动关系")
# AI 要词边界，否则英文里的 chain / sustain / email 全是假阳性
T_AI = re.compile(r"(?<![A-Za-z])AI(?![A-Za-z])|人工智能|大模型|智能体|Agent|数字化|智能", re.I)


def company_of(page: str):
    """从职位页取 (公司 id, 公司名)。"""
    cid = None
    m = re.search(r'"compId"\s*:\s*"?(\d+)"?', page)
    if m:
        cid = m.group(1)
    else:
        m = re.search(r"/company/(\d+)/", page)
        cid = m.group(1) if m else None
    name = ""
    mt = re.search(r"<title>(.*?)</title>", page, re.S)
    if mt:
        mm = re.search(r"招聘】-(.+?)招聘信息", html.unescape(mt.group(1)))
        if mm:
            tail = mm.group(1).strip()
            mc = re.search(r"【\s*(\S+?)\s", html.unescape(mt.group(1)))
            city = mc.group(1).split("-")[0] if mc else ""
            name = re.sub(re.escape(city) + r"$", "", tail).strip() or tail
    return cid, name


def title_of(page: str) -> str:
    mt = re.search(r"<title>(.*?)</title>", page, re.S)
    if not mt:
        return ""
    mm = re.search(r"【\s*\S+?\s+(.+?)招聘】", html.unescape(mt.group(1)))
    return mm.group(1).strip() if mm else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("seed")
    ap.add_argument("--max", type=int, default=80)
    ap.add_argument("--json", help="把公司名录写到这里")
    a = ap.parse_args()

    m = re.search(r"/job/(\d+)\.shtml", a.seed)
    if not m:
        sys.exit("种子应为 https://www.liepin.com/job/<数字>.shtml")

    s = requests.Session()
    s.headers["User-Agent"] = UA
    queue, seen, comps = [m.group(1)], set(), {}

    while queue and len(seen) < a.max:
        jid = queue.pop(0)
        if jid in seen:
            continue
        seen.add(jid)
        try:
            r = s.get(f"https://www.liepin.com/job/{jid}.shtml", timeout=25)
        except Exception:
            continue
        time.sleep(GAP)
        if r.status_code != 200:
            continue
        page = r.text
        for nid in re.findall(r"/job/(\d+)\.shtml", page):
            if nid not in seen and len(queue) < a.max * 3:
                queue.append(nid)

        t = title_of(page)
        if not (T_HR.search(t) or T_AI.search(t)):
            continue                       # 只统计像 AI×HR 的岗位所属公司
        cid, name = company_of(page)
        if not cid:
            continue
        e = comps.setdefault(cid, {"id": cid, "name": name or "?", "n": 0, "样例": []})
        e["n"] += 1
        if len(e["样例"]) < 3:
            e["样例"].append(t[:26])
        if name and e["name"] == "?":
            e["name"] = name

    rows = sorted(comps.values(), key=lambda x: -x["n"])
    print(f"\n扫了 {len(seen)} 个职位页，发现 {len(rows)} 家公司在招 AI×HR 类岗位：\n")
    print(f'{"公司 id":<10}{"公司名":<22}{"命中":<5}样例职位')
    for r_ in rows:
        print(f'{r_["id"]:<10}{r_["name"][:20]:<22}{r_["n"]:<5}{" / ".join(r_["样例"])}')
    print(f"\n下一步：对每个 id 跑 "
          f"python3 scripts/scan_liepin_company.py <id> --pages 30 --json out.json")
    if a.json:
        json.dump(rows, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"名录已写入 {a.json}")


if __name__ == "__main__":
    main()
