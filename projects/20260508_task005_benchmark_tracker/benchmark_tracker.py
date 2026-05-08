#!/usr/bin/env python3
"""
benchmark_tracker.py — AIベンチマーク追跡ツール
=================================================
主要AIモデルのベンチマーク情報をJSONで管理し、
Markdown比較表を自動生成する。

使い方:
  python benchmark_tracker.py generate          # benchmarks.md を生成
  python benchmark_tracker.py list              # 登録モデル一覧
  python benchmark_tracker.py add               # 新モデル追加（対話）
"""

import json, argparse, sys
from pathlib import Path
from datetime import datetime

DB_PATH = Path("benchmarks.json")

DEFAULT_DB = {
    "_meta": {"updated": "2026-05-08", "note": "2026年5月時点のデータ"},
    "models": [
        {
            "name": "Claude Mythos", "org": "Anthropic", "released": "2026-04（限定）",
            "available": False,
            "benchmarks": {
                "SWE-bench Verified": 93.9, "USAMO 2026": 97.6,
                "HumanEval": 98.5, "MMLU": 96.2
            },
            "notes": "11組織への限定プレビューのみ。一般公開未定。"
        },
        {
            "name": "Claude Opus 4.7", "org": "Anthropic", "released": "2026-04-16",
            "available": True,
            "benchmarks": {
                "SWE-bench Verified": 85.2, "USAMO 2026": 89.4,
                "HumanEval": 95.1, "MMLU": 93.8
            },
            "notes": "現時点の一般公開最強モデル。"
        },
        {
            "name": "Claude Opus 4.6", "org": "Anthropic", "released": "2026-02",
            "available": True,
            "benchmarks": {
                "SWE-bench Verified": 78.3, "USAMO 2026": 82.1,
                "HumanEval": 92.4, "MMLU": 91.5
            },
            "notes": "100万トークンコンテキスト対応。"
        },
        {
            "name": "Claude Sonnet 4.6", "org": "Anthropic", "released": "2026-02-17",
            "available": True,
            "benchmarks": {
                "SWE-bench Verified": 70.1, "USAMO 2026": 74.0,
                "HumanEval": 88.7, "MMLU": 88.9
            },
            "notes": "バランス型。コスパ最優秀。"
        },
        {
            "name": "GPT-4o", "org": "OpenAI", "released": "2024-05",
            "available": True,
            "benchmarks": {
                "SWE-bench Verified": 72.0, "USAMO 2026": 70.5,
                "HumanEval": 90.2, "MMLU": 88.7
            },
            "notes": "参考値（2026年5月時点）。"
        },
        {
            "name": "Gemini 2.0 Ultra", "org": "Google", "released": "2025-12",
            "available": True,
            "benchmarks": {
                "SWE-bench Verified": 68.4, "USAMO 2026": 75.0,
                "HumanEval": 87.5, "MMLU": 90.1
            },
            "notes": "参考値（2026年5月時点）。"
        },
    ]
}

def load_db():
    if DB_PATH.exists():
        return json.loads(DB_PATH.read_text(encoding="utf-8"))
    db = DEFAULT_DB.copy()
    DB_PATH.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")
    return db

def cmd_generate():
    db = load_db()
    models = db["models"]
    bench_keys = ["SWE-bench Verified", "HumanEval", "MMLU", "USAMO 2026"]

    lines = [
        "# AI モデル ベンチマーク比較表",
        f"\n> 最終更新: {datetime.now().strftime('%Y年%m月%d日')} | データソース: 各公式発表",
        "\n## スコア比較（%）\n",
        "| モデル | 組織 | 公開日 | 利用可否 | " +
        " | ".join(bench_keys) + " | 備考 |",
        "|--------|------|--------|----------|" +
        "--------|" * len(bench_keys) + "------|",
    ]

    # SWE-benchスコアで降順ソート
    sorted_models = sorted(
        models,
        key=lambda m: m["benchmarks"].get("SWE-bench Verified", 0),
        reverse=True
    )

    for m in sorted_models:
        avail = "✅ 公開中" if m["available"] else "🔒 限定"
        scores = " | ".join(
            f"{m['benchmarks'].get(k, 'N/A')}" for k in bench_keys
        )
        lines.append(
            f"| **{m['name']}** | {m['org']} | {m['released']} | {avail} | "
            f"{scores} | {m['notes']} |"
        )

    lines += [
        "\n## グラフ（SWE-bench Verified）\n",
        "```",
    ]
    for m in sorted_models:
        score = m["benchmarks"].get("SWE-bench Verified", 0)
        bar = "█" * int(score / 2.5)
        avail_mark = "🟢" if m["available"] else "🔴"
        lines.append(f"{avail_mark} {m['name']:<22} {bar} {score:.1f}%")
    lines.append("```")

    lines += [
        "\n## 凡例",
        "- 🟢 一般公開中  🔴 限定公開・未公開",
        "- **SWE-bench Verified**: コーディング能力（実際のGitHub Issues解決率）",
        "- **HumanEval**: コード生成正解率",
        "- **MMLU**: 多分野知識テスト",
        "- **USAMO 2026**: 数学オリンピック問題正解率",
        f"\n---\n*生成: {datetime.now().strftime('%Y-%m-%d %H:%M')} by benchmark_tracker.py*",
    ]

    output = Path("benchmarks.md")
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ benchmarks.md を生成しました（{len(sorted_models)} モデル）")
    print("\n--- プレビュー ---")
    print("\n".join(lines[:20]))

def cmd_list():
    db = load_db()
    print(f"\n=== 登録モデル一覧（{len(db['models'])} 件）===\n")
    for m in db["models"]:
        avail = "✅" if m["available"] else "🔒"
        swe = m["benchmarks"].get("SWE-bench Verified", "N/A")
        print(f"  {avail} {m['name']:<25} SWE-bench: {swe}%  ({m['released']})")

def cmd_add():
    db = load_db()
    print("\n=== 新規モデルを追加 ===\n")
    name    = input("モデル名: ").strip()
    org     = input("組織名: ").strip()
    released= input("公開日 (例: 2026-05): ").strip()
    avail   = input("一般公開? (y/n): ").strip().lower() == "y"
    swe     = float(input("SWE-bench Verified (%): ") or 0)
    humaneval = float(input("HumanEval (%): ") or 0)
    mmlu    = float(input("MMLU (%): ") or 0)
    notes   = input("備考: ").strip()

    db["models"].append({
        "name": name, "org": org, "released": released, "available": avail,
        "benchmarks": {"SWE-bench Verified": swe, "HumanEval": humaneval, "MMLU": mmlu},
        "notes": notes,
    })
    db["_meta"]["updated"] = datetime.now().strftime("%Y-%m-%d")
    DB_PATH.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ {name} を追加しました。")

def main():
    parser = argparse.ArgumentParser(description="AIベンチマーク追跡ツール")
    parser.add_argument("command", nargs="?", default="generate",
                        choices=["generate", "list", "add"])
    args = parser.parse_args()
    {"generate": cmd_generate, "list": cmd_list, "add": cmd_add}[args.command]()

if __name__ == "__main__":
    main()
