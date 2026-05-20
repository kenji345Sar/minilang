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

#### なぜトークンに分けるのか

生の文字列 `"1 + 2 * 3"` には、Parser にとって本質ではない問題が混ざっている：

- 空白を飛ばす
- `12` のような複数桁を「1個の数」として読み取る
- 文字（`+`）と数字（`2`）と単語（`print`）が混在している

これらを Lexer が片付けて `[1, +, 2, *, 3]` のような**意味のある単位の列**に整える。Parser は「次のトークンは何か」だけ見ればよくなり、**文字レベルの処理から解放される**。

役割分担：

- **Lexer = 文字の世界**：空白、数字のまとまり、キーワード判別
- **Parser = トークンの世界**：文法、優先順位、構造

#### 実装

- 入力文字列を1文字ずつ進めるカーソル方式
- 数字が続いたら `NUMBER` トークン（連続する桁を1つにまとめる）、空白は飛ばす、1文字記号はそのまま対応するトークンに
- 最後に必ず `EOF` を1つ付ける
- 未知の文字は `SyntaxError`

### AST ノード (`ast_nodes.py`)

- `Num(value)`：数値リテラル
- `BinOp(op, left, right)`：二項演算（`op` は `'+' '-' '*' '/'`）

### Parser (`parser.py`) — 再帰下降

#### なぜ構文木にするのか

トークン列 `[1, +, 2, *, 3]` は**平坦**で、どこからどこまでが一塊か分からない。`*` が `+` より先、というルールがこの並びだけからは読み取れない。

そこで構造を木にする：

```
       BinOp(+)
       /     \
      1     BinOp(*)
             /    \
            2      3
```

この木があれば、Evaluator は**葉から順に評価する**だけで自動的に正しい順番（`2*3` を先、その結果と `1` を後）で計算できる。**優先順位の判断は Parser が一度だけ行い、結果が木の形に焼き付けられる**。

`(1+2)*3` だと木の形が変わる：

```
       BinOp(*)
       /     \
   BinOp(+)   3
    /   \
   1     2
```

形が違うだけで、Evaluator のコードは1行も変えなくていい。

#### 実装：文法を関数に1対1対応させる

```
expr   = term   (('+' | '-') term)*
term   = factor (('*' | '/') factor)*
factor = NUMBER | '(' expr ')'
```

- `_expr` / `_term` / `_factor` の3関数
- **優先順位**は「呼ばれる深さ」で表現される（`_expr` が `_term` を呼び、`_term` が `_factor` を呼ぶ。`*` `/` の方が `+` `-` より**内側**で処理される＝**先に**評価される）
- **左結合**（`1 - 2 - 3` が `(1 - 2) - 3` になる）は `while` ループで実現

#### Parser のヘルパーメソッド

トレースに入る前に、Parser クラスが持つ補助メソッドを把握しておく。

**`self._peek()` — 次のトークンを覗き見する**

```python
def _peek(self, offset: int = 0) -> Token:
    return self.tokens[self.pos + offset]
```

カーソル位置 (`self.pos`) にあるトークンを**消費せずに**返す。「次に何が来るか」だけ確認したいときに使う。

たとえば `self._peek().kind in (TokenKind.STAR, TokenKind.SLASH)` は「次のトークンが `*` か `/` か？」を判定するだけで、カーソルは動かない。

**`self._advance()` — 次のトークンを消費する**

```python
def _advance(self) -> Token:
    t = self.tokens[self.pos]
    self.pos += 1
    return t
```

カーソル位置のトークンを返して、**カーソルを1つ進める**。

- `_peek()` = **見るだけ**（カーソル動かない）
- `_advance()` = **読み取って次へ**（カーソル進む）

判定のときは `_peek`、確定したら `_advance`、というペアで使う。

**`self._factor()` — 1つの「項」を読み取る**

```python
def _factor(self) -> Node:
    t = self._peek()
    if t.kind == TokenKind.NUMBER:
        self._advance()
        return Num(int(t.value))
    if t.kind == TokenKind.LPAREN:
        self._advance()
        node = self._expr()
        ...
```

数値1個（`Num`）か、括弧で囲まれた式（`(...)`）を1つ読んで AST ノードを返す。文法の一番内側＝**もうこれ以上分解できない単位**を扱う層。

たとえば「`_factor()` が `2` を読んで `Num(2)` を返す」というのは内部的にこう動いている：

1. `_peek()` で次のトークンを見る → `NUMBER("2")`
2. `_advance()` でそのトークンを消費（カーソルが進む）
3. `Num(2)` という AST ノードを作って返す

#### `_term` が `BinOp("*", 2, 3)` を作る瞬間

`1 + 2 * 3` を読むとき、`2 * 3` の部分が木になる流れを `_term` の中で追う。

```python
def _term(self) -> Node:
    node = self._factor()                                            # 行A
    while self._peek().kind in (TokenKind.STAR, TokenKind.SLASH):
        op = "*" if self._advance().kind == TokenKind.STAR else "/"  # 行B
        node = BinOp(op, node, self._factor())                       # 行C
    return node
```

| ステップ | 行 | 起きること | この時点の変数 |
|---|---|---|---|
| 1 | 行A | `_factor()` が `2` を読んで `Num(2)` を返す | `node = Num(2)` |
| 2 | while条件 | 次のトークンは `*` → 条件成立、ループに入る | `node = Num(2)` |
| 3 | 行B | `*` を消費して `op = "*"` | `op = "*"`, `node = Num(2)` |
| 4 | 行C 評価中 | 右側の `self._factor()` が呼ばれて `3` を読み `Num(3)` を返す | （戻り値 = `Num(3)`） |
| 5 | 行C 代入 | `BinOp("*", Num(2), Num(3))` を作って `node` を上書き | `node = BinOp("*", Num(2), Num(3))` |
| 6 | while条件 | 次は EOF → ループ終了 | |
| 7 | return | `node` を返す | 戻り値 = `BinOp("*", Num(2), Num(3))` |

ポイントは**行C の `BinOp(op, node, self._factor())` という1行**：

- 第1引数 `op` = `"*"`
- 第2引数 `node` = `Num(2)`（直前の `_factor()` の結果を変数に取っておいたもの）
- 第3引数 `self._factor()` = この場で呼んで `Num(3)` を取ってくる

「左を変数で保持しておく／右はその場で取りに行く／3つまとめて BinOp にする」、これだけ。

#### 使われている Python 構文

**メソッド定義の読み方（`def ... -> Token:`）**

```python
def _peek(self, offset: int = 0) -> Token:
```

これは次のように読む：

```
def _peek(self, offset: int = 0) -> Token:
 │   │     │      │      │   │     │
 │   │     │      │      │   │     └ 戻り値の型：このメソッドは Token を返す
 │   │     │      │      │   └ デフォルト値（指定しなければ 0）
 │   │     │      │      └ offset の型注釈（int）
 │   │     │      └ 第2引数の名前：offset
 │   │     └ 第1引数：self（自分自身のインスタンス）
 │   └ メソッド名：_peek
 └ キーワード：これから関数/メソッドを定義する
```

- `_peek` は**これから定義しようとしているメソッドの名前**（クラスではない）
- `Token` は**このメソッドが返す値の型**（呼ばれるオブジェクトではない）
- 引数の `: int = 0` は「型は int、デフォルトは 0」

別の例：

```python
def add(x: int, y: int) -> int:
    return x + y

result = add(2, 3)   # result = 5
```

**`from ... import ...` — 別ファイルの定義を持ってくる**

[parser.py:1-2](../parser.py#L1-L2)：

```python
from tokens import Token, TokenKind
from ast_nodes import Num, BinOp, Node
```

`from <ファイル名> import <名前>` は「別のファイルで定義してあるクラスや関数を、このファイル内で使えるようにする」という命令。

- `from tokens import Token` → tokens.py で定義されている `Token` を、このファイル内で `Token` という名前で参照できるようにする
- `Token` の実体は import 元のファイル（tokens.py）にある

これにより、parser.py で `def _peek(...) -> Token:` と書ける（`Token` はファイル先頭で持ち込み済みのため）。「型がどこから来ているか」を追うときは、ファイル冒頭の import 文を見れば分かる。

**`@dataclass` で自動生成されるコンストラクタ**

```python
@dataclass
class BinOp:
    op: str
    left: Node
    right: Node

# __init__ を自分で書かなくても以下が使える：
node = BinOp("*", Num(2), Num(3))
node.op       # "*"
node.left     # Num(2)
```

**引数の中で関数を呼ぶ**

```python
BinOp(op, node, self._factor())
```

Python の評価規則：

1. `op` の値を取る
2. `node` の値を取る
3. `self._factor()` を実行して戻り値を取る（ここで `Num(3)` が返る）
4. 揃った3引数で `BinOp(...)` を呼んでインスタンスを作る

引数は**左から順に評価され**、全部揃ってから外側の関数が呼ばれる。

**`node = ...` の上書き（変数の使い回し）**

```python
node = self._factor()             # node = Num(2)
node = BinOp("*", node, ...)      # node = BinOp("*", Num(2), ...)
                                  # ↑ 元の Num(2) は新しい BinOp の left に取り込まれてから上書きされる
```

変数 `node` を使い回しているが、**直前の値を新しい BinOp の中に取り込んでから上書きする**ので情報は失われない。これが左結合（`1 - 2 - 3` を `(1 - 2) - 3` にする）の仕組みでもある。

**`self` の意味**

`self._factor()` の `self` は「今このメソッドが呼ばれているインスタンス自身」。`self` を書かないとローカル変数扱いになって `_factor` が見つけられない。Python のメソッドは必ず第1引数に `self` を取る決まり。

### Evaluator (`evaluator.py`)

- `Num` なら `node.value` を返す
- `BinOp` なら左右を再帰評価し、`op` に応じて Python の `+` `-` `*` `/` を呼ぶ

> 実際の計算は Python の演算子に丸投げしている。Evaluator がやっているのは「BinOp ノードの `op` を見て、どの Python 演算子を呼ぶか振り分ける」だけ。

### main.py

`input()` で1行受け取り、Lexer → Parser → Evaluator を通して結果を表示する REPL。`Ctrl+C` / `Ctrl+D` で終了。

## Python 初心者向け：コードの読み方

Python 初心者にとって、コード中に出てくる名前のうち「**Python 自体の機能**」と「**このプロジェクトで定義したもの**」を見分けるのが難しい。ここをまとめておく。

### 「Python 独自」と「プロジェクト独自」の見分け方

| 名前 | 出どころ |
|---|---|
| `self`, `def`, `return`, `if`, `while`, `class`, `for`, `in`, `is`, `None`, `True`, `False` | Python のキーワード |
| `int`, `list`, `dict`, `str`, `print` | Python の組み込み型・関数 |
| `@dataclass`, `Enum`, `auto`, `Union`, `Optional`, `Any` | Python 標準ライブラリ（`dataclasses` / `enum` / `typing`） |
| `Token`, `TokenKind` | プロジェクト独自（`tokens.py`） |
| `Num`, `BinOp`, `Var`, `Assign`, `Print`, `If`, `While`, `Block` | プロジェクト独自（`ast_nodes.py`） |
| `Lexer`, `Parser`, `Env`, `Function` | プロジェクト独自のクラス |

**不明な名前に出会ったら、まずファイル冒頭の `from ... import ...` を辿る**のが基本動作。プロジェクト独自の名前は必ずどこかで `class ...` か `def ...` で定義されているので、import 文が「定義の所在地マップ」になる。

### 命名の慣習

| 慣習 | 例 | 意味 |
|---|---|---|
| **大文字始まり** | `Num`, `BinOp`, `Token`, `Lexer`, `Parser` | **クラス**（型）。インスタンスを作って使う |
| **小文字＋アンダースコア** | `evaluate`, `_peek`, `tokenize` | 関数・メソッド。呼び出して使う |
| **全部大文字** | `KEYWORDS`, `COMPARISON_OPS`, `TokenKind.NUMBER` | 定数・enum メンバー |
| **アンダースコア始まり** | `_peek`, `_advance`, `_factor` | 「クラス内部用」のヒント。外から呼ばない約束 |

`Num(2)` のように大文字始まりに `(...)` が付いていたら「クラスのインスタンスを作っている」、`evaluate(node)` のように小文字始まりなら「関数を呼んでいる」、と読み分けられる。

### `def` は関数とメソッドの両方を定義する

`def` は**関数とメソッドの両方**を定義するキーワード。区別は「**どこに書いてあるか**」で決まる：

```python
# class の中に書いた def → メソッド
class Parser:
    def _peek(self, offset=0):    # ← メソッド（self が第1引数）
        ...

# class の外（ファイル直下）に書いた def → 普通の関数
def evaluate(node, env):           # ← 関数（self なし）
    ...
```

呼び出し方も違う：

- メソッド：**そのクラスのインスタンスを通して呼ぶ** → `parser._peek()`
- 関数：**直接呼ぶ** → `evaluate(tree, env)`

第1引数に `self` があるかどうかで見分けられる。

### `@dataclass` がある場合とない場合の違い

**ある場合**（`Token`、`Num`、`BinOp` など）：

```python
@dataclass
class Token:
    kind: TokenKind
    value: str | None = None
```

`@dataclass` がフィールド定義を読み取って `__init__` を**自動生成**する。だから `__init__` を書いていないのに `Token(TokenKind.NUMBER, "2")` が動く。`__repr__` や `__eq__` も自動生成される。

**ない場合**（`Parser`、`Lexer`、`Env`、`Function`）：

```python
class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0
```

`__init__` を**自分で書く**必要がある。`def __init__(self, tokens):` が「インスタンスを作るときに呼ばれる初期化メソッド」で、ここで `self.tokens` と `self.pos` を設定している。

#### 使い分け

| | 用途 | 例 |
|---|---|---|
| `@dataclass` 付き | **データの入れ物**：フィールドを並べるだけ | `Token`、`Num`、`BinOp` |
| `@dataclass` なし | **動作を持つクラス**：状態を管理しメソッドで操作する | `Parser`、`Lexer`、`Env` |

ざっくり：**フィールドを並べたいだけ → `@dataclass`、メソッドで何かするクラス → 普通の class**。

### ヘルパーメソッドは私たちが作ったもの（Python 組み込みではない）

`_peek` / `_advance` / `_factor` などは**全部 `parser.py` 内で `def` で定義したメソッド**で、Python が用意してくれているものではない。

#### Python 組み込みメソッドとの対比

| 用途 | Python 組み込みメソッド | プロジェクトのメソッド |
|---|---|---|
| リストに追加 | `list.append(x)` | — |
| 文字列を小文字に | `str.lower()` | — |
| 辞書のキー取得 | `dict.keys()` | — |
| 次のトークンを見る | — | `Parser._peek()`（自作） |
| カーソルを進める | — | `Parser._advance()`（自作） |

`statements.append(self._statement())` を例にすると：

- `statements.append(...)` ← **Python の組み込み**（リストに要素を追加するメソッド）
- `self._statement()` ← **私たちが作ったメソッド**（Parser クラス内で `def _statement` と定義）

同じ「`.メソッド名()`」の形でも、**左側のオブジェクトが何か**（リストか自作クラスか）でメソッドの出どころが変わる。

#### `_` 始まりの慣習

`_peek` のようにアンダースコア始まりの名前は、Python の慣習で「**そのクラス／モジュール内部用、外から呼ばない約束**」を示すサイン。これも我々が付けた名前で、Python 強制ではなくマナー。

### `TokenKind` と `Enum` の仕組み

`tokens.py` 冒頭：

```python
from enum import Enum, auto

class TokenKind(Enum):
    NUMBER = auto()
    PLUS = auto()
    MINUS = auto()
    ...
```

- `Enum` ＝ Python 標準ライブラリの「**取りうる値が限定されたタグ集合**」を作るためのクラス
- `NUMBER = auto()` ＝ `NUMBER` という名前のメンバーを定義。`auto()` は自動で重複しない整数値（1, 2, 3, ...）を割り当てる
- 値そのもの（1 や 2 という整数）は中身として使わない。**比較するのはメンバー名同士**

つまり `TokenKind.NUMBER` は「数字種別を表す**専用の値**」であり、文字列 `"NUMBER"` でも整数でもない。`TokenKind.NUMBER == TokenKind.NUMBER` は `True`、`TokenKind.NUMBER == TokenKind.PLUS` は `False`。

### `Token` インスタンスの中身と例

`Token` クラス（`tokens.py`）：

```python
@dataclass
class Token:
    kind: TokenKind
    value: str | None = None
```

各 `Token` インスタンスは2つのフィールドを持つ：

| フィールド | 例 | 意味 |
|---|---|---|
| `kind` | `TokenKind.NUMBER` | このトークンの**種類**（enum メンバー） |
| `value` | `"12"` | 種類に付随する**文字列の中身**（記号系は `None`） |

具体的な Token インスタンスの例：

```python
Token(TokenKind.NUMBER, "12")    # 数字 "12"
Token(TokenKind.PLUS, None)      # 記号 "+"
Token(TokenKind.IDENT, "x")      # 識別子 "x"（step 2 以降）
Token(TokenKind.EOF, None)       # 終端マーカー
```

### Token を作っているのは Lexer（Parser ではない）

Token は **Parser が作っているのではなく、Lexer が作っている**。これは重要な分担。

`lexer.py` の `tokenize()` の中で、文字を読んで該当する Token を生成しリストに追加していく：

```python
elif ch.isdigit():
    tokens.append(self._number())        # _number() が Token(NUMBER, "12") を返す
elif ch == "+":
    tokens.append(Token(TokenKind.PLUS)) # Token(PLUS, None) を作って追加
    self.pos += 1
```

`_number()` の中身：

```python
def _number(self) -> Token:
    start = self.pos
    while self.pos < len(self.source) and self.source[self.pos].isdigit():
        self.pos += 1
    return Token(TokenKind.NUMBER, self.source[start:self.pos])
    #     ↑ ここで Token インスタンスを作っている
```

Parser はもう出来上がった**リストを受け取って読むだけ**。Token を新規に作ったりはしない。

### データの流れ：文字列 → トークン列 → AST

入力：`"1 + 2 * 3"`

Lexer の処理（1文字ずつ進める）：

| 読んだ文字 | 作る Token | tokens リストの状態 |
|---|---|---|
| `1` | `Token(NUMBER, "1")` | `[NUMBER("1")]` |
| ` ` | （スキップ） | 同 |
| `+` | `Token(PLUS, None)` | `[NUMBER("1"), PLUS]` |
| ` ` | （スキップ） | 同 |
| `2` | `Token(NUMBER, "2")` | `[NUMBER("1"), PLUS, NUMBER("2")]` |
| ` ` | （スキップ） | 同 |
| `*` | `Token(STAR, None)` | `[NUMBER("1"), PLUS, NUMBER("2"), STAR]` |
| `3` | `Token(NUMBER, "3")` | `[NUMBER("1"), PLUS, NUMBER("2"), STAR, NUMBER("3")]` |
| 終端 | `Token(EOF, None)` | `[NUMBER("1"), PLUS, NUMBER("2"), STAR, NUMBER("3"), EOF]` |

この**完成したリストが Parser に渡される**：

```python
tokens = Lexer(source).tokenize()    # ← Lexer が Token を作る
program = Parser(tokens).parse()     # ← Parser はリストを読むだけ
```

まとめると：

```
入力文字列 "1+2"
   ↓ Lexer.tokenize() が Token を作る
tokens = [Token(NUMBER, "1"), Token(PLUS, None), Token(NUMBER, "2"), Token(EOF, None)]
   ↓ Parser は tokens を読むだけ（新規に Token を作らない）
Parser が t.kind を見て分岐し AST を組み立てる
   ↓
AST: BinOp("+", Num(1), Num(2))
```

`t.kind == TokenKind.NUMBER` が出てくる場面（次のサブセクションで解説）は、**Lexer が前もって作っておいた Token の `kind` フィールドを Parser が読んで判定している**、という関係です。

### `self.tokens[self.pos]` の読み方（リストアクセス）

`_peek()` の中身：

```python
return self.tokens[self.pos + offset]
```

部品ごとに：

- `self.tokens` ＝ Parser インスタンスが持つ**トークンのリスト**（`__init__` で `self.tokens = tokens` と保存）
- `self.pos` ＝ 今のカーソル位置（整数）
- `self.tokens[X]` ＝ **リストの X 番目を取り出す**（Python のリストアクセス構文）
- `self.pos + offset` ＝ X を計算で作る

つまり「自分が持っているリストの、今の位置のトークンを返すだけ」。リスト自体は書き換えない（**読み取りのみ**）。

### `self.pos += 1` の読み方（カーソル進行）

`_advance()` の中身：

```python
def _advance(self) -> Token:
    t = self.tokens[self.pos]   # 1. 今の位置のトークンを t に
    self.pos += 1               # 2. カーソルを 1 進める
    return t                    # 3. t を返す
```

`self.pos += 1` は `self.pos = self.pos + 1` の短縮形（**Python の augmented assignment**）。**これがカーソルを次のトークンに進める部分**。これがあるから、次に `_peek()` を呼ぶと違うトークンが見える。

`_peek()` と `_advance()` の違いは**カーソルを動かすかどうか**だけ：

| | カーソル | 用途 |
|---|---|---|
| `_peek()` | **動かさない** | 「次に何が来るか」を判定したいとき（`if` / `while` の条件） |
| `_advance()` | **1つ進める** | 判定後、確定して読み取りたいとき |

### `t.kind == TokenKind.NUMBER` の読み方（属性アクセスと比較）

```python
if t.kind == TokenKind.NUMBER:
    ...
```

ここに出てくる名前を1つずつ：

| 名前 | 出どころ | 何者か |
|---|---|---|
| `t` | ローカル変数 | `_peek()` などが返した `Token` のインスタンス |
| `.kind` | tokens.py の属性 | `@dataclass class Token` の `kind: TokenKind` フィールド |
| `TokenKind` | tokens.py の enum | `class TokenKind(Enum)` |
| `.NUMBER` | TokenKind のメンバー | `NUMBER = auto()` で定義 |
| `==` | Python の比較演算子 | 等しいかを bool（`True` / `False`）で返す |

意味は「**`t` のフィールド `kind` が `TokenKind.NUMBER` と等しいか？**」＝「次のトークンは数字か？」の判定。

### `Num(2)` の読み方（クラスのコンストラクタ呼び出し）

```python
return Num(int(t.value))
```

`Num` は **Python の組み込みではなく、`ast_nodes.py` で定義したクラス**：

```python
@dataclass
class Num:
    value: int
```

`Num(2)` と書くと、`@dataclass` が自動生成した `__init__(value=2)` が呼ばれて、`value` が 2 のインスタンスができる。**プロジェクト独自の型**。

見た目は関数呼び出し（`func(...)`）に似ているが、**大文字始まり**なのでクラス＝「インスタンスを作っている」と読める。同様に：

- `BinOp("+", left, right)` ＝ BinOp のインスタンスを作る
- `Token(TokenKind.NUMBER, "2")` ＝ Token のインスタンスを作る
- `Lexer(source)` ＝ Lexer のインスタンスを作る

`int(t.value)` の `int` は **Python の組み込み型**（小文字始まり）。文字列を整数に変換する。同じ「`X(...)`」の形でも、X が何者かで意味が変わる。

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
