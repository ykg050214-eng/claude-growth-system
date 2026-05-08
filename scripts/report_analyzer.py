#!/usr/bin/env python3
"""
report_analyzer.py — レポート解析・統計ユーティリティ
======================================================
Claude Code が実行前に呼び出し、今日のタスク・進捗状況を確認するツール。

使い方:
  python scripts/report_analyzer.py --show-pending    # 未実装タスク一覧
  python scripts/report_analyzer.py --stats           # 累計統計
  python scripts/report_analyzer.py --next            # 次に実装すべきタスクを1つ表示
  python scripts/report_analyzer.py --complete TASK_ID  # タスクを完了済みにする
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

BASE_DIR = Path(__file__).parent.parent
REPORTS_DIR = BASE_DIR / "reports" / "raw"
REGISTRY_PATH = BASE_DIR / "projects" / "registry.json"

# ============================================================
# YAML 読み込み（PyYAML なしでも動く簡易パーサー）
# ============================================================

def load_yaml_simple(path: Path) -> dict:
    """PyYAML がなくても動く最小限のYAML読み込み。"""
    if HAS_YAML:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    # フォールバック: タスクIDとタイトルだけ抽出
    tasks = []
    current_task = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith('- id: "task_'):
                if current_task:
                    tasks.append(current_task)
                current_task = {"id": stripped.split('"')[1], "status": "pending"}
            elif current_task and stripped.startswith('title: "'):
                current_task["title"] = stripped.split('"')[1]
            elif current_task and stripped.startswith('status: "'):
                current_task["status"] = stripped.split('"')[1]
            elif current_task and stripped.startswith('type: "'):
                current_task["type"] = stripped.split('"')[1]
            elif current_task and stripped.startswith('priority: "'):
                current_task["priority"] = stripped.split('"')[1]
            elif current_task and stripped.startswith('difficulty: "'):
                current_task["difficulty"] = stripped.split('"')[1]
    if current_task:
        tasks.append(current_task)

    return {"tasks": tasks}


def load_registry() -> dict:
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"tasks": [], "stats": {}}


def save_registry(registry: dict):
    registry["_meta"]["last_updated"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)


# ============================================================
# 最新レポートを取得
# ============================================================

def get_latest_report_path() -> Path | None:
    reports = sorted(REPORTS_DIR.glob("*.yaml"), reverse=True)
    return reports[0] if reports else None


def get_pending_tasks(report: dict, registry: dict) -> list[dict]:
    """レポートのタスクのうち、未実装のものを返す。"""
    completed_ids = {t["id"] for t in registry.get("tasks", []) if t["status"] == "completed"}
    in_progress_ids = {t["id"] for t in registry.get("tasks", []) if t["status"] == "in_progress"}

    pending = []
    for task in report.get("tasks", []):
        task_id = task.get("id", "")
        if task_id not in completed_ids and task_id not in in_progress_ids:
            if task.get("status", "pending") not in ("completed", "failed"):
                pending.append(task)

    # 優先順位でソート
    priority_order = {"high": 0, "medium": 1, "low": 2}
    difficulty_order = {"easy": 0, "medium": 1, "hard": 2}
    pending.sort(key=lambda t: (
        priority_order.get(t.get("priority", "medium"), 1),
        difficulty_order.get(t.get("difficulty", "medium"), 1),
        len(t.get("dependencies", [])),
    ))
    return pending


# ============================================================
# コマンド実装
# ============================================================

def cmd_show_pending():
    report_path = get_latest_report_path()
    if not report_path:
        print("[ERROR] レポートが見つかりません。先に scout.py を実行してください。")
        sys.exit(1)

    report = load_yaml_simple(report_path)
    registry = load_registry()
    pending = get_pending_tasks(report, registry)

    print(f"\n=== 未実装タスク一覧 ({report_path.stem}) ===\n")
    if not pending:
        print("✅ 本日のタスクはすべて完了しています！")
        return

    for i, task in enumerate(pending, 1):
        deps = task.get("dependencies", [])
        dep_str = f" [依存: {', '.join(deps)}]" if deps else ""
        print(
            f"{i}. [{task.get('priority','?').upper()}/{task.get('difficulty','?')}] "
            f"{task.get('id', '?')} — {task.get('title', '?')}"
            f"{dep_str}"
        )
        print(f"   タイプ: {task.get('type', '?')} | "
              f"推定時間: {task.get('estimated_minutes', '?')}分")
        print()


def cmd_next():
    report_path = get_latest_report_path()
    if not report_path:
        print("[ERROR] レポートが見つかりません。")
        sys.exit(1)

    report = load_yaml_simple(report_path)
    registry = load_registry()
    pending = get_pending_tasks(report, registry)

    if not pending:
        print("✅ 本日のタスクはすべて完了しています！")
        return

    task = pending[0]
    impl = task.get("implementation", {})

    print(f"\n=== 次の実装タスク ===\n")
    print(f"ID       : {task.get('id')}")
    print(f"タイトル : {task.get('title')}")
    print(f"タイプ   : {task.get('type')}")
    print(f"優先度   : {task.get('priority')} / 難易度: {task.get('difficulty')}")
    print(f"推定時間 : {task.get('estimated_minutes', '?')}分")
    print(f"\n--- 説明 ---")
    print(task.get("description", "").strip())
    print(f"\n--- 実装ステップ ---")
    for step in impl.get("steps", []):
        print(f"  {step}")
    print(f"\n--- 成果物 ---")
    print(f"  出力先     : {impl.get('output_dir', '?')}")
    print(f"  ファイル   : {impl.get('expected_output', '?')}")
    print(f"  テスト実行 : {impl.get('test_command', '?')}")
    deps = impl.get("dependencies", [])
    if deps:
        print(f"  pip install: {' '.join(deps)}")

    sample = impl.get("sample_code", "").strip()
    if sample:
        print(f"\n--- サンプルコード ---")
        print(sample[:800])
        if len(sample) > 800:
            print("  ... (省略)")


def cmd_stats():
    registry = load_registry()
    tasks = registry.get("tasks", [])
    stats = registry.get("stats", {})

    completed = [t for t in tasks if t.get("status") == "completed"]
    pending   = [t for t in tasks if t.get("status") == "pending"]
    failed    = [t for t in tasks if t.get("status") == "failed"]

    # レポートファイル数
    report_count = len(list(REPORTS_DIR.glob("*.yaml")))

    print("\n=== Claude 自走型成長システム — 統計 ===\n")
    print(f"📅 分析済みレポート日数 : {report_count} 日")
    print(f"✅ 完了タスク           : {len(completed)} 件")
    print(f"⏳ 未実装タスク         : {len(pending)} 件")
    print(f"❌ 失敗タスク           : {len(failed)} 件")
    print(f"📦 総タスク数           : {len(tasks)} 件")

    if completed:
        print(f"\n--- 完了済みタスク ---")
        for t in completed:
            print(f"  ✅ [{t['report_date']}] {t['title']}")

    # タイプ別集計
    type_counts: dict[str, int] = {}
    for t in completed:
        type_counts[t.get("type", "other")] = type_counts.get(t.get("type", "other"), 0) + 1
    if type_counts:
        print(f"\n--- タイプ別完了数 ---")
        for k, v in sorted(type_counts.items(), key=lambda x: -x[1]):
            print(f"  {k}: {v} 件")

    # プロジェクトフォルダ数
    projects_dir = BASE_DIR / "projects"
    project_dirs = [d for d in projects_dir.iterdir() if d.is_dir()]
    prompts_dir = BASE_DIR / "prompts"
    prompt_files = list(prompts_dir.glob("*.md"))
    print(f"\n🗂  実装済みプロジェクト : {len(project_dirs)} 個")
    print(f"💡 蓄積プロンプト       : {len(prompt_files)} 個")


def cmd_complete(task_id: str, output_path: str = "", notes: str = ""):
    registry = load_registry()
    tasks = registry.get("tasks", [])

    for t in tasks:
        if t["id"] == task_id:
            t["status"] = "completed"
            t["completed_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            t["output_path"] = output_path or f"projects/{task_id}/"
            t["execution_notes"] = notes or "Claude Code により自動実装・完了"
            save_registry(registry)
            print(f"✅ タスク {task_id} を完了済みにしました。")
            return

    print(f"[ERROR] タスク {task_id} がレジストリに見つかりません。")
    sys.exit(1)


# ============================================================
# メイン
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Claude 成長システム — レポートアナライザー")
    parser.add_argument("--show-pending", action="store_true", help="未実装タスク一覧を表示")
    parser.add_argument("--next",         action="store_true", help="次のタスクの詳細を表示")
    parser.add_argument("--stats",        action="store_true", help="累計統計を表示")
    parser.add_argument("--complete",     metavar="TASK_ID",   help="タスクを完了済みにする")
    parser.add_argument("--output-path",  default="",          help="--complete と一緒に使う成果物パス")
    parser.add_argument("--notes",        default="",          help="--complete と一緒に使う実行メモ")
    args = parser.parse_args()

    if args.complete:
        cmd_complete(args.complete, args.output_path, args.notes)
    elif args.stats:
        cmd_stats()
    elif args.next:
        cmd_next()
    else:
        # デフォルト: pending 表示
        cmd_show_pending()


if __name__ == "__main__":
    main()
