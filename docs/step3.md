# Step 3: if / while

## 目的

文を上から順に実行するだけだった step 2 から、「**条件で分岐し、繰り返し実行する**」言語へ拡張する。具体的には `if` / `else` による分岐と `while` による反復を導入する。

## Step 2 との違い

| | Step 2 | Step 3 |
|---|---|---|
| 制御フロー | 文を上から順に実行 | 条件で分岐、ループで繰り返し |
| Python の eval / exec で代替 | 概ね可能 | **不可能**（独自の制御フローが必要） |
| 新しい構文要素 | 文（statement） | **ブロック**（`{ ... }`）と条件式 |
| Evaluator の役割 | 順に評価して結果を返す | **実行制御の主導権を握る** |
| 新しい AST | Var / Assign / Print / ExprStmt / Program | If / While / Block |

step 2 までは「Python の eval / exec で何とかなる」範囲だった。step 3 で初めて、minilang の Evaluator が **「どのコードを実行する／何回実行する」** を自分で判断する段に入る。

## ここで身につく考え方

- **ブロック構造**：`{ ... }` で文をまとめて1つの「ブロック」として扱う。これで if / while の本体に任意の数の文を書ける
- **条件式と比較演算子**：`==` `<` `>` などは既存の `BinOp` に演算子を追加するだけで対応できる（新ノードは不要）
- **Evaluator が主導する制御フロー**：if 文の評価は「条件を評価 → どちらの枝を実行するか決める」を Evaluator が行う。while 文も同じく「条件を再評価 → 本体を実行 → 条件を再評価」を Evaluator がループする
- **演算子の優先順位レベルが1段増える**：比較演算子は四則演算より優先順位が低い（`a + b > c` は `(a + b) > c` と解釈）

## 入出力例

```
> i = 0;
> while i < 3 { print(i); i = i + 1; }
0
1
2
> if i == 3 { print(99); } else { print(0); }
99
```

## 追加するトークン

### なぜ新しいトークンが必要になるか

- `if` `else` `while` という新しい**キーワード**
- ブロックを囲む `{` `}` の記号
- **比較演算子**：`==` `!=` `<` `>` `<=` `>=`

複数文字の演算子（`==` など）は Lexer で「次の文字も `=` か」を**先読み**して1個のトークンにまとめる必要がある。

### 追加するもの

`tokens.py` に以下を追加：

- `IF` `ELSE` `WHILE`：制御フローのキーワード
- `LBRACE` `RBRACE`：`{` `}`
- `EQEQ` `BANGEQ` `LT` `GT` `LTEQ` `GTEQ`：比較演算子

## Lexer の変更

### 多文字演算子の扱い（先読み）

`=` は単独だと代入（`EQUAL`）、`==` だと等価比較（`EQEQ`）。**次の文字を1文字先読み**してどちらか判断する：

```python
elif ch == "=":
    if self._peek_char(1) == "=":
        tokens.append(Token(TokenKind.EQEQ))
        self.pos += 2
    else:
        tokens.append(Token(TokenKind.EQUAL))
        self.pos += 1
```

同じパターンで `<` / `<=`、`>` / `>=` を処理。`!` は `!=` の形でしか現れないので、次が `=` でなければエラー。

### キーワード追加

ファイル冒頭の `KEYWORDS` 表に3行追加するだけ：

```python
KEYWORDS = {
    "print": TokenKind.PRINT,
    "if": TokenKind.IF,
    "else": TokenKind.ELSE,
    "while": TokenKind.WHILE,
}
```

step 2 で作った `_ident_or_keyword()` の仕組みがそのまま使える（**設計の元が取れている**例）。

## AST ノードの追加

### 制御フロー用のノード

```python
@dataclass
class If:
    cond: Node                # 条件式
    then_block: Node          # Block
    else_block: Optional[Node]  # Block か None（else 省略時）

@dataclass
class While:
    cond: Node                # 条件式
    body: Node                # Block

@dataclass
class Block:
    statements: list[Node]    # ブロック内の文の並び
```

### Block を別ノードにする理由

`Program` と `Block` はどちらも「文の並びを評価する」点では同じ。それでも別ノードにするのは、**意味的な役割が違う**から：

- `Program`：トップレベル全体。REPL 表示用に**最後の文の値を返す**
- `Block`：if / while の本体。値は使わない（あくまで副作用のため）

実装上はほぼ同じだが、AST 上の意味は区別しておく。

### 比較演算子は BinOp に追加するだけ

`a == b` は新ノード（`Compare` など）を作らず、既存の `BinOp` に `op = "=="` などを追加して扱う。**Evaluator の分岐が増えるだけで、AST の型は増やさない**。

## Parser の変更

### 文の振り分けロジック

```python
def _statement(self) -> Node:
    t = self._peek()
    if t.kind == TokenKind.IF:
        return self._if_stmt()
    if t.kind == TokenKind.WHILE:
        return self._while_stmt()
    if t.kind == TokenKind.PRINT:
        return self._print_stmt()
    if t.kind == TokenKind.IDENT and self._peek(1).kind == TokenKind.EQUAL:
        return self._assign_stmt()
    return self._expr_stmt()
```

step 2 から `IF` / `WHILE` の2つの分岐を追加しただけ。

### ブロック `{ ... }` のパース

```python
def _block(self) -> Block:
    self._expect(TokenKind.LBRACE)
    statements: list[Node] = []
    while self._peek().kind not in (TokenKind.RBRACE, TokenKind.EOF):
        statements.append(self._statement())
    self._expect(TokenKind.RBRACE)
    return Block(statements)
```

`{` と `}` の間にある文を全部 `_statement()` で読み取って `Block` にまとめる。これで if / while の本体に任意の数の文を書ける。

### if 文と while 文

```python
def _if_stmt(self) -> If:
    self._advance()                # 'if' を消費
    cond = self._expr()
    then_block = self._block()
    else_block = None
    if self._peek().kind == TokenKind.ELSE:
        self._advance()
        else_block = self._block()
    return If(cond, then_block, else_block)

def _while_stmt(self) -> While:
    self._advance()                # 'while' を消費
    cond = self._expr()
    body = self._block()
    return While(cond, body)
```

`else` は省略可能なので `if` で判定（あれば消費）。

### 比較演算子の優先順位レベル

四則演算より比較演算子の方が**優先順位が低い**（`a + b > c` は `(a + b) > c` と解釈したい）ので、文法に1段追加：

```
expr       = comparison
comparison = additive (('==' | '!=' | '<' | '>' | '<=' | '>=') additive)?
additive   = term (('+' | '-') term)*
term       = factor (('*' | '/') factor)*
factor     = NUMBER | IDENT | '(' expr ')'
```

旧 `_expr` を `_additive` に改名し、新たに `_comparison` 層を追加。`_expr` は `_comparison` を呼ぶエントリーポイントになる。

比較は**連鎖しない**設計：`a < b < c` のような書き方はサポートしない（Parser がエラーにする）。これで「比較結果を別の比較と比べる」混乱を避ける。

### `while i < 3 { ... }` の AST

入力：`i = 0; while i < 3 { i = i + 1; }`

Parser が作る AST：

```
Program([
    Assign("i", Num(0)),
    While(
        cond = BinOp("<", Var("i"), Num(3)),
        body = Block([
            Assign("i", BinOp("+", Var("i"), Num(1))),
        ])
    ),
])
```

## Evaluator の変更

### 制御フローのノードを評価する

**`If`**：

```python
if isinstance(node, If):
    if evaluate(node.cond, env):
        return evaluate(node.then_block, env)
    if node.else_block is not None:
        return evaluate(node.else_block, env)
    return None
```

条件を評価して、Python の truthy / falsy 判定でどちらの枝を実行するか決める。

**`While`**：

```python
if isinstance(node, While):
    while evaluate(node.cond, env):
        evaluate(node.body, env)
    return None
```

Python の while を使って、条件が真である限り body を繰り返し評価する。**Python の while がそのまま minilang の while を実装**している（足し算が Python の `+` を借りていたのと同じパターン）。

**`Block`**：

```python
if isinstance(node, Block):
    result = None
    for stmt in node.statements:
        result = evaluate(stmt, env)
    return result
```

`Program` とほぼ同じ。文を順に評価。

### 比較演算子を BinOp に追加

```python
if isinstance(node, BinOp):
    left = evaluate(node.left, env)
    right = evaluate(node.right, env)
    if node.op == "+":
        return left + right
    ...
    if node.op == "==":
        return left == right
    if node.op == "!=":
        return left != right
    if node.op == "<":
        return left < right
    if node.op == ">":
        return left > right
    if node.op == "<=":
        return left <= right
    if node.op == ">=":
        return left >= right
```

四則演算と同じく、比較も Python の比較演算子に丸投げ。結果は Python の `True` / `False`。

### while ループのトレース

入力：`i = 0; while i < 3 { print(i); i = i + 1; }`

env の変化と出力：

| ステップ | 動き | env | 出力 |
|---|---|---|---|
| 1 | `Assign("i", Num(0))` | `{"i": 0}` | |
| 2 | While：cond `0 < 3` → `True` | | |
| 3 | Block：`print(0)` | | `0` |
| 4 | Block：`i = i + 1` | `{"i": 1}` | |
| 5 | While：cond `1 < 3` → `True` | | |
| 6 | Block：`print(1)` | | `1` |
| 7 | Block：`i = i + 1` | `{"i": 2}` | |
| 8 | While：cond `2 < 3` → `True` | | |
| 9 | Block：`print(2)` | | `2` |
| 10 | Block：`i = i + 1` | `{"i": 3}` | |
| 11 | While：cond `3 < 3` → `False` | | |
| 12 | While 終了 | | |

## main.py の変更

REPL の起動メッセージを step 3 用に変更するだけ。env の扱いは step 2 のまま。

REPL は1行入力なので、if / while を使うときは1行にまとめて書く：

```
> if 5 > 0 { print(5); }
5
> i = 0; while i < 3 { print(i); i = i + 1; }
```

複数行入力は将来的に拡張（step 3 の範囲外）。

## 使われている Python 構文（step 3 追加分）

### `Optional[Node]` — None になり得る型

```python
@dataclass
class If:
    cond: Node
    then_block: Node
    else_block: Optional[Node]    # ← Block か None
```

`Optional[T]` は **「T 型または None」** を意味する型注釈。`from typing import Optional` で持ってくる。`else_block` は「Block ノードがあるか、`None`（else なし）」のどちらか。

Python 3.10 以降は `Node | None` でも書ける（短いが、`Union` の型エイリアスと組み合わせる場合は `Optional` の方が安全）。

### Python の `while` で minilang の `while` を実装

```python
while evaluate(node.cond, env):
    evaluate(node.body, env)
```

minilang のループは **Python のループに丸投げ**している。これは step 1 で `+` を Python の `+` に丸投げしていたのと同じパターン。**ホスト言語の機能を借りて自言語の機能を実装する**インタプリタの定石。

### truthy / falsy 判定

```python
if evaluate(node.cond, env):
    ...
```

Python の if 文は **truthy / falsy 判定** を使う。`0`、空文字列 `""`、`None` などは falsy（偽）、それ以外は truthy（真）。minilang の条件式もこの判定をそのまま借りる。

比較演算子（`<` など）の結果は Python の `True` / `False`。`True` は truthy、`False` は falsy なので問題なく動く。

## 完了の判定

以下が動けば step 3 完了：

```
> i = 0;
> while i < 3 { print(i); i = i + 1; }
0
1
2

> x = 5;
> if x > 0 { print(x); } else { print(0); }
5

> y = 0;
> if y > 0 { print(y); } else { print(99); }
99
```
