# Claude 自走型成長システム — CLAUDE.md

> このファイルはClaude Codeが毎日読み込み、自律的にタスクを実行するための**行動指示書**です。
> 指示に従って、レポートを解析し、プロジェクトを実装し、GitHubに蓄積してください。

---

## システム概要

YouTube上のClaude解説動画を毎日分析し、動画内で紹介された機能・テクニック・プロジェクトを
実際に実装して蓄積していく自走型学習システムです。

**目標**: 毎日5本の動画から学び、コード・プロンプト・ワークフローとして具体化する。

---

## ディレクトリ構成

```
claude-growth-system/
├── CLAUDE.md              ← このファイル（行動指示書）
├── reports/
│   ├── raw/               ← 日次レポート YYYY-MM-DD.yaml
│   └── archive/           ← 実行済みレポートの保管先
├── projects/
│   ├── registry.json      ← 全タスクの実装状況トラッカー
│   └── YYYYMMDD_taskid/   ← 各タスクの実装物
├── prompts/               ← 学習したプロンプト・テクニック集
├── workflows/             ← 自動化スクリプト・ワークフロー
├── scripts/
│   ├── scout.py           ← YouTube動画スカウト（毎朝実行）
│   └── report_analyzer.py ← レポート解析ユーティリティ
└── logs/                  ← 実行ログ
```

---

## 毎日の実行フロー

Claude Codeは以下の順序で自律実行してください。

### STEP 1: 最新レポートを読み込む

```bash
# 最新のレポートファイルを特定
ls reports/raw/ | sort -r | head -1
```

`reports/raw/YYYY-MM-DD.yaml` を読み込み、全タスクを把握する。

### STEP 2: レジストリを確認してpendingタスクを特定

`projects/registry.json` を読み込み、`status: pending` のタスクを抽出する。
すでに `completed` または `in_progress` のタスクはスキップ。

**優先順位**:
1. `priority: high` のタスク
2. `difficulty: easy` → `medium` → `hard` の順
3. `dependencies` が空のタスク（依存なし優先）

### STEP 3: タスクを1つ選択して実装

選択したタスクの `implementation` セクションに従って実装する。

#### タスクタイプ別の実装方針

**`code_generation`（コード自動生成）**
- `projects/YYYYMMDD_taskid/` フォルダを作成
- `implementation.steps` を順番に実行
- `implementation.language` と `dependencies` に合わせた環境で実装
- 必ずREADME.mdを生成（何をするコードか・使い方・実行例）
- `implementation.sample_code` がある場合はベースとして使用し、完全動作するものに仕上げる
- 実行してエラーがないか確認する

**`prompt_technique`（プロンプト・活用術）**
- `prompts/YYYYMMDD_technique_name.md` として保存
- プロンプトのテンプレート・使い方・効果を記録
- 実際にClaude APIで試してサンプル出力も記録

**`data_pipeline`（データ収集・分析）**
- `projects/YYYYMMDD_taskid/` フォルダを作成
- データソース・変換処理・出力形式を実装
- サンプルデータで動作確認

**`workflow_automation`（ワークフロー自動化）**
- `workflows/YYYYMMDD_name/` フォルダを作成
- スクリプト・設定ファイルを実装
- 実行手順をREADMEに記録

### STEP 4: レジストリを更新

実装完了後、`projects/registry.json` を更新:

```json
{
  "task_id": "task_001",
  "status": "completed",
  "completed_at": "2026-05-08T10:30:00",
  "output_path": "projects/20260508_task001/",
  "notes": "動作確認済み。Python 3.11で実行可能。"
}
```

### STEP 5: 実行ログを記録

`logs/YYYY-MM-DD.md` に以下を記録:

```markdown
# 実行ログ 2026-05-08

## 実行タスク: task_001 — リサーチBot実装
- 開始時刻: 10:00
- 完了時刻: 10:30
- 成果物: projects/20260508_task001/
- 結果: 成功
- 学んだこと: Claude APIの長文コンテキスト処理は~500ms/1k tokens
```

### STEP 6: GitHubにPush

```bash
git add .
git commit -m "feat(auto): [YYYY-MM-DD] {task_title}

- Type: {task_type}
- Source: {video_url}
- Output: {output_path}"

git push origin main
```

---

## 重要なルール

1. **絶対に既存ファイルを削除しない** — 蓄積がこのシステムの価値
2. **動作確認必須** — コードは必ず実行してエラーがないか確認
3. **1日1タスク以上** — 最低1つは完了させる
4. **レポートが存在しない場合** — `scripts/scout.py` を実行してレポートを生成する
5. **エラー時** — `logs/` にエラーログを残し、次のタスクに移る
6. **依存関係** — `dependencies` に記載されたタスクが未完了なら別タスクを選ぶ

---

## 成長の記録方法

このシステムは実行するたびに賢くなります:

- `projects/registry.json` の `completed` 数が増えるほど複合実装が可能になる
- `prompts/` に蓄積されたテクニックを後続タスクで参照・活用する
- `logs/` の知見を次のscoutフェーズにフィードバックする

---

## 手動実行コマンド

```bash
# スカウトのみ実行（レポート生成）
python scripts/scout.py --date today

# 今日の実行タスクを確認
python scripts/report_analyzer.py --show-pending

# レジストリ状況確認
python scripts/report_analyzer.py --stats
```
