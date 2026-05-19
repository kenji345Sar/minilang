# Step 1: 電卓

## 目的

Lexer → Parser → Evaluator の3段構成を最小コードで動かす。四則演算と括弧を持つ式を評価できるところまで。

## ここで何ができるようになるか

- 文字列の式を受け取り、計算結果を返す（電卓相当）
- 1回の入力＝1個の式＝1個の結果。**前の入力は覚えない**（状態がない）
- 演算子の優先順位と括弧が効く

## ここで身につく考え方

- **文字列 → トークン列 → 構文木 → 値**、という4段階の橋渡し。各段で扱うデータ型が違うことを体で理解する
- 演算子の優先順位を「Parser 関数の呼ばれる深さ」で表現するテクニック（`_expr` が `_term` を呼び、`_term` が `_factor` を呼ぶ）
- 左結合の `1 - 2 - 3` が `(1 - 2) - 3` になる仕組み（`while` ループで実現）

## 入出力例

```
> 1 + 2 * 3
7
> (1 + 2) * 3
9
> 10 - 4 / 2
8.0
```

## トークン

`tokens.py`：

- `NUMBER`：整数
- `PLUS` `MINUS` `STAR` `SLASH`：`+` `-` `*` `/`
- `LPAREN` `RPAREN`：`(` `)`
- `EOF`：終端マーカー

`Token` は `kind` と `value` を持つ `dataclass`。

## Lexer

`lexer.py`：

- 入力文字列を1文字ずつ進めるカーソル方式
- 数字が続いたら `NUMBER` トークン、空白は飛ばす、1文字記号はそのまま対応するトークンに
- 最後に必ず `EOF` を1つ付ける
- 未知の文字は `SyntaxError`

## AST ノード

`ast_nodes.py`：

- `Num(value)`：数値リテラル
- `BinOp(op, left, right)`：二項演算（`op` は `'+' '-' '*' '/'`）

## Parser（再帰下降）

`parser.py`：以下の文法を3関数に1対1で対応させる。

```
expr   = term   (('+' | '-') term)*
term   = factor (('*' | '/') factor)*
factor = NUMBER | '(' expr ')'
```

- `_expr` / `_term` / `_factor` の3関数
- 優先順位は「呼ばれる深さ」で表現される（`*` `/` の方が `+` `-` より内側で処理される＝先に評価される）
- 左結合は `while` ループで実現

## Evaluator

`evaluator.py`：

- `evaluate(node)` を1関数で再帰
- `Num` なら `node.value`
- `BinOp` なら左右を評価して、`op` に応じて演算

## main.py

- REPL：`input()` で1行受け取り、Lexer → Parser → Evaluator を通して結果を表示
- `Ctrl+C` / `Ctrl+D` で終了

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

- **Lexer がおかしい**：`print(Lexer(src).tokenize())` でトークン列を目視確認
- **Parser がおかしい**：`print(Parser(tokens).parse())` で AST を目視確認。優先順位どおりに木になっているか
- **Evaluator がおかしい**：AST は合っているはずなので評価関数の再帰だけ疑う
