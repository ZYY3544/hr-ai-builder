#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 frontend/course-data.js（唯一真相源）重新生成 backend/lessons/_index.json。

为什么存在：后端的课程清单（登录闸、Sparky 指路的封闭集合）曾与前端脱节
——前端加了节、改了标题，后端没人同步。改完课程跑一次本脚本即可；
site_check.py 会校验两者一致，脱节直接 FAIL。
"""
import json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CD   = os.path.join(ROOT, 'frontend', 'course-data.js')
OUT  = os.path.join(ROOT, 'backend', 'lessons', '_index.json')


def load_course():
    out = subprocess.run(
        ['node', '-e',
         f'const s=require("fs").readFileSync({CD!r},"utf8");'
         'const m=s.match(/=\\s*(\\{[\\s\\S]*\\});?\\s*$/);'
         'process.stdout.write(JSON.stringify(eval("("+m[1]+")")))'],
        capture_output=True, text=True)
    if out.returncode:
        sys.exit(f'course-data.js 解析失败: {out.stderr[:200]}')
    return json.loads(out.stdout)


def build(co):
    idx = {}
    for p in co['parts']:
        for t in p['topics']:
            for l in t['lessons']:
                idx[l['file']] = {
                    'title': l['title'],
                    'free': l.get('free') is not False,
                    'ready': bool(l.get('ready')),
                    'ksa': l.get('ksa', ''),
                    'min': l.get('min', 0),
                    'part': p['num'],           # 如「第六篇章」
                    'part_title': p['title'],
                    'topic': t['title'],
                    'seo': l.get('seo', ''),
                }
    return idx


if __name__ == '__main__':
    idx = build(load_course())
    old = {}
    if os.path.exists(OUT):
        old = json.loads(open(OUT, encoding='utf-8').read())
    json.dump(idx, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    added   = sorted(set(idx) - set(old))
    removed = sorted(set(old) - set(idx))
    print(f'✓ _index.json 已重生成：{len(idx)} 节'
          f'（新增 {len(added)}，移除 {len(removed)}）')
    for f in added:   print(f'   + {f}')
    for f in removed: print(f'   - {f}')
