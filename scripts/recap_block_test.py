"""recap 学习小结的区间聚合单测（不碰生产库：store 全部 stub）。
改 _recap_block 后必跑：venv/bin/python scripts/recap_block_test.py
为什么要有它：LESSON_IDX 是 make_router 的参数不是全局，模块级函数直接引用会 NameError——
这类作用域错在线上只有真点一次才炸，而那一次会写掉用户的「上次小结」标记。
含阴性对照：上次小结之前的记录必须被排除（断言 怎样学 not in out）。"""
import sys, types
sys.path.insert(0, '/Users/zy/Desktop/HR-AI-Builder/backend')

# stub store：不碰生产库
fake = types.ModuleType('store')
ROWS = [
    {"kind": "recap", "key": "sparky", "created_at": "2026-08-20T02:00:00+00:00", "value": {}},
    {"kind": "done", "key": "start-dunning-kruger.html", "created_at": "2026-08-22T03:00:00+00:00", "value": {"on": True}},
    {"kind": "done", "key": "hallu-fix-prompt.html", "created_at": "2026-08-23T03:00:00+00:00", "value": {"on": True}},
    {"kind": "done", "key": "不存在的节.html", "created_at": "2026-08-23T04:00:00+00:00", "value": {"on": True}},
    {"kind": "quiz", "key": "p-1", "created_at": "2026-08-24T03:00:00+00:00", "value": {"correct": 5, "n": 8}},
    {"kind": "done", "key": "start-how-to-learn.html", "created_at": "2026-08-18T03:00:00+00:00", "value": {"on": True}},  # 上次小结之前，应被排除
]
fake.user_progress = lambda uid, limit=2000: ROWS
fake.now_iso = lambda: "2026-08-26T02:50:00+00:00"
fake.add_progress = lambda *a, **k: True
fake.add_feedback = lambda *a, **k: True
fake.add_signal = lambda *a, **k: True
fake.hard_lessons = lambda *a, **k: []
fake.is_test_row = lambda r: False
fake.store = object()
fake.PROGRESS='hab_progress'
sys.modules['store'] = fake

import sparky
IDX = {
  "start-dunning-kruger.html": {"part": "第零篇章", "title": "我们在哪里？达克效应"},
  "hallu-fix-prompt.html": {"part": "第一篇章", "title": "把约束写进 Prompt"},
  "start-how-to-learn.html": {"part": "第零篇章", "title": "怎样学"},
}
out = sparky._recap_block("ms:test", IDX, "p-1 现存错题 3 道；p-zero 现存错题 1 道")
print(out)
print("=== 断言 ===")
assert "达克效应" in out and "把约束写进 Prompt" in out, "读过的节没进去"
assert "怎样学" not in out, "上次小结之前的记录没被排除"
assert "第一篇章小测：累计答 8 题对 5 题" in out, "小测聚合不对"
assert out.index("达克效应") < out.index("把约束写进 Prompt"), "时间序不对(应旧→新)"
assert "第一篇章 现存错题 3 道" in out, "错题章代码没转中文"
assert "上次小结时间：2026-08-20" in out
print("全部通过")

# 边界：无任何记录
fake.user_progress = lambda uid, limit=2000: []
out2 = sparky._recap_block("ms:new", IDX, "")
assert "第一次小结" in out2 and "没有新的阅读或小测记录" in out2
print("空轨迹分支通过")
