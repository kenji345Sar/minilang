# minilang

学習用の小さい言語処理系。Lexer → Parser → Evaluator を手書きで理解するためのリポジトリ。

## ステップ

1. **電卓**：四則演算と括弧
2. **変数と print**（現在地）
3. **if / while**
4. **関数定義（クロージャ）**

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
