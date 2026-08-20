#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按公司名查猎聘的公司 id（scan_liepin_company.py 要用它当入口）。

猎聘的公司搜索 /companys/?key=<名> 是匿名可读的。返回按相关度排的候选，
**不自动选第一个**——同名/近名公司很多（搜「美团」会先出「昆山瑞世洛斯自动化」
这种毫不相干的），必须人眼确认再用。宁可多打印几个，也不要猜错公司扫半天。

用法：
    python3 scripts/liepin_company_id.py 美团 阿里巴巴 腾讯 小米
"""
import html
import re
import sys
import time

import requests

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")


def search(s, name: str, top: int = 6) -> list:
    r = s.get("https://www.liepin.com/companys/", params={"key": name}, timeout=25)
    r.raise_for_status()
    # <a href=".../company/123/" ...><div class="company-left"><div class="company-name">名</div>
    #   <div class="company-tip"><span>行业</span><span>规模</span>…
    out = []
    for m in re.finditer(
            r'/company/(\d+)/"[^>]*>.*?class="company-name">(.*?)</div>'
            r'(.*?)</li>', r.text, re.S):
        cid, cname, rest = m.group(1), m.group(2), m.group(3)
        cname = re.sub(r"<[^>]+>", "", html.unescape(cname)).strip()
        tips = [re.sub(r"<[^>]+>", "", html.unescape(x)).strip()
                for x in re.findall(r"<span>(.*?)</span>", rest, re.S)][:3]
        out.append((cid, cname, " · ".join(t for t in tips if t)))
        if len(out) >= top:
            break
    return out


def main():
    if len(sys.argv) < 2:
        sys.exit("用法：python3 scripts/liepin_company_id.py <公司名> [公司名 …]")
    s = requests.Session()
    s.headers["User-Agent"] = UA
    for i, name in enumerate(sys.argv[1:]):
        if i:
            time.sleep(2)
        print(f"\n【{name}】")
        try:
            res = search(s, name)
        except Exception as e:
            print(f"  查询失败：{e}")
            continue
        if not res:
            print("  没搜到——换个更完整的名字试试（如「北京三快在线科技」）")
        for cid, cname, tip in res:
            print(f"  {cid:<10} {cname[:28]:30s} {tip}")


if __name__ == "__main__":
    main()
