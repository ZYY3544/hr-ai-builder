#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把前端的课程真相源同步进 backend/lessons/ —— Sparky 的全部课程知识来自这三个文件。

为什么要这一步：后端在 Render 上 rootDir=backend，**运行时读不到 frontend/slides/**，
所以课件内容必须在提交时抽出来放进 backend/。前端永远是唯一真相源，这里只做单向同步。

产出三层（对应 Sparky 看世界的三个分辨率）：
  _index.json     每节 标题/分钟/篇章/一句话讲什么      —— 全量进 prompt，回答"有哪些课"
  _skeleton.json  每节 小节名 + 表头                    —— 全量进 prompt，回答"这节分哪几块、有没有表"
  _text.json      每节 正文纯文本                       —— 按需注入，回答"第三条具体是什么"

为什么必须分层：全量正文 ≈ 13.2 万 token，是模型上下文窗口的 2.1 倍，物理上塞不下；
而骨架只有 8.8k token，装得下。单节正文平均 890 token，用到哪节注入哪节。
三层都查不到的，Sparky 被要求老实说不知道——绝不许猜。

改完课件跑一次本脚本；site_check.py 会校验三个文件与 slides 是否同步，脱节直接 FAIL。
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CD = os.path.join(ROOT, 'frontend', 'course-data.js')
SLIDES = os.path.join(ROOT, 'frontend', 'slides')
OUT_DIR = os.path.join(ROOT, 'backend', 'lessons')


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


def build_index(co):
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
                    'part': p['num'],
                    'part_title': p['title'],
                    'topic': t['title'],
                    'seo': l.get('seo', ''),
                }
    return idx


def _strip(html: str) -> str:
    """扒成纯文本。script/style 整段丢掉，否则 CSS 会被当正文喂给模型。"""
    s = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', html, flags=re.S)
    s = re.sub(r'<br\s*/?>|</p>|</div>|</li>|</tr>', '\n', s)
    s = re.sub(r'<[^>]+>', ' ', s)
    s = (s.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<')
          .replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'"))
    s = re.sub(r'[ \t]+', ' ', s)
    return re.sub(r'\n\s*\n+', '\n', s).strip()


def build_skeleton_and_text(idx):
    """从课件抽骨架与正文。返回 (skeleton, text, 无骨架的节列表)。"""
    skel, text, thin = {}, {}, []
    for f in idx:
        p = os.path.join(SLIDES, f)
        if not os.path.exists(p):
            continue
        html = open(p, encoding='utf-8').read()

        # 小节名：课件里 sec-label 是稳定的结构标记（全站 604 处），h3 作补充
        secs = [re.sub(r'\s+', ' ', x).strip()
                for x in re.findall(r'class="sec-label"[^>]*>(.*?)<', html, re.S)]
        if len(secs) < 2:
            secs += [_strip(x)[:40] for x in re.findall(r'<h3[^>]*>(.*?)</h3>', html, re.S)]
        secs = [s for s in dict.fromkeys(secs) if s]          # 去重保序

        # 表头：用户问"有没有表""表里比了什么"，靠这个答
        tables = []
        for t in re.findall(r'<table.*?</table>', html, re.S):
            th = [_strip(x)[:18] for x in re.findall(r'<th[^>]*>(.*?)</th>', t, re.S)]
            th = [x for x in th if x]
            if th:
                tables.append(th[:6])

        skel[f] = {'secs': secs, 'tables': tables}
        text[f] = _strip(html)
        if not secs and not tables:
            thin.append(f)
    return skel, text, thin


def _dump(name, obj):
    path = os.path.join(OUT_DIR, name)
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)
    return os.path.getsize(path)


if __name__ == '__main__':
    co = load_course()
    idx = build_index(co)
    old = {}
    ip = os.path.join(OUT_DIR, '_index.json')
    if os.path.exists(ip):
        old = json.loads(open(ip, encoding='utf-8').read())

    skel, text, thin = build_skeleton_and_text(idx)

    s1 = _dump('_index.json', idx)
    s2 = _dump('_skeleton.json', skel)
    s3 = _dump('_text.json', text)

    chars = sum(len(v) for v in text.values())
    print(f'✓ _index.json     {len(idx)} 节  ({s1/1024:.0f} KB)')
    print(f'✓ _skeleton.json  {sum(len(v["secs"]) for v in skel.values())} 个小节 / '
          f'{sum(len(v["tables"]) for v in skel.values())} 张表  ({s2/1024:.0f} KB)')
    print(f'✓ _text.json      {chars:,} 字符正文  ({s3/1024:.0f} KB)')
    added = sorted(set(idx) - set(old))
    removed = sorted(set(old) - set(idx))
    if added:
        print(f'  新增 {len(added)}:', *added)
    if removed:
        print(f'  移除 {len(removed)}:', *removed)
    if thin:
        # 抽不出骨架 = Sparky 对这几节只有一句话简介，回答具体问题时会更容易卡壳
        print(f'  ⚠ {len(thin)} 节抽不出小节名或表头，Sparky 对它们只有粗粒度认知:', *thin[:8])
