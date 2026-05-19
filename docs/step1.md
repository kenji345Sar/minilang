# Step 1: 電卓

> 3段構造の枠組みそのものを作り、四則演算と括弧の式が評価できるところまで。
> なぜ3段に分けるのか・なぜ `eval()` で済まさないのかは [README](../README.md) を参照。

## できること

- 文字列の式を受け取り、計算結果を返す（電卓相当）
- 1回の入力＝1個の式＝1個の結果。**状態は持たない**（前の入力を覚えない）
- 演算子の優先順位と括弧が効く

## 入出力例

```
> 1 + 2 * 3
7
> (1 + 2) * 3
9
> 10 - 4 / 2
8.0
```

## 実装：3段の中身

### トークン (`tokens.py`)

- `NUMBER`：整数
- `PLUS` `MINUS` `STAR` `SLASH`：`+` `-` `*` `/`
- `LPAREN` `RPAREN`：`(` `)`
- `EOF`：終端マーカー

`Token` は `kind` と `value` を持つ `dataclass`。

### Lexer (`lexer.py`)

- 入力文字列を1文字ずつ進めるカーソル方式
- 数字が続いたら `NUMBER` トークン、空白は飛ばす、1文字記号はそのまま対応するトークンに
- 最後に必ず `EOF` を1つ付ける
- 未知の文字は `SyntaxError`

### AST ノード (`ast_nodes.py`)

- `Num(value)`：数値リテラル
- `BinOp(op, left, right)`：二項演算（`op` は `'+' '-' '*' '/'`）

### Parser (`parser.py`) — 再帰下降

以下の文法を3関数に1対1で対応させる：

```
expr   = term   (('+' | '-') term)*
term   = factor (('*' | '/') factor)*
factor = NUMBER | '(' expr ')'
```

- `_expr` / `_term` / `_factor` の3関数
- **優先順位**は「呼ばれる深さ」で表現される（`*` `/` の方が `+` `-` より内側で処理される＝先に評価される）
- **左結合**（`1 - 2 - 3` が `(1 - 2) - 3` になる）は `while` ループで実現

### Evaluator (`evaluator.py`)

- `Num` なら `node.value` を返す
- `BinOp` なら左右を再帰評価し、`op` に応じて Python の `+` `-` `*` `/` を呼ぶ

> 実際の計算は Python の演算子に丸投げしている。Evaluator がやっているのは「BinOp ノードの `op` を見て、どの Python 演算子を呼ぶか振り分ける」だけ。

### main.py

`input()` で1行受け取り、Lexer → Parser → Evaluator を通して結果を表示する REPL。`Ctrl+C` / `Ctrl+D` で終了。

## 完了の判定

以下が動けば step 1 完了：

```
> 1 + 2 * 3
7
> (1 + 2) * 3
9
> 2 * (3 + 4) - 1
13
```

## 詰まったらやること

3段に分けてあるので、どの段で間違えているかを段ごとに確認できる：

- **Lexer がおかしい**：`print(Lexer(src).tokenize())` でトークン列を目視確認
- **Parser がおかしい**：`print(Parser(tokens).parse())` で AST を目視確認。優先順位どおりに木になっているか
- **Evaluator がおかしい**：AST は合っているはずなので評価関数の再帰だけ疑う
