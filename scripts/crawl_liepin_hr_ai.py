#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""顺着猎聘「猜你喜欢」滚雪球，找 AI×HR 岗位。

为什么不扫企业官网：招聘方**不一定在官网维护**这些岗位。实测京东——
猎聘上有「AI型组织人才发展专家」「HR AI产品专家」「AI产品经理(职能系统方向)」，
官网社招列表一个都没有；官网最接近的「组织与人才发展岗」JD 里 AI 一个字不提。
只扫官网会系统性漏掉，并且**低估**招聘方对 AI 的真实要求。

为什么不用猎聘搜索：搜索结果是 JS 渲染的，匿名 curl 拿不到；
而用用户自己的登录态跑自动化有被风控的风险，不值得。
职位详情页反而是匿名可读的，且每页底部「猜你喜欢」带 20 个同类岗位链接——
以一条已知岗位为种子顺着爬，既拿得到原文，又能不断发现新岗位。

礼貌抓取：串行、每次请求间隔 2 秒、总量设上限。这是别人的服务器，不是我们的。

用法：
    python3 scripts/crawl_liepin_hr_ai.py <种子职位链接> [--max 60]
输出：候选岗位清单（公司/标题/薪资/链接/AI 命中位置），供人逐条读后决定收不收。
"""
import argparse
import hashlib
import html
import re
import sys
import time

import requests

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
GAP = 2.0                     # 每次请求间隔（秒）

HR = re.compile(r"HR|人力|人事|人才|招聘|组织|薪酬|绩效|员工|培训|学发|干部|HRBP|HRIS|假勤|考勤")
# ⚠️ AI 必须加词边界：re.I 下的裸 AI 会命中英文单词内部的 ai
#    （chain / sustain / main / email / available…），英文 JD 会整片假阳性。
#    实测京东「HRBP-常驻英国」就是这么被误判成 AI 岗的。
AI = re.compile(r"(?<![A-Za-z])AI(?![A-Za-z])|人工智能|大模型|智能体|Agent|LLM|GPT|Vibe|Prompt|RAG|MCP|数字化", re.I)
# 强信号：真要求任职者动手用 AI，而不是「对 AI 有热情」
STRONG = re.compile(r"(?<![A-Za-z])AI(?![A-Za-z])|人工智能|大模型|智能体|Agent|LLM|Vibe\s?Coding|Prompt|RAG|MCP", re.I)

# 猎聘有两套 JD 模板，都要认：
#   A：「职位描述: … 职位要求: …」
#   B：「职位介绍 … 要求 … 其他信息」
# 只写 A 的后果：B 版页面正文抠成空 → 被当成「没有 JD」静默丢掉。
# 实测一次爬 35 页只命中 2 条，就是这么丢的——不是没岗位，是读成了空白。
START = r"职位描述|职位介绍|岗位职责|职位职责|工作职责"
SPLIT = r"职位要求|任职要求|岗位要求|任职资格|要求"
END = (r"其他信息|公司简介|公司介绍|公司信息|企业信息|工作地址|职位福利|"
       r"猎聘温馨提示|猜你喜欢|查看全部|举报|语言要求|行业要求")


def visible(page: str) -> str:
    b = re.sub(r"<script.*?</script>", " ", page, flags=re.S)
    b = re.sub(r"<style.*?</style>", " ", b, flags=re.S)
    b = re.sub(r"<[^>]+>", " ", b)
    return html.unescape(re.sub(r"\s+", " ", b)).strip()


def parse(page: str, url: str) -> dict:
    t = visible(page)
    m = re.search(r"(?:" + START + r")[:：]?\s*(.*?)\s*(?:" + END + r"|$)", t, re.S)
    jd = m.group(1).strip() if m else ""
    parts = re.split(r"\s*(?:" + SPLIT + r")[:：]?\s+", jd, maxsplit=1)
    desc, req = parts[0].strip(), (parts[1].strip() if len(parts) > 1 else "")
    full = "职位描述\n" + desc + ("\n\n职位要求\n" + req if req else "")

    # 页面标题形如：【北京 人才系统AI产品经理-管理研究院招聘】-字节跳动北京招聘信息-猎聘
    # 【城市 职位名招聘】-公司名+城市+招聘信息-猎聘。城市在两处都出现，用它当锚点把公司名切出来。
    title = company = city = ""
    mt = re.search(r"<title>(.*?)</title>", page, re.S)
    if mt:
        raw = html.unescape(mt.group(1)).strip()
        mm = re.search(r"【\s*(\S+?)\s+(.+?)招聘】-(.+?)招聘信息", raw)
        if mm:
            city, title, tail = (x.strip() for x in mm.groups())
            # tail = 公司名 + 城市（城市可能是「北京」而 city 是「北京-通州区」，取主城名去尾）
            company = re.sub(re.escape(city.split("-")[0]) + r"$", "", tail).strip() or tail
    ms = re.search(r"(\d+\-\d+k(?:·\d+薪)?)", t)
    return {"url": url, "title": title, "company": company, "city": city,
            "salary": ms.group(1) if ms else "",
            "desc": desc, "req": req, "full": full,
            "sha": hashlib.sha256(full.encode()).hexdigest()[:16] if desc else ""}


def rec_ids(page: str) -> list:
    return list(dict.fromkeys(re.findall(r"/job/(\d+)\.shtml", page)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("seed")
    ap.add_argument("--max", type=int, default=60, help="最多抓多少个职位页")
    a = ap.parse_args()

    seed = re.search(r"/job/(\d+)\.shtml", a.seed)
    if not seed:
        sys.exit("种子链接格式应为 https://www.liepin.com/job/<数字>.shtml")

    queue, seen, hits = [seed.group(1)], set(), []
    s = requests.Session()
    s.headers["User-Agent"] = UA

    while queue and len(seen) < a.max:
        jid = queue.pop(0)
        if jid in seen:
            continue
        seen.add(jid)
        url = f"https://www.liepin.com/job/{jid}.shtml"
        try:
            r = s.get(url, timeout=25)
            if r.status_code != 200:
                continue
            page = r.text
        except Exception as e:
            print(f"  跳过 {jid}: {e}", file=sys.stderr)
            continue
        time.sleep(GAP)

        d = parse(page, url)
        for nid in rec_ids(page):
            if nid not in seen and len(seen) + len(queue) < a.max * 3:
                queue.append(nid)

        label = (d["title"] or "") + " " + (d["company"] or "")
        if not d["desc"]:
            continue
        if not HR.search(label + d["full"]):
            continue
        where = []
        if STRONG.search(d["title"] or ""):
            where.append("标题")
        if STRONG.search(d["desc"]):
            where.append("职责")
        if STRONG.search(d["req"]):
            where.append("要求")
        if not where:
            continue
        d["where"] = "+".join(where)
        hits.append(d)
        print(f"[{len(hits):2d}] {d['company'][:12]:14s} {d['title'][:28]:30s} "
              f"{d['city'][:8]:10s} {d['salary']:12s} AI在{d['where']:8s} "
              f"{len(d['full']):4d}字 {d['sha']}")

    print(f"\n抓了 {len(seen)} 个职位页，HR×AI 候选 {len(hits)} 条。"
          f"\n下一步：逐条读 JD 判是不是真要求（只要求『对AI有热情』/ 给AI业务做HR / 招AI人才 → 剔）。")
    for h in hits:
        print("\n" + "=" * 70)
        print(f"{h['company']} · {h['title']} · {h['city']} · {h['salary']}\n{h['url']}\nsha={h['sha']}")
        print("-" * 70)
        print(h["full"])


if __name__ == "__main__":
    main()
