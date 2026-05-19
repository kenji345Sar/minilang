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
