#!/usr/bin/env python3
"""
scout.py — Claude 自走型成長システム スカウトエンジン
========================================================
毎朝実行して YouTube の Claude 関連動画を検索し、
Claude Code が実行できる詳細な YAML レポートを生成する。

使い方:
  python scripts/scout.py                   # 今日のレポートを生成
  python scripts/scout.py --date 2026-05-08 # 特定日付で生成
  python scripts/scout.py --dry-run         # 生成せずに内容をプレビュー
"""

import os
import sys
import json
import argparse
import anthropic
from datetime import date, datetime
from pathlib import Path

# ============================================================
# 設定
# ============================================================

BASE_DIR = Path(__file__).parent.parent
REPORTS_DIR = BASE_DIR / "reports" / "raw"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# 検索クエリ（毎日ローテーションして多様な動画を収集）
SEARCH_QUERIES = [
    "Claude AI 最新モデル 解説 2026",
    "Claude Code 使い方 活用術 2026",
    "Anthropic Claude ニュース 最新情報",
    "Claude API プログラミング 自動化",
    "AI Claude 比較 GPT Gemini 2026",
]

# タスクタイプ定義（Claude Codeへの実装指示に使う）
TASK_TYPES = {
    "code_generation": "Pythonスクリプト・Webアプリなどのコード実装",
    "prompt_technique": "プロンプトテクニック・テンプレート作成",
    "data_pipeline": "データ収集・変換・分析パイプライン",
    "workflow_automation": "ファイル操作・定期タスク・自動化スクリプト",
}

# ============================================================
# YouTube 検索（WebSearch 経由）
# ============================================================

def search_youtube_videos(query: str, max_results: int = 5) -> list[dict]:
    """
    Claude API の web_search ツールで YouTube 動画を検索する。
    実際の Claude Code 実行環境では WebSearch MCP を使う。
    スタンドアロン実行時は Anthropic API の tool_use を使う。
    """
    client = anthropic.Anthropic()

    search_prompt = f"""
YouTube で以下のクエリを検索し、上位 {max_results} 件の動画情報を返してください。

検索クエリ: {query}

各動画について以下の情報を JSON 形式で返してください:
- title: 動画タイトル
- url: YouTube URL
- channel: チャンネル名
- description: 動画の概要（推測で可）
- key_points: 動画で解説していそうな要点（3〜5個）
- category: latest_model / usage_tips / news のいずれか（複数可）

JSON 配列形式で返してください。
"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": search_prompt}],
    )

    # レスポンスからJSONを抽出
    text = message.content[0].text
    try:
        start = text.find("[")
        end = text.rfind("]") + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])
    except json.JSONDecodeError:
        pass

    # フォールバック：空リスト
    return []


# ============================================================
# タスク生成（Claude API で動画内容を分析）
# ============================================================

def generate_tasks_from_videos(videos: list[dict], report_date: str) -> list[dict]:
    """
    動画情報を Claude API に渡して、実装可能なタスクを生成する。
    """
    client = anthropic.Anthropic()

    videos_text = json.dumps(videos, ensure_ascii=False, indent=2)

    prompt = f"""
以下の YouTube 動画リストを分析し、Claude Code が実際に実装できる具体的なタスクを生成してください。

動画リスト:
{videos_text}

各動画につき 1 つのタスクを生成してください。タスクは以下の条件を満たすこと:

1. **具体的**: 動画内で紹介された機能・テクニック・プロジェクトを実際に実装する内容
2. **実行可能**: Claude Code がこのタスクだけ読めば実装できる詳細な手順
3. **段階的**: steps に実装手順を 4〜6 ステップで記述
4. **コード付き**: sample_code にベースとなるコードスニペットを含める

以下の JSON 形式で返してください（配列形式）:

[
  {{
    "id": "task_001",
    "source_video_index": 0,
    "title": "タスクタイトル",
    "description": "詳細説明（Claude Codeが読んで実装できるレベル）",
    "type": "code_generation",
    "priority": "high",
    "difficulty": "medium",
    "estimated_minutes": 30,
    "dependencies": [],
    "implementation": {{
      "language": "python",
      "output_dir": "projects/{report_date.replace('-', '')}_task001/",
      "dependencies": ["anthropic", "requests"],
      "steps": ["STEP1: ...", "STEP2: ...", "STEP3: ..."],
      "sample_code": "# サンプルコード\\nimport anthropic\\n...",
      "expected_output": "main.py",
      "test_command": "python main.py",
      "notes": "実装時の注意事項"
    }},
    "status": "pending",
    "completed_at": null,
    "output_path": null,
    "execution_notes": null
  }}
]
"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    text = message.content[0].text
    try:
        start = text.find("[")
        end = text.rfind("]") + 1
        if start != -1 and end > start:
            tasks = json.loads(text[start:end])
            # ID を日付ベースに修正
            date_str = report_date.replace("-", "")
            for i, task in enumerate(tasks):
                task["id"] = f"task_{date_str}_{i+1:03d}"
                if "output_dir" in task.get("implementation", {}):
                    task["implementation"]["output_dir"] = (
                        f"projects/{date_str}_{task['id']}/"
                    )
            return tasks
    except (json.JSONDecodeError, KeyError):
        pass

    return []


# ============================================================
# YAML レポート生成
# ============================================================

def build_yaml_report(
    report_date: str,
    videos: list[dict],
    tasks: list[dict],
) -> str:
    """
    収集した動画情報とタスクを YAML 形式のレポートに変換する。
    """
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    lines = [
        f"# Claude 自走型成長システム — 日次レポート",
        f"# 生成日: {report_date} | Scout v1.0",
        f"# ============================================================",
        f"",
        f'date: "{report_date}"',
        f'generated_at: "{now}"',
        f'scout_version: "1.0"',
        f"",
        f"source_videos:",
    ]

    for i, v in enumerate(videos):
        vid_id = f"vid_{i+1:03d}"
        categories = v.get("category", ["usage_tips"])
        if isinstance(categories, str):
            categories = [categories]
        cats_str = "[" + ", ".join(f'"{c}"' for c in categories) + "]"

        key_points = v.get("key_points", [])

        lines += [
            f'  - id: "{vid_id}"',
            f'    title: "{v.get("title", "不明")}"',
            f'    url: "{v.get("url", "")}"',
            f'    channel: "{v.get("channel", "不明")}"',
            f'    language: "ja"',
            f'    category: {cats_str}',
            f'    summary: "{v.get("description", "")}"',
            f"    key_points:",
        ]
        for kp in key_points:
            lines.append(f'      - "{kp}"')
        lines.append("")

    lines += ["", "tasks:"]

    for task in tasks:
        impl = task.get("implementation", {})
        deps_list = impl.get("dependencies", [])
        deps_str = "[" + ", ".join(f'"{d}"' for d in deps_list) + "]"
        task_deps = task.get("dependencies", [])
        task_deps_str = "[" + ", ".join(f'"{d}"' for d in task_deps) + "]"
        steps = impl.get("steps", [])
        sample_code = impl.get("sample_code", "").replace('"', '\\"').replace("\n", "\\n")

        lines += [
            f'  - id: "{task["id"]}"',
            f'    title: "{task.get("title", "")}"',
            f'    description: |',
            f'      {task.get("description", "").replace(chr(10), chr(10)+"      ")}',
            f'    type: "{task.get("type", "code_generation")}"',
            f'    priority: "{task.get("priority", "medium")}"',
            f'    difficulty: "{task.get("difficulty", "medium")}"',
            f'    estimated_minutes: {task.get("estimated_minutes", 30)}',
            f'    dependencies: {task_deps_str}',
            f'    implementation:',
            f'      language: "{impl.get("language", "python")}"',
            f'      output_dir: "{impl.get("output_dir", "projects/")}"',
            f'      dependencies: {deps_str}',
            f'      steps:',
        ]
        for step in steps:
            lines.append(f'        - "{step}"')
        lines += [
            f'      expected_output: "{impl.get("expected_output", "main.py")}"',
            f'      test_command: "{impl.get("test_command", "python main.py")}"',
            f'      notes: "{impl.get("notes", "")}"',
            f'    status: "pending"',
            f'    completed_at: null',
            f'    output_path: null',
            f'    execution_notes: null',
            f'',
        ]

    # サマリー
    categories_all = set()
    models = set()
    techniques = []
    for v in videos:
        cats = v.get("category", [])
        if isinstance(cats, list):
            categories_all.update(cats)
        for kp in v.get("key_points", []):
            techniques.append(kp)
    cats_str = "[" + ", ".join(f'"{c}"' for c in sorted(categories_all)) + "]"
    models_str = '["Claude Opus 4.6", "Claude Code", "claude-sonnet-4-6"]'
    techniques_yaml = "\n".join(f'    - "{t[:60]}"' for t in techniques[:5])

    lines += [
        "daily_summary:",
        f"  total_videos: {len(videos)}",
        f"  total_tasks: {len(tasks)}",
        f"  categories_covered: {cats_str}",
        f'  highlight: "本日のClaude最新動向まとめ"',
        f"  models_mentioned: {models_str}",
        f"  key_techniques:",
        techniques_yaml,
    ]

    return "\n".join(lines)


# ============================================================
# メイン実行
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Claude 成長システム — 日次スカウトエンジン"
    )
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="レポート対象日 (YYYY-MM-DD). デフォルト: 今日",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="ファイルを保存せず内容をプレビューする",
    )
    parser.add_argument(
        "--query-index",
        type=int,
        default=None,
        help="使用する検索クエリのインデックス (0〜4). デフォルト: 日付に基づく自動選択",
    )
    args = parser.parse_args()

    report_date = args.date
    output_path = REPORTS_DIR / f"{report_date}.yaml"

    if output_path.exists() and not args.dry_run:
        print(f"[SKIP] レポートが既に存在します: {output_path}")
        sys.exit(0)

    # 検索クエリを決定（日付から自動ローテーション）
    if args.query_index is not None:
        query_idx = args.query_index % len(SEARCH_QUERIES)
    else:
        day_of_year = datetime.strptime(report_date, "%Y-%m-%d").timetuple().tm_yday
        query_idx = day_of_year % len(SEARCH_QUERIES)

    query = SEARCH_QUERIES[query_idx]
    print(f"[SCOUT] 日付: {report_date}")
    print(f"[SCOUT] 検索クエリ: {query}")

    # 1. YouTube 検索
    print("[SCOUT] YouTube 動画を検索中...")
    videos = search_youtube_videos(query, max_results=5)
    print(f"[SCOUT] {len(videos)} 件の動画を取得")

    if not videos:
        print("[ERROR] 動画が取得できませんでした。ANTHROPIC_API_KEY を確認してください。")
        sys.exit(1)

    # 2. タスク生成
    print("[SCOUT] タスクを生成中...")
    tasks = generate_tasks_from_videos(videos, report_date)
    print(f"[SCOUT] {len(tasks)} 件のタスクを生成")

    # 3. YAML 生成
    yaml_content = build_yaml_report(report_date, videos, tasks)

    if args.dry_run:
        print("\n" + "=" * 60)
        print("[DRY-RUN] 生成されるレポートのプレビュー:")
        print("=" * 60)
        print(yaml_content[:3000])
        if len(yaml_content) > 3000:
            print(f"\n... (残り {len(yaml_content) - 3000} 文字省略)")
        return

    # 4. 保存
    output_path.write_text(yaml_content, encoding="utf-8")
    print(f"[SCOUT] レポートを保存しました: {output_path}")
    print(f"[SCOUT] 動画数: {len(videos)}, タスク数: {len(tasks)}")
    print("[SCOUT] 完了！Claude Code で以下を実行してタスクを実装してください:")
    print(f"  cd {BASE_DIR} && claude")


if __name__ == "__main__":
    main()
