# minilang

学習用の小さい言語処理系。Lexer → Parser → Evaluator を手書きで理解するためのリポジトリ。

## ステップ

1. **電卓**：四則演算と括弧
2. **変数と print**（現在地）
3. **if / while**
4. **関数定義（クロージャ）**

## 各ステップで何が増えるか

| | 扱う単位 | できること | 内部で増えるもの |
|---|---|---|---|
| Step 1 | 式 1個 | 四則演算と括弧を評価 | Lexer / Parser / Evaluator の3段 |
| Step 2 | 文の並び | 変数に値を保持、`print` で出力 | 環境 `env`、文（statement） |
| Step 3 | 文の並び | `if` / `while` で分岐・反復 | 制御フローのノード |
| Step 4 | 文の並び | 関数定義と呼び出し（クロージャ） | スコープ・第一級関数 |

各ステップは「前のステップで足りなかったもの」を1つずつ足す構成。Step 1 は式の評価しかできない＝**状態がない**。Step 2 で「値を覚えておく＝環境」と「文」の概念が入り、ここで初めて「プログラムを実行する」という言語の姿になる。Step 3 以降はその状態をどう操作・隠蔽するか、の話。

## 実行

```
cd minilang
python main.py
```

REPL が起動し、式または文を入力すると評価される。

```
> 1 + 2 * 3
7
> x = 1 + 2;
> y = x * 4;
> print(y);
12
```

## 構成

| ファイル | 役割 |
|---|---|
| `tokens.py` | Token / TokenKind 定義 |
| `lexer.py` | 文字列 → トークン列 |
| `ast_nodes.py` | AST ノード（Num / BinOp） |
| `parser.py` | トークン列 → AST |
| `evaluator.py` | AST → 値 |
| `main.py` | REPL エントリ |

## 学習用：途中段階を覗く

各段の出力を見たいときは、`main.py` の `run` を一時的に書き換える：

```python
tokens = Lexer(source).tokenize()
print(tokens)             # 1段目：トークン列
tree = Parser(tokens).parse()
print(tree)               # 2段目：AST
return evaluate(tree)
```

## ステップ別の実装手順

各ステップを始める前に `docs/` に手順を書いてから実装に進む。

- [Step 1: 電卓](docs/step1.md)
- [Step 2: 変数と print](docs/step2.md)
