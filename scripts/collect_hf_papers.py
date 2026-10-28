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
# 普段は flash-lite（モデル一覧から最新の安定版を選ぶ）。混雑時の予備がこちら
GEMINI_BACKUP_MODEL = "gemini-3.8-flash"
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"

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
details { margin-top: -6px; }
details summary { cursor: pointer; font-size: 0.82rem; color: #111; }
details blockquote { font-size: 0.85rem; line-height: 1.7; margin: 8px 0 0 0; padding: 8px 12px; color: #333; border-left: 3px solid #ddd; background: transparent; }
</style>"""

TAB_LABELS = [
    ("new", "NEW"), ("agent", "Agent"), ("ml", "ML"), ("cv", "CV"),
    ("nlp", "NLP"), ("llm", "LLM"), ("audio", "Audio"), ("quant", "Quant"),
]


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


ELI5_KEYS = [("problem", "どんな問題？"), ("idea", "どうやった？"), ("impact", "何がうれしい？")]
ELI5_CHUNK = 5
# プロンプトを変えたら上げる。古い版の要約はキャッシュとして使わず作り直す
ELI5_VERSION = 2
# Geminiに使う合計時間の上限。超えた分は英語abstractで出し、次回の実行で要約する
GEMINI_BUDGET_SEC = 300

ELI5_PROMPT = """あなたは機械学習の論文を、専門外のエンジニアにも一読で分かるように紹介する解説者です。
下のJSON配列の各要素（title と abstract）について、ELI5（5歳児にも分かるくらい噛み砕く）の考え方で、次の3項目を日本語で書いてください。

- problem: どんな困りごとを解決したいのか。それがなぜ困るのか、背景も含めて書く
- idea: どうやって解決したのか。仕組みを順を追って書き、できるだけ身近なもののたとえを使う（無理なたとえは不要）
- impact: 結果として何がうれしいのか。それで何ができるようになるかまで書く。abstractに数値があれば1〜2個入れる

書き方のルール:
- 各項目は2〜3文、100〜150字。「〜する」「〜だ」の常体で書く
- 専門用語は必要なときだけ使い、初出で（）に一言の説明を付ける。例: ファインチューニング（学習済みモデルの追加学習）
- モデル名・手法名・データセット名は英語のまま
- abstractに書かれていないことは書かない。誇張しない

入力と同じ順番・同じ件数で返すこと。

"""

ELI5_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {k: {"type": "STRING"} for k, _ in ELI5_KEYS},
        "required": [k for k, _ in ELI5_KEYS],
    },
}


def load_previous(today: str) -> tuple[set[str], dict[str, dict[str, str]]]:
    """前日以前の最新記事の論文ID（NEW判定用）と、直近記事のELI5要約キャッシュを返す"""
    files = sorted(OUTPUT_DIR.glob("*-neta-trend-hf.md"))
    prev_ids: set[str] = set()
    for f in reversed(files):
        if f.name[:10] < today:
            prev_ids = set(re.findall(r'arxiv\.org/abs/([0-9.]+)"', f.read_text(encoding="utf-8")))
            break

    # 同日の再実行でも要約し直さないよう、日付を問わず直近数件から拾う
    cache: dict[str, dict[str, str]] = {}
    for f in files[-5:]:
        for block in f.read_text(encoding="utf-8").split('<div class="paper"')[1:]:
            m_id = re.search(r'arxiv\.org/abs/([0-9.]+)"', block)
            m_eli5 = re.search(rf'<details data-eli5="([^"]*)" data-v="{ELI5_VERSION}">', block)
            if m_id and m_eli5:
                try:
                    cache[m_id.group(1)] = json.loads(unescape(m_eli5.group(1)))
                except json.JSONDecodeError:
                    pass
    return prev_ids, cache


# thinkingLevel に対応していなかったモデル
_no_thinking_models: set[str] = set()
# 1日の無料枠を使い切ったモデル（枠はモデルごとに別）
_exhausted_models: set[str] = set()


def gemini_models() -> list[str]:
    """flash-lite の最新安定版を先頭に、混雑・枠切れ時の予備として GEMINI_BACKUP_MODEL を後ろに並べる"""
    lite = os.environ.get("GEMINI_MODEL", "")
    if not lite and GEMINI_API_KEY:
        try:
            resp = requests.get(f"{GEMINI_API_BASE}/models", params={"pageSize": 1000},
                                headers={"x-goog-api-key": GEMINI_API_KEY}, timeout=30)
            resp.raise_for_status()
            names = [m["name"].removeprefix("models/") for m in resp.json().get("models", [])
                     if "generateContent" in m.get("supportedGenerationMethods", [])]
            lites = [n for n in names if "flash-lite" in n and not re.search(r"preview|exp|tts|image|live", n)]
            if lites:
                lite = max(lites, key=lambda n: [int(x) for x in re.findall(r"\d+", n)])
        except Exception as e:
            print(f"  [WARN] Gemini モデル一覧の取得に失敗: {e}", file=sys.stderr)
    models = ([lite] if lite and lite != GEMINI_BACKUP_MODEL else []) + [GEMINI_BACKUP_MODEL]
    print(f"Gemini モデル: {models}")
    return models


def _request_gemini(model: str, items: list[dict], n: int) -> list[dict[str, str]] | None:
    """1モデルに1回だけ送る。失敗理由はログに出して None"""
    config = {
        "temperature": 0.3,
        "responseMimeType": "application/json",
        "responseSchema": ELI5_SCHEMA,
    }
    if model not in _no_thinking_models:
        config["thinkingConfig"] = {"thinkingLevel": "low"}
    payload = {
        "contents": [{"parts": [{"text": ELI5_PROMPT + json.dumps(items, ensure_ascii=False)}]}],
        "generationConfig": config,
    }
    url = f"{GEMINI_API_BASE}/models/{model}:generateContent"
    try:
        resp = requests.post(url, json=payload, headers={"x-goog-api-key": GEMINI_API_KEY}, timeout=90)
        if resp.status_code == 400 and "thinkingConfig" in config and "thinking" in resp.text.lower():
            print(f"  [WARN] {model}: thinkingConfig 非対応のため外して再試行", file=sys.stderr)
            _no_thinking_models.add(model)
            return _request_gemini(model, items, n)
        if resp.status_code == 200:
            text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            result = json.loads(text)
            if (isinstance(result, list) and len(result) == n
                    and all(all(str(r.get(k, "")).strip() for k, _ in ELI5_KEYS) for r in result)):
                return [{k: " ".join(str(r[k]).split()) for k, _ in ELI5_KEYS} for r in result]
            print(f"  [WARN] {model}: 応答の形式不一致: {text[:200]}", file=sys.stderr)
        elif resp.status_code == 429 and "PerDay" in resp.text:
            quota_ids = sorted(set(re.findall(r'"quotaId":\s*"([^"]+)"', resp.text)))
            print(f"  [WARN] {model}: 1日の無料枠を使い切ったので今回は使わない {quota_ids}", file=sys.stderr)
            _exhausted_models.add(model)
        else:
            quota_ids = sorted(set(re.findall(r'"quotaId":\s*"([^"]+)"', resp.text)))
            print(f"  [WARN] {model}: HTTP {resp.status_code} {quota_ids or resp.text[:150]}", file=sys.stderr)
    except Exception as e:
        print(f"  [WARN] {model}: {e}", file=sys.stderr)
    return None


def summarize_gemini(papers: list[dict], models: list[str], deadline: float) -> list[dict[str, str]] | None:
    """論文リストをELI5要約。混雑・タイムアウト時は待たずに次のモデルへ切り替え、全滅なら少し待ってもう1巡。
    失敗したモデルは models の末尾に回すので、次の呼び出しは直前に成功したモデルから試す"""
    if not GEMINI_API_KEY or not papers:
        return None
    items = [{"title": p["title"], "abstract": p["summary"]} for p in papers]
    for round_ in range(2):
        if round_:
            time.sleep(15)
        for model in list(models):
            if model in _exhausted_models:
                continue
            if time.monotonic() > deadline:
                print("  [WARN] Gemini の時間上限に達したため中断", file=sys.stderr)
                return None
            result = _request_gemini(model, items, len(papers))
            if result:
                return result
            models.remove(model)
            models.append(model)
    return None


def summarize_papers(papers: list[dict], cache: dict[str, dict[str, str]]) -> None:
    """キャッシュにない論文だけ Gemini でELI5要約。失敗した論文は英語abstractのまま"""
    targets = []
    for p in papers:
        p["eli5"] = cache.get(p["id"])
        if not p["eli5"] and p["summary"]:
            targets.append(p)
    done = 0
    if targets and GEMINI_API_KEY:
        models = gemini_models()
        deadline = time.monotonic() + GEMINI_BUDGET_SEC
        for i in range(0, len(targets), ELI5_CHUNK):
            if time.monotonic() > deadline or all(m in _exhausted_models for m in models):
                break
            if i:
                time.sleep(5)  # 無料枠の1分あたり上限対策
            part = targets[i:i + ELI5_CHUNK]
            for p, r in zip(part, summarize_gemini(part, models, deadline) or []):
                p["eli5"] = r
                done += 1
    print(f"ELI5要約: {done}/{len(targets)} 件（キャッシュ {len(papers) - len(targets)} 件）")


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

    summarize_papers(filtered, summary_cache)

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
        # 改行が入るとkramdownがHTMLブロックを途中で切るので1行にする
        if p["eli5"]:
            eli5_attr = escape(json.dumps(p["eli5"], ensure_ascii=False), quote=True)
            body = "<br>".join(f'<b>{label}</b> {escape(p["eli5"][k])}' for k, label in ELI5_KEYS)
            detail_lines += [
                f'<details data-eli5="{eli5_attr}" data-v="{ELI5_VERSION}">',
                '<summary>要約を読む</summary>',
                f'<blockquote>{body}</blockquote>',
                '</details>',
            ]
        elif p["summary"]:
            detail_lines += [
                '<details>',
                '<summary>Abstract（英語）</summary>',
                f'<blockquote>{escape(p["summary"])}</blockquote>',
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
