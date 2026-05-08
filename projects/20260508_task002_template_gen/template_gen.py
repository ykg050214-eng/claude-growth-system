#!/usr/bin/env python3
"""
template_gen.py — Claude Code プロジェクトテンプレート自動生成ツール
====================================================================
プロジェクトの種類を指定すると CLAUDE.md + フォルダ構成 + .gitignore を自動生成する。

使い方:
  python template_gen.py python-script my_project
  python template_gen.py web-app my_website
  python template_gen.py data-pipeline my_pipeline
  python template_gen.py api-integration my_api_bot
  python template_gen.py --list   # 対応タイプ一覧
"""

import argparse
import sys
from pathlib import Path

# ============================================================
# テンプレート定義
# ============================================================

TEMPLATES = {
    "python-script": {
        "description": "Pythonスクリプト・CLIツール",
        "dirs": ["src", "tests", "data", "logs", "docs"],
        "files": {
            "src/main.py": (
                '#!/usr/bin/env python3\n'
                '"""メインスクリプト"""\n\n'
                'def main():\n'
                '    print("Hello, Claude!")\n\n'
                'if __name__ == "__main__":\n'
                '    main()\n'
            ),
            "tests/test_main.py": (
                'from src.main import main\n\n'
                'def test_main():\n'
                '    main()  # smoke test\n'
            ),
            "requirements.txt": "anthropic>=0.40.0\npython-dotenv\n",
            ".env.example": "ANTHROPIC_API_KEY=sk-ant-your-key-here\n",
        },
        "claude_md": (
            "# {name} — Pythonスクリプトプロジェクト\n\n"
            "## 概要\n{name} の機能を記述してください。\n\n"
            "## セットアップ\n```bash\npip install -r requirements.txt\ncp .env.example .env\n# .env に ANTHROPIC_API_KEY を設定\n```\n\n"
            "## 実行方法\n```bash\npython src/main.py\n```\n\n"
            "## テスト\n```bash\npython -m pytest tests/\n```\n\n"
            "## ディレクトリ構成\n- `src/` : メインコード\n- `tests/` : テスト\n- `data/` : 入出力データ\n- `logs/` : 実行ログ\n"
        ),
        "gitignore": (
            "__pycache__/\n*.pyc\n.env\n*.egg-info/\ndist/\nbuild/\n"
            ".venv/\nvenv/\nlogs/*.log\ndata/output/\n"
        ),
    },

    "web-app": {
        "description": "HTML/CSS/JS Webアプリ",
        "dirs": ["src", "public/css", "public/js", "public/images", "assets"],
        "files": {
            "src/index.html": (
                '<!DOCTYPE html>\n<html lang="ja">\n<head>\n'
                '  <meta charset="UTF-8">\n'
                '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
                '  <title>{name}</title>\n'
                '  <link rel="stylesheet" href="public/css/style.css">\n'
                '</head>\n<body>\n'
                '  <h1>{name}</h1>\n'
                '  <script src="public/js/main.js"></script>\n'
                '</body>\n</html>\n'
            ),
            "public/css/style.css": (
                "* { box-sizing: border-box; margin: 0; padding: 0; }\n"
                "body { font-family: Arial, sans-serif; padding: 20px; }\n"
                "h1 { color: #1E3A5F; }\n"
            ),
            "public/js/main.js": 'console.log("{name} loaded");\n',
        },
        "claude_md": (
            "# {name} — Webアプリ\n\n"
            "## 概要\n{name} の機能を記述してください。\n\n"
            "## 起動方法\n```bash\n# ブラウザで開く\nopen src/index.html\n```\n\n"
            "## 構成\n- `src/index.html` : メインHTML\n- `public/css/` : スタイルシート\n- `public/js/` : JavaScriptファイル\n"
        ),
        "gitignore": "node_modules/\n.DS_Store\ndist/\n*.log\n",
    },

    "data-pipeline": {
        "description": "データ収集・変換・分析パイプライン",
        "dirs": ["src", "data/raw", "data/processed", "data/output", "notebooks", "logs"],
        "files": {
            "src/pipeline.py": (
                '#!/usr/bin/env python3\n"""データパイプライン"""\n\n'
                'from pathlib import Path\n\n'
                'RAW_DIR = Path("data/raw")\nPROCESSED_DIR = Path("data/processed")\nOUTPUT_DIR = Path("data/output")\n\n'
                'def extract():\n    """データ収集"""\n    pass\n\n'
                'def transform(data):\n    """データ変換"""\n    return data\n\n'
                'def load(data):\n    """データ保存"""\n    pass\n\n'
                'if __name__ == "__main__":\n    raw = extract()\n    processed = transform(raw)\n    load(processed)\n    print("パイプライン完了")\n'
            ),
            "requirements.txt": "pandas\nrequests\npython-dotenv\nopenpyxl\n",
        },
        "claude_md": (
            "# {name} — データパイプライン\n\n"
            "## 概要\nETL（Extract → Transform → Load）パイプライン。\n\n"
            "## 実行方法\n```bash\npython src/pipeline.py\n```\n\n"
            "## データフロー\n`data/raw/` → `src/pipeline.py` → `data/processed/` → `data/output/`\n\n"
            "## ディレクトリ\n- `data/raw/` : 生データ\n- `data/processed/` : 中間データ\n- `data/output/` : 最終出力\n- `notebooks/` : 分析ノートブック\n"
        ),
        "gitignore": (
            "__pycache__/\n*.pyc\n.env\ndata/raw/*\ndata/output/*\n"
            "!data/raw/.gitkeep\n!data/output/.gitkeep\nlogs/*.log\n"
        ),
    },

    "api-integration": {
        "description": "外部API連携・Claude API活用",
        "dirs": ["src", "tests", "logs", "examples"],
        "files": {
            "src/client.py": (
                '#!/usr/bin/env python3\n"""API クライアント"""\n\n'
                'import os\nimport anthropic\nfrom dotenv import load_dotenv\n\n'
                'load_dotenv()\n\n'
                'class ClaudeClient:\n'
                '    def __init__(self):\n'
                '        self.client = anthropic.Anthropic()\n'
                '        self.model = "claude-sonnet-4-6"\n\n'
                '    def chat(self, message: str, system: str = "") -> str:\n'
                '        kwargs = dict(\n'
                '            model=self.model,\n'
                '            max_tokens=2048,\n'
                '            messages=[{"role": "user", "content": message}],\n'
                '        )\n'
                '        if system:\n'
                '            kwargs["system"] = system\n'
                '        response = self.client.messages.create(**kwargs)\n'
                '        return response.content[0].text\n\n'
                'if __name__ == "__main__":\n'
                '    client = ClaudeClient()\n'
                '    print(client.chat("こんにちは！"))\n'
            ),
            "requirements.txt": "anthropic>=0.40.0\npython-dotenv\n",
            ".env.example": "ANTHROPIC_API_KEY=sk-ant-your-key-here\n",
            "examples/basic_usage.py": (
                'from src.client import ClaudeClient\n\n'
                'client = ClaudeClient()\n'
                'response = client.chat(\n'
                '    message="Pythonでリストを逆順にする方法を教えてください",\n'
                '    system="あなたは親切なプログラミング講師です"\n'
                ')\nprint(response)\n'
            ),
        },
        "claude_md": (
            "# {name} — Claude API 連携プロジェクト\n\n"
            "## セットアップ\n```bash\npip install -r requirements.txt\ncp .env.example .env\n# .env に ANTHROPIC_API_KEY を設定\n```\n\n"
            "## 実行方法\n```bash\npython src/client.py\npython examples/basic_usage.py\n```\n\n"
            "## 使用モデル\n- `claude-sonnet-4-6` : バランス型（デフォルト）\n- `claude-opus-4-6` : 高精度\n- `claude-haiku-4-5-20251001` : 高速・低コスト\n"
        ),
        "gitignore": "__pycache__/\n*.pyc\n.env\nlogs/*.log\n",
    },
}

# ============================================================
# 生成関数
# ============================================================

def generate(project_type: str, output_dir: str) -> bool:
    if project_type not in TEMPLATES:
        print(f"[ERROR] 未対応タイプ: {project_type}")
        print(f"対応タイプ: {', '.join(TEMPLATES.keys())}")
        return False

    tmpl = TEMPLATES[project_type]
    root = Path(output_dir)
    name = root.name

    print(f"\n🚀 {project_type} プロジェクトを生成中: {output_dir}")
    print(f"   説明: {tmpl['description']}\n")

    # フォルダ作成
    root.mkdir(parents=True, exist_ok=True)
    for d in tmpl["dirs"]:
        (root / d).mkdir(parents=True, exist_ok=True)
        (root / d / ".gitkeep").touch()
    print(f"  ✅ フォルダ作成: {len(tmpl['dirs'])} 個")

    # ファイル生成
    for filepath, content in tmpl["files"].items():
        target = root / filepath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content.replace("{name}", name), encoding="utf-8")
    print(f"  ✅ ファイル生成: {len(tmpl['files'])} 個")

    # CLAUDE.md
    claude_md = tmpl["claude_md"].replace("{name}", name)
    (root / "CLAUDE.md").write_text(claude_md, encoding="utf-8")
    print(f"  ✅ CLAUDE.md 生成")

    # .gitignore
    (root / ".gitignore").write_text(tmpl["gitignore"], encoding="utf-8")
    print(f"  ✅ .gitignore 生成")

    # ツリー表示
    print(f"\n📂 生成されたフォルダ構成:")
    for p in sorted(root.rglob("*")):
        if ".gitkeep" in p.name:
            continue
        indent = "  " * (len(p.relative_to(root).parts) - 1)
        icon = "📁" if p.is_dir() else "📄"
        print(f"  {indent}{icon} {p.name}")

    print(f"\n✨ 完了！次のコマンドで Claude Code を起動してください:")
    print(f"  cd {output_dir} && claude\n")
    return True


# ============================================================
# メイン
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Claude Code プロジェクトテンプレート自動生成ツール"
    )
    parser.add_argument("project_type", nargs="?", help="プロジェクトタイプ")
    parser.add_argument("output_dir",   nargs="?", help="出力先ディレクトリ名")
    parser.add_argument("--list", action="store_true", help="対応タイプ一覧を表示")
    args = parser.parse_args()

    if args.list or not args.project_type:
        print("\n=== 対応プロジェクトタイプ ===\n")
        for k, v in TEMPLATES.items():
            print(f"  {k:<20} {v['description']}")
        print(f"\n使い方: python template_gen.py <タイプ> <プロジェクト名>\n")
        return

    if not args.output_dir:
        print("[ERROR] 出力先ディレクトリを指定してください")
        parser.print_help()
        sys.exit(1)

    success = generate(args.project_type, args.output_dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
