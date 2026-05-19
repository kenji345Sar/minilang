# Step 2: 変数と print

## 目的

「式の評価」だけだった step 1 から、「**文の並びを順に実行する言語**」へ拡張する。具体的には、変数への代入・参照と `print(...)` による出力を導入する。

## Step 1 との違い

| | Step 1 | Step 2 |
|---|---|---|
| 入力の単位 | 式 1個 | 文の並び |
| 状態 | なし | 環境 `env` に変数を保持 |
| 出力 | 評価結果を REPL が自動表示 | `print(...)` 文が明示する |
| AST のトップ | `BinOp` or `Num` | `Program(statements=[...])` |
| 評価関数 | `evaluate(node)` | `evaluate(node, env)` |

電卓は「入れたら出る」だけだった。step 2 で**値を覚える（env）**と**いつ出力するかを決める（print）**が入り、ここで初めて言語処理系らしくなる。

## ここで身につく考え方

- **式と文の違い**：式は値を返す（`1 + 2`）、文は副作用を起こす（`x = 1`、`print(x)`）
- **環境（変数テーブル）を引数で渡して回す設計**：`evaluate(node, env)` の `env` がインタプリタの状態を担う
- REPL でセッションをまたいで状態を保持する仕組み（環境を REPL ループの外で1つ作る）
- **キーワードと識別子の区別**：Lexer が単語を読み終わった時点で予約語テーブルと照合する

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
