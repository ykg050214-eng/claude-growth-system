#!/usr/bin/env python3
"""
research_bot.py — Claude API リサーチ自動化スクリプト
======================================================
Claude Opus 4.6 の100万トークンコンテキストを活用して
複数のテキストソースを横断分析し、Markdownレポートを自動生成する。

使い方:
  python research_bot.py "Claude AI" doc1.txt doc2.txt
  python research_bot.py "Anthropic" --demo   # サンプルデータで試す
"""

import argparse
import sys
import os
from pathlib import Path
from datetime import datetime

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

# ============================================================
# デモ用サンプルテキスト（API不要で動作確認できる）
# ============================================================

DEMO_TEXTS = {
    "doc1_claude_overview.txt": """
Claude はAnthropicが開発した大規模言語モデルです。
Constitutional AI という手法で安全性を重視して訓練されています。
2026年現在、Claude Opus 4.6 が100万トークンのコンテキストウィンドウを持ち、
大量の文書を一度に処理できます。
コーディング・リサーチ・文書作成など幅広いタスクに対応しています。
""",
    "doc2_claude_models.txt": """
Claudeシリーズのモデル一覧（2026年5月）:
- claude-haiku-4-5: 最速・最安。チャットボットや分類タスクに最適。
- claude-sonnet-4-6: バランス型。コード生成やビジネス文書に推奨。
- claude-opus-4-6: 高精度・1Mコンテキスト。リサーチ・長文処理に最適。
- claude-opus-4-7: 最新一般公開モデル。高難度コーディングに最強。
APIはAnthropic公式サイトから取得可能。
""",
    "doc3_use_cases.txt": """
Claude の主な活用事例:
1. 企業での文書自動化（議事録・報告書・メール）
2. ソフトウェア開発支援（コード生成・レビュー・デバッグ）
3. リサーチ・データ分析（複数文献の横断分析）
4. コンテンツ制作（ブログ・マーケティング文書）
5. カスタマーサポートの自動化
中小企業での導入コストは月額数千円〜で始められる。
""",
}

# ============================================================
# コア関数
# ============================================================

def load_files(file_paths: list[str]) -> dict[str, str]:
    """複数ファイルを読み込んで辞書で返す。"""
    texts = {}
    for fp in file_paths:
        path = Path(fp)
        if not path.exists():
            print(f"  ⚠️  ファイルが見つかりません: {fp}")
            continue
        texts[path.name] = path.read_text(encoding="utf-8")
        print(f"  ✅ 読み込み完了: {path.name} ({len(texts[path.name])} 文字)")
    return texts


def build_prompt(keyword: str, texts: dict[str, str]) -> str:
    """リサーチプロンプトを構築する。"""
    sources_block = ""
    for i, (fname, content) in enumerate(texts.items(), 1):
        sources_block += f"\n---\n【ソース{i}: {fname}】\n{content}\n"

    return f"""以下の資料を横断的に分析し、「{keyword}」に関するリサーチレポートを作成してください。

=== 資料 ===
{sources_block}

=== 出力形式 ===

# リサーチレポート：{keyword}

## エグゼクティブサマリー
（3〜5文で要点をまとめる）

## 主要な発見事項
（資料から抽出した重要ポイントを箇条書き）

## 詳細分析
（各トピックを深掘り）

## 資料間の共通点・相違点
（複数資料を横断した比較・統合）

## 結論と示唆
（このリサーチから導き出せるインサイト）

## 参照資料
（使用したソースファイルの一覧）

---
レポート生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}
"""


def research_with_api(keyword: str, texts: dict[str, str]) -> str:
    """Claude API を使ってリサーチレポートを生成する。"""
    client = anthropic.Anthropic()
    prompt = build_prompt(keyword, texts)

    print(f"\n  🤖 Claude Opus 4.6 でリサーチ中... ({len(prompt)} 文字のプロンプト)")

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        system=(
            "あなたは優秀なリサーチアナリストです。"
            "提供された資料を批判的・横断的に分析し、"
            "構造化された高品質なレポートを作成してください。"
            "事実に基づいて記述し、資料にない情報は明記してください。"
        ),
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def research_demo(keyword: str, texts: dict[str, str]) -> str:
    """APIなしのデモ出力（構造確認用）。"""
    sources_list = "\n".join(f"- {fname}" for fname in texts.keys())
    total_chars = sum(len(t) for t in texts.values())
    return f"""# リサーチレポート：{keyword}

## エグゼクティブサマリー
このレポートは {len(texts)} 件の資料（合計 {total_chars} 文字）を分析しました。
**※ これはデモ出力です。** 実際の分析には `ANTHROPIC_API_KEY` の設定が必要です。

## 主要な発見事項
- 資料1〜{len(texts)} から自動抽出されたキーポイントがここに入ります
- Claude Opus 4.6 の100万トークンコンテキストにより大量文書を一度に処理可能
- 複数ソースの矛盾点・共通点を自動検出

## 詳細分析
（Claude API 接続時に自動生成されます）

## 資料間の比較
（Claude API 接続時に横断分析が実行されます）

## 結論と示唆
（Claude API 接続時に生成されます）

## 参照資料
{sources_list}

---
レポート生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}
生成モード: デモ（APIなし）
"""


# ============================================================
# メイン
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Claude API リサーチ自動化スクリプト"
    )
    parser.add_argument("keyword", help="リサーチキーワード")
    parser.add_argument("files", nargs="*", help="入力テキストファイル")
    parser.add_argument("--demo", action="store_true", help="サンプルデータでデモ実行")
    parser.add_argument("--output", default="", help="出力ファイル名（省略時は自動生成）")
    args = parser.parse_args()

    print(f"\n🔬 リサーチBotを起動します")
    print(f"   キーワード: {args.keyword}")

    # テキスト読み込み
    if args.demo:
        print(f"\n📄 デモ用サンプルデータを使用します（{len(DEMO_TEXTS)} 件）")
        texts = DEMO_TEXTS
    elif args.files:
        print(f"\n📄 ファイルを読み込み中...")
        texts = load_files(args.files)
        if not texts:
            print("[ERROR] 有効なファイルがありません。")
            sys.exit(1)
    else:
        print("[ERROR] ファイルを指定するか --demo オプションを使ってください。")
        parser.print_help()
        sys.exit(1)

    print(f"   合計 {sum(len(t) for t in texts.values())} 文字を処理します")

    # リサーチ実行
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if HAS_ANTHROPIC and api_key:
        report = research_with_api(args.keyword, texts)
        mode = "Claude Opus 4.6"
    else:
        if not HAS_ANTHROPIC:
            print("\n  ℹ️  anthropic パッケージ未インストール → デモモードで実行")
        elif not api_key:
            print("\n  ℹ️  ANTHROPIC_API_KEY 未設定 → デモモードで実行")
        report = research_demo(args.keyword, texts)
        mode = "デモ"

    # 保存
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = args.output or f"report_{args.keyword}_{date_str}.md"
    Path(output_file).write_text(report, encoding="utf-8")

    print(f"\n  ✅ レポート生成完了！")
    print(f"     出力ファイル: {output_file}")
    print(f"     モード: {mode}")
    print(f"     文字数: {len(report)} 文字")
    print(f"\n--- レポートプレビュー（先頭500文字） ---")
    print(report[:500])
    if len(report) > 500:
        print("...(続きはファイルを参照)")


if __name__ == "__main__":
    main()
