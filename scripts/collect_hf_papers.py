#!/usr/bin/env python3
"""
HF Daily Papers 収集スクリプト
Claude Code 不要 - HF API から直接データ取得してJekyll Markdownを生成
"""
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from html import escape, unescape
from pathlib import Path
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

JST = timezone(timedelta(hours=9))
REPO_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = REPO_ROOT / "_posts" / "arxiv"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-3.8-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

TAGS_RULES = {
    "agent": ["agent", "agentic", "multi-agent", "tool use", "react", "workflow", "planning"],
    "llm": ["language model", "llm", "large language", "gpt", "rlhf", "rag",
            "chain-of-thought", "reasoning", "instruction", "alignment", "fine-tun"],
    "ml": ["reinforcement learning", "optimization", "training", "generalization",
           "neural network", "gradient", "attention mechanism"],
    "cv": ["image", "video", "vision", "diffusion", "generation", "segmentation",
           "detection", "3d", "rendering", "gan", "vae"],
    "nlp": ["nlp", "text", "translation", "summarization", "sentiment", "parsing",
            "embedding", "tokeniz"],
    "audio": ["audio", "speech", "music", "sound", "voice", "tts", "asr", "acoustic"],
    "quant": ["quantum", "qubit", "quantum circuit"],
}

CSS = """<style>
.tag { font-size: 0.72rem; font-weight: 700; padding: 2px 7px; border-radius: 3px; white-space: nowrap; }
.tag-cv    { color: #1a6bbf; background: #e8f0fb; }
.tag-ml    { color: #6a1b9a; background: #f3e5f5; }
.tag-nlp   { color: #2a8a4a; background: #e6f4ea; }
.tag-agent { color: #bf5a00; background: #fff3e0; }
.tag-audio { color: #c2185b; background: #fce4ec; }
.tag-llm   { color: #00695c; background: #e0f2f1; }
.tag-quant { color: #1a4f7a; background: #e3f0fb; }
.tag-hf    { color: #ff6b35; background: #fff0eb; }
.tag-new   { color: #fff; background: #d32f2f; }
.tag-other { color: #666; background: #f2f2f2; }
.tab-nav { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 1.2rem; }
.tab-btn { padding: 5px 13px; border: none; border-radius: 20px; cursor: pointer; font-size: 0.82rem; font-weight: 700; background: #e8e8e8; color: #444; }
.tab-btn.active { background: #333; color: #fff; }
.paper { margin-bottom: 0; border-top: 1px solid rgba(128,128,128,0.35); padding-top: 1.2rem; margin-top: 0.8rem; }
.paper:first-of-type { border-top: none; padding-top: 0; margin-top: 0; }
.summary-ja { font-size: 0.85rem; line-height: 1.6; color: #999; margin-top: -4px; }
details { margin-top: -6px; }
details summary { cursor: pointer; font-size: 0.82rem; color: #888; }
details blockquote { font-size: 0.85rem; line-height: 1.7; margin: 8px 0 0 0; padding: 8px 12px; color: #bbb; border-left: 3px solid #555; background: transparent; }
</style>"""

TAB_LABELS = [
    ("new", "NEW"), ("agent", "Agent"), ("ml", "ML"), ("cv", "CV"),
    ("nlp", "NLP"), ("llm", "LLM"), ("audio", "Audio"), ("quant", "Quant"),
]

JA_CHAR = re.compile(r"[぀-ヿ一-鿿]")


def build_tab_nav(papers: list[dict]) -> str:
    buttons = [f'  <button class="tab-btn active" onclick="filterTag(\'all\',this)">ALL({len(papers)})</button>']
    for tag, label in TAB_LABELS:
        n = sum(tag in p["tags"] for p in papers)
        buttons.append(f'  <button class="tab-btn" onclick="filterTag(\'{tag}\',this)">{label}({n})</button>')
    return '<div class="tab-nav">\n' + "\n".join(buttons) + "\n</div>"

FILTER_JS = """<script>
function filterTag(tag, btn) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.paper').forEach(p => {
    p.style.display = (tag === 'all' || p.dataset.tags.split(' ').includes(tag)) ? '' : 'none';
  });
}
</script>"""


def assign_tags(paper: dict) -> list[str]:
    text = (
        paper.get("title", "") + " " +
        paper.get("summary", "") + " " +
        " ".join(paper.get("ai_keywords", []))
    ).lower()
    tags = [tag for tag, keywords in TAGS_RULES.items() if any(kw in text for kw in keywords)]
    return tags or ["other"]



def _make_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1.5, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({
        "User-Agent": f"news-claw/1.0 (+{os.environ.get('REPO_URL', 'https://github.com/news-claw')})",
        "Accept": "application/json",
    })
    return session


def fetch_papers(date_str: str) -> list[dict]:
    url = f"https://huggingface.co/api/daily_papers?date={date_str}"
    for attempt in range(3):
        try:
            session = _make_session()
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            print(f"  {date_str}: {len(data)} 件")
            return data
        except Exception as e:
            print(f"  {date_str}: attempt {attempt+1} error ({e})", file=sys.stderr)
            if attempt < 2:
                time.sleep(2 ** attempt)
    return []


# (訳を入れるキー, 原文のキー, 記事HTMLから訳を拾う正規表現, 1リクエストあたりの件数)
TRANSLATE_FIELDS = [
    ("summary_ja", "ai_summary", re.compile(r'<p class="summary-ja">(.*?)</p>'), 30),
    ("abstract_ja", "summary", re.compile(r'<blockquote class="abstract-ja">(.*?)</blockquote>'), 10),
]


def load_previous(today: str) -> tuple[set[str], dict[str, dict[str, str]]]:
    """前日以前の最新記事の論文ID（NEW判定用）と、直近記事の日本語訳キャッシュを返す"""
    files = sorted(OUTPUT_DIR.glob("*-neta-trend-hf.md"))
    prev_ids: set[str] = set()
    for f in reversed(files):
        if f.name[:10] < today:
            prev_ids = set(re.findall(r'arxiv\.org/abs/([0-9.]+)"', f.read_text(encoding="utf-8")))
            break

    # 同日の再実行でも翻訳し直さないよう、日付を問わず直近数件から拾う
    cache: dict[str, dict[str, str]] = {}
    for f in files[-5:]:
        for block in f.read_text(encoding="utf-8").split('<div class="paper"')[1:]:
            m_id = re.search(r'arxiv\.org/abs/([0-9.]+)"', block)
            if not m_id:
                continue
            for key, _, pattern, _ in TRANSLATE_FIELDS:
                m = pattern.search(block)
                if m and JA_CHAR.search(m.group(1)):
                    cache.setdefault(m_id.group(1), {})[key] = unescape(m.group(1))
    return prev_ids, cache


def translate_gemini(texts: list[str]) -> list[str] | None:
    """英文リストを1回のAPI呼び出しで日本語化。失敗時は None"""
    if not GEMINI_API_KEY or not texts:
        return None
    prompt = (
        "Translate each English text in the JSON array below into natural Japanese "
        "for ML researchers. Keep technical terms and model names in English where natural. "
        "Return a JSON array of strings in the same order and of the same length.\n\n"
        + json.dumps(texts, ensure_ascii=False)
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"},
    }
    for attempt in range(3):
        try:
            resp = requests.post(GEMINI_URL, json=payload, headers={"x-goog-api-key": GEMINI_API_KEY}, timeout=180)
            if resp.status_code == 200:
                text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                result = json.loads(text)
                if isinstance(result, list) and len(result) == len(texts) and all(isinstance(s, str) for s in result):
                    return result
                print(f"  [WARN] Gemini 応答の形式不一致: {text[:200]}", file=sys.stderr)
            elif resp.status_code in (429, 503) and attempt < 2:
                wait = (attempt + 1) * 30
                print(f"  [RETRY] HTTP {resp.status_code}, {wait}秒待機...")
                time.sleep(wait)
                continue
            else:
                print(f"  [WARN] Gemini HTTP {resp.status_code}: {resp.text[:300]}", file=sys.stderr)
        except Exception as e:
            print(f"  [WARN] Gemini error: {e}", file=sys.stderr)
        break
    return None


def translate_summaries(papers: list[dict], cache: dict[str, dict[str, str]]) -> None:
    """1行要約とabstractを日本語化。キャッシュにないものだけ Gemini に送り、失敗時は英語のまま"""
    requested = False
    for key, src, _, chunk in TRANSLATE_FIELDS:
        targets = []
        for p in papers:
            cached = cache.get(p["id"], {}).get(key)
            p[key] = cached or p[src]
            if not cached and p[src]:
                targets.append(p)
        done = 0
        for i in range(0, len(targets), chunk):
            if requested:
                time.sleep(15)  # 無料枠のレートリミット対策
            requested = True
            part = targets[i:i + chunk]
            for p, ja in zip(part, translate_gemini([p[src] for p in part]) or []):
                if ja.strip():
                    p[key] = ja.strip()
                    done += 1
        print(f"{key} 翻訳: {done}/{len(targets)} 件（キャッシュ {len(papers) - len(targets)} 件）")


def main():
    now = datetime.now(JST)
    dates = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

    # 7日分を並列取得（max_workers=3でレート制限回避）
    results: dict[str, list] = {}
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(fetch_papers, d): d for d in dates}
        for fut in as_completed(futures):
            d = futures[fut]
            results[d] = fut.result()

    # 重複排除しながら統合
    seen_ids: set[str] = set()
    all_papers: list[dict] = []
    for d in dates:
        for entry in results.get(d, []):
            paper = entry.get("paper", {})
            pid = paper.get("id")
            if not pid or pid in seen_ids:
                continue
            seen_ids.add(pid)
            all_papers.append({
                "id": pid,
                "title": paper.get("title", ""),
                "summary": " ".join((paper.get("summary") or "").split()),
                "upvotes": paper.get("upvotes", 0) or 0,
                "github_stars": paper.get("githubStars", 0) or 0,
                "github_repo": paper.get("githubRepo"),
                "hf_date": d,
                "first_author": ((paper.get("authors") or [{}])[0]).get("name", ""),
                "ai_keywords": paper.get("ai_keywords", []),
                "ai_summary": (paper.get("ai_summary") or "").strip(),
            })

    print(f"取得: {len(all_papers)} 件（重複排除後）")

    # フィルタリング
    filtered = [p for p in all_papers if p["upvotes"] >= 5 or p["github_stars"] >= 10]
    if len(filtered) < 5:
        filtered = [p for p in all_papers if p["upvotes"] >= 2]
    filtered.sort(key=lambda p: p["upvotes"], reverse=True)
    filtered = filtered[:30]

    print(f"フィルタ後: {len(filtered)} 件")

    timestamp = now.strftime("%Y-%m-%d-%H-%M")
    date_label = now.strftime("%Y-%m-%d")
    time_label = now.strftime("%H:%M")

    prev_ids, summary_cache = load_previous(date_label)

    # タグ付け（前日の記事にいなかった論文は new）
    for p in filtered:
        p["tags"] = assign_tags(p)
        p["is_new"] = p["id"] not in prev_ids
        if p["is_new"]:
            p["tags"].append("new")

    translate_summaries(filtered, summary_cache)

    # Markdown生成

    lines: list[str] = [
        "---",
        "layout: post",
        f'title: "{date_label} : トレンド論文"',
        f"date: {date_label} {time_label}:00 +0900",
        "categories: [arxiv]",
        "---",
        "",
        CSS,
        "",
        build_tab_nav(filtered),
        "",
    ]

    for p in filtered:
        tags = p["tags"]
        data_tags = " ".join(tags)
        tag_spans = " ".join(
            f'<span class="tag tag-{t}">{t.upper()}</span>' for t in tags if t != "new"
        )
        new_span = '<span class="tag tag-new">NEW</span> ' if p["is_new"] else ""
        upvote_span = f'<span class="tag tag-hf">▲ {p["upvotes"]} upvotes</span>'
        star_span = (
            f' <span class="tag tag-hf">★ {p["github_stars"]} stars</span>'
            if p["github_stars"] > 0 else ""
        )
        arxiv_url = f'https://arxiv.org/abs/{escape(p["id"])}'
        hf_date = p.get("hf_date", "")
        summary_ja = escape(p.get("summary_ja", ""))
        title_esc = escape(p["title"])
        author_esc = escape(p["first_author"])
        github_repo_url = p["github_repo"] or ""
        if github_repo_url and urlparse(github_repo_url).scheme in ("http", "https"):
            github_link_html = f' · <a href="{escape(github_repo_url, quote=True)}" target="_blank" rel="noopener">GitHub</a>'
        else:
            github_link_html = ""

        detail_lines = [
            f'<div class="paper" data-tags="{data_tags}">',
            f'<p>{new_span}<strong><a href="{arxiv_url}" target="_blank" rel="noopener">{title_esc}</a></strong></p>',
            f'<p>{tag_spans} {upvote_span}{star_span} · {hf_date[5:]} · {author_esc}{github_link_html}</p>',
        ]
        if summary_ja:
            detail_lines.append(f'<p class="summary-ja">{summary_ja}</p>')
        # 改行が入るとkramdownがHTMLブロックを途中で切るので1行にする
        abstract_ja = escape(" ".join(p.get("abstract_ja", "").split()))
        if abstract_ja:
            detail_lines += [
                '<details>',
                '<summary>アブストラクトを読む</summary>',
                f'<blockquote class="abstract-ja">{abstract_ja}</blockquote>',
                '</details>',
            ]
        detail_lines += ["</div>", ""]
        lines += detail_lines

    lines += [FILTER_JS, ""]

    # ファイル保存
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"{timestamp}-neta-trend-hf.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"保存: {out_path}")

    # Slack通知用URLをファイルに書き出す
    date_path = now.strftime("%Y/%m/%d")
    time_slug = now.strftime("%H-%M")
    site_url = os.environ.get("SITE_URL", "https://canon-so8.github.io/news-claw")
    page_url = f"{site_url}/arxiv/{date_path}/{time_slug}-neta-trend-hf/"
    try:
        Path("/tmp/hf_url.txt").write_text(page_url)
    except Exception:
        pass
    return str(out_path)


if __name__ == "__main__":
    main()
