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

### なぜ新しいトークンが必要になるか

step 1 のトークンは1文字記号（`+ - * /`）と数字だけだった。step 2 では：

- `x = 1 + 2;` のように **複数文字の単語（変数名）** が現れる
- `print(...)` のように **特定の単語をキーワードとして扱う** 必要がある
- `=` `;` のような新しい1文字記号が必要

これらを Parser に渡せるよう、対応するトークン型を tokens.py に追加する。

### 追加するもの

`tokens.py` に以下を追加：

- `IDENT`：識別子（変数名）。`x` や `y` のような任意の単語に対応
- `EQUAL`：`=`（代入の記号）
- `SEMICOLON`：`;`（文の区切り）
- `PRINT`：キーワード `print`（識別子と区別される予約語）

### なぜキーワードを識別子と区別するか

`x` と `print` は見た目はどちらも英字の単語。両者が同じ `IDENT` トークンだと、Parser が「この単語は `print` か？」と中身を毎回見る必要が出てくる。

Lexer の時点で**特定の単語だけ別のトークン型に振り分ける**と、Parser は `kind` を見るだけで判断できる。**「文字の世界」の処理は Lexer に閉じ込め、Parser はトークンの種類で構造を組み立てるだけ**、という step 1 で確立した役割分担をそのまま維持できる。

## Lexer の変更

### なぜ複数文字を読む必要が出たか

step 1 では数字（`12` のような複数桁）以外は全部1文字記号だった。step 2 では `print`、`x`、`hello_world` のような**任意長の単語**を1つのトークンとして読む必要がある。

step 1 の `_number()` と同じ「先頭から条件に合う限り読み進める」パターンを、英字始まりの単語にも適用する。

### 実装

`lexer.py` の主な変更：

1. メインループに「英字始まりの単語」分岐を追加
2. 単語を読む `_ident_or_keyword()` メソッドを新設
3. `=` `;` を1文字記号として追加

メインループの分岐：

```python
elif ch.isalpha() or ch == "_":
    tokens.append(self._ident_or_keyword())
```

`_ident_or_keyword()` の中身：

```python
def _ident_or_keyword(self) -> Token:
    start = self.pos
    while self.pos < len(self.source) and (
        self.source[self.pos].isalnum() or self.source[self.pos] == "_"
    ):
        self.pos += 1
    word = self.source[start:self.pos]
    if word in KEYWORDS:
        return Token(KEYWORDS[word], word)
    return Token(TokenKind.IDENT, word)
```

「先頭は英字または `_`、続きは英数字または `_`」というルール（一般的な識別子の慣習どおり）。

### キーワード判別のタイミング

ファイル冒頭にキーワード表を定義しておく：

```python
KEYWORDS = {"print": TokenKind.PRINT}
```

単語を**読み終わってから**この表と照合する。`print` という単語が出てきたら `PRINT` トークン、それ以外は `IDENT` トークン。step 3 以降で `if` や `while` を足すときも、ここに1行追加するだけで済む設計。

## AST ノードの追加

### 式と文の違い — step 2 で一番大事な概念

step 1 のノードは `Num` と `BinOp` の2つだけだった。両方とも**式（expression）**——「評価すると値を返すもの」。

step 2 で新たに登場するのは**文（statement）**——「評価しても値を返さない、副作用を起こすもの」。

| | 例 | 性質 |
|---|---|---|
| 式 | `1 + 2`、`x`、`(x + y) * 3` | 評価すると**値**が得られる |
| 文 | `x = 1;`、`print(x);` | **副作用**（変数の代入、出力）を起こす |

`1 + 2` は `3` という値になるので「右辺で使える」。一方、`x = 1` は値にならないので `y = (x = 1)` のようには書けない（minilang の設計）。

この区別は AST ノードの型に表れる：

- **式**ノード：`Num`、`BinOp`、`Var`
- **文**ノード：`Assign`、`Print`、`ExprStmt`

そして「プログラム」は**文の並び**として表される（`Program(statements)`）。

### 追加するノード

`ast_nodes.py` に以下を追加：

```python
@dataclass
class Var:
    name: str            # 変数参照（式）：env から値を引く

@dataclass
class Assign:
    name: str
    expr: Node           # 代入（文）：env に値を入れる

@dataclass
class Print:
    expr: Node           # 出力（文）：値を評価して print する

@dataclass
class ExprStmt:
    expr: Node           # 式文（文）：式を評価して値を捨てる

@dataclass
class Program:
    statements: list[Node]  # トップレベル：文のリスト
```

`Node` 型エイリアスに新ノードを含める。

### なぜ `Program(statements)` がリストなのか

step 1 では `parse()` が単一の式ノード（`BinOp` か `Num`）を返していた。step 2 の入力には複数の文が並ぶ：

```
x = 1 + 2;     ← 文1
y = x * 4;     ← 文2
print(y);      ← 文3
```

これを表現するためにトップレベルを「文のリストを持つコンテナ」にする。Evaluator はリストを順に評価していけばいい。

### `ExprStmt` は何のためか

`ExprStmt` は「式を文として扱う」ラッパー。`1 + 2;` のような行をパースできるようにする。REPL で `1 + 2` と入力したら結果を表示する、という step 1 互換のために用意。

通常のプログラムでは `print(x);` を使うのが主流だが、`ExprStmt` があると「式だけ書けば結果が見られる」REPL 体験を維持できる。

## Parser の変更

### なぜトップレベルが「文の並び」になるか

step 1 では `parse()` が単一の式ノードを返していた。step 2 では入力に複数の文が並ぶので、`parse()` は全体を `Program(statements)` という1つのノードに包んで返す。Evaluator はその `statements` を順に処理するだけ。

### 文の振り分けロジック（`_statement`）

```python
def _statement(self) -> Node:
    t = self._peek()
    if t.kind == TokenKind.PRINT:
        return self._print_stmt()
    if t.kind == TokenKind.IDENT and self._peek(1).kind == TokenKind.EQUAL:
        return self._assign_stmt()
    return self._expr_stmt()
```

各文の入り口を**最初の1〜2トークンで見分ける**：

- 先頭が `print` → `Print` 文
- 先頭が `IDENT` で、次が `=` → `Assign` 文
- それ以外 → 式文（`1 + 2;` のような行）

### なぜ `_peek(1)` の lookahead が必要か

`x` という識別子を見ても、それだけでは「変数参照（式の一部）」なのか「代入の左辺」なのか決まらない：

- `x;` → 式文（`Var("x")` を評価して捨てる）
- `x = 1;` → 代入文

**次のトークンが `=` かどうか**で判別する必要がある。これを実現するのが `_peek(1)`（**1個先のトークンを覗き見る**）。`_peek(offset=0)` がデフォルトで現在位置、`_peek(1)` で1個先を見る。

カーソルは進めずに見るだけなので、判別後にどちらの分岐に行っても token 列を読み直す必要がない。

### `_factor` に `IDENT` 分岐を追加

step 1 の `_factor` は数値と括弧式しか扱えなかった。step 2 では「変数参照」も式の一部として現れるので分岐を追加：

```python
def _factor(self) -> Node:
    t = self._peek()
    if t.kind == TokenKind.NUMBER:
        self._advance()
        return Num(int(t.value))
    if t.kind == TokenKind.IDENT:        # ← step 2 で追加
        self._advance()
        return Var(t.value)
    if t.kind == TokenKind.LPAREN:
        ...
```

これだけで `x + 1` のような「変数を含む式」を Parser が認識できるようになる。AST 上は `BinOp("+", Var("x"), Num(1))` が出来る。

### `x = 1 + 2;` を `Assign` 木にするトレース

入力：`x = 1 + 2;`

Lexer の出力（トークン列）：

```
[IDENT("x"), EQUAL, NUMBER("1"), PLUS, NUMBER("2"), SEMICOLON, EOF]
```

| ステップ | 動き | 結果 |
|---|---|---|
| 1 | `parse()` → `_statement()` を呼ぶ | |
| 2 | `_statement` が `_peek()`：`IDENT("x")`。`_peek(1)`：`EQUAL`。代入と判定 | `_assign_stmt()` へ |
| 3 | `_assign_stmt`：`_advance()` で `IDENT("x")` を消費し、`name = "x"` | `name = "x"` |
| 4 | `_expect(EQUAL)` で `=` を消費 | |
| 5 | `_expr()` を呼んで `1 + 2` を読み、`BinOp("+", Num(1), Num(2))` を作る | `expr = BinOp(...)` |
| 6 | `_consume_optional_semicolon()` で `;` を消費 | |
| 7 | `Assign("x", BinOp("+", Num(1), Num(2)))` を返す | |
| 8 | `parse()` が次のトークン EOF を見てループ終了 | |
| 9 | `Program([Assign(...)])` を返す | 最終 AST |

最終的に出来上がる木：

```
Program
└── Assign("x")
    └── BinOp("+")
        ├── Num(1)
        └── Num(2)
```

ポイント：`_assign_stmt` は最初に名前を取り、`=` を消費した後は **step 1 と同じ `_expr` を呼んでいるだけ**。式パースのロジックを使い回している。

### 末尾 `;` の省略許可

文の末尾の `;` は `_consume_optional_semicolon()` で「あれば消費、なくてもよい」扱いにしてある：

```python
def _consume_optional_semicolon(self) -> None:
    if self._peek().kind == TokenKind.SEMICOLON:
        self._advance()
```

これにより REPL で `1 + 2`（`;` なし）と入力しても式文としてパースできる。step 1 互換のための配慮。

## Evaluator の変更

### なぜ `env` を引数で回す設計か

step 1 の `evaluate(node)` は引数1つだった（状態を持たないから）。step 2 では変数の値を覚えておく場所が必要：

```python
def evaluate(node, env: dict[str, Any]):
    ...
```

`env` を**毎回引数として渡す**設計の利点：

- グローバル変数を使わないので、Evaluator が純粋関数に近くなる
- 同じ AST を**別の env で評価**できる（テスト時に空の env を渡せる）
- step 4 でスコープ（関数呼び出しごとに新しい env を作る）を導入するときに、自然に拡張できる

### `isinstance` による振り分け

step 1 では2種類のノード（`Num`、`BinOp`）を `isinstance` で振り分けていた。step 2 で扱うノード型は増える：

```python
def evaluate(node, env):
    if isinstance(node, Program):
        result = None
        for stmt in node.statements:
            result = evaluate(stmt, env)
        return result
    if isinstance(node, Assign):
        env[node.name] = evaluate(node.expr, env)
        return None
    if isinstance(node, Print):
        print(evaluate(node.expr, env))
        return None
    if isinstance(node, ExprStmt):
        return evaluate(node.expr, env)
    if isinstance(node, Var):
        if node.name not in env:
            raise NameError(f"undefined variable: {node.name}")
        return env[node.name]
    if isinstance(node, Num):
        return node.value
    if isinstance(node, BinOp):
        ...
```

ノード型ごとに「どう処理するか」を直接書ける。AST に新しいノードを足すたびに `isinstance` 分岐を1つ追加すれば対応できる、というのが3段構成のスケーラビリティの源。

### 代入と print のトレース

入力：`x = 10; print(x);`

Parser が作る AST：

```
Program([
    Assign("x", Num(10)),
    Print(Var("x")),
])
```

評価のトレース（`env = {}` から開始）：

| ステップ | ノード | 動き | env / 出力 |
|---|---|---|---|
| 1 | `Program` | 文を順に評価していく | |
| 2 | `Assign("x", Num(10))` | 右辺 `Num(10)` を評価 → `10` | |
| 3 | | `env["x"] = 10` | `env = {"x": 10}` |
| 4 | `Print(Var("x"))` | `Var("x")` を評価 → `env["x"]` → `10` | |
| 5 | | `print(10)` を実行 | 標準出力: `10` |

「文ごとに env を書き換える／読み出す」という流れがわかれば step 2 の Evaluator は理解できたと言える。

### REPL 表示用の戻り値

`Program` を評価するとき、**最後の文の値**を返している：

```python
if isinstance(node, Program):
    result = None
    for stmt in node.statements:
        result = evaluate(stmt, env)
    return result
```

これは `main.py` 側で **「単一の式文なら結果を表示する」** という REPL 互換のため。`1 + 2`（式文）と入力したら `3` を返し、`x = 1;`（代入文）は `None` を返す、という挙動を支える戻り値設計。

## main.py の変更

### env の生存期間が変わる

step 1 の `run()` は毎回 `evaluate(tree)` を呼んで終わり。状態を持たない。

step 2 では「変数の値を REPL のセッション中ずっと覚えておく」必要があるので、`env` を **REPL ループの外側**で1つ作り、毎回の `evaluate(program, env)` に渡し回す：

```python
def main():
    env: dict[str, Any] = {}      # ← ループ外で1つ作る
    while True:
        line = input("> ")
        ...
        run(line, env)            # ← 同じ env を毎回渡す
```

これで `x = 10;` と入力した後に `print(x);` と入力しても `x` が見える。`env` は REPL を終了するまで生き続ける。

### `exit` / `quit` のメタコマンド

`exit` を `Var("exit")` として評価しようとすると未定義変数エラーになる。これは Lexer/Parser/Evaluator のルールどおりの正しい挙動だが、REPL の使い勝手としては不便。

そこで main.py 側で**評価前に**特別扱いする：

```python
stripped = line.strip().rstrip(";").strip()
if stripped in ("exit", "quit"):
    break
```

minilang 本体（Lexer/Parser/Evaluator）には手を入れずに、REPL のメタコマンドとして処理。Python の対話モードと同じ発想。

## 使われている Python 構文（step 2 追加分）

step 1 で説明した構文（`def ... -> Token:`、`from ... import ...`、`@dataclass`、引数評価順、`self`）に加えて、step 2 で新しく出てくる構文。

### `dict[str, Any]` — 辞書の型注釈

```python
env: dict[str, Any] = {}
```

`dict[str, Any]` は「**キーが文字列で、値は何でも良い辞書**」という型注釈。Python 3.9 以降ではこの形で書ける（古い書き方は `Dict[str, Any]` で `from typing import Dict` が必要だった）。

- `str`：キーの型
- `Any`：値の型。`from typing import Any` で持ってくる「何でもアリ」を意味する型

minilang の `env` は変数名（文字列）と任意の値（整数、`None` など）を結びつけるので `dict[str, Any]` がぴったり。

### `Union[...]` — 複数の型のどれか1つ

```python
Node = Union[
    "Num", "BinOp", "Var",
    "Assign", "Print", "ExprStmt",
    "Program",
]
```

`Union[A, B, C]` は「A か B か C のいずれか」という型。`ast_nodes.py` の `Node` は**いずれかの AST ノード型**を指す型エイリアスとして定義してある。

文字列リテラル（`"Num"` のように引用符で囲んだ）になっているのは、**まだ定義していないクラスを前方参照する**ため。`Union` を書いた時点で `Num` クラスはまだ定義されていないので、文字列として書いて後で解決させるという Python の文法。

Python 3.10 以降は `|` で同じことが書ける：

```python
Node = "Num" | "BinOp" | "Var" | ...
```

### `isinstance(...)` — 型の判定

```python
if isinstance(node, BinOp):
    ...
```

`isinstance(値, 型)` は「**値がその型のインスタンスかどうか**」を判定する組み込み関数。Evaluator が AST ノードの種類を見分けるために使う。

minilang では AST のノード型ごとに動きを変える設計なので、`isinstance` 分岐の連続で評価関数が組み立てられる。これは Python における**型に応じた振り分け**（簡易版 pattern matching）の典型パターン。

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
