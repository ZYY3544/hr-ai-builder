#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成「周末入楼统计」任务数据包 → frontend/data/task-weekend/

原型是站主在大厂真实交付过的统计活，坑按真实口径逐个埋进假数据里：
  ①法定节假日落在周末（要剔）②调休上班的周日（要剔）③早于 06:00 的刷卡（不算）
  ④门禁工号带前导零、花名册不带（对不上）⑤同人同日多刷（要去重）
  ⑥部门字段是路径且粒度不一、含别名（BU 归属要自己立规则）
  ⑦实习生刷卡有、正式花名册无 ⑧两个月花名册人数不同（入楼率分母按月）

答案卡由本脚本按标准口径直接算出——生成器就是真相源。
末尾自带阴性对照：故意用一个"漏坑"的错误算法重算，确认它算出来的数跟答案不同；
若相同说明坑没埋成，直接 FAIL。固定随机种子，可复现。
"""
import csv
import os
import random
from collections import defaultdict
from datetime import date, datetime, timedelta

random.seed(20260819)
ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "frontend", "data", "task-weekend")
os.makedirs(ROOT, exist_ok=True)

# ── 虚构公司结构（任何真实公司无关）──────────────────────────────
BUS = {
    "技术平台中心": ["基础架构部", "数据智能部", "应用研发部"],
    "商业化中心":   ["销售一部", "销售二部", "商业产品部"],
    "用户增长中心": ["市场部", "内容运营部"],
    "职能线":       ["人力资源部", "财务部", "行政法务部"],
}
# 刷卡系统里同一个 BU 会写出好几种样子（真实系统就这德行）
BU_STYLES = {
    "技术平台中心": ["星云科技/技术平台中心/{sub}", "技术平台中心/{sub}", "星云科技/技术平台/{sub}"],
    "商业化中心":   ["星云科技/商业化中心/{sub}", "商业化中心/{sub}"],
    "用户增长中心": ["星云科技/用户增长中心/{sub}", "用户增长/{sub}"],
    "职能线":       ["星云科技/职能线/{sub}", "职能线/{sub}"],
}
FUNC_BY_BU = {"技术平台中心": "技术", "商业化中心": "销售", "用户增长中心": "运营", "职能线": "职能"}

SURNAMES = "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜"
GIVEN = ("伟芳娜敏静丽强磊军洋勇艳杰娟涛明超秀兰霞平刚桂英华玉萍红志斌宇浩天晨曦悦欣怡")


def _name():
    return random.choice(SURNAMES) + "".join(
        random.choice(GIVEN) for _ in range(random.choice([1, 2])))


# ── 人员 ────────────────────────────────────────────────────────
people = []
eid = 30001
for bu, subs in BUS.items():
    n = {"技术平台中心": 210, "商业化中心": 160, "用户增长中心": 90, "职能线": 60}[bu]
    for _ in range(n):
        sub = random.choice(subs)
        people.append({"eid": f"{eid:05d}", "name": _name(), "bu": bu, "sub": sub,
                       "func": FUNC_BY_BU[bu],
                       "level": random.choice(["P4", "P5", "P6", "P7", "M1", "M2"])})
        eid += 1
# 坑⑥的极端例：两位高管在刷卡表里没有部门路径
execs = [{"eid": f"{eid:05d}", "name": _name(), "bu": "", "sub": "", "func": "高管", "level": "E1"},
         {"eid": f"{eid+1:05d}", "name": _name(), "bu": "", "sub": "", "func": "高管", "level": "E1"}]
eid += 2
# 坑⑦：实习生只出现在刷卡表
interns = []
for _ in range(14):
    interns.append({"eid": f"{eid:05d}", "name": _name(),
                    "bu": random.choice(list(BUS)), "func": "实习"})
    eid += 1

# 4 月入职 18 人、3 月底离职 12 人 → 两个月花名册人数不同（坑⑧）
leavers_mar = random.sample(people, 12)
joiners_apr = []
for _ in range(18):
    bu = random.choice(list(BUS))
    joiners_apr.append({"eid": f"{eid:05d}", "name": _name(), "bu": bu,
                        "sub": random.choice(BUS[bu]), "func": FUNC_BY_BU[bu],
                        "level": random.choice(["P4", "P5"])})
    eid += 1

roster_mar = people + execs
roster_apr = [p for p in people if p not in leavers_mar] + execs + joiners_apr

# ── 日历（虚构行政通知，任务书原文给出）────────────────────────────
HOLIDAY_WEEKEND = {date(2026, 4, 4), date(2026, 4, 5)}     # 清明放假，落在周六/周日
MAKEUP_SUNDAY = {date(2026, 4, 26)}                        # 调休上班的周日
D0, D1 = date(2026, 3, 1), date(2026, 4, 30)


def true_weekend(d):
    """标准口径下算数的周末：周六日 − 落在周末的法定假 − 调休上班日。"""
    return d.weekday() >= 5 and d not in HOLIDAY_WEEKEND and d not in MAKEUP_SUNDAY


# ── 刷卡记录 ─────────────────────────────────────────────────────
def bu_path(p):
    if not p["bu"]:
        return ""
    return random.choice(BU_STYLES[p["bu"]]).format(sub=p["sub"])


def eid_card(e):
    return "0" + e if random.random() < 0.4 else e          # 坑④ 前导零

rows = []
truth = {"2026-03": defaultdict(set), "2026-04": defaultdict(set)}   # 月→BU→真去重集合
all_month = {"2026-03": set(), "2026-04": set()}

d = D0
while d <= D1:
    mon = f"2026-{d.month:02d}"
    roster = roster_mar if d.month == 3 else roster_apr
    if d.weekday() < 5 or d in MAKEUP_SUNDAY:               # 工作日（含调休）：大量正常刷卡
        for p in random.sample(roster, int(len(roster) * random.uniform(.82, .92))):
            t = f"{random.randint(8,10):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}"
            rows.append([eid_card(p["eid"]), p["name"], f"{d} {t}", "A座-闸机", bu_path(p)])
    else:                                                    # 周六日
        base = random.uniform(.022, .04) if true_weekend(d) else random.uniform(.018, .035)
        for p in random.sample(roster, int(len(roster) * base)):
            n_swipes = random.choice([1, 1, 1, 2, 3])        # 坑⑤ 同日多刷
            for _ in range(n_swipes):
                t = f"{random.randint(7,15):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}"
                rows.append([eid_card(p["eid"]), p["name"], f"{d} {t}", "A座-闸机", bu_path(p)])
            if true_weekend(d):
                truth[mon][p["bu"] or "BU未识别"].add(p["eid"])
                all_month[mon].add(p["eid"])
        # 坑③：保洁/夜班的凌晨误刷（不算入楼）
        for p in random.sample(roster, random.randint(2, 5)):
            t = f"{random.choice([4,5]):02d}:{random.randint(0,59):02d}:00"
            rows.append([eid_card(p["eid"]), p["name"], f"{d} {t}", "B1-货梯", bu_path(p)])
        # 坑⑦：实习生周末也来
        if true_weekend(d):
            for it in random.sample(interns, random.randint(3, 6)):
                t = f"{random.randint(9,14):02d}:{random.randint(0,59):02d}:00"
                rows.append([eid_card(it["eid"]), it["name"], f"{d} {t}", "A座-闸机",
                             f"星云科技/{it['bu']}"])
    d += timedelta(days=1)

random.shuffle(rows)

# ── 落盘 ────────────────────────────────────────────────────────
def wcsv(name, header, data):
    with open(os.path.join(ROOT, name), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(data)

wcsv("01_门禁刷卡明细.csv", ["工号", "姓名", "刷卡时间", "门禁点", "部门"], rows)
for tag, roster in (("2026-03", roster_mar), ("2026-04", roster_apr)):
    wcsv(f"02_花名册_{tag}月末.csv", ["工号", "姓名", "一级部门", "二级部门", "职能类别", "层级"],
         [[p["eid"], p["name"], p["bu"] or "-", p["sub"] or "-", p["func"], p["level"]]
          for p in roster])

# ── 答案卡 ───────────────────────────────────────────────────────
lines = ["# 答案卡 · 周末入楼统计\n",
         "先自己做完再打开对数。差一点就回去找口径——**每一个差值背后都是一个坑**。\n"]
for mon, roster in (("2026-03", roster_mar), ("2026-04", roster_apr)):
    denom = len(roster)
    tot = len(all_month[mon])
    lines.append(f"\n## {mon}\n")
    lines.append(f"- 周末入楼去重总人数：**{tot}**")
    lines.append(f"- 花名册期末人数（分母）：**{denom}**")
    lines.append(f"- 入楼率：**{tot/denom*100:.1f}%**")
    lines.append("- 分 BU：")
    for bu in list(BUS) + ["BU未识别"]:
        n = len(truth[mon].get(bu, set()))
        if n:
            lines.append(f"  - {bu}：{n} 人")
lines.append("\n## 你大概率踩过的坑（对不上就来这里找）\n")
lines.append("清明 4-04/4-05 落在周末要剔｜4-26 调休上班的周日要剔｜06:00 前的刷卡不算｜"
             "门禁工号可能带前导零｜同人同日多刷要去重｜两位高管没有部门路径（归 BU未识别 是对的）｜"
             "实习生不在正式花名册（列出名单、不进占比）｜两个月分母不同。")
open(os.path.join(ROOT, "答案卡.md"), "w", encoding="utf-8").write("\n".join(lines))

print(f"✓ 刷卡 {len(rows)} 行 · 花名册 {len(roster_mar)}/{len(roster_apr)} 人")
for mon in ("2026-03", "2026-04"):
    print(f"  {mon}: 周末去重 {len(all_month[mon])} 人")

# ── 阴性对照：漏坑的错误算法必须得出不同的数 ──────────────────────
naive = {"2026-03": set(), "2026-04": set()}
for r in rows:
    dt = datetime.strptime(r[2], "%Y-%m-%d %H:%M:%S")
    if dt.weekday() >= 5:                       # 只看星期，不剔节假日/调休/凌晨
        naive[f"2026-{dt.month:02d}"].add(r[0])  # 且不归一前导零
for mon in ("2026-03", "2026-04"):
    a, b = len(all_month[mon]), len(naive[mon])
    assert a != b, f"{mon} 阴性对照失败：漏坑算法竟与答案相同（坑没埋成）"
    print(f"  阴性对照 {mon}: 标准 {a} vs 漏坑算法 {b} ✓ 坑有效")
