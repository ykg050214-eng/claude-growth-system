# Claude 自走型成長システム

> YouTube の Claude 解説動画を毎日自動分析し、紹介された機能・テクニック・プロジェクトを
> **Claude Code が実際に実装して蓄積していく**自走型学習システムです。

---

## システムの仕組み

```
毎朝（自動）                        毎日（Claude Code が実行）
─────────────                       ──────────────────────────
scout.py 実行                       claude コマンド起動
    ↓                                   ↓
YouTube動画を5本検索               CLAUDE.md を読み込む
    ↓                                   ↓
動画内容を Claude API で分析       最新レポート(YAML)を読む
    ↓                                   ↓
アクション可能な YAML レポート生成  pendingタスクを1つ選んで実装
    ↓                                   ↓
reports/raw/YYYY-MM-DD.yaml 保存   成果物を projects/ に保存
                                        ↓
                                   registry.json を更新
                                        ↓
                                   git commit & push（GitHub）
```

---

## ディレクトリ構成

```
claude-growth-system/
├── CLAUDE.md                      ← Claude Code の行動指示書（最重要）
├── README.md                      ← このファイル
│
├── reports/
│   ├── schema.yaml                ← レポートのスキーマ定義
│   └── raw/
│       └── YYYY-MM-DD.yaml        ← 日次分析レポート（自動生成）
│
├── projects/
│   ├── registry.json              ← タスク実装状況トラッカー
│   └── YYYYMMDD_task001/          ← 実装済みプロジェクト（Claude Codeが生成）
│       ├── main.py
│       └── README.md
│
├── prompts/
│   └── YYYYMMDD_technique.md      ← 学習したプロンプト・テクニック集
│
├── workflows/
│   └── YYYYMMDD_workflow/         ← 自動化スクリプト・ワークフロー
│
├── scripts/
│   ├── scout.py                   ← YouTube スカウトエンジン
│   └── report_analyzer.py         ← レポート解析ユーティリティ
│
└── logs/
    └── YYYY-MM-DD.md              ← 日次実行ログ（Claude Codeが記録）
```

---

## セットアップ（初回のみ）

### 1. リポジトリをクローンまたはこのフォルダを GitHub に push

```bash
cd claude-growth-system
git init
git remote add origin https://github.com/あなたのユーザー名/claude-growth-system.git
git add .
git commit -m "chore: initial setup"
git push -u origin main
```

### 2. 依存パッケージをインストール

```bash
pip install anthropic python-dotenv pyyaml requests
```

### 3. 環境変数を設定

```bash
# .env ファイルを作成
echo "ANTHROPIC_API_KEY=sk-ant-あなたのAPIキー" > .env
```

> APIキーは https://console.anthropic.com から取得できます。

### 4. Claude Code をインストール（未インストールの場合）

```bash
npm install -g @anthropic-ai/claude-code
```

---

## 毎日の使い方

### フェーズ1：スカウト（レポート生成）

```bash
# 今日の YouTube 動画を検索してレポートを生成
python scripts/scout.py

# 特定の日付で生成
python scripts/scout.py --date 2026-05-09

# 生成内容をプレビュー（保存しない）
python scripts/scout.py --dry-run
```

### フェーズ2：実行（Claude Code でタスクを実装）

```bash
# このフォルダで Claude Code を起動
cd claude-growth-system
claude

# Claude Code は CLAUDE.md を読んで自動的に以下を実行します：
# 1. 最新レポートを読む
# 2. pending タスクを選択
# 3. タスクを実装
# 4. registry.json を更新
# 5. git push
```

### 状況確認コマンド

```bash
# 未実装タスクを確認
python scripts/report_analyzer.py --show-pending

# 次のタスクの詳細を確認
python scripts/report_analyzer.py --next

# 累計統計を確認
python scripts/report_analyzer.py --stats

# タスクを手動で完了済みにする
python scripts/report_analyzer.py --complete task_001 --output-path projects/20260508_task001/
```

---

## 自動化（毎日自動実行）

### macOS の場合（launchd / cron）

```bash
# crontab に追加（毎朝 7:00 にスカウト実行）
crontab -e
```

```cron
# 毎朝 7:00 にスカウトを実行
0 7 * * * cd /path/to/claude-growth-system && python scripts/scout.py >> logs/scout.log 2>&1

# 毎朝 8:00 に Claude Code でタスクを実行
0 8 * * * cd /path/to/claude-growth-system && claude --print "CLAUDE.mdの指示に従って今日のタスクを1つ実装してください" >> logs/execute.log 2>&1
```

### Cowork スケジュールタスクで自動化する場合

Cowork の「スケジュール」機能から毎日のスカウトタスクを登録できます。

---

## タスクタイプ一覧

| タイプ | 内容 | 成果物の場所 |
|--------|------|-------------|
| `code_generation` | Pythonスクリプト・Webアプリ実装 | `projects/YYYYMMDD_taskid/` |
| `prompt_technique` | プロンプトテンプレート作成 | `prompts/YYYYMMDD_name.md` |
| `data_pipeline` | データ収集・分析パイプライン | `projects/YYYYMMDD_taskid/` |
| `workflow_automation` | 自動化スクリプト・ワークフロー | `workflows/YYYYMMDD_name/` |

---

## 成長の記録

このシステムを毎日動かすことで：

- **Week 1**: 基本的なClaude APIの使い方・プロンプトテクニックが蓄積
- **Week 2**: データパイプライン・自動化スクリプトが実装される
- **Month 1**: 複合プロジェクト（複数技術の組み合わせ）が実装可能に
- **Month 3+**: 前日の成果を活用した発展的なプロジェクトへ自動進化

`projects/registry.json` の `completed` 数と `projects/` フォルダが成長の証です。

---

## トラブルシューティング

**scout.py が動かない**
→ `ANTHROPIC_API_KEY` が正しく設定されているか確認してください。

**Claude Code がタスクを実装しない**
→ `claude-growth-system/` フォルダ内で `claude` を起動しているか確認してください。
→ `CLAUDE.md` が存在するか確認してください。

**git push が失敗する**
→ `git remote -v` でリモートリポジトリが設定されているか確認してください。
