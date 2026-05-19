# Step 4: 関数定義（クロージャ）

## 目的

制御フローまで作れた step 3 から、「**自分で関数を定義できる**」言語へ拡張する。関数定義（`def`）、呼び出し、戻り値（`return`）、そして**クロージャ**（定義時の変数を覚えている関数）を導入する。

## Step 3 との違い

| | Step 3 | Step 4 |
|---|---|---|
| プログラムの単位 | 1個の文の並び | **関数**に切り出して再利用できる |
| 変数のスコープ | 1つの env | **環境のチェーン**（lexical scoping） |
| 環境の表現 | `dict` | **`Env` クラス**（親へのリンクを持つ） |
| 関数 | なし | **第一級**（env に保存して受け渡せる） |
| 制御の抜け方 | フォールスルー | **`return` で関数から脱出** |

step 3 までは「上から下へ実行する1本のプログラム」しか書けなかった。step 4 で**処理を関数として切り出す**ことができ、初めて再利用可能な抽象が手に入る。

## ここで身につく考え方

- **第一級関数**：関数は値。`f = ある関数;` のように変数に入れられる。env が `Function` オブジェクトを保持する
- **レキシカルスコープ**：関数は**定義された場所の env を覚える**。実行された場所の env は関係ない
- **環境のチェーン**：呼び出しごとに新しい env を作り、捕捉した env を**親**として連結する。変数参照は親をたどって解決する
- **クロージャ**：定義時の env を覚えている関数。`adder(5)` が返す関数は `x=5` を覚え続ける
- **return の実装**：Python の例外を使って「関数の途中から戻る」を実現する（ジャンプを別の手段で表現する古典的テク）

## 入出力例

```
> def add(a, b) { return a + b; }
> print(add(3, 4));
7

> def fact(n) { if n <= 1 { return 1; } return n * fact(n - 1); }
> print(fact(5));
120

> def adder(x) { def add_x(y) { return x + y; } return add_x; }
> add5 = adder(5);
> print(add5(3));
8
```

## 追加するトークン

`tokens.py` に以下を追加：

- `DEF`：関数定義のキーワード
- `RETURN`：戻り値のキーワード
- `COMMA`：`,`（引数の区切り）

## Lexer の変更

キーワード表に2行、`,` を1文字記号として追加するだけ：

```python
KEYWORDS = {
    "print": TokenKind.PRINT,
    "if": TokenKind.IF,
    "else": TokenKind.ELSE,
    "while": TokenKind.WHILE,
    "def": TokenKind.DEF,           # ← 追加
    "return": TokenKind.RETURN,     # ← 追加
}

# メインループに以下を追加
elif ch == ",":
    tokens.append(Token(TokenKind.COMMA))
    self.pos += 1
```

## AST ノードの追加

```python
@dataclass
class FunctionDef:
    name: str
    params: list[str]
    body: Node              # Block

@dataclass
class Call:
    callee: Node            # 呼び出す関数（普通は Var だが式でも OK）
    args: list[Node]        # 引数の式リスト

@dataclass
class Return:
    expr: Optional[Node]    # return 値（省略時 None）
```

- `FunctionDef` は**文**（env に関数を登録する副作用）
- `Call` は**式**（戻り値を持つ。式の中に書ける）
- `Return` は**文**（実行を中断して値を持って戻る）

## Parser の変更

### 文の振り分け

```python
def _statement(self) -> Node:
    t = self._peek()
    if t.kind == TokenKind.DEF:
        return self._def_stmt()
    if t.kind == TokenKind.RETURN:
        return self._return_stmt()
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

`DEF` / `RETURN` の2つを先頭に追加。

### def 文のパース

```python
def _def_stmt(self) -> FunctionDef:
    self._advance()                              # 'def'
    name = self._expect(TokenKind.IDENT).value
    self._expect(TokenKind.LPAREN)
    params: list[str] = []
    if self._peek().kind != TokenKind.RPAREN:
        params.append(self._expect(TokenKind.IDENT).value)
        while self._peek().kind == TokenKind.COMMA:
            self._advance()
            params.append(self._expect(TokenKind.IDENT).value)
    self._expect(TokenKind.RPAREN)
    body = self._block()
    return FunctionDef(name, params, body)
```

`def 名前 ( パラメータ列 ) { 本体 }` を読み取る。パラメータが0個（`()`）の場合にも対応。

### return 文のパース

```python
def _return_stmt(self) -> Return:
    self._advance()                              # 'return'
    expr = None
    if self._peek().kind != TokenKind.SEMICOLON:
        expr = self._expr()
    self._consume_optional_semicolon()
    return Return(expr)
```

`return;`（値なし）と `return expr;`（値あり）の両方に対応。

### 関数呼び出し — `_factor` を分割

関数呼び出しは「**式の後ろに `(...)` を付ける**」形なので、`_factor` を「基本要素（_primary）+ その後の `(` 連鎖」に分割する：

```python
def _factor(self) -> Node:
    node = self._primary()
    while self._peek().kind == TokenKind.LPAREN:
        node = self._finish_call(node)
    return node

def _primary(self) -> Node:
    t = self._peek()
    if t.kind == TokenKind.NUMBER:
        self._advance()
        return Num(int(t.value))
    if t.kind == TokenKind.IDENT:
        self._advance()
        return Var(t.value)
    if t.kind == TokenKind.LPAREN:
        self._advance()
        node = self._expr()
        self._expect(TokenKind.RPAREN)
        return node
    raise SyntaxError(...)

def _finish_call(self, callee: Node) -> Call:
    self._expect(TokenKind.LPAREN)
    args: list[Node] = []
    if self._peek().kind != TokenKind.RPAREN:
        args.append(self._expr())
        while self._peek().kind == TokenKind.COMMA:
            self._advance()
            args.append(self._expr())
    self._expect(TokenKind.RPAREN)
    return Call(callee, args)
```

`while` で連鎖させているので `f(1)(2)`（関数を返す関数を即座に呼ぶ）にも対応できる。

## Evaluator の大変更 — `Env` クラスの導入

### なぜ dict ではダメか

step 3 までの env は1つの dict だった。関数を導入すると：

- 関数の中で定義した変数は**外に漏れてはいけない**（ローカル変数）
- 関数の中から外側の変数は**読めるべき**（クロージャ）
- 同じ関数を別の引数で呼んだら、互いに干渉してはいけない

これを実現するには「env を入れ子の階層構造にする」必要がある。それが `Env` クラス。

### Env クラスの設計

```python
class Env:
    def __init__(self, parent: "Env | None" = None):
        self.vars: dict[str, Any] = {}
        self.parent = parent

    def __getitem__(self, name: str) -> Any:
        if name in self.vars:
            return self.vars[name]
        if self.parent is not None:
            return self.parent[name]
        raise KeyError(name)

    def __setitem__(self, name: str, value: Any) -> None:
        self.vars[name] = value          # ← 常にローカルに書く

    def __contains__(self, name: str) -> bool:
        if name in self.vars:
            return True
        if self.parent is not None:
            return name in self.parent
        return False
```

ポイント：

- **参照**（`__getitem__`）は親をたどる → 外側の変数が見える
- **代入**（`__setitem__`）は**常に現在の env に書く** → ローカル変数になる
- `__getitem__` / `__setitem__` / `__contains__` を実装したので、既存の Evaluator コード（`env[name]` / `env[name] = v` / `name in env`）はそのまま動く

### Function クラス

```python
class Function:
    def __init__(self, name, params, body, env):
        self.name = name
        self.params = params
        self.body = body
        self.env = env          # ← 定義時の env を捕捉（クロージャの正体）

    def __repr__(self):
        return f"<function {self.name}>"
```

env を「定義時の参照」として持つのがクロージャの本体。後から呼び出すときにこの env を**親**として新しい env を作る。

### ReturnValue 例外で return を実現

```python
class ReturnValue(Exception):
    def __init__(self, value):
        self.value = value
```

`return` 文を評価すると `ReturnValue` を投げる。関数呼び出し側で `try/except ReturnValue` でキャッチして戻り値を取り出す。

「関数の途中から脱出する」をプログラム言語で実装する典型パターン。Python の `for` から抜ける `break` も内部的には似た仕組みで実装されている。

### Evaluator の追加分

```python
if isinstance(node, FunctionDef):
    env[node.name] = Function(node.name, node.params, node.body, env)
    return None

if isinstance(node, Call):
    callee = evaluate(node.callee, env)
    args = [evaluate(a, env) for a in node.args]
    if not isinstance(callee, Function):
        raise TypeError(f"not callable: {callee}")
    new_env = Env(parent=callee.env)               # ← 捕捉 env を親に
    for p, a in zip(callee.params, args):
        new_env[p] = a                             # ← パラメータをローカルに束縛
    try:
        evaluate(callee.body, new_env)
    except ReturnValue as r:
        return r.value
    return None

if isinstance(node, Return):
    value = None
    if node.expr is not None:
        value = evaluate(node.expr, env)
    raise ReturnValue(value)
```

## クロージャのトレース

入力：

```
def adder(x) {
    def add_x(y) { return x + y; }
    return add_x;
}
add5 = adder(5);
print(add5(3));
```

| ステップ | 動き | env の状態 |
|---|---|---|
| 1 | `def adder(x) {...}` を評価 | `global = {adder: <Function>}` |
| 2 | `add5 = adder(5)` の右辺：`adder(5)` を呼ぶ | |
| 3 | adder 用の env を作る（親 = adder.env = global） | `adder_env = {x: 5}, parent → global` |
| 4 | adder 本体を評価：`def add_x(y) {...}` | `adder_env = {x: 5, add_x: <Function>}` |
| 5 | `add_x.env = adder_env` を捕捉（クロージャ） | |
| 6 | `return add_x` → ReturnValue 発生、adder の戻り値は add_x | |
| 7 | `add5 = <add_x の Function>` | `global = {adder: ..., add5: <add_x>}` |
| 8 | `print(add5(3))` の引数：`add5(3)` を呼ぶ | |
| 9 | add5 用の env を作る（親 = add5.env = adder_env） | `call_env = {y: 3}, parent → adder_env` |
| 10 | `return x + y` を評価。x を親（adder_env）から検索 → 5、y を local → 3 | |
| 11 | ReturnValue(8) | |
| 12 | `print(8)` | 標準出力: `8` |

ポイントは **add_x が adder_env を捕捉している**こと。adder が終了しても adder_env オブジェクトは add5（add_x）から参照されているので生き続け、`x=5` を覚え続ける。

## main.py の変更

`env = Env()` に変更するだけ：

```python
def main():
    print("minilang step 4: functions and closures")
    ...
    env = Env()                  # ← dict から Env クラスに
    ...
```

`Env` をどこに置くか：runtime values（Function や ReturnValue）と一緒に **`evaluator.py`** に置くのが自然。

## 使われている Python 構文（step 4 追加分）

### カスタム例外で非ローカル脱出

```python
class ReturnValue(Exception):
    def __init__(self, value):
        self.value = value

# 投げる側：
raise ReturnValue(value)

# 受ける側：
try:
    evaluate(callee.body, new_env)
except ReturnValue as r:
    return r.value
```

Python の例外機構を使って「関数の深い位置から外側まで一気に脱出する」を実現する。**例外＝制御フローの道具**として使う、インタプリタ実装の典型パターン。

### `__getitem__` / `__setitem__` / `__contains__` — クラスを dict のように使う

```python
class Env:
    def __getitem__(self, name): ...      # env[name]
    def __setitem__(self, name, value): ... # env[name] = value
    def __contains__(self, name): ...      # name in env
```

これらの**特殊メソッド**（dunder methods）を実装すると、自作クラスを組み込み型と同じ構文で使える。`Env` インスタンスを dict のように扱えるので、既存コードを書き換えずに済む。

### リスト内包表記

```python
args = [evaluate(a, env) for a in node.args]
```

`for` ループ + `list.append` を1行で書ける Python の構文。`Call` ノードの引数を全部評価して新しいリストにする処理を簡潔に書ける。

### 前方参照の型注釈

```python
class Env:
    def __init__(self, parent: "Env | None" = None):
        ...
```

`Env` 自身を引数の型として使いたいが、クラス定義の途中ではまだ `Env` という名前が解決できない。文字列リテラルにしておくと評価が遅延され、後で解決される。

## 既知の制限

### 外側の変数を書き換えるクロージャは作れない

`__setitem__` が常にローカルに書く設計なので、Python の `nonlocal` のような「外側の変数を書き換える」機構はない：

```
def make_counter() {
    count = 0;
    def inc() {
        count = count + 1;     # ← inc のローカル count に書く（外の count は不変）
        return count;
    }
    return inc;
}
counter = make_counter();
print(counter());   # 1
print(counter());   # 1（2 にはならない）
```

これは Python のデフォルト動作（`nonlocal` なし）と同じ。read-only クロージャは成立するが、書き換え型のクロージャは別の機構が必要。step 5 以降での課題。

## 完了の判定

以下が動けば step 4 完了：

```
> def add(a, b) { return a + b; }
> print(add(3, 4));
7

> def fact(n) { if n <= 1 { return 1; } return n * fact(n - 1); }
> print(fact(5));
120

> def adder(x) { def add_x(y) { return x + y; } return add_x; }
> add5 = adder(5);
> print(add5(3));
8
```
