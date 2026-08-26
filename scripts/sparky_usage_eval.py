# -*- coding: utf-8 -*-
"""Sparky 使用问题评估——「用户关于怎么用这个站的任何问题，都要答清楚」的常设量具。

用法:
    python3 scripts/sparky_usage_eval.py            # 打线上，全量 23 问
    python3 scripts/sparky_usage_eval.py --selfcheck  # 只跑量具自检，不打网络

设计纪律:
- 每个 case 带 expect_any(答案里至少命中一个关键词才算过)。关键词判分只是初筛，
  全文会完整打印——最终裁决靠人读，尤其是阴性对照。
- 阴性对照(kind=negative): 问不存在的功能(APP/视频课/证书/群)，Sparky 必须否认。
  这是防"补完知识后什么都说有"的闸——正向补丁最常见的副作用就是把否认能力冲掉。
- 量具自检(--selfcheck 或每次运行开头自动跑): 拿两条已知错误答案喂判分器，
  抓不住就先修量具再谈结果——量具第一个数默认是假的。
- visitor 用 agenttest- 前缀，FB 落库会被 insights 过滤，不污染改课信号。
- 限流 8/min: 每问间隔 12s，全量约 5 分钟。RPD 80/天，全量一次花 23。
"""
import json
import sys
import time
import urllib.request

API = "https://hr-ai-builder-api.onrender.com/api/sparky/chat"
VISITOR = "agenttest-usage-eval"
GAP_S = 12

# (id, 问题, expect_any 关键词列表, kind)
CASES = [
    # ---- 正向: 站内真实功能/规则,必须答对事实 ----
    ("login",     "怎么登录?需要注册账号密码吗?",              ["微信", "扫码"],                    "positive"),
    ("sync",      "我换了台电脑,之前的学习进度还在吗?",         ["同步", "登录", "账号"],            "positive"),
    ("free-ch",   "不登录能看哪些课?",                        ["第零", "第一"],                    "positive"),
    ("coldstart", "登录怎么一直转圈,等好久了?",                ["冷启动", "20", "等"],              "positive"),
    ("pricing",   "这个网站收费吗?课程以后会收费吗?",           ["永久免费", "免费"],                "positive"),
    ("opensource","你们开源吗?代码在哪里?",                   ["AGPL", "GitHub", "开源"],          "positive"),
    ("quiz-pass", "本章小测怎么才算通关?",                     ["70"],                              "positive"),
    ("wrongbook", "小测做错的题在哪里能再练?",                 ["错题本", "错题"],                  "positive"),
    ("recap",     "成长地图去哪了?我想看我的学习进展",          ["小结", "下线"],                    "positive"),
    ("taskpack",  "实战任务的任务包在哪里领?",                 ["实战任务", "登录"],                "positive"),
    ("review",    "作品评审怎么交?什么价格?",                  ["50", "免费"],                      "positive"),
    ("coach",     "就业辅导怎么开始?",                        ["15 分钟", "免费沟通", "15分钟"],    "positive"),
    ("apply-job", "岗位库里看中一个岗位,怎么投递?",            ["投递", "链接", "官网", "猎聘"],     "positive"),
    ("memory",    "你会记住我们聊过的内容吗?存在哪里?",         ["浏览器", "本地", "不保存"],         "positive"),
    ("sleep",     "你怎么睡着了?怎么叫醒你?",                  ["夜", "23", "碰"],                  "positive"),
    ("ratelimit", "为什么提示我问得太快?",                     ["限", "歇", "快"],                  "positive"),
    ("mobile",    "手机上能用这个网站吗?",                     ["能", "手机", "浏览器"],            "positive"),
    ("contact",   "课程里发现一处错别字,怎么反馈?找谁?",        ["跟我说", "公众号", "记下来", "直接说"], "positive"),
    # ---- 阴性对照: 不存在的功能,必须否认,不许含糊或拿别的顶 ----
    ("neg-app",   "有 APP 或者小程序吗?",                     ["没有"],                            "negative"),
    ("neg-video", "课程有视频版或者直播吗?",                   ["没有", "图文", "文字"],            "negative"),
    ("neg-cert",  "学完有结业证书吗?",                        ["没有"],                            "negative"),
    ("neg-group", "有学习交流群吗?拉我进群呗",                 ["还没", "没建", "没有"],            "negative"),
    ("neg-fapiao","作品评审可以开发票吗?",                    ["公众号", "站主", "表单", "问"],     "negative"),
]


def grade(answer: str, expect_any: list) -> bool:
    a = answer.replace(" ", "")
    return any(k.replace(" ", "") in a for k in expect_any)


def selfcheck() -> bool:
    """量具自检: 已知错误答案必须被抓住,已知正确答案必须放行。"""
    bad = [
        # 若 Sparky 幻觉出 APP,否认词缺席 → 必须 FAIL
        ("neg-app", "有的,我们的 APP 在应用商店搜 meansights 就能下载。"),
        # 若答错解锁规则(说全部要登录),第零/第一缺席 → 必须 FAIL
        ("free-ch", "所有课程都需要登录之后才能阅读。"),
    ]
    good = [
        ("neg-app", "没有 APP 也没有小程序,手机浏览器直接打开就能用。"),
        ("free-ch", "不登录可以直接读第零篇章和第一篇章,其余要登录解锁。"),
    ]
    cases = {c[0]: c for c in CASES}
    ok = True
    for cid, ans in bad:
        if grade(ans, cases[cid][2]):
            print(f"  自检 FAIL: 错误答案未被抓住 [{cid}] {ans[:30]}"); ok = False
    for cid, ans in good:
        if not grade(ans, cases[cid][2]):
            print(f"  自检 FAIL: 正确答案被误杀 [{cid}] {ans[:30]}"); ok = False
    print("  量具自检:", "通过" if ok else "不通过——先修量具,结果无效")
    return ok


def ask(q: str):
    body = json.dumps({
        "messages": [{"role": "user", "content": q}],
        "ctx": {"page": "index", "done": [], "visitor": VISITOR},
    }).encode()
    req = urllib.request.Request(API, data=body,
                                 headers={"Content-Type": "application/json"})
    text, err = [], None
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            for raw in r:
                line = raw.decode("utf-8", "ignore").strip()
                if not line.startswith("data: "):
                    continue
                try:
                    obj = json.loads(line[6:])
                except Exception:
                    continue
                if obj.get("t") == "delta":
                    text.append(obj.get("text", ""))
                elif obj.get("t") == "err":
                    err = obj.get("msg")
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
    return "".join(text).strip(), err


def main():
    print("== 量具自检 ==")
    if not selfcheck():
        sys.exit(2)
    if "--selfcheck" in sys.argv:
        return
    only = [a for a in sys.argv[1:] if not a.startswith("-")]
    cases = [c for c in CASES if not only or c[0] in only]
    results = []
    for i, (cid, q, expect, kind) in enumerate(cases):
        if i:
            time.sleep(GAP_S)
        ans, err = ask(q)
        ok = (not err) and grade(ans, expect)
        results.append((cid, kind, ok))
        mark = "✓" if ok else "✗"
        print(f"\n{'='*64}\n{mark} [{cid}|{kind}] Q: {q}")
        if err:
            print(f"  ERR: {err}")
        print(f"  A: {ans}")
        sys.stdout.flush()
    npass = sum(1 for *_, ok in results if ok)
    print(f"\n{'='*64}\n通过 {npass}/{len(results)}")
    fails = [(cid, kind) for cid, kind, ok in results if not ok]
    if fails:
        print("未过:", fails)
    print("⚠️ 关键词判分只是初筛,阴性对照请通读全文确认没有含糊其辞。")
    sys.exit(0 if not fails else 1)


if __name__ == "__main__":
    main()
