#!/usr/bin/env python3
"""
model_selector.py — Claude モデル選択ガイドスクリプト
========================================================
ユースケースを入力するとベストなモデルと設定を推薦する。
（2026年5月時点のモデル情報）

使い方:
  python model_selector.py          # 対話モード
  python model_selector.py --list   # モデル一覧
"""

import argparse

# ============================================================
# モデル定義（2026年5月時点）
# ============================================================

MODELS = {
    "claude-haiku-4-5-20251001": {
        "nickname": "Haiku（高速・低コスト）",
        "speed": "超高速（~0.5秒）",
        "cost": "最安（約$0.0008/1K tokens）",
        "context": "200K tokens",
        "strengths": ["高速応答", "大量バッチ処理", "シンプルなタスク", "分類・フィルタリング"],
        "weaknesses": ["複雑な推論", "長文の高品質生成"],
        "best_for": ["チャットボット", "リアルタイム応答", "大量テキスト分類", "要約"],
        "temperature": 0.3,
        "max_tokens": 1024,
    },
    "claude-sonnet-4-6": {
        "nickname": "Sonnet（バランス型・推奨）",
        "speed": "高速（~1〜2秒）",
        "cost": "中（約$0.003/1K tokens）",
        "context": "200K tokens",
        "strengths": ["バランス", "コード生成", "分析", "日本語品質"],
        "weaknesses": ["超高精度な推論はOpusに劣る"],
        "best_for": ["コード生成・レビュー", "ビジネス文書", "データ分析", "一般的なChatBot"],
        "temperature": 0.5,
        "max_tokens": 2048,
    },
    "claude-opus-4-6": {
        "nickname": "Opus 4.6（高精度・大容量）",
        "speed": "中速（~3〜5秒）",
        "cost": "高（約$0.015/1K tokens）",
        "context": "1,000,000 tokens（100万！）",
        "strengths": ["最高精度", "複雑な推論", "長文処理", "研究・分析", "創作"],
        "weaknesses": ["コスト高", "応答速度"],
        "best_for": ["リサーチ・横断分析", "複雑なコーディング", "長編文書生成", "高精度が必要なタスク"],
        "temperature": 0.7,
        "max_tokens": 4096,
    },
    "claude-opus-4-7": {
        "nickname": "Opus 4.7（最新・一般公開最強）",
        "speed": "中速（~3〜6秒）",
        "cost": "最高（約$0.020/1K tokens）",
        "context": "200K tokens",
        "strengths": ["最高精度", "ソフトウェアエンジニアリング", "実世界タスク"],
        "weaknesses": ["コスト最高", "応答速度"],
        "best_for": ["高難度コーディング", "複雑なエージェントタスク", "品質最優先の場面"],
        "temperature": 0.5,
        "max_tokens": 4096,
    },
}

# ユースケース → モデル推薦マッピング
USE_CASE_MAP = {
    "1": ("claude-haiku-4-5-20251001", "リアルタイムチャット・単純応答が中心のため"),
    "2": ("claude-sonnet-4-6",         "コード生成に最もバランスが良いため"),
    "3": ("claude-opus-4-6",           "100万トークンコンテキストで大量文書を横断分析できるため"),
    "4": ("claude-sonnet-4-6",         "ビジネス文書生成はSonnetのコスパが最適のため"),
    "5": ("claude-haiku-4-5-20251001", "大量テキストの高速分類にはHaikuが最適のため"),
    "6": ("claude-opus-4-7",           "高難度コーディングは現時点の一般公開最強モデルが最適のため"),
    "7": ("claude-opus-4-6",           "長文・創作はOpus 4.6の大コンテキストが有利のため"),
}

def print_separator(char="─", width=60):
    print(char * width)

def show_model_list():
    print("\n" + "=" * 60)
    print("  Claude モデル一覧（2026年5月時点）")
    print("=" * 60)
    for model_id, info in MODELS.items():
        print(f"\n📌 {info['nickname']}")
        print(f"   モデルID : {model_id}")
        print(f"   速度     : {info['speed']}")
        print(f"   コスト   : {info['cost']}")
        print(f"   コンテキスト: {info['context']}")
        print(f"   得意     : {', '.join(info['strengths'])}")
        print(f"   最適用途 : {', '.join(info['best_for'])}")
    print()

def show_recommendation(model_id: str, reason: str):
    info = MODELS[model_id]
    print_separator("═")
    print(f"\n  ✅ 推奨モデル: {info['nickname']}")
    print(f"  理由: {reason}")
    print_separator()
    print(f"\n  モデルID    : {model_id}")
    print(f"  速度        : {info['speed']}")
    print(f"  コスト      : {info['cost']}")
    print(f"  コンテキスト: {info['context']}")
    print(f"\n  推奨パラメータ:")
    print(f"    temperature : {info['temperature']}")
    print(f"    max_tokens  : {info['max_tokens']}")
    print(f"\n  APIサンプルコード:")
    print_separator()
    sample = f"""import anthropic

client = anthropic.Anthropic()
message = client.messages.create(
    model="{model_id}",
    max_tokens={info['max_tokens']},
    temperature={info['temperature']},
    system="あなたは親切なアシスタントです。",
    messages=[
        {{"role": "user", "content": "ここにメッセージを入力"}}
    ]
)
print(message.content[0].text)"""
    print(sample)
    print_separator()

def interactive_mode():
    print("\n" + "=" * 60)
    print("  🤖 Claude モデル選択ガイド")
    print("  ユースケースに最適なモデルを推薦します")
    print("=" * 60)

    print("""
ユースケースを選んでください：

  1. チャットボット / リアルタイム応答
  2. コード生成・プログラミング支援
  3. 長文リサーチ・複数文書の横断分析
  4. ビジネス文書生成（メール・報告書など）
  5. 大量テキストの分類・フィルタリング
  6. 高難度コーディング・エージェントタスク
  7. 長編小説・創作・長文コンテンツ生成
""")

    while True:
        choice = input("番号を入力 (1〜7、またはqで終了): ").strip()
        if choice.lower() == "q":
            print("\nお疲れさまでした！\n")
            break
        if choice in USE_CASE_MAP:
            model_id, reason = USE_CASE_MAP[choice]
            show_recommendation(model_id, reason)

            again = input("\n別のユースケースも確認しますか？(y/n): ").strip().lower()
            if again != "y":
                break
            print()
        else:
            print("  1〜7 の番号を入力してください。")

def main():
    parser = argparse.ArgumentParser(description="Claude モデル選択ガイド")
    parser.add_argument("--list", action="store_true", help="モデル一覧を表示")
    args = parser.parse_args()

    if args.list:
        show_model_list()
    else:
        interactive_mode()

if __name__ == "__main__":
    main()
