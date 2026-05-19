# Step 2: 変数と print

## 目的

変数への代入と参照、`print(...)` による出力を導入する。「式の評価」だけだった step 1 から、「文の並びを順に実行する言語」へ拡張する。

## 入出力例

```
> x = 1 + 2;
> y = x * 4;
> print(y);
12
```

## 追加するトークン

`tokens.py` に以下を追加：

- `IDENT`：識別子（変数名）
- `EQUAL`：`=`
- `SEMICOLON`：`;`
- `PRINT`：キーワード `print`

## Lexer の変更

`lexer.py`：

- 英字始まりの単語を読み進める処理を追加。読み終えた単語が `print` ならキーワードトークン、それ以外は `IDENT(value=単語)`
- `=` `;` を1文字記号として処理

## AST ノードの追加

`ast_nodes.py` に以下を追加：

- `Var(name)`：変数参照（式）
- `Assign(name, expr)`：代入（文）
- `Print(expr)`：出力（文）
- `Program(statements)`：トップレベル。文の並びを保持

`Node` 型エイリアスに新ノードを含める。

## Parser の変更

`parser.py`：

- トップレベルを「文の並び」に変更：`parse()` は `Program(statements)` を返す
- 文の文法：
  - `IDENT '=' expr ';'` → `Assign(name, expr)`
  - `'print' '(' expr ')' ';'` → `Print(expr)`
  - `expr ';'` → 式文（評価して結果を捨てる。REPL 互換のために用意）
- `_factor` に `IDENT` を追加：`Var(name)` を返す
- 末尾の `;` は省略可能にする（最後の文だけ）

## Evaluator の変更

`evaluator.py`：

- `evaluate(node, env)` の形に変更。`env` は `dict[str, Any]`
- `Program`：各文を順に `evaluate(stmt, env)`。最後の文の値を返す（REPL 表示用）
- `Assign`：`env[name] = evaluate(expr, env)`、戻り値は `None`
- `Print`：`print(evaluate(expr, env))`、戻り値は `None`
- `Var`：`env[name]`（未定義なら `NameError`）

## main.py の変更

- 環境 `env: dict[str, Any] = {}` を REPL ループの外側で1つ作り、入力ごとに使い回す
- 入力が単一の式（`;` なし）でも動くように、parser 側で末尾 `;` 省略を許可する設計にしておく

## 完了の判定

以下が動けば step 2 完了：

```
> x = 1 + 2;
> y = x * 4;
> print(y);
12
> print(x + y);
15
```
