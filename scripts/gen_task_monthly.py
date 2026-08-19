#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成「人力月报·完整战役」任务包 → frontend/data/task-monthly/

原型 = 站主真实交付过的经营月报（口径手册 200+ 行那个）。复刻的是口径的**类型**，
数据与名称全部虚构（星云科技/星耀服务），不对应任何真实公司。

复刻的口径类型（每一条都是真实月报里踩过的）：
  ①两套并行口径：月度指标用 raw 部门，YTD 指标用重分类后的部门
  ②权威顺序：离职表 Corp 列权威、BU 路径兜底
  ③操作顺序敏感：汰换先回填、表单状态后过滤
  ④两刀切汰换 + 子串匹配 + 不覆盖人工标注
  ⑤枚举值陷阱（校招正式≠校招）、字段名陷阱（全角括号、"表单状态名称"）
  ⑥P8+ 含 M 序列换算（P8=M3）
  ⑦月入职排除子公司
  ⑧YTD 分母在另一张历史宽表（月均）、财年 4 月起
  ⑨非工作日=周末+法定假−调休；入楼分子五重过滤
  ⑩时间字段多格式混杂；被驳回的离职者仍在在职表里（人数对账彩蛋）

口径说明.md 故意留三处不完备（分母未写明/未提 M 序列/未写去重）——发现模糊、
跟 AI 掰扯清楚、做决定并记录，正是这个任务要考的东西。标准选择写在答案说明里。

生成器即真相源：答案卡由本脚本按标准口径算出；末尾阴性对照用五种典型错法重算，
任何一种与标准答案相同即 FAIL（说明坑没埋成）。固定种子可复现。
"""
import os
import random
import shutil
import zipfile
from collections import defaultdict
from datetime import date, datetime, timedelta

from openpyxl import Workbook

random.seed(20260420)
ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "frontend", "data", "task-monthly")
PKG = os.path.join(ROOT, "_pkg")          # zip 的内容根
if os.path.exists(PKG):
    shutil.rmtree(PKG)
os.makedirs(PKG, exist_ok=True)

# ── 组织结构（全部虚构）─────────────────────────────────────────
GROUP_DEPTS = ["技术平台中心", "数据智能中心", "AI应用业务部", "商业化中心", "用户增长中心",
               "内容业务中心", "职能线", "平台运营部", "创新孵化部"]
SUBCO = "星耀服务"                        # 集团控股的服务子公司
OUT_ROWS = ["公司整体", "集团合计"] + GROUP_DEPTS + [SUBCO]

SUBS = {
    "技术平台中心": ["基础架构部", "应用研发部"], "数据智能中心": ["数据平台部", "算法部"],
    "AI应用业务部": ["智能体产品部", "解决方案部"], "商业化中心": ["销售一部", "销售二部"],
    "用户增长中心": ["市场部", "增长运营部"], "内容业务中心": ["内容生态部", "平台产品部"],
    "职能线": ["人力资源部", "财务部", "法务部"], "平台运营部": ["运营支持部"],
    "创新孵化部": ["孵化项目组"],
    SUBCO: ["本地服务部", "商户运营部", "客服交付部"],
}
# 重分类规则（YTD 口径专用；月度指标不用）——(父,子) 同时出现 → 改归属
RECLASSIFY = {
    ("内容业务中心", "本地服务部"): SUBCO,
    ("内容业务中心", "商户运营部"): SUBCO,
    (SUBCO, "平台产品部"): "内容业务中心",
    (SUBCO, "人力资源部"): "职能线",
}
SERIES_BY_DEPT = {"技术平台中心": "技术", "数据智能中心": "技术", "AI应用业务部": "产品",
                  "商业化中心": "销售", "用户增长中心": "运营", "内容业务中心": "运营",
                  "职能线": "职能", "平台运营部": "运营", "创新孵化部": "产品", SUBCO: "运营"}

SURN = "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦许何吕施张孔曹严华金魏陶姜戚谢邹喻柏窦苏潘葛范彭鲁韦昌马苗方俞任袁柳"
GIVEN = "伟芳娜敏静丽强磊军洋勇艳杰娟涛明超秀兰霞平刚桂英华玉萍红志斌宇浩天晨曦悦欣怡楠帆锐晗璐彬"


def name():
    return random.choice(SURN) + "".join(random.choice(GIVEN) for _ in range(random.choice([1, 2])))


def level():
    r = random.random()
    if r < .04:
        return random.choice(["M3", "M4", "P8", "P9"])       # P8+ 层（含 M 序列——坑⑥）
    if r < .10:
        return random.choice(["M1", "M2"])
    return random.choice(["P4", "P5", "P5", "P6", "P6", "P7"])


def bu_path(dept, sub):
    styles = [f"星云科技-{dept}-{sub}", f"{dept}-{sub}", f"星云科技-{dept}"]
    return random.choice(styles)


def fmt_dt(d, with_time=random.random):
    """时间字段多格式混杂（坑⑩）。"""
    f = random.random()
    if f < .3:
        return d.strftime("%Y-%m-%d")
    if f < .55:
        return d.strftime("%Y/%m/%d")
    if f < .8:
        return d.strftime("%Y-%m-%d 00:00:00")
    return d                                                  # 真 date 对象


# ── 员工池（2026-03 期末在职）────────────────────────────────────
HEAD = {"技术平台中心": 132, "数据智能中心": 84, "AI应用业务部": 58, "商业化中心": 96,
        "用户增长中心": 55, "内容业务中心": 74, "职能线": 42, "平台运营部": 30,
        "创新孵化部": 18, SUBCO: 88}
emps, eid = [], 40001
for dept, n in HEAD.items():
    for _ in range(n):
        sub = random.choice(SUBS[dept])
        lv = level()
        emps.append({"eid": str(eid), "name": name(), "dept": dept, "sub": sub,
                     "lv": lv, "series": SERIES_BY_DEPT[dept] if random.random() > .12
                     else random.choice(["技术", "产品", "运营", "职能"]),
                     "span": (random.choice([3, 5, 8, 12]) if lv.startswith("M") or random.random() < .06
                              else random.choice([0, "", None, "0"])),
                     "hire": date(2023, 1, 1) + timedelta(days=random.randint(0, 1100)),
                     "rtype": random.choices(["社招", "校招正式", "实习转正"], [.7, .22, .08])[0]})
        eid += 1

# 4 月入职（含子公司——坑⑦：月入职口径要排除星耀）
joiners = []
for _ in range(26):
    dept = random.choices(list(HEAD), [8, 5, 6, 7, 4, 5, 2, 2, 2, 5])[0]
    sub = random.choice(SUBS[dept])
    joiners.append({"eid": str(eid), "name": name(), "dept": dept, "sub": sub,
                    "lv": random.choice(["P4", "P5", "P6"]), "series": SERIES_BY_DEPT[dept],
                    "span": "", "hire": date(2026, 4, random.randint(1, 28)),
                    "rtype": random.choices(["社招", "校招正式", "实习转正"], [.6, .3, .1])[0]})
    eid += 1

# ── 离职记录（FY 累计口径 + 全部坑）────────────────────────────────
REASONS_OK = ["个人发展", "家庭原因", "薪酬期望差异", "通勤距离"]
REASON_TH = "工作能力或态度问题"


def gen_exit(pool, d0, d1, n, prefix_th=0.5):
    rows = []
    chosen = random.sample(pool, n)
    for p in chosen:
        last = d0 + timedelta(days=random.randint(0, (d1 - d0).days))
        resign = random.choices(["是", "否", ""], [.62, .3, .08])[0]
        pri, sec = random.choice(REASONS_OK), ""
        if resign == "是" and random.random() < .3:            # 辞职但实为汰换（第二刀·子串）
            if random.random() < prefix_th:
                sec = f"绩效改进未通过-{REASON_TH}"
            else:
                pri = REASON_TH
        status = random.choices(["审批完成", "进行中", "已驳回", "草稿"], [.72, .12, .1, .06])[0]
        manual = ""
        if random.random() < .05:                              # 人工已标注（不覆盖——含与规则相反的）
            manual = random.choice(["是", "否"])
        rows.append({"p": p, "last": last, "resign": resign, "pri": pri, "sec": sec,
                     "status": status, "manual": manual,
                     "corp": SUBCO if p["dept"] == SUBCO else "星云集团"})
    return rows

exits_fy25 = gen_exit(emps, date(2025, 4, 1), date(2026, 3, 28), 118)
survivors = [e for e in emps if e not in [r["p"] for r in exits_fy25
             if r["status"] in ("审批完成", "进行中") and r["last"] <= date(2026, 3, 31)]]
# 3 月末在职 = survivors；4 月离职从 survivors 里出
exits_apr = gen_exit(survivors, date(2026, 4, 2), date(2026, 4, 27), 15)
gone_apr = [r["p"] for r in exits_apr if r["status"] in ("审批完成", "进行中")]
roster_mar = survivors
roster_apr = [p for p in survivors if p not in gone_apr] + joiners

# 外包（不参与重分类；离职表里掺外包行当干扰）
outsourced = [{"eid": f"W{9000+i}", "name": name(),
               "dept": random.choice(list(HEAD)), "job": random.choice(["客服", "测试", "运营支持"])}
              for i in range(92)]
exit_noise = [{"p": {"eid": o["eid"], "name": o["name"], "dept": o["dept"], "sub": "-"},
               "last": date(2026, random.choice([3, 4]), random.randint(3, 25)),
               "resign": "是", "pri": "项目结束", "sec": "", "status": "审批完成",
               "manual": "", "corp": "星云集团", "etype": "外包"}
              for o in random.sample(outsourced, 6)]

# ── 日历（与周末入楼任务同一套行政通知）─────────────────────────────
HOLIDAYS = {date(2026, 4, 4), date(2026, 4, 5), date(2026, 4, 6)}
MAKEUP = {date(2026, 4, 26)}


def nonwork(d):
    if d in MAKEUP:
        return False
    return d in HOLIDAYS or d.weekday() >= 5


# ── 入楼打卡（两栋楼两个文件）───────────────────────────────────────
def gen_swipes(roster, y, m):
    rows = []
    d = date(y, m, 1)
    while d.month == m:
        pool = random.sample(roster, int(len(roster) * (random.uniform(.55, .7) if not nonwork(d)
                                                        else random.uniform(.03, .06))))
        for p in pool:
            for _ in range(random.choice([1, 1, 2])):
                hh = random.choice([4, 5] if random.random() < .04 else list(range(7, 21)))
                rows.append([fmt_dt(d) if isinstance(fmt_dt(d), str) else d.strftime("%Y-%m-%d"),
                             f"{d} {hh:02d}:{random.randint(0,59):02d}:00",
                             p["eid"], p["name"], bu_path(p["dept"], p["sub"])])
        d += timedelta(days=1)
    random.shuffle(rows)
    return rows

swipes = {"2026-03": gen_swipes(roster_mar, 2026, 3), "2026-04": gen_swipes(roster_apr, 2026, 4)}


# ── 写 Excel ────────────────────────────────────────────────────
def wb_write(path, sheets):
    wb = Workbook()
    wb.remove(wb.active)
    for sname, header, rows in sheets:
        ws = wb.create_sheet(sname)
        ws.append(header)
        for r in rows:
            ws.append(r)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    wb.save(path)

FIELD_NOTE = [["字段", "说明"],
              ["管理幅度（主兼岗合计）", "直接下属数，主岗+兼岗；空值=无下属"],
              ["职务序列", "技术/产品/运营/销售/职能"],
              ["员工二层组织", "以本表为准；打卡表的组织路径仅供参考"]]

for tag, roster in (("2026-03", roster_mar), ("2026-04", roster_apr)):
    base = os.path.join(PKG, "raw_data", tag)
    wb_write(os.path.join(base, "在职正式.xlsx"),
             [("在职明细", ["工号", "姓名", "员工二层组织", "员工所在部门", "层级",
                          "职务序列", "管理幅度（主兼岗合计）", "入职日期", "招聘类型"],
               [[p["eid"], p["name"], p["dept"], p["sub"], p["lv"], p["series"],
                 p["span"], fmt_dt(p["hire"]), p["rtype"]] for p in roster]),
              ("字段说明", FIELD_NOTE[0], FIELD_NOTE[1:])])
    wb_write(os.path.join(base, "在职外包.xlsx"),
             [("外包明细", ["工号", "姓名", "职务", "受益部门(立项)"],
               [[o["eid"], o["name"], o["job"], o["dept"]] for o in outsourced])])

wb_write(os.path.join(PKG, "raw_data", "2026-04", "入职正式.xlsx"),
         [("入职明细", ["工号", "姓名", "员工入职2层组织", "员工入职部门", "入职层级", "招聘类型", "入职日期"],
           [[p["eid"], p["name"], p["dept"], p["sub"], p["lv"], p["rtype"], fmt_dt(p["hire"])]
            for p in joiners])])
# 3 月入职表（FY25 尾月，少量，供环比）
joiners_mar = random.sample(roster_mar, 18)
wb_write(os.path.join(PKG, "raw_data", "2026-03", "入职正式.xlsx"),
         [("入职明细", ["工号", "姓名", "员工入职2层组织", "员工入职部门", "入职层级", "招聘类型", "入职日期"],
           [[p["eid"], p["name"], p["dept"], p["sub"], p["lv"],
             random.choices(["社招", "校招正式", "实习转正"], [.6, .3, .1])[0],
             fmt_dt(date(2026, 3, random.randint(1, 27)))] for p in joiners_mar])])


def exit_rows(records):
    out = []
    for r in records:
        p = r["p"]
        out.append([p["eid"], p["name"], r.get("etype", "正式"), r["corp"],
                    bu_path(p["dept"], p.get("sub", "-")), fmt_dt(r["last"]),
                    r["resign"], r["pri"], r["sec"], r["manual"], r["status"]])
    return out

wb_write(os.path.join(PKG, "raw_data", "2026-03", "离职正式.xlsx"),
         [("离职明细", ["工号", "姓名", "员工类型名称", "Corp", "BU", "最后工作日",
                      "是否辞职", "主要离职原因", "次要离职原因", "是否汰换", "表单状态名称"],
           exit_rows(exits_fy25 + [x for x in exit_noise if x["last"].month == 3]))])
wb_write(os.path.join(PKG, "raw_data", "2026-04", "离职正式.xlsx"),
         [("离职明细", ["工号", "姓名", "员工类型名称", "Corp", "BU", "最后工作日",
                      "是否辞职", "主要离职原因", "次要离职原因", "是否汰换", "表单状态名称"],
           exit_rows(exits_apr + [x for x in exit_noise if x["last"].month == 4]))])

for tag in ("2026-03", "2026-04"):
    half = len(swipes[tag]) // 2
    for bld, chunk in (("A座", swipes[tag][:half]), ("B座", swipes[tag][half:])):
        wb_write(os.path.join(PKG, "raw_data", tag, f"入楼打卡_{bld}.xlsx"),
                 [("打卡记录", ["日期", "时间", "工号", "姓名", "BU"], chunk)])


# ── 标准口径计算（生成器即真相源）────────────────────────────────────
def reclass(dept, sub):
    return RECLASSIFY.get((dept, sub), dept)


def month_stats(roster, tag):
    st = defaultdict(lambda: defaultdict(float))
    for p in roster:
        for key in ("公司整体", p["dept"] if p["dept"] != SUBCO else SUBCO):
            g = st[key]
            g["期末在职"] += 1
            lv = p["lv"]
            if (lv[0] == "P" and int(lv[1:]) >= 8) or (lv[0] == "M" and int(lv[1:]) >= 3):
                g["P8+"] += 1
            sp = p["span"]
            try:
                if float(sp or 0) > 0:
                    g["管理者"] += 1
            except (TypeError, ValueError):
                pass
            g[f"序列_{p['series']}"] += 1
        if p["dept"] != SUBCO:
            st["集团合计"]["期末在职"] += 1
    return st

STAT = {"2026-03": month_stats(roster_mar, "2026-03"),
        "2026-04": month_stats(roster_apr, "2026-04")}

# 月入职（raw 口径 + 排除星耀）
hire_apr = defaultdict(lambda: defaultdict(int))
for p in joiners:
    if p["dept"] == SUBCO:
        continue                                   # 坑⑦
    for key in ("公司整体", p["dept"]):
        hire_apr[key]["合计"] += 1
        hire_apr[key][p["rtype"]] += 1

# 离职/汰换：先回填，后过滤
def taihuan(r):
    if r["manual"]:
        return r["manual"]                          # 不覆盖人工
    if r["resign"] == "否":
        return "是"
    if r["resign"] == "是" and (REASON_TH in r["pri"] or REASON_TH in r["sec"]):
        return "是"
    return "否" if r["resign"] == "是" else ""

def exit_stats(records, ytd_lo, ytd_hi, month):
    ytd = defaultdict(lambda: defaultdict(int))
    mon = defaultdict(lambda: defaultdict(int))
    for r in records:
        if r.get("etype") == "外包":
            continue                                # 员工类型名称过滤
        th = taihuan(r)                             # 先回填
        if r["status"] not in ("审批完成", "进行中"):
            continue                                # 后过滤
        p = r["p"]
        dept_raw = p["dept"]
        dept_ytd = SUBCO if r["corp"] == SUBCO else reclass(p["dept"], p.get("sub", ""))
        if ytd_lo <= r["last"] <= ytd_hi:
            for k in ("公司整体", dept_ytd):
                ytd[k]["离职"] += 1
                if th == "是":
                    ytd[k]["汰换"] += 1
        if r["last"].month == month:
            for k in ("公司整体", dept_raw):
                mon[k]["离职"] += 1
                if th == "是":
                    mon[k]["汰换"] += 1
    return ytd, mon

YTD3, MON3 = exit_stats(exits_fy25 + exit_noise, date(2025, 4, 1), date(2026, 3, 31), 3)
YTD4, MON4 = exit_stats(exits_apr + exit_noise, date(2026, 4, 1), date(2026, 4, 30), 4)

# 入楼（分子五重过滤）
def entry_stats(tag, roster):
    y, m = int(tag[:4]), int(tag[5:])
    byid = {p["eid"]: p for p in roster}
    seen = defaultdict(set)
    for _d, ts, eid_, _n, bu in swipes[tag]:
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        if dt.hour < 6 or dt.month != m or not nonwork(dt.date()) or not eid_:
            continue
        p = byid.get(eid_)
        dept = None
        for seg in bu.split("-"):
            if seg in HEAD:
                dept = seg
                break
        dept = dept or (p and p["dept"])
        if dept:
            seen[dept].add(eid_)
        seen["公司整体"].add(eid_)
    return seen

ENT = {t: entry_stats(t, r) for t, r in (("2026-03", roster_mar), ("2026-04", roster_apr))}

# 历史宽表（YTD 分母 + 同比基线；26-03/04 两点=真实统计，其余编平滑序列）
months_hist = ([f"2025-{m:02d}" for m in range(1, 13)] + ["2026-01", "2026-02", "2026-03", "2026-04"])
hist = {}
for row in OUT_ROWS:
    cur3 = STAT["2026-03"][row]["期末在职"] or (
        sum(STAT["2026-03"][d]["期末在职"] for d in GROUP_DEPTS) if row == "集团合计" else 0)
    cur4 = STAT["2026-04"][row]["期末在职"] or (
        sum(STAT["2026-04"][d]["期末在职"] for d in GROUP_DEPTS) if row == "集团合计" else 0)
    seq, v = [], cur3 * random.uniform(.9, .96)
    for _ in months_hist[:-2]:
        v *= random.uniform(.995, 1.012)
        seq.append(round(v))
    hist[row] = seq + [round(cur3), round(cur4)]
wb_write(os.path.join(PKG, "历史", "在职人数历史.xlsx"),
         [("月末在职", ["部门"] + months_hist, [[r] + hist[r] for r in OUT_ROWS])])
# 去年同期关键指标（同比基线）
LY = {r: {"期末在职": hist[r][3], "YTD离职率FY25同期": round(random.uniform(.06, .16), 4)}
      for r in OUT_ROWS}
wb_write(os.path.join(PKG, "历史", "关键指标历史.xlsx"),
         [("2025-04", ["部门", "期末在职人数", "YTD离职率(FY25同期)"],
           [[r, LY[r]["期末在职"], LY[r]["YTD离职率FY25同期"]] for r in OUT_ROWS])])


def ytd_denom(row, lo_idx, hi_idx):
    vals = hist[row][lo_idx:hi_idx + 1]
    return sum(vals) / len(vals) if vals else 0

# ── 交付答案表（12 行 × 指标）——目标月 2026-04 ─────────────────────
COLS = ["期末在职人数", "外包人数", "月入职合计", "其中校招正式", "其中社招", "其中实习转正",
        "月离职人数", "月汰换人数", "YTD离职人数", "YTD离职率", "YTD汰换人数", "YTD汰换率",
        "P8+人数", "P8+占比", "管理者人数", "技术序列占比", "产品序列占比", "运营序列占比",
        "非工作日入楼人数", "非工作日入楼率", "期末在职环比", "期末在职同比", "YTD离职率同比(pp)"]

OS_CNT = defaultdict(int)
for o in outsourced:
    OS_CNT["公司整体"] += 1
    OS_CNT[o["dept"]] += 1

ANS = {}
for row in OUT_ROWS:
    s4, s3 = STAT["2026-04"][row], STAT["2026-03"][row]
    if row == "集团合计":
        s4 = {k: sum(STAT["2026-04"][d].get(k, 0) for d in GROUP_DEPTS)
              for k in ["期末在职", "P8+", "管理者", "序列_技术", "序列_产品", "序列_运营"]}
        s3 = {"期末在职": sum(STAT["2026-03"][d].get("期末在职", 0) for d in GROUP_DEPTS)}
        h = {k: sum(hire_apr[d].get(k, 0) for d in GROUP_DEPTS) for k in ["合计", "校招正式", "社招", "实习转正"]}
        m4 = {k: sum(MON4[d].get(k, 0) for d in GROUP_DEPTS) for k in ["离职", "汰换"]}
        y4 = {k: sum(YTD4[d].get(k, 0) for d in GROUP_DEPTS) for k in ["离职", "汰换"]}
        ent = len(set().union(*[ENT["2026-04"].get(d, set()) for d in GROUP_DEPTS]))
        osn = sum(OS_CNT[d] for d in GROUP_DEPTS)
    else:
        h, m4, y4 = hire_apr[row], MON4[row], YTD4[row]
        ent = len(ENT["2026-04"].get(row, set()))
        osn = OS_CNT[row] if row != "集团合计" else 0
    end4, end3 = s4.get("期末在职", 0), s3.get("期末在职", 0)
    denom = ytd_denom(row, 15, 15)                  # FY26 YTD=仅 2026-04 → 月均=当月
    ly = LY[row]
    ytd_rate = (y4.get("离职", 0) / denom) if denom else 0
    ANS[row] = [
        int(end4), int(osn), h.get("合计", 0), h.get("校招正式", 0), h.get("社招", 0), h.get("实习转正", 0),
        m4.get("离职", 0), m4.get("汰换", 0), y4.get("离职", 0),
        round(ytd_rate, 4), y4.get("汰换", 0),
        round((y4.get("汰换", 0) / denom) if denom else 0, 4),
        int(s4.get("P8+", 0)), round(s4.get("P8+", 0) / end4, 4) if end4 else 0,
        int(s4.get("管理者", 0)),
        round(s4.get("序列_技术", 0) / end4, 4) if end4 else 0,
        round(s4.get("序列_产品", 0) / end4, 4) if end4 else 0,
        round(s4.get("序列_运营", 0) / end4, 4) if end4 else 0,
        ent, round(ent / end4, 4) if end4 else 0,
        round((end4 - end3) / end3, 4) if end3 else 0,
        round((end4 - ly["期末在职"]) / ly["期末在职"], 4) if ly["期末在职"] else 0,
        round((ytd_rate - ly["YTD离职率FY25同期"]) * 100, 2),
    ]

wb_write(os.path.join(PKG, "答案卡_做完再打开.xlsx"),
         [("2026-04 月报答案", ["部门"] + COLS, [[r] + ANS[r] for r in OUT_ROWS])])

# ── 阴性对照：五种典型错法必须得出不同的数 ───────────────────────────
def _assert_diff(label, wrong, right):
    assert wrong != right, f"阴性对照失败[{label}]：错法与标准答案相同（坑没埋成）wrong={wrong}"
    print(f"  阴性对照[{label}]: 标准 {right} vs 错法 {wrong} ✓")

# a) 漏表单状态过滤（把已驳回/草稿也算进 YTD 离职）
w = sum(1 for r in exits_apr if r.get("etype") != "外包"
        and date(2026, 4, 1) <= r["last"] <= date(2026, 4, 30))
_assert_diff("漏状态过滤", w, YTD4["公司整体"]["离职"])
# b) P8+ 不含 M 序列
w = sum(1 for p in roster_apr if p["lv"][0] == "P" and int(p["lv"][1:]) >= 8)
_assert_diff("P8+漏M序列", w, int(STAT["2026-04"]["公司整体"]["P8+"]))
# c) 月入职不排除星耀
w = len(joiners)
_assert_diff("入职未排除子公司", w, hire_apr["公司整体"]["合计"])
# d) 入楼不做同月去重（按打卡行数算）
w = sum(1 for _d, ts, e_, _n, _b in swipes["2026-04"]
        if (lambda dt: dt.hour >= 6 and nonwork(dt.date()))(datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")))
_assert_diff("入楼未去重", w, len(ENT["2026-04"]["公司整体"]))
# e) 漏人工标注不覆盖（全按两刀切重算汰换）
def th_rule_only(r):
    if r["resign"] == "否":
        return "是"
    if r["resign"] == "是" and (REASON_TH in r["pri"] or REASON_TH in r["sec"]):
        return "是"
    return "否"
w = sum(1 for r in exits_fy25 if r["status"] in ("审批完成", "进行中") and th_rule_only(r) == "是")
right = sum(1 for r in exits_fy25 if r["status"] in ("审批完成", "进行中") and taihuan(r) == "是")
_assert_diff("覆盖了人工标注", w, right)


# ── 三份文档（任务书刻意模糊；口径说明埋三处不完备；答案说明给标准与错法对照）──
TASKBOOK = """# 任务书 · 人力月报

（来自 HRD 的消息，周五 18:40）

> 下周一管理例会要用 4 月人力月报。老规矩，按咱们那张月报模板出，
> 口径参考口径说明（在包里）。上个月是外包同学帮忙做的，这次你来。
> 有拿不准的自己判断，但要能说清楚为什么这么算。
> 对了，历史数据在「历史」文件夹，行政的放假安排我转你了（见下）。

行政通知（转发）：清明节 2026-04-04 至 04-06 放假；2026-04-26（周日）调休上班。

## 交付

1. 按《月报模板》补全 2026 年 4 月全部数字（12 行 × 23 个指标）
2. 一页「口径决策记录」：口径说明里没写清楚的地方，你怎么定的、为什么
3. 你的产出方式不限——自动化脚本 / agent / skills / 任何工具，
   但要求下个月拿到 5 月数据时**能重复跑**

## 提示

只有一条：数据比看起来脏，口径比看起来多。先读完口径说明再动手。
做完之后再打开答案卡对数——每一个对不上的数字背后都是一条口径。
"""

TEMPLATE_NOTE = "\n\n## 月报模板（交付的表长这样）\n\n| 部门 | " + " | ".join(COLS) + " |\n" + \
    "|---" * (len(COLS) + 1) + "|\n" + \
    "\n".join("| " + r + " |" + "  |" * len(COLS) for r in OUT_ROWS) + "\n"

KOUJING = """# 口径说明 · 星云科技人力月报

> 本说明是月报所有指标的计算依据。字段名以 raw Excel 表头为准，注意精确匹配。

## 一、部门口径

1. 输出固定 12 行：公司整体 → 集团合计（9 个二层组织合计）→ 9 个二层组织 → 星耀服务。
2. **月度指标**（月入职/月离职/月汰换）按各表部门字段的原始值归属，不做重分类。
3. **YTD 指标**（YTD 离职/汰换及其率）按业务归属重分类后归属。重分类规则：
   (内容业务中心, 本地服务部)→星耀服务；(内容业务中心, 商户运营部)→星耀服务；
   (星耀服务, 平台产品部)→内容业务中心；(星耀服务, 人力资源部)→职能线。
   解析对象为 BU 多级路径（`-` 分隔），父子部门同时出现才触发。
4. 离职表判定星耀服务：**Corp 列权威**（Corp=星耀服务 → 星耀；否则按 BU 路径取首个命中的二层组织）。

## 二、在职与结构

5. 期末在职人数 = 当月末《在职正式》行数（该表即期末快照）。
6. 外包人数 = 《在职外包》行数，按「受益部门(立项)」归属，不做重分类。
7. P8 及以上人数 = 层级为 P8 及以上的员工数。
8. 管理者人数 = 「管理幅度（主兼岗合计）」> 0 的员工数（注意该列有空值与文本值）。
9. 序列占比 = 该序列人数 ÷ 期末在职人数，按「职务序列」列。

## 三、入离职

10. 月入职 = 《入职正式》中入职日期在当月的记录；**排除「员工入职2层组织」=星耀服务的行**
    （子公司入职内部消化，不计入集团口径）。按「招聘类型」拆分：校招正式 / 社招 / 实习转正
    （注意枚举值是「校招正式」）。
11. 离职记录先按「员工类型名称」=正式 过滤（表内混有外包行）。
12. 离职统计仅计「表单状态名称」∈ {审批完成, 进行中} 的行；其他状态（已驳回/草稿等）视为未生效
    ——**注意：未生效离职的员工仍在在职表中**。
13. 月离职人数 = 「最后工作日」在当月且状态有效的行数。
14. 汰换判定（两刀切）：「是否辞职」=否 → 汰换；「是否辞职」=是 且
    主要/次要离职原因任一**包含**「工作能力或态度问题」子串（可能带前缀）→ 汰换。
    「是否汰换」列已有人工标注的行，**以人工标注为准，不要覆盖**。
15. 汰换回填先于状态过滤（先对全量回填，再按状态筛统计范围）。

## 四、YTD 与财年

16. 财年从 4 月起：FY26 = 2026-04 至 2027-03。YTD 区间 = 财年起点至目标月末。
17. YTD 离职率 = YTD 离职人数 ÷ YTD 期间在职人数；YTD 汰换率同理。
18. YTD 离职人数的部门归属用重分类口径（见 3/4 条）。

## 五、入楼

19. 非工作日 = 周六日 + 法定节假日 − 调休上班日（安排见任务书的行政通知）。
20. 非工作日入楼人数 = 非工作日有入楼打卡的员工人数；打卡时间早于 06:00 的记录不算。
21. 入楼部门归属：打卡表 BU 路径解析优先，解析不到回《在职正式》查「员工二层组织」。
22. 非工作日入楼率 = 非工作日入楼人数 ÷ 期末在职人数。

## 六、同环比

23. 期末在职环比 = (本月 − 上月) ÷ 上月；同比 = (本月 − 去年同月) ÷ 去年同月
    （去年数据见《历史/关键指标历史.xlsx》）。
24. YTD 离职率同比：与去年同期 YTD 率的差，用百分点（pp）表示；YTD 率不看环比。
25. 历史各月在职人数见《历史/在职人数历史.xlsx》。
"""

ANSWER_NOTE = f"""# 答案说明 · 打开答案卡之前先读这页

## 口径说明里三处没写死的地方（这是刻意的），标准答案的选择：

1. **YTD 率的分母**（第 17 条只写了"YTD 期间在职人数"）——标准取
   《在职人数历史》中 YTD 区间各月月末在职的**算术平均**。FY26 的 4 月 YTD 只含一个月，
   分母即 4 月月末值。选月均而不是期末，是因为累计率的分母要反映整个期间的规模。
   你选了期末并在决策记录里说清了理由——也算对，但数字会和答案卡有偏差。

2. **P8 及以上**（第 7 条没提 M 序列）——标准含管理序列换算：P≥8 **或 M≥3**（P8=M3）。
   只数 P 序列会漏掉约一半的高阶人才：本包数据里标准 {int(STAT['2026-04']['公司整体']['P8+'])} 人 vs 只数 P 的 {sum(1 for p in roster_apr if p['lv'][0]=='P' and int(p['lv'][1:])>=8)} 人。

3. **入楼人数的去重**（第 20 条没写）——标准是**同工号同月只算一次**。
   不去重会把人数算成打卡行数：标准 {len(ENT['2026-04']['公司整体'])} vs 不去重 {sum(1 for _d, ts, e_, _n, _b in swipes['2026-04'] if (lambda dt: dt.hour >= 6 and nonwork(dt.date()))(datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')))}。

## 最常见的错法对照（公司整体口径，对不上先来这里找）

| 错法 | 错出来的数 | 标准 |
|---|---|---|
| 漏表单状态过滤（把已驳回也算离职） | {sum(1 for r in exits_apr if r.get('etype') != '外包' and date(2026,4,1) <= r['last'] <= date(2026,4,30))} | {YTD4['公司整体']['离职']} |
| 月入职没排除星耀服务 | {len(joiners)} | {hire_apr['公司整体']['合计']} |
| 覆盖了人工标注的「是否汰换」 | {sum(1 for r in exits_fy25 if r['status'] in ('审批完成','进行中') and th_rule_only(r)=='是')} | {sum(1 for r in exits_fy25 if r['status'] in ('审批完成','进行中') and taihuan(r)=='是')}（FY25 口径示例） |

另外记得：离职表里混着外包行；被驳回的离职者还在在职表里（人数对账时你会遇到他们）；
「管理幅度（主兼岗合计）」的括号是全角的；时间字段至少有四种格式。
"""

open(os.path.join(PKG, "任务书.md"), "w", encoding="utf-8").write(TASKBOOK + TEMPLATE_NOTE)
open(os.path.join(PKG, "口径说明.md"), "w", encoding="utf-8").write(KOUJING)
open(os.path.join(PKG, "答案说明_做完再打开.md"), "w", encoding="utf-8").write(ANSWER_NOTE)

# ── 打 zip ─────────────────────────────────────────────────────
zpath = os.path.join(ROOT, "人力月报任务包.zip")
with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
    for dirp, _dirs, files in os.walk(PKG):
        for fn in sorted(files):
            full = os.path.join(dirp, fn)
            z.write(full, os.path.relpath(full, PKG))
print(f"✓ zip: {os.path.getsize(zpath)/1024:.0f} KB → {zpath}")


n_files = sum(len(fs) for _, _, fs in os.walk(PKG))
print(f"✓ 数据包 {n_files} 个文件 · 在职 {len(roster_mar)}/{len(roster_apr)} · "
      f"离职记录 {len(exits_fy25)+len(exits_apr)+len(exit_noise)} · "
      f"打卡 {sum(len(v) for v in swipes.values())} 行")
print(f"  4月答案（公司整体）: 在职{ANS['公司整体'][0]} 入职{ANS['公司整体'][2]} "
      f"月离职{ANS['公司整体'][6]} YTD离职率{ANS['公司整体'][9]} 入楼{ANS['公司整体'][18]}")
