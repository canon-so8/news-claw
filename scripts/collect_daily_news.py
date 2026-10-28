#!/usr/bin/env python3
"""
デイリーニュース収集スクリプト
Claude Code 不要 - RSS/API から直接データ取得してJekyll Markdownを生成

ソース:
  - Zenn   : API (liked_count付き)
  - Qiita  : API v2 (likes_count付き)
  - はてな  : RSS/RDF (bookmarkcount付き)
  - HN     : Algolia API + DeepL（タイトル日本語訳）

※ 商用メディア（ITmedia・東洋経済等）はSlack配信の利用規約リスクのため除外
"""
import html
import json
import os
import re
import sys
import time
import urllib.parse
from defusedxml import ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

JST = timezone(timedelta(hours=9))
REPO_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = REPO_ROOT / "_posts" / "daily_news"

KINDLE_DAILY_URL = (
    "https://www.amazon.co.jp/kindle-dbs/browse/"
    "?_encoding=UTF8"
    "&metadata=storeType%3Debooks"
    "&widgetId=ebooks-deals-storefront_KindleDailyDealsStrategy"
    "&title=Kindle%E6%97%A5%E6%9B%BF%E3%82%8F%E3%82%8A%E3%82%BB%E3%83%BC%E3%83%AB"
    "&sourceType=recs"
)

# RSS 名前空間
RSS1   = "http://purl.org/rss/1.0/"
DC     = "http://purl.org/dc/elements/1.1/"
ATOM   = "http://www.w3.org/2005/Atom"
RDF    = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
HATENA = "http://www.hatena.ne.jp/info/xmlns#"

# --- 分野判定（1記事1分野。タイトル一致3点・説明文一致1点で最高点の分野、同点は GENRES の順）---
GENRES: list[tuple[str, str, list[str]]] = [
    ("sec", "セキュリティ", [
        "セキュリティ", "security", "脆弱性", "vulnerability", "cve", "サイバー", "cyber",
        "攻撃", "attack", "不正アクセス", "不正ログイン", "乗っ取り", "情報漏洩", "漏洩", "流出",
        "leak", "breach", "マルウェア", "malware", "ランサムウェア", "ransomware",
        "フィッシング", "phishing", "ゼロデイ", "zero-day", "サプライチェーン攻撃",
        "認証", "authentication", "認可", "oauth", "oidc", "sso", "パスワード", "password",
        "パスキー", "passkey", "xss", "csrf", "インジェクション", "injection",
        "ペネトレーション", "pentest", "ゼロトラスト", "zero trust", "暗号化", "encryption",
        "証明書", "tls", "ssl", "権限", "active directory", "セキュア", "secure",
        "プライバシー", "privacy", "ハッキング", "siem", "waf",
        "情報漏えい", "ハッカー", "hacker", "hacked", "exploit", "pwned", "スパイ", "spy", "otp", "bypass", "credential", "脅威", "threat", "詐欺", "fraud", "scam", "スパム", "spam", "csp", "certificate authority", "不正", "被害",
    ]),
    ("agent", "AIエージェント", [
        "aiエージェント", "ai agent", "エージェント", "agent", "agentic", "マルチエージェント",
        "サブエージェント", "subagent", "コーディングエージェント", "coding agent",
        "claude code", "codex", "cursor", "copilot", "devin", "cline", "windsurf", "kiro",
        "aider", "gemini cli", "claude.md", "agents.md", "mcp", "a2a",
        "langgraph", "langchain", "crewai", "autogen", "smolagents", "mastra",
        "computer use", "browser use", "tool use", "tool calling", "function calling",
        "バイブコーディング", "vibe coding", "ai駆動開発", "ハーネスエンジニアリング",
        "コンテキストエンジニアリング", "context engineering",
        "llmエージェント", "ハーネス", "harness", "skill", "skills", "tool-call", "kimi code",
    ]),
    ("llm", "LLM・生成AI", [
        "llm", "llms", "大規模言語モデル", "言語モデル", "生成ai", "generative ai", "ai",
        "人工知能", "chatgpt", "gpt", "openai", "anthropic", "claude", "gemini", "gemma",
        "llama", "mistral", "qwen", "deepseek", "grok", "notebooklm", "perplexity",
        "rag", "プロンプト", "prompt", "ファインチューニング", "fine-tun", "lora",
        "embedding", "埋め込み", "ベクトル検索", "vector", "チャットボット", "chatbot",
        "推論モデル", "reasoning model", "トークン",
        "fable", "opus", "sonnet", "haiku", "vllm", "ollama", "litellm", "lfm", "kimi", "sarashina", "国産モデル", "model training",
    ]),
    ("ml", "ML・データ", [
        "機械学習", "深層学習", "強化学習", "ニューラル", "machine learning", "deep learning",
        "reinforcement learning", "neural", "pytorch", "tensorflow", "jax", "kaggle",
        "transformer", "diffusion", "画像認識", "画像生成", "動画生成", "物体検出",
        "セグメンテーション", "ocr", "yolo", "コンピュータビジョン", "computer vision",
        "音声認識", "音声合成", "tts", "asr", "データ分析", "データサイエンス", "data science",
        "統計", "statistics", "pandas", "polars", "numpy", "scikit-learn", "xgboost", "lightgbm",
        "特徴量", "回帰", "時系列", "レコメンド", "推薦", "論文", "arxiv", "paper", "研究",
        "research", "量子", "quantum", "ロボット", "robot", "自動運転", "データ基盤", "etl",
        "dbt", "bigquery", "snowflake", "databricks",
        "visual", "vision", "3d", "数学", "mathematics", "spss", "判別モデル",
    ]),
    ("infra", "インフラ・運用", [
        "aws", "gcp", "google cloud", "azure", "クラウド", "cloud", "kubernetes", "k8s",
        "docker", "コンテナ", "container", "terraform", "ansible", "インフラ", "infrastructure",
        "サーバーレス", "serverless", "lambda", "cloud run", "ecs", "eks", "fargate",
        "cloudflare", "vercel", "netlify", "デプロイ", "deploy", "ci/cd", "github actions",
        "監視", "monitoring", "オブザーバビリティ", "observability", "opentelemetry",
        "datadog", "new relic", "sre", "障害", "incident", "インシデント", "運用", "オンコール",
        "ログ設計", "ログ収集", "ログ基盤", "ロギング", "nginx", "linux", "サーバー", "server", "ネットワーク", "network", "dns",
        "cdn", "vps", "自宅サーバー", "homelab", "マイクロサービス", "microservice",
        "re:invent", "jaws-ug", "s3", "ジョブ基盤", "定期実行", "valkey", "tailscale", "ci", "本番db", "nw",
    ]),
    ("web", "Web・アプリ", [
        "react", "vue", "svelte", "next.js", "nuxt", "angular", "astro", "remix",
        "フロントエンド", "frontend", "css", "html", "tailwind", "ブラウザ", "browser",
        "chrome", "web", "ui", "ux", "デザインシステム", "figma", "アクセシビリティ",
        "バックエンド", "backend", "api", "graphql", "grpc", "データベース", "database",
        "sql", "postgres", "postgresql", "mysql", "sqlite", "redis", "mongodb", "dynamodb",
        "orm", "django", "rails", "laravel", "fastapi", "express.js", "spring", "wordpress",
        "flutter", "react native", "swiftui", "ios", "android", "モバイル", "mobile",
        "アプリ開発", "スマホアプリ", "webassembly", "wasm",
        "website", "websites", "vite", "vuefes", "chromium", "v8", "canvas", "riverpod", "duckdb", "署名付きurl", "スクロール", "ゲーム", "game", "unity", "unreal", "godot", "ゲームエンジン",
    ]),
    ("tools", "言語・開発ツール", [
        "python", "javascript", "typescript", "rust", "go", "golang", "java", "kotlin",
        "swift", "c++", "c#", "ruby", "elixir", "zig", "haskell", "scala", "dart", "lua",
        "php", "perl", "ocaml", "r言語", "プログラミング言語",
        "git", "github", "gitlab", "プルリクエスト", "pull request", "vscode", "vim", "neovim",
        "emacs", "jetbrains", "intellij", "cli", "ターミナル", "terminal", "シェル", "shell",
        "bash", "zsh", "makefile", "npm", "pnpm", "yarn", "bun", "deno", "node.js", "pip",
        "uv", "poetry", "cargo", "homebrew", "パッケージ", "ライブラリ", "library",
        "フレームワーク", "テスト", "testing", "tdd", "リファクタリング", "refactor",
        "コードレビュー", "code review", "設計", "アーキテクチャ", "architecture",
        "ドメイン駆動", "ddd", "デザインパターン", "プログラミング", "programming",
        "コーディング", "コンパイラ", "compiler", "アルゴリズム", "algorithm", "正規表現",
        "regex", "wsl", "dotfiles", "開発環境", "エディタ", "oss", "オープンソース",
        "open source", "個人開発", "自作",
        "型安全", "ユーティリティ", "パターン", "ドメイン", "要件定義", "qa", "品質保証", "e2e", "スタックトレース", "ヒープ", "debugger", "デバッグ", "obsidian", "ghostty", "fzf", "ノーコード", "power automate", "sharepoint", "スプレッドシート", "excel", "ソフトウェアエンジニアリング", "software",
    ]),
    ("career", "キャリア・組織", [
        "キャリア", "career", "転職", "働き方", "エンジニアとして", "新人", "新卒", "未経験",
        "マネジメント", "マネージャー", "manager", "組織", "チーム", "リーダー", "採用",
        "hiring", "評価制度", "1on1", "育成", "学習法", "勉強法", "勉強会", "資格", "試験",
        "マインドセット", "生き方", "ポエム", "振り返り", "属人化", "仕事術", "生産性",
        "コミュニケーション", "burnout", "燃え尽き",
        "lt会", "登壇", "参加記", "参加レポート", "レポ", "インターン", "入社", "報連相", "読書", "アジャイル", "agile", "スクラム", "バックログ", "エンジニア歴", "シニア", "中堅", "ライティング", "advice", "pm",
    ]),
    ("biz", "業界・製品", [
        "株価", "決算", "買収", "acquisition", "資金調達", "ipo", "スタートアップ", "startup",
        "半導体", "nvidia", "tsmc", "規制", "政策", "法案", "訴訟", "lawsuit", "裁判",
        "政府", "government", "doj", "fcc", "市場", "業界", "経済", "economy", "値上げ",
        "料金", "価格", "提供開始", "サービス開始", "サービス終了", "macbook", "iphone",
        "ipad", "imac", "censorship", "検閲",
        "gpu", "tpu", "raspberry pi", "ハードウェア", "hardware", "ガジェット", "gadget", "buyout", "buyouts", "layoff", "laid off", "レイオフ", "撤退", "上場", "経営", "penalty", "court", "shutting down",
    ]),
]
GENRE_LABELS = {key: label for key, label, _ in GENRES} | {"other": "その他"}
_GENRE_ORDER = {key: i for i, (key, _, _) in enumerate(GENRES)}


def _kw_pattern(kw: str) -> re.Pattern:
    # 英数字のキーワードは単語の途中に反応しないよう前後を区切る（evaluation の lua など）。
    # 後ろは英字の連続だけ弾く（qwen3 は拾う）。5文字以上は agents / fine-tuning のような語形変化も拾う
    if re.fullmatch(r"[a-z0-9 .+#/\-]+", kw):
        tail = r"(?![a-z])" if len(kw) <= 4 or not kw[-1].isalnum() else ""
        return re.compile(r"(?<![a-z0-9])" + re.escape(kw) + tail)
    return re.compile(re.escape(kw))


# 長いキーワードから順に照合して一致部分を消す。"claude code" が先に当たれば "claude" は数えない
_KEYWORDS = [
    (_kw_pattern(kw), key)
    for kw, key in sorted(((kw, key) for key, _, kws in GENRES for kw in kws), key=lambda x: -len(x[0]))
]


def _score(text: str, weight: int, scores: dict[str, int]) -> None:
    for pattern, key in _KEYWORDS:
        text, n = pattern.subn(" ", text)
        if n:
            scores[key] = scores.get(key, 0) + weight


def classify_tags(title: str, desc: str = "") -> list[str]:
    """タイトル+説明文から分野を1つ決めて [分野] で返す"""
    scores: dict[str, int] = {}
    _score(title.lower(), 3, scores)
    _score(desc.lower(), 1, scores)
    if not scores:
        return ["other"]
    return [max(scores, key=lambda k: (scores[k], -_GENRE_ORDER[k]))]


def tag_spans(tag_keys: list[str]) -> str:
    return " ".join(f'<span class="tag tag-{k}">{GENRE_LABELS.get(k, "その他")}</span>' for k in tag_keys)


# --- HTTP セッション ---
QIITA_TOKEN = os.environ.get("QIITA_TOKEN", "")

ALLOWED_DOMAINS = {
    "qiita.com", "zenn.dev", "b.hatena.ne.jp",
    "hn.algolia.com", "news.ycombinator.com",
    "api-free.deepl.com", "api.deepl.com",
    "yuji.software",
    "yashikota.github.io",
}


def is_allowed_url(url: str) -> bool:
    """URLのドメインがホワイトリストに含まれるか検証"""
    try:
        hostname = urlparse(url).hostname or ""
        return any(hostname == d or hostname.endswith("." + d) for d in ALLOWED_DOMAINS)
    except Exception:
        return False


def _session() -> requests.Session:
    s = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    s.mount("https://", HTTPAdapter(max_retries=retry))
    repo_url = os.environ.get("REPO_URL", "https://github.com/news-claw")
    headers = {"User-Agent": f"news-claw/1.0 (+{repo_url})"}
    if QIITA_TOKEN:
        headers["Authorization"] = f"Bearer {QIITA_TOKEN}"
    s.headers.update(headers)
    return s

SESSION = _session()


def get(url: str, timeout: int = 20, **kwargs) -> Optional[requests.Response]:
    try:
        r = SESSION.get(url, timeout=timeout, **kwargs)
        r.raise_for_status()
        return r
    except Exception as e:
        print(f"  fetch error [{url[:70]}]: {e}", file=sys.stderr)
        return None


# --- RSS パーサー ---
def _text(el) -> str:
    return (el.text or "").strip() if el is not None else ""


def _parse_date(raw: str) -> str:
    """RSS 2.0 の pubDate (RFC 2822) や ISO 日付を YYYY-MM-DD に正規化"""
    if not raw:
        return ""
    if re.match(r'\d{4}-\d{2}-\d{2}', raw):
        return raw[:10]
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(raw).strftime("%Y-%m-%d")
    except Exception:
        return raw[:10]


def parse_rss(data: bytes) -> list[dict]:
    """RSS 1.0(RDF) / RSS 2.0 / Atom を解析。
    はてブRDFの場合は hatena:bookmarkcount も返す。"""
    items = []
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        try:
            text = data.decode("utf-8", errors="replace")
            if "?>" in text:
                text = text[text.index("?>") + 2:]
            root = ET.fromstring(text)
        except Exception:
            return items

    ns = root.tag

    # --- Atom ---
    if root.tag == f"{{{ATOM}}}feed":
        for entry in root.findall(f"{{{ATOM}}}entry"):
            title_el = entry.find(f"{{{ATOM}}}title")
            link_el  = entry.find(f"{{{ATOM}}}link")
            _pub     = entry.find(f"{{{ATOM}}}published")
            pub_el   = _pub if _pub is not None else entry.find(f"{{{ATOM}}}updated")
            _sum     = entry.find(f"{{{ATOM}}}summary")
            sum_el   = _sum if _sum is not None else entry.find(f"{{{ATOM}}}content")
            title = _text(title_el)
            url   = link_el.get("href") or _text(link_el) if link_el is not None else ""
            pub   = _text(pub_el)[:10]
            desc  = _text(sum_el)
            if title and url:
                items.append({"title": title, "url": url, "date": pub, "desc": desc, "meta": {}})
        return items

    # --- RSS 1.0 (RDF) ---
    if root.tag == f"{{{RDF}}}RDF":
        for item in root.findall(f"{{{RSS1}}}item"):
            title  = _text(item.find(f"{{{RSS1}}}title"))
            url    = _text(item.find(f"{{{RSS1}}}link"))
            pub    = _text(item.find(f"{{{DC}}}date"))[:10]
            desc   = _text(item.find(f"{{{RSS1}}}description"))
            bmarks = _text(item.find(f"{{{HATENA}}}bookmarkcount"))
            if title and url:
                items.append({
                    "title": title, "url": url, "date": pub, "desc": desc,
                    "meta": {"bookmarks": int(bmarks) if bmarks.isdigit() else 0},
                })
        return items

    # --- RSS 2.0 ---
    _ch = root.find("channel")
    channel = _ch if _ch is not None else root
    for item in channel.findall("item"):
        title  = _text(item.find("title"))
        url    = _text(item.find("link"))
        _pd    = item.find("pubDate")
        pub_el = _pd if _pd is not None else item.find(f"{{{DC}}}date")
        pub    = _parse_date(_text(pub_el))
        desc   = _text(item.find("description"))
        if title and url:
            items.append({"title": title, "url": url, "date": pub, "desc": desc, "meta": {}})
    return items


# --- 翻訳 ---
DEEPL_AUTH_KEY = os.environ.get("DEEPL_AUTH_KEY", "")
DEEPL_ENABLED = os.environ.get("DEEPL_ENABLED", "false").lower() == "true"
DEEPL_API_BASE = (
    "https://api-free.deepl.com"
    if DEEPL_AUTH_KEY.endswith(":fx")
    else "https://api.deepl.com"
)
deepl_chars_used = 0


def translate_deepl(text: str) -> str:
    """DeepL API で英語→日本語翻訳"""
    global deepl_chars_used
    if not DEEPL_AUTH_KEY or not DEEPL_ENABLED or not text:
        return ""
    truncated = text[:500]
    try:
        resp = SESSION.post(
            f"{DEEPL_API_BASE}/v2/translate",
            headers={"Authorization": f"DeepL-Auth-Key {DEEPL_AUTH_KEY}"},
            data={"text": truncated, "target_lang": "JA"},
            timeout=15,
        )
        if resp.status_code == 200:
            deepl_chars_used += len(truncated)
            return resp.json()["translations"][0]["text"]
        print(f"  DeepL HTTP {resp.status_code}: {resp.text[:200]}", file=sys.stderr)
    except Exception as e:
        print(f"  DeepL error: {e}", file=sys.stderr)
    return ""


def translate_ja(text: str) -> str:
    """DeepL で翻訳（無効時・失敗時は空文字）"""
    return translate_deepl(text)


# --- 各ソース収集 ---
ZENN_TOPICS = [
    "claudecode", "llm", "machinelearning", "deeplearning",
    "computervision", "kaggle", "audio", "nlp", "statistics", "pytorch", "agent",
]

QIITA_TAGS = [
    "MachineLearning", "DeepLearning", "ComputerVision", "Python",
    "kaggle", "NLP", "PyTorch", "音声認識", "統計", "LLM",
]


def collect_zenn() -> list[dict]:
    """Zenn API: ウィークリートレンドで取得してからいいね数でソート"""
    seen: set[str] = set()
    articles: list[dict] = []

    def _parse(a: dict) -> Optional[dict]:
        slug = a.get("slug", "")
        title = a.get("title", "")
        if not title or not slug:
            return None
        return {
            "title": title,
            "url": f"https://zenn.dev{a.get('path', f'/articles/{slug}')}",
            "date": (a.get("published_at") or "")[:10],
            "desc": "",
            "meta": {
                "likes": a.get("liked_count", 0) or 0,
                "author": (a.get("user") or {}).get("name", ""),
            },
        }

    def fetch_topic(topic: str) -> list[dict]:
        url = f"https://zenn.dev/api/articles?topicname={topic}&order=weekly&count=20"
        r = get(url)
        if not r:
            return []
        return [p for a in r.json().get("articles", []) if (p := _parse(a))]

    # Techs + Ideas（デイリートレンド）
    for atype in ("tech", "idea"):
        r = get(f"https://zenn.dev/api/articles?order=weekly&count=50&article_type={atype}")
        if r:
            for a in r.json().get("articles", []):
                p = _parse(a)
                if p and p["url"] not in seen:
                    seen.add(p["url"])
                    articles.append(p)

    with ThreadPoolExecutor(max_workers=6) as ex:
        for items in ex.map(fetch_topic, ZENN_TOPICS):
            for item in items:
                if item["url"] not in seen:
                    seen.add(item["url"])
                    articles.append(item)

    # いいね数降順でソート・タグ付け
    articles.sort(key=lambda a: a["meta"].get("likes", 0), reverse=True)
    for a in articles:
        a["tags"] = classify_tags(a["title"])
    return articles[:50]


def collect_qiita() -> list[dict]:
    """Qiita: popular-items/feed (Atom=トレンド順) + タグ別API補完"""
    seen: set[str] = set()
    trend_articles: list[dict] = []
    tag_articles: list[dict] = []

    # トレンドフィード（https://qiita.com/trend 相当、順序がトレンド順）
    r = get("https://qiita.com/popular-items/feed")
    if r:
        for item in parse_rss(r.content):
            item["url"] = _strip_utm(item["url"])
            if item["url"] and item["url"] not in seen:
                seen.add(item["url"])
                item["tags"] = classify_tags(item["title"], item["desc"])
                item["meta"].setdefault("likes", 0)
                item["meta"].setdefault("author", "")
                trend_articles.append(item)

    # トレンド記事のlikes_countをAPI経由で補完
    for a in trend_articles:
        if not is_allowed_url(a["url"]):
            continue
        # URLからitem_idを抽出: https://qiita.com/user/items/XXXXX → XXXXX
        parts = a["url"].rstrip("/").split("/")
        if len(parts) >= 2 and parts[-2] == "items":
            item_id = parts[-1]
            if not re.fullmatch(r'[a-zA-Z0-9_-]+', item_id):
                continue
            r2 = get(f"https://qiita.com/api/v2/items/{item_id}")
            if r2:
                data = r2.json()
                a["meta"]["likes"] = data.get("likes_count", 0) or 0
                a["meta"]["author"] = (data.get("user") or {}).get("id", "")
                a["date"] = (data.get("created_at") or "")[:10]

    # タグ別でトレンドに載らない専門記事も補完
    since = (datetime.now(JST) - timedelta(days=7)).strftime("%Y-%m-%d")

    def fetch_tag(tag: str) -> list[dict]:
        encoded = urllib.parse.quote(tag)
        url = f"https://qiita.com/api/v2/items?per_page=15&query=tag:{encoded}+created:>={since}+stocks:>3"
        r = get(url)
        if not r:
            return []
        result = []
        for it in r.json():
            art_url = it.get("url", "")
            title = it.get("title", "")
            if title and art_url:
                result.append({
                    "title": title, "url": art_url,
                    "date": (it.get("created_at") or "")[:10], "desc": "",
                    "tags": classify_tags(title),
                    "meta": {
                        "likes": it.get("likes_count", 0) or 0,
                        "author": (it.get("user") or {}).get("id", ""),
                    },
                })
        return result

    with ThreadPoolExecutor(max_workers=5) as ex:
        for items in ex.map(fetch_tag, QIITA_TAGS):
            for item in items:
                if item["url"] not in seen:
                    seen.add(item["url"])
                    tag_articles.append(item)

    # 全記事をいいね数順でソート
    all_articles = trend_articles + tag_articles
    all_articles.sort(key=lambda a: a["meta"].get("likes", 0), reverse=True)
    return all_articles[:40]


def collect_hatena() -> list[dict]:
    """はてなブックマーク: IT人気エントリー + キーワード検索RSS"""
    urls = [
        "https://b.hatena.ne.jp/hotentry/it.rss",
        # サブカテゴリRSSは廃止済みのためキーワード検索RSSで代替
        "https://b.hatena.ne.jp/q/AI?date_range=1w&sort=hot&mode=rss&safe=on&target=entry&users=3",
        "https://b.hatena.ne.jp/q/%E6%A9%9F%E6%A2%B0%E5%AD%A6%E7%BF%92?date_range=1w&sort=hot&mode=rss&safe=on&target=entry&users=3",
        "https://b.hatena.ne.jp/q/%E3%83%97%E3%83%AD%E3%82%B0%E3%83%A9%E3%83%9F%E3%83%B3%E3%82%B0?date_range=1w&sort=hot&mode=rss&safe=on&target=entry&users=3",
    ]
    seen: set[str] = set()
    articles: list[dict] = []

    def fetch_one(url: str) -> list[dict]:
        r = get(url)
        return parse_rss(r.content) if r else []

    with ThreadPoolExecutor(max_workers=4) as ex:
        for items in ex.map(fetch_one, urls):
            for item in items:
                if item["url"] not in seen:
                    seen.add(item["url"])
                    item["tags"] = classify_tags(item["title"], item["desc"])
                    articles.append(item)

    articles.sort(key=lambda a: a["meta"].get("bookmarks", 0), reverse=True)
    return articles[:30]


def collect_hatena_blog() -> list[dict]:
    """はてなブログ注目記事: はてブ検索RSSでエンジニア系ブログ記事を収集"""
    keywords = [
        "エンジニア",
        "プログラマ",
        "技術ブログ",
    ]
    seen: set[str] = set()
    articles: list[dict] = []

    def fetch_keyword(kw: str) -> list[dict]:
        encoded = urllib.parse.quote(kw)
        url = f"https://b.hatena.ne.jp/q/{encoded}?date_range=1m&sort=hot&mode=rss&safe=on&target=entry&users=5"
        r = get(url)
        return parse_rss(r.content) if r else []

    with ThreadPoolExecutor(max_workers=3) as ex:
        for items in ex.map(fetch_keyword, keywords):
            for item in items:
                if item["url"] not in seen:
                    seen.add(item["url"])
                    item["tags"] = classify_tags(item["title"], item["desc"])
                    articles.append(item)

    articles.sort(key=lambda a: a["meta"].get("bookmarks", 0), reverse=True)
    return articles[:20]


def collect_hn() -> list[dict]:
    """Algolia API でHacker Newsの記事を収集（当日のみ）"""
    since_ts = int((datetime.now(timezone.utc) - timedelta(days=1)).timestamp())
    # points は numericAttributesForFiltering から除外されたため、
    # created_at_i のみでフィルタし、Python側で points>=100 を適用
    url = (
        "https://hn.algolia.com/api/v1/search"
        f"?tags=story&numericFilters=created_at_i%3E{since_ts}&hitsPerPage=50"
        "&attributesToRetrieve=title,url,points,num_comments,created_at,objectID"
    )
    r = get(url)
    if not r:
        return []
    articles = []
    for h in r.json().get("hits", []):
        if (h.get("points") or 0) < 100:
            continue
        title = h.get("title", "")
        story_url = h.get("url", "")
        if not title or not story_url:
            continue
        hn_url = f"https://news.ycombinator.com/item?id={h.get('objectID', '')}"
        articles.append({
            "title": title,
            "url": story_url,
            "date": (h.get("created_at") or "")[:10],
            "desc": "",
            "tags": classify_tags(title),
            "meta": {
                "points": h.get("points", 0),
                "comments": h.get("num_comments", 0),
                "hn_url": hn_url,
                "title_ja": "",
            },
        })

    # タイトル翻訳（DEEPL_ENABLED時のみ翻訳、それ以外はスキップ）
    if DEEPL_ENABLED:
        print(f"  HN翻訳中... ({len(articles)}件)")
        for a in articles:
            a["meta"]["title_ja"] = translate_ja(a["title"])
            time.sleep(0.15)
    else:
        print(f"  HN翻訳スキップ（DEEPL_ENABLED=false）")

    return articles


def collect_slides() -> list[dict]:
    """勉強会スライドbot: JSON Feed からスライド情報を収集
    データソース: https://github.com/YujiSoftware/tech_slideshare
    """
    url = "https://yuji.software/tech_slideshare/feed.json"
    r = get(url)
    if not r:
        return []
    articles = []
    seen: set[str] = set()
    for item in r.json().get("items", []):
        title = item.get("title", "")
        link = item.get("link", "")
        if not title or not link or link in seen:
            continue
        seen.add(link)
        author = item.get("author") or ""
        date = _parse_date(item.get("date") or "")
        desc = item.get("description") or ""
        articles.append({
            "title": title,
            "url": link,
            "date": date,
            "desc": desc,
            "tags": classify_tags(title, desc),
            "meta": {
                "author": author,
            },
        })
    return articles


# --- Markdown ---
CSS = """<style>
.tag { font-size: 0.72rem; font-weight: 700; padding: 2px 7px; border-radius: 3px; white-space: nowrap; }
.tag-sec    { color: #fff; background: #ef5350; }
.tag-agent  { color: #fff; background: #66bb6a; }
.tag-llm    { color: #fff; background: #ffa726; }
.tag-ml     { color: #fff; background: #ab47bc; }
.tag-infra  { color: #fff; background: #29b6f6; }
.tag-web    { color: #fff; background: #26c6da; }
.tag-tools  { color: #fff; background: #78909c; }
.tag-career { color: #fff; background: #ec407a; }
.tag-biz    { color: #fff; background: #a1887f; }
.tag-other  { color: #fff; background: #bdbdbd; }
.src { font-size: 0.7rem; font-weight: 700; color: #666; border: 1px solid #ccc; border-radius: 3px; padding: 0 5px; }
.filter-bar { display: none; gap: 5px; flex-wrap: wrap; margin-bottom: 1rem; }
.filter-btn { padding: 3px 10px; border: 1px solid #ccc; border-radius: 20px; cursor: pointer;
  font-size: 0.75rem; font-weight: 700; background: #fff; color: #444; }
.filter-btn.on { background: #333; color: #fff; border-color: #333; }
.filter-btn.empty { opacity: 0.35; }
.sort-btn.new-toggle.on { background: #d32f2f; color: #fff; border-color: #d32f2f; }
.new-divider { font-size: 0.75rem; color: #888; text-align: center; padding: 10px 0 4px; border-bottom: 1px dashed #ccc; }
.tab-nav { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 0.5rem; }
.tab-btn { padding: 6px 14px; border: none; border-radius: 20px; cursor: pointer;
  font-size: 0.85rem; font-weight: 700; background: #e8e8e8; color: #444; transition: background 0.15s; }
.tab-btn.active { background: #333; color: #fff; }
.sort-bar { display: flex; gap: 5px; margin-bottom: 0.5rem; }
.sort-btn { padding: 3px 11px; border: 1px solid #ccc; border-radius: 20px; cursor: pointer;
  font-size: 0.75rem; font-weight: 700; background: #fff; color: #666; transition: all 0.15s; }
.sort-btn.active { background: #333; color: #fff; border-color: #333; }
.tab-pane { display: none; }
.tab-pane.active { display: block; }
.item { padding: 8px 0; border-bottom: 1px solid #eee; }
.item-title { font-size: 0.95rem; font-weight: 600; }
.item-title a, .item-title a:visited { color: #2a7ae2 !important; text-decoration: none; }
.item-title a:hover { text-decoration: underline; }
.item-meta { font-size: 0.78rem; color: #888; margin-top: 2px; }
details { margin-top: 6px; }
details summary { cursor: pointer; font-size: 0.82rem; color: #888; margin-top: 4px; }
details blockquote { font-size: 0.85rem; line-height: 1.6; margin: 8px 0 0 0; padding: 8px 12px; color: #555; border-left: 3px solid #ddd; background: transparent; }
.kindle-footer { margin-top: 2rem; padding: 1rem 0; border-top: 1px solid #eee; }
.kindle-btn { display: inline-block; padding: 8px 20px; background: #fff !important; color: #ff9900 !important;
  border: 2px solid #ff9900; font-size: 0.85rem; font-weight: 700; border-radius: 4px; text-decoration: none !important; }
.kindle-btn:hover { background: #fff8f0 !important; }
</style>"""

TAB_NAV = """<div class="tab-nav">
  <button class="tab-btn active" onclick="switchTab('zenn',this)">Zenn</button>
  <button class="tab-btn" onclick="switchTab('qiita',this)">Qiita</button>
  <button class="tab-btn" onclick="switchTab('hatena',this)">はてな</button>
  <button class="tab-btn" onclick="switchTab('blog',this)">Blog</button>
  <button class="tab-btn" onclick="switchTab('hn',this)">HN</button>
  <button class="tab-btn" onclick="switchTab('slides',this)">Slides</button>
  <button class="tab-btn" onclick="switchTab('all',this)">ALL</button>
</div>
<div class="sort-bar">
  <button id="sort-latest" class="sort-btn active" data-sort="latest" onclick="setSort('latest',this)">Latest</button>
  <button id="sort-hotness" class="sort-btn" data-sort="hotness" onclick="setSort('hotness',this)">Hotness</button>
  <button id="toggle-new" class="sort-btn new-toggle" onclick="toggleNew(this)">NEW <span class="cnt"></span></button>
</div>"""


def build_filter_bar(articles: list[dict]) -> str:
    """ALLタブ用の分野トグル。件数はJSで更新する"""
    present = {t for a in articles for t in a.get("tags", [])}
    buttons = [
        f'  <button class="filter-btn" data-tag="{key}" onclick="toggleGenre(this)">{label} <span class="cnt"></span></button>'
        for key, label in GENRE_LABELS.items() if key in present
    ]
    return '<div class="filter-bar">\n' + "\n".join(buttons) + "\n</div>"


SWITCH_JS = """<script>
let _sort = 'latest';
let _onlyNew = false;
const _genres = new Set();
const isNew = it => (it.dataset.tags || '').split(' ').includes('new');

function toggleNew(btn) {
  _onlyNew = !_onlyNew;
  btn.classList.toggle('on', _onlyNew);
  applyFilter();
}

function toggleGenre(btn) {
  const g = btn.dataset.tag;
  if (_genres.has(g)) _genres.delete(g); else _genres.add(g);
  btn.classList.toggle('on', _genres.has(g));
  applyFilter();
}

// NEW と分野は AND、分野同士は OR。分野の絞り込みは ALL タブだけに効かせる
function applyFilter() {
  document.querySelectorAll('.item').forEach(it => {
    const tags = (it.dataset.tags || '').split(' ');
    const inAll = it.parentElement.id === 'tab-all';
    const ok = (!_onlyNew || tags.includes('new'))
      && (!inAll || _genres.size === 0 || [..._genres].some(g => tags.includes(g)));
    it.style.display = ok ? '' : 'none';
  });
  const pane = document.querySelector('.tab-pane.active');
  document.querySelector('#toggle-new .cnt').textContent = pane.querySelectorAll('.item[data-tags~="new"]').length;
  const all = document.getElementById('tab-all');
  document.querySelectorAll('.filter-btn').forEach(b => {
    const sel = '.item[data-tags~="' + b.dataset.tag + '"]' + (_onlyNew ? '[data-tags~="new"]' : '');
    const n = all.querySelectorAll(sel).length;
    b.querySelector('.cnt').textContent = n;
    b.classList.toggle('empty', n === 0);
  });
  const div = document.getElementById('new-divider');
  div.style.display = (!_onlyNew && div.dataset.boundary === '1') ? '' : 'none';
}

// ALL は NEW を先頭に並べ、NEW とそれ以外の境目に区切り線を置く
function sortPane(pane, mode) {
  const all = pane.id === 'tab-all';
  const items = Array.from(pane.querySelectorAll('.item'));
  items.sort((a, b) => {
    if (all && isNew(a) !== isNew(b)) return isNew(a) ? -1 : 1;
    return mode === 'latest'
      ? (b.dataset.date || '').localeCompare(a.dataset.date || '')
      : parseInt(b.dataset.count || '0') - parseInt(a.dataset.count || '0');
  });
  items.forEach(item => pane.appendChild(item));
  if (all) {
    const div = document.getElementById('new-divider');
    const first = items.find(it => !isNew(it));
    div.dataset.boundary = (first && items.some(isNew)) ? '1' : '0';
    if (first) pane.insertBefore(div, first);
  }
}

function setSort(mode, btn) {
  _sort = mode;
  document.querySelectorAll('.sort-btn[data-sort]').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const active = document.querySelector('.tab-pane.active');
  if (active) sortPane(active, mode);
}

function switchTab(id, btn) {
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  const pane = document.getElementById('tab-' + id);
  pane.classList.add('active');
  btn.classList.add('active');
  const btnL = document.getElementById('sort-latest');
  const btnH = document.getElementById('sort-hotness');
  document.getElementById('credit-slides').style.display = id === 'slides' ? '' : 'none';
  document.querySelector('.filter-bar').style.display = id === 'all' ? 'flex' : 'none';
  if (id === 'slides') {
    btnH.style.display = 'none';
    setSort('latest', btnL);
  } else {
    btnH.style.display = '';
    sortPane(pane, _sort);
  }
  applyFilter();
}

sortPane(document.getElementById('tab-all'), _sort);
applyFilter();
</script>"""


def _strip_utm(url: str) -> str:
    """URLからUTMパラメータを除去して正規化"""
    if "?" not in url:
        return url
    base, _, qs = url.partition("?")
    params = [p for p in qs.split("&") if not p.startswith("utm_")]
    return f"{base}?{'&'.join(params)}" if params else base


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def safe_href(url: str) -> str:
    """URLスキームを検証し、http/https以外は '#' に置換してXSSを防止"""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return "#"
    return esc(url)


def data_tags(a: dict) -> str:
    return " ".join(a.get("tags", ["other"]) + (["new"] if a.get("is_new") else []))


def load_previous_urls(today: str) -> set[str]:
    """前日以前の最新記事に載っていたURL（UTM除去済み）。NEW判定用"""
    for f in sorted(OUTPUT_DIR.glob("*-neta-trend.md"), reverse=True):
        if f.name[:10] < today:
            hrefs = re.findall(r'<div class="item-title">(?:<span[^>]*>NEW</span> )?<a href="([^"]+)"',
                               f.read_text(encoding="utf-8"))
            return {_strip_utm(html.unescape(h)) for h in hrefs}
    return set()


def render_pane(tab_id: str, items: list[list[str]]) -> list[str]:
    active = " active" if tab_id == "zenn" else ""
    lines = [f'<div id="tab-{tab_id}" class="tab-pane{active}">']
    for item in items:
        lines += item
    if tab_id == "all":
        lines.append('<div id="new-divider" class="new-divider">ここから前回までの記事</div>')
    lines.append("</div>")
    return lines


def standard_item(a: dict, count_icon: str, count_key: str, source: str = "") -> list[str]:
    title  = esc(a["title"])
    url    = safe_href(a["url"])
    date   = a.get("date", "")[5:10]
    count  = a["meta"].get(count_key, 0)
    author = esc(a["meta"].get("author", ""))
    ts     = tag_spans(a.get("tags", ["other"]))
    count_str  = f"{count_icon} {count}" if (count_icon and count) else ""
    author_str = f"@{author}" if author else ""
    src_str    = f'<span class="src">{source}</span>' if source else ""
    meta_parts = [p for p in [src_str, date, count_str, author_str] if p] + [ts]
    return [
        f'<div class="item" data-date="{a.get("date","")}" data-count="{count}" data-tags="{data_tags(a)}">',
        f'  <div class="item-title"><a href="{url}" target="_blank" rel="noopener">{title}</a></div>',
        f'  <div class="item-meta">{" &nbsp; ".join(meta_parts)}</div>',
        "</div>",
    ]


def hn_item(a: dict, source: str = "") -> list[str]:
    title    = esc(a["title"])
    title_ja = esc(a["meta"].get("title_ja", ""))
    url      = safe_href(a["url"])
    pts      = a["meta"].get("points", 0)
    cmts     = a["meta"].get("comments", 0)
    date     = a.get("date", "")[5:10]
    ts       = tag_spans(a.get("tags", ["other"]))
    src_str  = f'<span class="src">{source}</span>' if source else ""
    meta_parts = [p for p in [src_str, date, f"🔥 {pts}" if pts else "", f"💬 {cmts}" if cmts else ""] if p] + [ts]
    lines = [
        f'<div class="item" data-date="{a.get("date","")}" data-count="{pts}" data-tags="{data_tags(a)}">',
        f'  <div class="item-title"><a href="{url}" target="_blank" rel="noopener">{title}</a></div>',
        f'  <div class="item-meta">{" &nbsp; ".join(meta_parts)}</div>',
    ]
    if title_ja:
        lines += [
            "  <details>",
            f'    <summary>タイトルの日本語訳</summary>',
            f'    <blockquote>{title_ja}</blockquote>',
            "  </details>",
        ]
    lines.append("</div>")
    return lines


def by_latest(articles: list[dict]) -> list[dict]:
    return sorted(articles, key=lambda a: a.get("date", ""), reverse=True)


def main():
    now = datetime.now(JST)
    date_label = now.strftime("%Y-%m-%d")
    time_label = now.strftime("%H:%M")
    timestamp  = now.strftime("%Y-%m-%d-%H-%M")

    print("収集開始...")

    with ThreadPoolExecutor(max_workers=6) as ex:
        f_zenn     = ex.submit(collect_zenn)
        f_qiita    = ex.submit(collect_qiita)
        f_hatena   = ex.submit(collect_hatena)
        f_blog     = ex.submit(collect_hatena_blog)
        f_hn       = ex.submit(collect_hn)
        f_slides   = ex.submit(collect_slides)

    zenn_articles    = f_zenn.result()
    qiita_articles   = f_qiita.result()
    hatena_articles  = f_hatena.result()
    blog_articles    = f_blog.result()
    hn_articles      = f_hn.result()
    slides_articles  = f_slides.result()

    print(f"  Zenn: {len(zenn_articles)}, Qiita: {len(qiita_articles)}, "
          f"はてな: {len(hatena_articles)}, Blog: {len(blog_articles)}, "
          f"HN: {len(hn_articles)}, Slides: {len(slides_articles)}")

    # --- 日付フィルタ（Zennはトレンドなのでフィルタなし、他は14日）---
    cutoff = (now - timedelta(days=14)).strftime("%Y-%m-%d")
    def recent(arts: list[dict]) -> list[dict]:
        """date が cutoff 以降の記事のみ残す。日付なし記事は保持。"""
        return [a for a in arts if not a.get("date") or a["date"][:10] >= cutoff]
    # Zennはorder=weeklyでその日のトレンド取得済みなのでフィルタ不要
    qiita_articles  = recent(qiita_articles)
    hatena_articles = recent(hatena_articles)
    slides_articles = recent(slides_articles)
    # blogは1ヶ月の検索RSSなのでフィルタ不要
    print(f"  日付フィルタ後 → Zenn: {len(zenn_articles)}(フィルタなし), Qiita: {len(qiita_articles)}, "
          f"はてな: {len(hatena_articles)}, Blog: {len(blog_articles)}, "
          f"Slides: {len(slides_articles)}")

    # --- タブ間の重複排除（先のタブを優先、UTMパラメータ除去して比較）---
    global_seen: set[str] = set()
    def dedup(arts: list[dict]) -> list[dict]:
        result = []
        for a in arts:
            canonical = _strip_utm(a["url"])
            if canonical not in global_seen:
                global_seen.add(canonical)
                result.append(a)
        return result
    zenn_articles   = dedup(zenn_articles)
    qiita_articles  = dedup(qiita_articles)
    hatena_articles = dedup(hatena_articles)
    blog_articles   = dedup(blog_articles)
    hn_articles     = dedup(hn_articles)
    slides_articles  = dedup(slides_articles)
    print(f"  重複排除後 → Zenn: {len(zenn_articles)}, Qiita: {len(qiita_articles)}, "
          f"はてな: {len(hatena_articles)}, Blog: {len(blog_articles)}, "
          f"HN: {len(hn_articles)}, Slides: {len(slides_articles)}")

    all_articles = (zenn_articles + qiita_articles + hatena_articles
                    + blog_articles + hn_articles + slides_articles)
    prev_urls = load_previous_urls(date_label)
    for a in all_articles:
        a["is_new"] = _strip_utm(a["url"]) not in prev_urls
    print(f"  NEW: {sum(a['is_new'] for a in all_articles)} / {len(all_articles)}")

    lines: list[str] = [
        "---",
        "layout: post",
        f'title: "{date_label} : ニュース"',
        f"date: {date_label} {time_label}:00 +0900",
        "categories: [daily]",
        "---",
        "",
        CSS,
        "",
        TAB_NAV,
        build_filter_bar(all_articles),
        "",
    ]

    sources = [
        ("zenn",   "Zenn",   zenn_articles,   lambda a, src="": standard_item(a, "❤️", "likes", src)),
        ("qiita",  "Qiita",  qiita_articles,  lambda a, src="": standard_item(a, "👍", "likes", src)),
        ("hatena", "はてな", hatena_articles, lambda a, src="": standard_item(a, "🔖", "bookmarks", src)),
        ("blog",   "Blog",   blog_articles,   lambda a, src="": standard_item(a, "🔖", "bookmarks", src)),
        ("hn",     "HN",     hn_articles,     hn_item),
        ("slides", "Slides", slides_articles, lambda a, src="": standard_item(a, "", "", src)),
    ]
    for tab_id, _, arts, item_fn in sources:
        lines += render_pane(tab_id, [item_fn(a) for a in by_latest(arts)])
        lines += [""]
    lines += render_pane("all", [item_fn(a, label) for _, label, arts, item_fn in sources for a in by_latest(arts)])
    lines += [
        "",
        '<div id="credit-slides" class="item-meta" style="margin-top:12px;display:none;">',
        '引用: <a href="https://yuji.software/tech_slideshare/" target="_blank" rel="noopener">勉強会スライドbot</a>'
        ' by <a href="https://github.com/YujiSoftware" target="_blank" rel="noopener">YujiSoftware</a>',
        '</div>',
        "",
        f'<div class="kindle-footer"><a class="kindle-btn" href="{KINDLE_DAILY_URL}" target="_blank" rel="noopener">Kindle 日替わりセール</a></div>',
        "",
        SWITCH_JS,
        "",
    ]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"{timestamp}-neta-trend.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"保存: {out_path}")
    if deepl_chars_used:
        print(f"  DeepL消費文字数: {deepl_chars_used:,} 文字")

    # Slack通知用URLをファイルに書き出す
    date_path = now.strftime("%Y/%m/%d")
    time_slug = now.strftime("%H-%M")
    site_url = os.environ.get("SITE_URL", "https://canon-so8.github.io/news-claw")
    page_url = f"{site_url}/daily/{date_path}/{time_slug}-neta-trend/"
    try:
        Path("/tmp/daily_url.txt").write_text(page_url)
    except Exception:
        pass
    return str(out_path)


if __name__ == "__main__":
    main()
