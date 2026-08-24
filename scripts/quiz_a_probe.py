# -*- coding: utf-8 -*-
"""判断题对话(quizA)探针——「Sparky 绝不宣判对错、绝不打分」的常设量具。

用法:
    python3 scripts/quiz_a_probe.py --selfcheck     # 只跑量具自检,不打网络
    python3 scripts/quiz_a_probe.py                 # 匿名 401 闸测试
    QTOKEN=<jwt> python3 scripts/quiz_a_probe.py    # 加跑登录态真实对话(3 轮)

设计纪律:
- 阴性对照先行:宣判检测器必须先抓住合成坏样本(「你答错了」「85 分」),
  抓不住就退出码 2,后面的数一个都不能报——量具第一个数默认是假的。
- 登录态用 QTOKEN 环境变量传入,visitor 用 agenttest- 前缀(insights 会滤掉)。
- quizA 每天 45 次/用户,一次全量探针花 3 次,别连跑。
"""
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error

API = "https://hr-ai-builder-api.onrender.com/api/sparky/chat"
VISITOR = "agenttest-quiza-probe"
# 抽固定三道 p-1 的 A 题,探针可复现(id 存在性由服务端校验,失效会 400 提示换题)
IDS = ["p1-26", "p1-24", "p1-28"]

# 宣判词:Sparky 在 quizA 模式的正文里绝不该出现的说法
VERDICT = [r"答对了", r"答错了", r"回答正确", r"回答错误", r"正确答案是",
           r"你错了", r"你对了", r"\d+\s*分\b", r"得分", r"不及格", r"通过率"]
_V = [re.compile(p) for p in VERDICT]


def verdicts_in(text: str) -> list:
    return [p.pattern for p in _V if p.search(text)]


def selfcheck() -> bool:
    bad = ["你答错了，正确答案是C。", "回答正确！这题你拿 85 分。", "很遗憾，不及格。"]
    good = ["课程的参照思路是先回捞被拒池——你的回答少了时间窗这个环节,差别在抽样方式上。",
            "你的思路比参照更谨慎,两条路的代价不一样:参照赌的是根因未知。"]
    ok = True
    for t in bad:
        if not verdicts_in(t):
            print(f"  自检 FAIL: 坏样本漏网: {t}"); ok = False
    for t in good:
        if verdicts_in(t):
            print(f"  自检 FAIL: 好样本误杀: {t} -> {verdicts_in(t)}"); ok = False
    print("  量具自检:", "通过" if ok else "不通过——先修量具,结果无效")
    return ok


def ask(messages, token=None):
    body = json.dumps({"messages": messages,
        "ctx": {"page": "learn", "mode": "quizA", "quiz_ids": IDS,
                "done": [], "visitor": VISITOR}}).encode()
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = "Bearer " + token
    req = urllib.request.Request(API, data=body, headers=h)
    text, err = [], None
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            for raw in r:
                line = raw.decode("utf-8", "ignore").strip()
                if not line.startswith("data: "):
                    continue
                try:
                    o = json.loads(line[6:])
                except Exception:
                    continue
                if o.get("t") == "delta":
                    text.append(o.get("text", ""))
                elif o.get("t") == "err":
                    err = o.get("msg")
    except urllib.error.HTTPError as e:
        err = f"HTTP{e.code}: {e.read().decode('utf-8','ignore')[:160]}"
    except Exception as e:
        err = str(e)
    return "".join(text).strip(), err


def main():
    print("== 量具自检 ==")
    if not selfcheck():
        sys.exit(2)
    if "--selfcheck" in sys.argv:
        return

    print("\n== 结构闸:匿名必须 401 ==")
    _, err = ask([{"role": "user", "content": "开始吧"}])
    ok401 = err and "401" in err
    print(("  ✓ 匿名被拦: " + err[:70]) if ok401 else f"  ✗ 没拦住: {err}")

    token = os.environ.get("QTOKEN", "").strip()
    if not token:
        print("\n(未设 QTOKEN,登录态对话质量部分跳过)")
        sys.exit(0 if ok401 else 1)

    print("\n== 登录态对话质量(4 轮) ==")
    hist, fails = [], []
    turns = [
        "开始吧,出第一道",
        # 故意给一个明显偏离参照的回答——阴性场景:即便答得糙,Sparky 也不许宣判"错"
        "我觉得应该立刻下线这个 agent,改回全人工,稳妥第一",
        "嗯,那按你说的参照,我重新想:先把这个案例加进评测集,再抽同期被拒的人工复核一遍",
        # 第二次作答已给出——按硬闸,这轮之后必须出参照,不许再追问
        "按临界分数段抽,发现漏人就先查根因,再决定动不动阈值",
    ]
    saw_ref = False
    for i, u in enumerate(turns):
        if i:
            time.sleep(12)
        hist.append({"role": "user", "content": u})
        a, err = ask(hist[-8:], token)
        hist.append({"role": "assistant", "content": a})
        print(f"\n--- 第{i+1}轮 ---\nU: {u}\nS: {a}")
        if err:
            fails.append(f"轮{i+1} ERR {err}")
        v = verdicts_in(a)
        if v:
            fails.append(f"轮{i+1} 出现宣判词: {v}")
        if re.search(r"参照", a):
            saw_ref = True
    if not saw_ref:
        fails.append("四轮里从未给出「参照」思路")
    print("\n======")
    print("结论:", "✓ 全过(无宣判/有参照/匿名被拦)" if (not fails and ok401) else f"✗ {fails}")
    sys.exit(0 if (not fails and ok401) else 1)


if __name__ == "__main__":
    main()
