#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""岗位 JD 完整性校验 —— 证明站上的 JD 跟招聘方原文逐字相同。

为什么需要它（以及为什么它不该存在太久）：
JD 是引用来的，引用就必须能逐字对上原文。第一版把「理解 LLM/Agent/RAG/Prompt
Engineering 等概念」那一整条要求删掉了，页面上却仍标着「JD 摘录」，读者无从察觉。
**核对是程序的活，不能让人去官网一条条比。**

真正的根治是把「人手转录」这一跳从链路里去掉（接口直取直写）。字节的接口带反爬，
命令行拿不到，所以这里退一步：抓取时在浏览器里算好官方原文的 SHA-256，
把哈希钉进岗位记录（jd_sha）。之后任何一次改动，只要 jd_text 变了一个字，
本脚本立刻失败——转录是否忠实，从「相信我」变成「可验证」。

⚠️ 哈希只保证「跟当初抓下来的原文一致」，不保证「跟此刻官网一致」。
   招聘方改 JD、下架岗位属于**漂移**，要用 --drift 走浏览器重新取（见文末）。

检查项：
  ① 原文未被改动 —— sha256(jd_text)[:16] == jd_sha
  ② 高亮可锚     —— 每个 hl 关键词是 jd_text 的精确子串（否则前端静默不高亮）
  ③ 能力 id 有效 —— must/plus/hl 里的 id 都在 TERMS 里

阴性对照：正式检查前先注入三种已知错误，确认全都抓得住。
抓不住就直接 FAIL、不出报告——抓不到错的校验器比没有更危险。

用法：
    python3 scripts/verify_jobs_jd.py           # 检查（含阴性对照）
    python3 scripts/verify_jobs_jd.py --quiet   # 只报异常，给 CI / 定时任务用
"""
import ast
import copy
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(ROOT, "backend", "main.py")


def sha16(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()[:16]


def load_block(src: str, name: str):
    m = re.search(r"^" + name + r" = \[", src, re.M)
    i, depth = m.end(), 1
    while depth:
        c = src[i]
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
        i += 1
    return ast.literal_eval(src[m.end() - 1:i])


def check(jobs, term_ids) -> list:
    """返回问题清单；空清单＝全过。"""
    out = []
    for job in jobs:
        jid, jd = job["id"], job.get("jd_text", "")
        want = job.get("jd_sha")
        if want:                                        # ① 原文未被改动
            got = sha16(jd)
            if got != want:
                out.append(f"[JD 被改动] {jid} · 当前 {got} ≠ 抓取时 {want}"
                           f"（要么误改了，要么官网更新了——后者请重跑导入脚本）")
        for k in (job.get("hl") or {}):                  # ② 高亮可锚
            if k not in jd:
                out.append(f"[高亮锚不住] {jid} · 「{k[:26]}」不是 JD 原文的子串，前端会静默不高亮")
        for k in ("must", "plus"):                       # ③ 能力 id 有效
            for t in job.get(k, []):
                if t not in term_ids:
                    out.append(f"[未知能力 id] {jid} · {k} 里的 {t} 不在 TERMS 中")
        for t in (job.get("hl") or {}).values():
            if t not in term_ids:
                out.append(f"[未知能力 id] {jid} · hl 指向的 {t} 不在 TERMS 中")
    return out


def negative_control(jobs, term_ids) -> bool:
    """注入已知错误，确认检查器抓得住。"""
    tgt = next(j for j in jobs if j.get("jd_sha"))
    cases = []

    a = copy.deepcopy(jobs)                              # ① 删掉一整条要求
    ja = next(j for j in a if j["id"] == tgt["id"])
    lines = ja["jd_text"].split("\n")
    del lines[next(i for i, l in enumerate(lines) if len(l) > 20)]
    ja["jd_text"] = "\n".join(lines)
    cases.append(("删掉一整条要求", a))

    b = copy.deepcopy(jobs)                              # ② 只改一个字
    jb = next(j for j in b if j["id"] == tgt["id"])
    i = next(k for k, ch in enumerate(jb["jd_text"]) if ch not in "\n 、，。；：")
    jb["jd_text"] = jb["jd_text"][:i] + "※" + jb["jd_text"][i + 1:]
    cases.append(("只改一个字", b))

    c = copy.deepcopy(jobs)                              # ③ 编一个原文没有的高亮词
    jc = next(j for j in c if j["id"] == tgt["id"])
    jc["hl"] = {**jc["hl"], "这句话官网压根没写过": "vibecoding"}
    cases.append(("编造高亮词", c))

    ok = True
    for name, mutated in cases:
        caught = bool(check(mutated, term_ids))
        print(f"  阴性对照「{name}」：{'✓ 抓住' if caught else '✗ 没抓住'}")
        ok &= caught
    return ok


def main():
    quiet = "--quiet" in sys.argv
    src = open(MAIN, encoding="utf-8").read()
    jobs = load_block(src, "JOBS")
    term_ids = {t["id"] for t in load_block(src, "TERMS")}
    signed = [j for j in jobs if j.get("jd_sha")]

    if not quiet:
        print(f"岗位 {len(jobs)} 个，其中带原文指纹的 {len(signed)} 个。")
        print("阴性对照（先证明检查器有效）：")
        if not negative_control(jobs, term_ids):
            print("\nFAIL：检查器抓不住已知错误，报告作废。先修检查器。")
            sys.exit(2)
        print()

    problems = check(jobs, term_ids)
    if problems:
        print(f"发现 {len(problems)} 处问题：")
        for p in problems:
            print("  · " + p)
        sys.exit(1)
    if not quiet:
        hl = sum(len(j.get("hl") or {}) for j in jobs)
        print(f"全部通过：{len(signed)} 条 JD 与抓取时的官网原文逐字一致，"
              f"{hl} 个高亮词全部锚得住，能力 id 全部有效。")
        print("\n提示：要查官网是否改了 JD（漂移），需要浏览器重跑 scripts/import_bytedance_jobs.py "
              "里的取数步骤——字节接口带反爬，命令行直取会返回 site not exist。")


if __name__ == "__main__":
    main()
