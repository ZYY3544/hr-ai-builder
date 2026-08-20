#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按公司扫猎聘，找 AI×HR 岗位。

为什么按公司扫，而不是顺着「猜你喜欢」滚雪球：
  · **不漏**——推荐是算法给的，没有覆盖保证；公司页是这家公司的完整在招列表。
  · **能刷新**——每隔一段时间对同一家再跑一次，就能对出新增和下架。
    滚雪球每次走的路径都不一样，两次结果没法比。

为什么不扫企业自己的官网：招聘方不一定在官网维护这些岗位。实测京东——
猎聘上有「AI型组织人才发展专家」「HR AI产品专家」「AI产品经理(职能系统方向)」，
官网社招列表一个都没有，官网最接近的「组织与人才发展岗」JD 里 AI 一个字不提。

两级筛，省请求也省对方服务器：
  ① 列表页只有标题 → 先按「标题像 HR 或像 AI」预筛，其余不再点开
  ② 命中的才抓职位页 → 要求 HR 上下文 **且** JD 里有 AI 强信号
最终收不收仍要人逐条读 JD（四条排除规则见 README 注释），机器只负责把候选端上来。

礼貌抓取：串行、每次请求间隔 2 秒、页数设上限。这是别人的服务器。

用法：
    python3 scripts/scan_liepin_company.py 1663745            # 用猎聘公司 id
    python3 scripts/scan_liepin_company.py --from-job <职位链接>  # 从任一职位反查公司 id
    python3 scripts/scan_liepin_company.py 1663745 --pages 40 --json out.json
"""
import argparse
import hashlib
import html
import json
import re
import sys
import time

import requests

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
GAP = 2.0

# 标题预筛：像 HR 的，或像 AI 的（AI 岗常见标题如「AI产品经理（职能系统方向）」
# 不含任何 HR 字样，但正文讲的是人力系统——只按 HR 词预筛会把它漏掉）
T_HR = re.compile(r"HR|人力|人事|人才|招聘|组织|薪酬|绩效|员工|培训|学发|干部|"
                  r"HRBP|HRIS|SSC|COE|假勤|考勤|雇主|职级|背调|入职|劳动关系")
# ⚠️ AI 必须加词边界：re.I 下的裸 AI 会命中英文单词内部的 ai
#    （chain / sustain / main / email / available…），英文 JD 会整片假阳性。
#    实测京东「HRBP-常驻英国」就是这么被误判成 AI 岗的。
T_AI = re.compile(r"(?<![A-Za-z])AI(?![A-Za-z])|人工智能|大模型|智能体|Agent|数字化|智能", re.I)
# 正文里的 HR 上下文。⚠️ 不能用「出现过任一 HR 词」当判据——技术岗的长 JD 里
# 顺带提一次「组织」「培训」就会被误收（实测锐捷 32 条候选几乎全是 AI 算法/架构岗，
# 每条正文只命中 1 个 HR 词）。改成：**标题里有 HR 词，或正文里至少命中 3 个不同 HR 词**。
# 校准依据（真/假阳性各两例，见 is_hr_job 的 doctest）：
#   假：AI算法负责人（标题无 · 正文仅「组织」）  假：AI产品专家（标题无 · 正文仅「HR」）
#   真：组织发展专家(AI变革方向)（标题有「组织」） 真：AI产品经理(职能系统方向)（正文 6 个）
HR_WORDS = ("HR", "人力", "人事", "人才", "招聘", "组织", "薪酬", "绩效",
            "员工", "培训", "干部", "入转调离", "花名册", "职级", "考勤", "假勤")
HR_MIN_DISTINCT = 3


def is_hr_job(title: str, body: str) -> bool:
    """这份 JD 讲的是不是 HR 的活。

    >>> is_hr_job("AI算法负责人", "带领AI团队…推动组织能力建设")
    False
    >>> is_hr_job("组织发展专家（AI变革方向）", "…")
    True
    >>> is_hr_job("AI产品经理（职能系统方向）", "薪酬 考勤 招聘 绩效 人力 员工")
    True
    """
    if any(w in (title or "") for w in HR_WORDS):
        return True
    return len({w for w in HR_WORDS if w in (body or "")}) >= HR_MIN_DISTINCT


C_HR = re.compile("|".join(HR_WORDS))     # 保留给粗筛用
C_AI = re.compile(r"(?<![A-Za-z])AI(?![A-Za-z])|人工智能|大模型|智能体|Agent|LLM|Vibe\s?Coding|Prompt|RAG|MCP", re.I)

START = r"职位描述|职位介绍|岗位职责|职位职责|工作职责"
SPLIT = r"职位要求|任职要求|岗位要求|任职资格|要求"
END = (r"其他信息|公司简介|公司介绍|公司信息|企业信息|工作地址|职位福利|"
       r"猎聘温馨提示|猜你喜欢|查看全部|举报|语言要求|行业要求")


def visible(page: str) -> str:
    b = re.sub(r"<script.*?</script>", " ", page, flags=re.S)
    b = re.sub(r"<style.*?</style>", " ", b, flags=re.S)
    b = re.sub(r"<[^>]+>", " ", b)
    return html.unescape(re.sub(r"\s+", " ", b)).strip()


def parse_job(page: str, url: str) -> dict:
    """猎聘有两套 JD 模板都要认（A：职位描述/职位要求；B：职位介绍/要求）。
    只认一套的后果是另一套被读成空白然后静默丢掉——实测能让命中数差 12 倍。"""
    t = visible(page)
    m = re.search(r"(?:" + START + r")[:：]?\s*(.*?)\s*(?:" + END + r"|$)", t, re.S)
    jd = m.group(1).strip() if m else ""
    parts = re.split(r"\s*(?:" + SPLIT + r")[:：]?\s+", jd, maxsplit=1)
    desc, req = parts[0].strip(), (parts[1].strip() if len(parts) > 1 else "")
    full = "职位描述\n" + desc + ("\n\n职位要求\n" + req if req else "")

    title = company = city = ""
    mt = re.search(r"<title>(.*?)</title>", page, re.S)
    if mt:
        mm = re.search(r"【\s*(\S+?)\s+(.+?)招聘】-(.+?)招聘信息",
                       html.unescape(mt.group(1)).strip())
        if mm:
            city, title, tail = (x.strip() for x in mm.groups())
            company = re.sub(re.escape(city.split("-")[0]) + r"$", "", tail).strip() or tail
    ms = re.search(r"(\d+\-\d+k(?:·\d+薪)?)", t)
    return {"url": url, "title": title, "company": company, "city": city,
            "salary": ms.group(1) if ms else "", "desc": desc, "req": req, "full": full,
            "sha": hashlib.sha256(full.encode()).hexdigest()[:16] if desc else ""}


class FetchFailed(Exception):
    """取数失败——**不是**「这家公司没岗位」。

    两者必须分开：把失败当成 0，扫描器会安安静静地报出一份漂亮的空结果。
    实测批量跑到第 7 家起被限流，41 家全报 0 命中，差点当真数用。
    """


def listing(s, comp_id: str, pages: int) -> list:
    """翻公司在招列表，返回 (职位id, 标题)。翻到没有新 id 就停。

    第 1 页取不到 → 抛 FetchFailed（多半是被限流），交给调用方退避重试；
    第 1 页有数据、后面翻空 → 正常结束。"""
    out, seen = [], set()
    for pn in range(1, pages + 1):
        url = f"https://www.liepin.com/company-jobs/{comp_id}/" + (f"pn{pn}/" if pn > 1 else "")
        try:
            r = s.get(url, timeout=25)
        except Exception as e:
            if pn == 1:
                raise FetchFailed(f"第 1 页请求异常：{e}")
            print(f"  列表第 {pn} 页失败：{e}", file=sys.stderr)
            break
        if r.status_code != 200:
            if pn == 1:
                raise FetchFailed(f"第 1 页 HTTP {r.status_code}")
            break
        pairs = re.findall(r'href="https://www\.liepin\.com/job/(\d+)\.shtml"[^>]*>(.*?)</a>',
                           r.text, re.S)
        fresh = 0
        for jid, raw in pairs:
            if jid in seen:
                continue
            seen.add(jid)
            t = re.sub(r"<[^>]+>", "", html.unescape(raw)).strip()
            if t:
                out.append((jid, t))
                fresh += 1
        print(f"  第 {pn} 页：新增 {fresh} 个（累计 {len(out)}）")
        if pn == 1 and fresh == 0:
            raise FetchFailed("第 1 页一个职位链接都没有——页面结构变了或被限流")
        if fresh == 0:
            break
        time.sleep(GAP)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("comp_id", nargs="?", help="猎聘公司 id，如京东 1663745")
    ap.add_argument("--from-job", help="给一条该公司的猎聘职位链接，自动反查公司 id")
    ap.add_argument("--pages", type=int, default=30, help="最多翻多少页列表")
    ap.add_argument("--json", help="把候选写到 json，供入库脚本读")
    a = ap.parse_args()

    s = requests.Session()
    s.headers["User-Agent"] = UA

    comp_id = a.comp_id
    if a.from_job:
        p = s.get(a.from_job, timeout=25).text
        m = re.search(r'"compId"\s*:\s*"?(\d+)"?', p) or \
            re.search(r"/company/(\d+)/", p)
        if not m:
            sys.exit("没从这条职位里找到公司 id")
        comp_id = m.group(1)
        print(f"公司 id = {comp_id}")
    if not comp_id:
        sys.exit("要么给公司 id，要么给 --from-job")

    print(f"翻 {comp_id} 的在招列表…")
    items = listing(s, comp_id, a.pages)
    cand = [(i, t) for i, t in items if T_HR.search(t) or T_AI.search(t)]
    print(f"\n共 {len(items)} 个在招岗位，标题像 HR 或像 AI 的 {len(cand)} 个，逐个看正文…\n")

    hits = []
    for jid, t in cand:
        url = f"https://www.liepin.com/job/{jid}.shtml"
        try:
            r = s.get(url, timeout=25)
        except Exception as e:
            print(f"  跳过 {jid}：{e}", file=sys.stderr)
            continue
        time.sleep(GAP)
        if r.status_code != 200:
            continue
        d = parse_job(r.text, url)
        if not d["desc"]:
            print(f"  ⚠️ {jid} 正文抠不出来（模板又变了？）：{t[:24]}", file=sys.stderr)
            continue
        if not is_hr_job(d["title"] or t, d["full"]):
            continue
        where = [n for n, txt in (("标题", d["title"]), ("职责", d["desc"]), ("要求", d["req"]))
                 if C_AI.search(txt or "")]
        if not where:
            continue
        d["where"] = "+".join(where)
        hits.append(d)
        print(f"[{len(hits):2d}] {d['title'][:30]:32s} {d['city'][:9]:11s} "
              f"{d['salary']:12s} AI在{d['where']:9s} {len(d['full']):4d}字 {d['sha']}")

    print(f"\n候选 {len(hits)} 条。逐条读 JD 后再定收不收——"
          f"只要求『对AI有热情』/ AI 只是并列加分项 / 给 AI 业务做 HR / 招 AI 人才，都剔。")
    if a.json:
        json.dump(hits, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"已写入 {a.json}")
    for h in hits:
        print("\n" + "=" * 70)
        print(f"{h['company']} · {h['title']} · {h['city']} · {h['salary']}\n{h['url']}\nsha={h['sha']}")
        print("-" * 70)
        print(h["full"])


if __name__ == "__main__":
    main()
