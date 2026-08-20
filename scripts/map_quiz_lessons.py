#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 quiz_bank 的 259 道题从「篇章级」绑到「节级」→ backend/quiz_lesson_map.json

方法：题目文本(题干+选项+解析+tag) 对同篇章每一节的课程全文(_text.json)做
字符二元组 TF-IDF 余弦相似度，取最高者为绑定节。
置信分档：top1 与 top2 的差距(margin) + 绝对分数，低置信的单独列出来供人工复核。

质量闸(阴性对照)：每道题除了在本篇章内找最佳节，还在「随机其他篇章」的节里
打分——若本篇章最佳分数不显著高于外篇章基线，说明匹配根本没找到信号，
这题标记 unmapped，宁缺毋滥（没绑上的题继续留在篇章级测评页，不进随堂小测）。
"""
import json
import math
import os
import random
from collections import Counter

random.seed(20260820)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, "backend")

quiz = json.load(open(os.path.join(B, "quiz_bank.json"), encoding="utf-8"))
idx = json.load(open(os.path.join(B, "lessons", "_index.json"), encoding="utf-8"))
txt = json.load(open(os.path.join(B, "lessons", "_text.json"), encoding="utf-8"))

# 篇章号 → 该篇章的节列表
CH2PART = {"p-zero": "第零篇章", "p-1": "第一篇章", "p-2": "第二篇章", "p-3": "第三篇章",
           "p-4": "第四篇章", "p-5": "第五篇章", "p-6": "第六篇章", "p-7": "第七篇章",
           "p-8": "第八篇章", "p-9": "第九篇章"}
by_part = {}
for f, m in idx.items():
    by_part.setdefault(m["part"], []).append(f)


def bigrams(s):
    s = "".join(ch for ch in s if not ch.isspace())
    return Counter(s[i:i + 2] for i in range(len(s) - 1))


def lesson_text(f):
    t = txt.get(f, "")
    if isinstance(t, dict):
        t = json.dumps(t, ensure_ascii=False)
    m = idx[f]
    # 标题/seo/小节名加权：出现在骨架里的词比正文散词更能代表这节讲什么
    head = (m["title"] + " " + m.get("seo", "") + " " + m.get("topic", "")) * 3
    return head + " " + str(t)


# 全库 IDF（罕见二元组权重高，「的」「我们」之类权重归零）
doc_bg = {f: bigrams(lesson_text(f)) for f in idx}
df = Counter()
for bg in doc_bg.values():
    df.update(bg.keys())
N = len(doc_bg)
IDF = {g: math.log(N / (1 + c)) for g, c in df.items()}


def vec(bg):
    return {g: n * IDF.get(g, 0) for g, n in bg.items() if IDF.get(g, 0) > 0.5}


def cos(a, b):
    if not a or not b:
        return 0.0
    dot = sum(w * b[g] for g, w in a.items() if g in b)
    na = math.sqrt(sum(w * w for w in a.values()))
    nb = math.sqrt(sum(w * w for w in b.values()))
    return dot / (na * nb) if na and nb else 0.0


doc_vec = {f: vec(bg) for f, bg in doc_bg.items()}
all_files = list(idx)

mapping, review, unmapped = {}, [], []
for q in quiz["items"]:
    part = CH2PART[q["chapter"]]
    cands = by_part.get(part, [])
    qtext = q["q"] + " " + " ".join(map(str, q.get("opts", []))) + " " + \
        str(q.get("exp", "")) + " " + str(q.get("tag", ""))
    qv = vec(bigrams(qtext))
    scored = sorted(((cos(qv, doc_vec[f]), f) for f in cands), reverse=True)
    if not scored:
        unmapped.append((q["id"], "篇章无节"))
        continue
    s1, f1 = scored[0]
    s2 = scored[1][0] if len(scored) > 1 else 0.0
    # 阴性对照：随机 12 个外篇章节的分数基线
    outs = [cos(qv, doc_vec[f]) for f in random.sample(
        [f for f in all_files if f not in cands], 12)]
    base = max(outs) if outs else 0.0
    if s1 < 0.05 or s1 <= base:          # 信号还不如外篇章 → 不绑
        unmapped.append((q["id"], f"s1={s1:.3f} base={base:.3f}"))
        continue
    conf = "high" if (s1 - s2) / max(s1, 1e-9) > 0.25 or s1 > 0.30 else "low"
    # 综合题/低置信题：在分数打平(≥0.7×top1)的候选里选课程顺序最靠后的一节——
    # 这类题往往横跨本篇章几节的内容，绑早了会考用户还没读到的东西
    if conf == "low" or q["type"] == "multi":
        order = list(idx)
        tied = [f for s, f in scored[:3] if s >= 0.7 * s1]
        f1 = max(tied, key=order.index)
    mapping[q["id"]] = f1
    if conf == "low":
        review.append({"id": q["id"], "q": q["q"][:40], "top": [
            (round(s, 3), idx[f]["title"]) for s, f in scored[:3]]})

out = os.path.join(B, "quiz_lesson_map.json")
json.dump(mapping, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

per_lesson = Counter(mapping.values())
covered = sum(1 for f in idx if per_lesson.get(f))
print(f"绑定 {len(mapping)}/{len(quiz['items'])} 题 · unmapped {len(unmapped)} · "
      f"待人工复核 {len(review)}")
print(f"节覆盖：{covered}/{len(idx)} 节至少 1 题；≥2 题的 {sum(1 for c in per_lesson.values() if c >= 2)} 节")
print("\n-- unmapped 样例 --")
for i, r in unmapped[:8]:
    print(" ", i, r)
print("\n-- 低置信待复核（题干 vs 前三候选节）--")
for r in review[:40]:
    print(f"  {r['id']} {r['q']}")
    for s, t in r["top"]:
        print(f"      {s}  {t}")
