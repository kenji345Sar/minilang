# 用語集

minilang のドキュメントで使われる用語の定義をまとめたもの。

## REPL

**R**ead-**E**val-**P**rint-**L**oop の頭文字。「1行読む → 評価する → 結果を出す → ループする」という対話型実行環境。

Python の対話モード（`>>>`）、ブラウザの開発者コンソール、minilang の `main.py` も全部 REPL。`main.py` のメインループがまさにこの4ステップを繰り返している。

```python
while True:
    line = input("> ")           # R: 読む
    program = parse(lex(line))   #
    result = evaluate(program)   # E: 評価
    print(result)                # P: 出す
                                 # L: while でループ
```

## Lexer（字句解析器）

文字列を**トークン列**に変換する第1段。空白の除去、複数桁の数字を1つにまとめる、識別子とキーワードの判別など、文字レベルの処理を担う。

→ 詳細：[step1.md の Lexer セクション](step1.md)

## Parser（構文解析器）

トークン列を**構文木（AST）**に変換する第2段。文法ルールに従ってトークンを階層構造に組み立て、演算子の優先順位や入れ子を木の形に焼き付ける。

→ 詳細：[step1.md の Parser セクション](step1.md)

## Evaluator（評価器）

構文木を辿って実際に**値を計算する**第3段。AST のノードを再帰的に処理し、変数の参照や代入、出力などの実行を担う。

→ 詳細：[step1.md の Evaluator セクション](step1.md)

## Token / トークン

Lexer が文字列から切り出した「意味のある単位」。`kind`（種類）と `value`（中身の文字列）を持つ。

例：`Token(NUMBER, "12")`、`Token(PLUS, None)`。

→ 定義：`tokens.py`

## AST / 構文木 / 抽象構文木

Abstract Syntax Tree の略。プログラムの構造を木として表現したもの。葉に数値リテラル、内部ノードに演算や文が並ぶ。Evaluator はこの木を辿って実行する。

例：`1 + 2 * 3` の AST は `BinOp("+", Num(1), BinOp("*", Num(2), Num(3)))`。

## Node

AST を構成する個々のノードの総称。minilang では `Num` `BinOp` `Var` `Assign` `Print` `ExprStmt` `Program` のいずれか。型エイリアスとして `ast_nodes.py` に定義してある。

## 環境（env / environment）

変数名から値への**対応表（辞書）**。Evaluator が `evaluate(node, env)` の形で持ち回し、`Assign` で書き込み、`Var` で読み出す。minilang では `dict[str, Any]` で実装。

中身の例：

```python
env = {"x": 10, "y": 40}
```

### 何が入るか

- 代入文 `x = 10;` が走ると `env["x"] = 10` が書き込まれる
- 変数を参照する式（`x` 単体や `x + 1` の中の `x`）が出てくると `env["x"]` が読み出される

### 何が入らないか（よくある誤解）

env は**結果を入れる場所ではない**。`1 + 2` を評価した結果 `3` は関数の戻り値として返るだけで、env には入らない：

```python
result = evaluate(node, env)   # result = 計算結果（戻り値）
                               # env    = 変数テーブル（別物）
```

env に入るのは「`x = 1 + 2;` のように**名前を付けて保存した値**」だけ。一時的な計算結果は env を経由せずに関数の戻り値として伝わる。

### 登場時期

step 2 で初めて登場。step 3 以降のスコープ管理でも中心的な役割を担う。

## 式（expression）

評価すると**値が得られる**もの。例：`1 + 2`、`x`、`(x + y) * 3`。

AST 上は `Num`、`BinOp`、`Var` などが該当。

## 文（statement）

評価しても値を返さず、**副作用**（代入、出力など）を起こすもの。例：`x = 1;`、`print(x);`。

AST 上は `Assign`、`Print`、`ExprStmt` などが該当。

## 識別子（identifier）

変数名や関数名など、プログラマが自由に付ける名前。minilang では英字か `_` で始まり、英数字か `_` が続く文字列。Lexer が `IDENT` トークンとして切り出す。

## キーワード（予約語）

言語仕様で**特別な意味が決まっている単語**。識別子としては使えない。minilang では `print` が該当（step 3 以降で `if` `while` などが増える予定）。

Lexer が単語を読み終わった時点でキーワード表と照合し、該当すれば専用のトークン型（`PRINT` など）に変換する。

## 再帰下降パーサ（recursive descent parser）

Parser の実装方式の1つ。文法のルールごとに関数を作り、文法が互いを参照する形で再帰的に呼び合うパーサ。minilang の `_expr` / `_term` / `_factor` がこれにあたる。

優先順位を関数の呼び出しの深さで表現する（深い関数ほど優先順位が高い）のが特徴。

## 左結合（left-associative）

同じ優先順位の演算子が連続したとき、**左から順にまとめる**こと。`1 - 2 - 3` を `(1 - 2) - 3` と解釈するルール。

minilang では `_expr` / `_term` の `while` ループでこれを実現している（直前の結果を新しい BinOp の左に取り込む方式）。
