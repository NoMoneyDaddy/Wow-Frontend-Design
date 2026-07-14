#!/usr/bin/env python3
"""Advisory source-signal checks; browser behavior is evaluated separately."""

import re
from pathlib import Path


ROOT = Path(__file__).parent
html = (ROOT / "index.html").read_text(encoding="utf-8")
css = (ROOT / "styles.css").read_text(encoding="utf-8")
js = (ROOT / "app.js").read_text(encoding="utf-8")
theme_init = (ROOT / "theme-init.js").read_text(encoding="utf-8")
js_without_comments = re.sub(r"//.*?$|/\*.*?\*/", "", js, flags=re.MULTILINE | re.DOTALL)

requirements = {
    "traditional Chinese language tag": 'lang="zh-Hant"' in html,
    "filter behavior preserved": "data-filter" in html and "product.dataset.category" in js_without_comments,
    "favorite behavior preserved": "data-favorite" in html and "favoriteCount" in js_without_comments,
    "newsletter behavior preserved": "newsletter-form" in html and "checkValidity" in js_without_comments,
    "mobile-specific CSS exists": "@media" in css,
    "reduced motion considered": "prefers-reduced-motion" in css,
    "visible keyboard focus exists": "focus-visible" in css,
    "three-state appearance control exists": all(
        value in html for value in ('value="system"', 'value="light"', 'value="dark"')
    ),
    "theme preference is initialized before CSS": 'src="theme-init.js"' in html
    and html.index('src="theme-init.js"') < html.index('rel="stylesheet"')
    and "localStorage" in theme_init,
    "system and forced color paths exist": "prefers-color-scheme" in css
    and "forced-colors" in css,
    "demo form does not claim delivery": "訂閱成功" not in js_without_comments
    and "沒有送出或儲存" in js_without_comments,
    "form exposes recoverable invalid state": 'aria-describedby="form-note form-status"' in html
    and 'id="form-note"' in html
    and "setAttribute('aria-invalid', 'true')" in js_without_comments
    and "removeAttribute('aria-invalid')" in js_without_comments,
}

failed = [name for name, passed in requirements.items() if not passed]
for name, passed in requirements.items():
    print(f"{'FOUND' if passed else 'MISSING'}: {name}")
raise SystemExit(1 if failed else 0)
