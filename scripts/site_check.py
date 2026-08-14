#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HR AI Builder 全站体检 —— 静态站没有编译期兜底，这是唯一的闸。
用法:  python3 scripts/site_check.py           正常体检
       python3 scripts/site_check.py --self    先跑阴性对照（注入已知错，验刀），再体检

每次改课程/改页面后必跑。退出码非 0 表示有 FAIL。
"""
import json, os, re, subprocess, sys, tempfile, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FE   = os.path.join(ROOT, 'frontend')
SL   = os.path.join(FE, 'slides')

fails, warns = [], []
def FAIL(c, m): fails.append((c, m))
def WARN(c, m): warns.append((c, m))


def load_course(fe=FE):
    """course-data.js 是 JS 不是 JSON，用 node 转出来。"""
    js = os.path.join(fe, 'course-data.js')
    out = subprocess.run(
        ['node', '-e',
         f'const s=require("fs").readFileSync({js!r},"utf8");'
         'const m=s.match(/=\\s*(\\{[\\s\\S]*\\});?\\s*$/);'
         'process.stdout.write(JSON.stringify(eval("("+m[1]+")")))'],
        capture_output=True, text=True)
    if out.returncode:
        FAIL('course-data', f'解析失败: {out.stderr.strip()[:200]}')
        return None
    return json.loads(out.stdout)


def check(fe=FE, sl=SL):
    CO = load_course(fe)
    if not CO:
        return

    lessons, declared = [], []
    for p in CO['parts']:
        for t in p['topics']:
            for l in t['lessons']:
                lessons.append((l, p, t))
                declared.append(l['file'])

    # ── 1. 三方对账：声明 ↔ 磁盘 ↔ 站内链接 ──────────────────
    on_disk = {f for f in os.listdir(sl) if f.endswith('.html')}
    dset = set(declared)
    for f in sorted(dset - on_disk):
        FAIL('对账', f'course-data 声明了但 slides/ 里没有: {f}')
    orphan = on_disk - dset
    for f in sorted(orphan):
        WARN('对账', f'slides/ 里有但没进目录（孤儿页）: {f}')

    linked = set()
    for root, _, files in os.walk(fe):
        for fn in files:
            if not fn.endswith(('.html', '.js')):
                continue
            txt = open(os.path.join(root, fn), encoding='utf-8').read()
            linked |= set(re.findall(r'learn\.html#([\w\-]+\.html)', txt))
    for f in sorted(linked - dset):
        FAIL('对账', f'站内链接指向一个不在目录里的节: learn.html#{f}')

    if len(declared) != len(dset):
        dup = [f for f in dset if declared.count(f) > 1]
        FAIL('对账', f'course-data 里有重复节: {dup}')

    # ── 2. meta 统计数字属实 ────────────────────────────────
    st, acc = CO['meta']['stats'], CO['meta'].get('access', {})
    real_min = sum(l.get('min', 0) for l, _, _ in lessons)
    real_free = sum(1 for l, _, _ in lessons if l.get('free') is not False)
    for label, got, want in [
        ('lessons', st.get('lessons'), len(lessons)),
        ('minutes', st.get('minutes'), real_min),
        ('parts',   st.get('parts'),   len(CO['parts'])),
        ('access.free',   acc.get('free'),   real_free),
        ('access.locked', acc.get('locked'), len(lessons) - real_free),
    ]:
        if got != want:
            FAIL('统计', f'meta.{label} 声明 {got}，实际 {want}')

    # ── 3. 每节自身：kicker / JSON-LD / 标签平衡 ─────────────
    for l, p, t in lessons:
        fp = os.path.join(sl, l['file'])
        if not os.path.exists(fp):
            continue
        s = open(fp, encoding='utf-8').read()

        k = re.search(r'<div class="kicker">([^<]*)</div>', s)
        want = f"{p['num']} · {t['title']}"
        if not k:
            FAIL('kicker', f"{l['file']} 没有 kicker")
        elif k.group(1).strip() != want:
            FAIL('kicker', f"{l['file']} kicker=「{k.group(1).strip()}」应为「{want}」")

        for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
            try:
                json.loads(m.group(1))
            except Exception as e:
                FAIL('JSON-LD', f"{l['file']} 无效: {e}")

        o, c = s.count('<div'), s.count('</div>')
        if o != c:
            FAIL('标签', f"{l['file']} div 不平衡: {o} 开 / {c} 闭")

        # 篇章引用不能超出实际篇章数
        for m in re.finditer(r'第([零一二三四五六七八九])篇章', s):
            n = '零一二三四五六七八九'.index(m.group(1))
            if n >= len(CO['parts']):
                FAIL('引用', f"{l['file']} 引用了不存在的第{m.group(1)}篇章")

    # ── 4. 学习路径完整性（当前无 paths；保留能力，将来若再引入自动生效）──
    for P in CO.get('paths', []):
        files, mins, cnt = [], 0, 0
        for n in P['nights']:
            for it in n['items']:
                files.append(it['file']); cnt += 1
            mins += n.get('min', 0)
            if {x['file'] for x in n['items']} != set(n.get('les', [])):
                FAIL('路径', f"{P['id']} 第{n['n']}晚 items 与 les 不一致")
        for f in files:
            if f not in dset:
                FAIL('路径', f"{P['id']} 引用了不在目录里的节: {f}")
        if P.get('total_les') != cnt:
            FAIL('路径', f"{P['id']} total_les 声明 {P.get('total_les')}，实际 {cnt}")
        if P.get('total_read') != mins:
            FAIL('路径', f"{P['id']} total_read 声明 {P.get('total_read')}，实际 {mins}")

    # ── 5. id 体检：$('#x') 引用的 id 必须在主脚本之前存在 ────
    for page in ('index.html', 'learn.html', 'quiz.html', 'jobs.html'):
        fp = os.path.join(fe, page)
        if not os.path.exists(fp):
            continue
        s = open(fp, encoding='utf-8').read()
        # 最后一个内联 <script>（不带 src）之前的 DOM
        starts = [m.start() for m in re.finditer(r'<script(?![^>]*\bsrc=)', s)]
        if not starts:
            continue
        dom = s[:starts[-1]]
        # 静态 DOM 里的 id + 脚本里用 innerHTML/insertAdjacentHTML 动态生成的 id
        have = set(re.findall(r'\bid="([\w\-]+)"', dom)) | \
               set(re.findall(r'''id=\\?["'#]?([\w\-]+)\\?["']''', s[starts[-1]:]))
        used = set(re.findall(r"""\$\(['"]#([\w\-]+)['"]\)""", s)) | \
               set(re.findall(r"""getElementById\(['"]([\w\-]+)['"]\)""", s))
        miss = used - have
        if miss:
            FAIL('id体检', f'{page} 引用了脚本之前不存在的 id: {sorted(miss)}')

    # ── 5b. 后端映射表对账（Sparky 分诊/面试全靠这张表指路）────
    bp = os.path.join(ROOT, 'backend', 'main.py')
    if os.path.exists(bp):
        bs = open(bp, encoding='utf-8').read()
        if 'TERM_LESSONS' in bs:
            i = bs.index('TERM_LESSONS = {')
            blk = bs[i:bs.index('\n}\n', i)]
            term_ids = set()
            for m in re.finditer(r'"(\w+)":\s*\[(.*?)\]', blk, re.S):
                term_ids.add(m.group(1))
                for f in re.findall(r'"([\w\-]+\.html)"', m.group(2)):
                    if f not in dset:
                        FAIL('后端映射', f'TERM_LESSONS[{m.group(1)}] 指向不在目录里的节: {f}')
            # 每个 TERMS 词条都该有课程映射，否则分诊指不出路
            for m in re.finditer(r'\{"id":\s*"(\w+)"', bs[:i]):
                if m.group(1) not in term_ids:
                    WARN('后端映射', f'词条 {m.group(1)} 没有对应课程（TERM_LESSONS 缺）')
        # 岗位引用的词条必须存在
        all_terms = set(re.findall(r'\{"id":\s*"(\w+)"', bs))
        for m in re.finditer(r'"(?:must|plus)":\s*\[(.*?)\]', bs, re.S):
            for t in re.findall(r'"(\w+)"', m.group(1)):
                if t not in all_terms:
                    FAIL('后端映射', f'岗位引用了不存在的能力词条: {t}')

    # ── 6. 质量红线 ────────────────────────────────────────
    for fn in sorted(on_disk):
        s = open(os.path.join(sl, fn), encoding='utf-8').read()
        for bad, why in [
            ('洛小山', '站内 UI 不该出现原作者署名（LICENSE/README 保留）'),
            ('xueai',  '原站域名残留'),
            ('xsct',   '原站关联站点残留'),
            ('达克鲁宁', '错词，应为达克效应'),
            ('产品经理的', 'PM 受众残留'),
        ]:
            if bad in s:
                FAIL('红线', f'{fn} 出现「{bad}」—— {why}')


def negative_control():
    """阴性对照：往副本里注入 6 类已知错，量具必须全抓到。"""
    tmp = tempfile.mkdtemp(prefix='sitecheck_nc_')
    fe2 = os.path.join(tmp, 'frontend')
    shutil.copytree(FE, fe2)
    sl2 = os.path.join(fe2, 'slides')

    cd = os.path.join(fe2, 'course-data.js')
    s = open(cd, encoding='utf-8').read()
    s = s.replace('"minutes": 584', '"minutes": 999', 1)                       # ① 统计
    s = s.replace('"file": "jargon-why.html"', '"file": "ZZZ-nonexistent.html"', 1)  # ② 声明了不存在的文件
    open(cd, 'w', encoding='utf-8').write(s)

    p = os.path.join(sl2, 'harness-what.html')                                  # ③ kicker 错
    t = open(p, encoding='utf-8').read().replace(
        '<div class="kicker">第七篇章', '<div class="kicker">第二篇章', 1)
    open(p, 'w', encoding='utf-8').write(t)

    p = os.path.join(sl2, 'jargon-eval.html')                                   # ④ 越界引用 + ⑤ 红线词
    t = open(p, encoding='utf-8').read().replace('</main>', '<p>见第九篇章后面的第九篇章</p>\n<p>洛小山</p></main>', 1)
    t = t.replace('第九篇章后面的第九篇章', '第九篇章和不存在的那一章')
    t = t.replace('</main>', '<p>参考 xsct 那个站</p></main>', 1)
    open(p, 'w', encoding='utf-8').write(t)

    # ⑥ 后端映射表死链（Sparky 指路的地基）
    bp2 = os.path.join(tmp, 'backend'); shutil.copytree(os.path.join(ROOT,'backend'), bp2)
    t = open(os.path.join(bp2,'main.py'), encoding='utf-8').read().replace(
        '"eval":           ["eval-why.html"', '"eval":           ["ZZZ-gone.html"', 1)
    open(os.path.join(bp2,'main.py'),'w',encoding='utf-8').write(t)

    global fails, warns
    fails, warns = [], []
    _root_bak = globals()['ROOT']; globals()['ROOT'] = tmp
    check(fe2, sl2)
    globals()['ROOT'] = _root_bak
    shutil.rmtree(tmp)

    cats = {c for c, _ in fails}
    expect = {'统计', '对账', 'kicker', '红线', '后端映射'}
    print('══ 阴性对照（先验刀）══')
    for c, m in fails:
        print(f'   抓到 [{c}] {m[:88]}')
    missed = expect - cats
    if missed:
        print(f'\n   ✕ 量具是钝的：这几类注入的错没抓到 → {missed}')
        return False
    print(f'\n   ✓ 注入的 {len(expect)} 类错全部抓到，量具有效\n')
    return True


if __name__ == '__main__':
    os.chdir(FE)
    if '--self' in sys.argv:
        if not negative_control():
            sys.exit(2)
        fails, warns = [], []

    check()
    print('══ 全站体检 ══')
    if fails:
        for c, m in fails:
            print(f'   ✕ [{c}] {m}')
    if warns:
        for c, m in warns:
            print(f'   ⚠ [{c}] {m}')
    if not fails:
        print(f'   ✓ 全部通过（{len(warns)} 条提醒）')
    sys.exit(1 if fails else 0)
