#!/usr/bin/env python3
"""
suggest_assets.py — 相談内容から既存資産の再利用候補を提案する

使い方:
  python scripts/suggest_assets.py "Instagram投稿を自動生成したい"
  python scripts/suggest_assets.py "メールを自動送信したい" --top 5
"""

import sys
import json
import argparse
import ast
import re
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).parent.parent

# ─── 資産スキャン ────────────────────────────────────────────────

def load_registry_assets():
    """registry.json からプロジェクト資産を読み込む"""
    registry_path = WORKSPACE_ROOT / "projects" / "registry.json"
    assets = []
    if not registry_path.exists():
        return assets
    with open(registry_path) as f:
        registry = json.load(f)
    for task in registry.get("tasks", []):
        output_path = task.get("output_path", "")
        full_path = WORKSPACE_ROOT / output_path
        assets.append({
            "id": task["id"],
            "title": task["title"],
            "type": task["type"],
            "path": output_path,
            "tags": extract_tags_from_title(task["title"]),
            "notes": task.get("execution_notes", ""),
            "source": "registry",
        })
    return assets


def extract_docstring(filepath):
    """Pythonファイルのモジュールdocstringを抽出する"""
    try:
        with open(filepath, encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
        return ast.get_docstring(tree) or ""
    except Exception:
        return ""


def extract_tags_from_title(title):
    """タイトルからキーワードを抽出する（英数字・カタカナ語・漢字ブロック単位）"""
    tags = []
    # 英数字の連続（例: API, Claude, Python）
    tags += re.findall(r'[a-zA-Z][a-zA-Z0-9]*', title)
    # カタカナ語（長音符含む）
    tags += re.findall(r'[ァ-ヶー]+', title)
    # 漢字+ひらがな混じりの意味ブロック（3文字以上）
    tags += re.findall(r'[一-龥ぁ-ん]{3,}', title)
    # 重複除去して返す
    seen = set()
    result = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            result.append(t)
    return result


def scan_scripts():
    """scripts/ フォルダのPythonファイルを資産として追加する"""
    assets = []
    scripts_dir = WORKSPACE_ROOT / "scripts"
    for py_file in scripts_dir.glob("*.py"):
        if py_file.name == "suggest_assets.py":
            continue
        docstring = extract_docstring(py_file)
        first_line = docstring.split("\n")[0] if docstring else py_file.stem
        assets.append({
            "id": py_file.stem,
            "title": first_line,
            "type": "script",
            "path": str(py_file.relative_to(WORKSPACE_ROOT)),
            "tags": extract_tags_from_title(py_file.stem + " " + first_line),
            "notes": docstring[:120].replace("\n", " "),
            "source": "scripts",
        })
    return assets


def scan_prompts():
    """prompts/ フォルダのMarkdownファイルを資産として追加する"""
    assets = []
    prompts_dir = WORKSPACE_ROOT / "prompts"
    for md_file in prompts_dir.glob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception:
            continue
        # 最初の見出しをタイトルに
        match = re.search(r'^#\s+(.+)', content, re.MULTILINE)
        title = match.group(1) if match else md_file.stem
        assets.append({
            "id": md_file.stem,
            "title": title,
            "type": "prompt_template",
            "path": str(md_file.relative_to(WORKSPACE_ROOT)),
            "tags": extract_tags_from_title(title),
            "notes": content[:120].replace("\n", " "),
            "source": "prompts",
        })
    return assets


def load_all_assets():
    assets = []
    assets.extend(load_registry_assets())
    assets.extend(scan_scripts())
    assets.extend(scan_prompts())
    return assets


# ─── マッチング ──────────────────────────────────────────────────

def score_asset(asset, query_keywords):
    """資産とクエリの関連スコアを計算する（0〜100）"""
    score = 0
    title = asset.get("title", "")
    notes = asset.get("notes", "")
    path  = asset.get("path", "")
    tags  = asset.get("tags", [])
    full_text = f"{title} {notes} {path} {' '.join(tags)}"

    for kw in query_keywords:
        k = kw.lower()
        if k in title.lower():
            score += 25
        elif k in full_text.lower():
            score += 10

    return min(score, 100)


def tokenize_query(query):
    """クエリを検索キーワードに分解する"""
    keywords = []
    # 英数字
    keywords += re.findall(r'[a-zA-Z][a-zA-Z0-9]*', query)
    # カタカナ語（長音符含む）
    keywords += re.findall(r'[ァ-ヶー]+', query)
    # 漢字ブロック（2文字以上）
    keywords += re.findall(r'[一-龥]{2,}', query)
    # 重複除去
    stopwords = {"スクリプト", "ツール", "機能", "処理", "自動", "システム"}
    seen = set()
    result = []
    for k in keywords:
        if k not in seen and k not in stopwords and len(k) > 1:
            seen.add(k)
            result.append(k)
    return result


def infer_new_implementations(query, matched_paths):
    """クエリから新規実装が必要そうな要素を推測する"""
    hints = []
    keywords_map = {
        "Instagram":    "Instagram API連携・投稿処理",
        "Twitter":      "Twitter/X API連携・投稿処理",
        "LINE":         "LINE Messaging API連携",
        "画像":         "画像生成・画像処理",
        "動画":         "動画生成・編集処理",
        "音声":         "音声合成・文字起こし処理",
        "データベース": "DB設計・CRUD処理",
        "スケジュール": "スケジューラ・cron設定",
        "Slack":        "Slack API連携",
        "翻訳":         "翻訳API連携",
        "PDF":          "PDF生成・解析処理",
        "スクレイピング": "Webスクレイピング処理",
        "認証":         "認証・セッション管理",
        "通知":         "プッシュ通知・アラート処理",
        "承認":         "承認フロー・ワークフロー制御",
        "自動投稿":     "SNS自動投稿スケジューラ",
        "分析":         "データ分析・可視化処理",
    }
    for kw, desc in keywords_map.items():
        if kw in query and desc not in matched_paths:
            hints.append(desc)
    return hints[:4]


# ─── 出力 ────────────────────────────────────────────────────────

def print_results(query, scored_assets, new_impls):
    reuse = [(a, s) for a, s in scored_assets if s >= 20]
    low   = [(a, s) for a, s in scored_assets if 5 <= s < 20]

    print(f"\n{'='*55}")
    print(f"  相談: {query}")
    print(f"{'='*55}")

    if reuse:
        print(f"\n【再利用候補】")
        for i, (asset, score) in enumerate(reuse, 1):
            print(f"\n  {i}. {asset['path']}")
            print(f"     タイトル: {asset['title']}")
            print(f"     種別    : {asset['type']}")
            if asset.get("notes"):
                note = asset["notes"][:80]
                print(f"     概要    : {note}{'...' if len(asset['notes']) > 80 else ''}")
            print(f"     関連度  : {'█' * (score // 10)}{'░' * (10 - score // 10)} {score}/100")
    else:
        print("\n【再利用候補】  該当なし")

    if low:
        print(f"\n【参考（低関連）】")
        for asset, score in low[:3]:
            print(f"  - {asset['path']}  ({score}/100)")

    if new_impls:
        print(f"\n【新規実装が必要】")
        for item in new_impls:
            print(f"  + {item}")
    else:
        print(f"\n【新規実装が必要】  クエリからは特定できず（詳細を教えてください）")

    print(f"\n{'='*55}\n")


# ─── メイン ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="既存資産の再利用候補を提案する")
    parser.add_argument("query", help="相談内容（例: 'Instagram投稿を自動生成したい'）")
    parser.add_argument("--top", type=int, default=5, help="最大表示件数（デフォルト: 5）")
    args = parser.parse_args()

    assets = load_all_assets()
    if not assets:
        print("資産が見つかりませんでした。registry.json や scripts/ を確認してください。")
        sys.exit(1)

    query_tokens = tokenize_query(args.query)
    scored = [(a, score_asset(a, query_tokens)) for a in assets]
    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:args.top]

    matched_paths = [a["title"] for a, s in top if s >= 20]
    new_impls = infer_new_implementations(args.query, matched_paths)

    print_results(args.query, top, new_impls)


if __name__ == "__main__":
    main()
