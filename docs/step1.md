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

## 全体像：3段の役割とデータの流れ

実装に入る前に、コードがどう分かれていて、データがどう流れるかを把握しておく。

### ファイルの役割

| ファイル | 役割 |
|---|---|
| tokens.py | `Token` クラスと `TokenKind` enum の**定義** |
| lexer.py | **Lexer**：文字列をトークン列に変換する |
| ast_nodes.py | AST ノード型（`Num` / `BinOp`）の**定義** |
| parser.py | **Parser**：トークン列を構文木に変換する |
| evaluator.py | **Evaluator**：構文木を評価して値にする |
| main.py | REPL ループ（3段を順に呼び出す） |

3つの「動詞」ファイル（Lexer / Parser / Evaluator）と、2つの「データ型を定義する」ファイル（tokens / ast_nodes）に分かれている。

### 3段の入出力

| 段 | 入力 | 出力 |
|---|---|---|
| Lexer | 文字列 `"1+2"` | トークン列 |
| Parser | トークン列 | 構文木（AST） |
| Evaluator | 構文木 | 値 `3` |

各段で扱うデータ型が**全部違う**ことに注目（文字列 → トークン列 → 木 → 整数）。

### `"1 + 2 * 3"` を3段に通すと

```
"1 + 2 * 3"                                              ← 入力（文字列）
   ↓ Lexer
[NUMBER(1), PLUS, NUMBER(2), STAR, NUMBER(3), EOF]       ← トークン列
   ↓ Parser
BinOp("+", Num(1), BinOp("*", Num(2), Num(3)))           ← 構文木
   ↓ Evaluator
7                                                         ← 値
```

入力が**3段で姿を変えながら**進む。`main.py` はこの3段を順に呼ぶだけ：

```python
tokens = Lexer(source).tokenize()    # 文字列 → トークン列
program = Parser(tokens).parse()     # トークン列 → 構文木
result = evaluate(program, env)      # 構文木 → 値
```

ここから先は、それぞれの段の中身を詳しく見ていく。ただしコードを読むには Python の基本ルール（`def` の意味、`@dataclass` とは何か、など）を知っておく必要があるので、まず次のセクションでそこを押さえる。

## Python の読み方（このコードを読むのに必要な分）

Python 初心者にとって、コード中に出てくる名前のうち「**Python 自体の機能**」と「**このプロジェクトで定義したもの**」を見分けるのが難しい。ここをまとめておくと、実装セクションを読むときに迷子になりにくい。

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

### メソッド定義の読み方（`def ... -> Token:`）

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

### `from ... import ...` — 別ファイルの定義を持ってくる

```python
from tokens import Token, TokenKind
from ast_nodes import Num, BinOp, Node
```

`from <ファイル名> import <名前>` は「別のファイルで定義してあるクラスや関数を、このファイル内で使えるようにする」という命令。

- `from tokens import Token` → tokens.py で定義されている `Token` を、このファイル内で `Token` という名前で参照できるようにする
- `Token` の実体は import 元のファイル（tokens.py）にある

「型がどこから来ているか」を追うときは、ファイル冒頭の import 文を見れば分かる。

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

### `Token` インスタンスの中身（デバッグ出力で確認）

各 `Token` インスタンスは2つのフィールドを持つ：

| フィールド | 例 | 意味 |
|---|---|---|
| `kind` | `TokenKind.NUMBER` | このトークンの**種類**（enum メンバー） |
| `value` | `"12"` | 種類に付随する**文字列の中身**（記号系は `None`） |

実際に動かして `print()` で確認：

```python
from lexer import Lexer
for t in Lexer("1 + 2 * 3").tokenize():
    print(t)
```

実行結果：

```
Token(kind=<TokenKind.NUMBER: 1>, value='1')
Token(kind=<TokenKind.PLUS: 3>, value=None)
Token(kind=<TokenKind.NUMBER: 1>, value='2')
Token(kind=<TokenKind.STAR: 5>, value=None)
Token(kind=<TokenKind.NUMBER: 1>, value='3')
Token(kind=<TokenKind.EOF: 26>, value=None)
```

ポイント：

- どの Token も**必ず `kind` と `value` の両方のフィールドを持っている**（`value` が `None` でも存在する）
- `<TokenKind.NUMBER: 1>` の右の `: 1` は `auto()` が割り当てた整数値。比較には使わない（`==` は名前で判定）
- `value='1'` は**文字列**の `"1"`。整数に変換するのは Parser の `_factor` の中で `int(t.value)` を呼ぶ瞬間

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

Parser はもう出来上がった**リストを受け取って読むだけ**。Token を新規に作ったりはしない。

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

`self.pos += 1` は `self.pos = self.pos + 1` の短縮形（**Python の augmented assignment**）。**これがカーソルを次のトークンに進める部分**。

`_peek()` と `_advance()` の違いは**カーソルを動かすかどうか**だけ：

| | カーソル | 用途 |
|---|---|---|
| `_peek()` | **動かさない** | 「次に何が来るか」を判定したいとき |
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
| `==` | Python の比較演算子 | 等しいかを bool で返す |

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

## 実装：3段の中身

ここまでで全体の見取り図と Python の読み方が揃ったので、各段の中身に入る。

### トークン (`tokens.py`)

トークンは、Lexer が文字列を切り分けて作る「**意味のある単位**」。step 1 で使う種類：

| TokenKind | 表す文字 | 意味 | `value` の例 |
|---|---|---|---|
| `NUMBER` | `0-9` の並び | 数字リテラル | `"12"` |
| `PLUS` | `+` | 加算演算子 | `None` |
| `MINUS` | `-` | 減算演算子 | `None` |
| `STAR` | `*` | 乗算演算子 | `None` |
| `SLASH` | `/` | 除算演算子 | `None` |
| `LPAREN` | `(` | 開き括弧 | `None` |
| `RPAREN` | `)` | 閉じ括弧 | `None` |
| `EOF` | — | 終端マーカー（Lexer が末尾に必ず1つ付ける） | `None` |

`NUMBER` だけ `value` に「実際の数字文字列」が入る。記号は種類だけ分かれば意味が決まるので `value` は `None`。

`Token` クラスは `kind: TokenKind` と `value: str | None` の2フィールドだけを持つ単純なデータ入れ物（`@dataclass`）。`TokenKind` は取りうる種類を限定するための enum。

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

#### `"1 + 2 * 3"` を Lexer が処理する流れ

| 読んだ文字 | 作る Token | tokens リストの状態（短縮表記） |
|---|---|---|
| `1` | `Token(NUMBER, "1")` | `[NUMBER("1")]` |
| ` ` | （スキップ） | 同 |
| `+` | `Token(PLUS, None)` | `[NUMBER("1"), PLUS]` |
| ` ` | （スキップ） | 同 |
| `2` | `Token(NUMBER, "2")` | `[NUMBER("1"), PLUS, NUMBER("2")]` |
| ` ` | （スキップ） | 同 |
| `*` | `Token(STAR, None)` | `[NUMBER("1"), PLUS, NUMBER("2"), STAR]` |
| `3` | `Token(NUMBER, "3")` | `[..., STAR, NUMBER("3")]` |
| 終端 | `Token(EOF, None)` | `[..., NUMBER("3"), EOF]` |

> 表の中の `NUMBER("1")` は `Token(TokenKind.NUMBER, "1")` の**短縮表記**。実際に Python のリストに入っているのは完全形の Token インスタンス。

### AST ノード (`ast_nodes.py`)

AST（抽象構文木）のノード。step 1 では2種類だけ：

| ノード | フィールド | 意味 |
|---|---|---|
| `Num` | `value: int` | 数値リテラル（**葉**ノード。これ以上分解されない） |
| `BinOp` | `op: str`, `left: Node`, `right: Node` | 二項演算（**内部**ノード。左右に子を持つ） |

`Num(2)` は `value=2` を持つだけのシンプルなノード。`BinOp("+", Num(1), Num(2))` は「`Num(1) + Num(2)`」を表す。**Num が葉、BinOp が枝**として木構造を作る。

`(1 + 2) * 3` のような括弧式も、最終的には BinOp のネストとして表現される：

```python
BinOp("*",
    BinOp("+", Num(1), Num(2)),     # 内側の (1+2)
    Num(3))
```

**括弧自体はトークン列には現れるが、AST には残らない**（木の形に焼き込まれる）。`(1+2)*3` と `1+2*3` で木の形が違うのが優先順位の表現。

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

カーソル位置のトークンを**消費せずに**返す。判定だけしたいときに使う。

**`self._advance()` — 次のトークンを消費する**

```python
def _advance(self) -> Token:
    t = self.tokens[self.pos]
    self.pos += 1
    return t
```

カーソル位置のトークンを返して、**カーソルを1つ進める**。

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

#### 引数の中で関数を呼ぶ評価順

```python
BinOp(op, node, self._factor())
```

Python の評価規則：

1. `op` の値を取る
2. `node` の値を取る
3. `self._factor()` を実行して戻り値を取る（ここで `Num(3)` が返る）
4. 揃った3引数で `BinOp(...)` を呼んでインスタンスを作る

引数は**左から順に評価され**、全部揃ってから外側の関数が呼ばれる。

#### `node = ...` の上書きが左結合を作る

```python
node = self._factor()             # node = Num(2)
node = BinOp("*", node, ...)      # node = BinOp("*", Num(2), ...)
                                  # ↑ 元の Num(2) は新しい BinOp の left に取り込まれてから上書きされる
```

変数 `node` を使い回しているが、**直前の値を新しい BinOp の中に取り込んでから上書きする**ので情報は失われない。これが左結合（`1 - 2 - 3` を `(1 - 2) - 3` にする）の仕組みでもある。

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

## 各段の出力を実際に見る（デバッグ例）

`main.py` を一時的に改造して、Lexer / Parser / Evaluator それぞれの出力を覗ける：

```python
def run(source: str):
    tokens = Lexer(source).tokenize()
    print("--- tokens ---")
    for t in tokens:
        print(" ", t)

    tree = Parser(tokens).parse()
    print("--- AST ---")
    print(" ", tree)

    result = evaluate(tree)
    print("--- result ---")
    print(" ", result)
    return result
```

これで「文字列 → トークン列 → AST → 値」の3段が**1つの入力でどう姿を変えるか**を一度に見られる。

### 例1：`1+2*3`

```
> 1+2*3
--- tokens ---
  Token(kind=<TokenKind.NUMBER: 1>, value='1')
  Token(kind=<TokenKind.PLUS: 2>, value=None)
  Token(kind=<TokenKind.NUMBER: 1>, value='2')
  Token(kind=<TokenKind.STAR: 4>, value=None)
  Token(kind=<TokenKind.NUMBER: 1>, value='3')
  Token(kind=<TokenKind.EOF: 8>, value=None)
--- AST ---
  BinOp(op='+', left=Num(value=1), right=BinOp(op='*', left=Num(value=2), right=Num(value=3)))
--- result ---
  7
```

AST を読みやすい形にすると：

```
BinOp(op='+',
      left=Num(value=1),
      right=BinOp(op='*',
                  left=Num(value=2),
                  right=Num(value=3)))
```

- 外側の `BinOp("+")` は左に `Num(1)`、右にもう1つの BinOp
- 内側の `BinOp("*")` は左に `Num(2)`、右に `Num(3)`
- **`*` が内側にある** → Evaluator が再帰で葉から戻ってくるとき先に評価される（`2*3=6` を先、`1+6=7` を後）

### 例2：`(1+2)*3`（括弧で順番が変わる）

```
> (1+2)*3
--- tokens ---
  Token(kind=<TokenKind.LPAREN: 6>, value=None)
  Token(kind=<TokenKind.NUMBER: 1>, value='1')
  Token(kind=<TokenKind.PLUS: 2>, value=None)
  Token(kind=<TokenKind.NUMBER: 1>, value='2')
  Token(kind=<TokenKind.RPAREN: 7>, value=None)
  Token(kind=<TokenKind.STAR: 4>, value=None)
  Token(kind=<TokenKind.NUMBER: 1>, value='3')
  Token(kind=<TokenKind.EOF: 8>, value=None)
--- AST ---
  BinOp(op='*', left=BinOp(op='+', left=Num(value=1), right=Num(value=2)), right=Num(value=3))
--- result ---
  9
```

AST を整形：

```
BinOp(op='*',
      left=BinOp(op='+',
                 left=Num(value=1),
                 right=Num(value=2)),
      right=Num(value=3))
```

例1と比べると **木の形が違う**：

- 例1 `1+2*3`：`*` が内側、`+` が外側 → `2*3=6` を先、`1+6=7`
- 例2 `(1+2)*3`：**`+` が内側、`*` が外側** → `1+2=3` を先、`3*3=9`

括弧トークン `LPAREN` / `RPAREN` は**トークン列には現れるが AST には残らない**ことに注目。Parser の `_factor` が `(` を見たら中身を読み終わって `)` を消費し、**中身の木だけを返す**から。

### 例3：`10-4/2`（左結合と除算の優先順位）

```
> 10-4/2
--- AST ---
  BinOp(op='-', left=Num(value=10), right=BinOp(op='/', left=Num(value=4), right=Num(value=2)))
--- result ---
  8.0
```

`/` が内側、`-` が外側。`4/2=2.0` を先、`10-2.0=8.0`。Python の `/` は浮動小数点除算なので結果が `8.0`（float）になる。

### 形の違いまとめ

| 入力 | AST の形（簡易表記） | 結果 |
|---|---|---|
| `1+2*3` | `(1) + ((2) * (3))` | `7` |
| `(1+2)*3` | `((1) + (2)) * (3)` | `9` |
| `10-4/2` | `(10) - ((4) / (2))` | `8.0` |

「**優先順位の判断は Parser が一度だけ行い、結果が木の形に焼き付けられる**」というのが、この AST の形の違いに表れている。Evaluator は形が違うだけで同じコード（再帰で葉から評価）が走るので、何も変えなくていい。

### REPL で各段の出力を見る

`main.py` を改造せずに、Python の対話モードから各段を直接呼んで確認することもできる：

```
$ cd /Users/apple/Desktop/Site/minilang
$ python3
>>> from lexer import Lexer
>>> from parser import Parser
>>> from evaluator import evaluate
>>>
>>> tokens = Lexer("1 + 2 * 3").tokenize()
>>> tokens
[Token(kind=<TokenKind.NUMBER: 1>, value='1'), Token(kind=<TokenKind.PLUS: 2>, value=None), ...]
>>>
>>> tree = Parser(tokens).parse()
>>> tree
BinOp(op='+', left=Num(value=1), right=BinOp(op='*', left=Num(value=2), right=Num(value=3)))
>>>
>>> evaluate(tree)
7
```

入力文字列を変えれば、その都度どんなトークン列・どんな AST が作られるかが見える。**バグが出たときの切り分け（Lexer / Parser / Evaluator のどこか）にも使える**。
