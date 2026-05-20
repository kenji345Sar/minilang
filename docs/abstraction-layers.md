# 抽象化の層 — Python はどこまで肩代わりしているか

minilang を読んでいると「これって Python が裏で何をやってくれているのか」「自分で書いているのはどこまでか」が気になってくる。この文書は **minilang の立ち位置**と **Python が引き受けている範囲**を整理する。

step 1〜4 のどこかに依存する話ではなく、プロジェクト全体に通底するメタな話。

## 階層図

```
minilang プログラム ("1+2*3")
   ↑ を解釈する
minilang インタプリタ（私たちが書いた Python コード）
   ↑ が動く土台
Python 処理系（CPython、C で書かれている）
   ↑ が動く土台
C ランタイム + OS
   ↑ が動く土台
CPU（機械語）
   ↑ が動く土台
シリコン（トランジスタ、論理ゲート）
```

minilang は **Python の上に1層**だけ載っている。下の階層（CPython 以下）は全部既存の実装に任せている。

## Python が肩代わりしているもの

### データ構造

| 使っているもの | Python がやってくれていること |
|---|---|
| `list[Token]`（トークン列） | 動的配列、メモリ確保、サイズ自動拡張、index アクセス |
| `dict[str, Any]`（env） | ハッシュテーブル、衝突処理、リサイズ |
| `str`（ソース文字列） | Unicode、可変長、スライス、`isdigit()` などの判定 |

### メモリ管理

- Token / Num / BinOp / Function などのインスタンスを生成しても、不要になれば**自動で解放**される（ガベージコレクション）
- 参照カウント、循環参照検出も Python 任せ
- minilang のコードに `free()` 相当が1つもない

### 言語機能の抽象

| 使っているもの | Python が中でやっていること |
|---|---|
| `@dataclass` | `__init__` / `__repr__` / `__eq__` の自動生成 |
| `Enum` | メンバーの一意性保証、値割当、比較 |
| `isinstance(node, BinOp)` | オブジェクトの型タグを実行時に検査 |
| `class` / `def` | メソッドテーブル、self バインディング、属性アクセス |
| `try / except ReturnValue`（step 4） | スタック巻き戻し、例外オブジェクトの伝播 |
| 再帰呼び出し | Python のコールスタック管理（深いと `RecursionError`） |

### 計算と比較

- `left + right`（[evaluator.py](../evaluator.py)）→ Python の `int.__add__()` に丸投げ → 内部で CPU の add 命令へ
- `<` `==` などの比較も同様
- `int(t.value)`（文字列 → 整数）も Python が変換ロジックを持つ

### I/O

| 使っているもの | Python が中でやっていること |
|---|---|
| `print(...)` | システムコール `write()` への変換、バッファリング、改行付加 |
| `input("> ")` | 標準入力の読み込み、エコー、行編集 |

## 自前でやろうとすると何が増えるか

例えば C で書き直すと、Lexer / Parser / Evaluator の**アルゴリズム本体は数百行**で同じだが、**周辺で数千行**増える：

| Python の機能 | C で自前なら |
|---|---|
| `list.append()` | 動的配列の実装（capacity 管理、realloc） |
| `dict[str]` | ハッシュテーブル実装（hash 関数、衝突処理、resize） |
| `str` 操作 | char 配列 + 長さ管理、メモリ寿命の追跡 |
| 自動メモリ解放 | malloc/free を全部手書き、参照追跡 |
| `@dataclass` | 構造体定義 + コンストラクタ手書き + 比較関数 |
| `Enum` | `enum` キーワード（C にもある）か `#define` の数値定数 |
| 例外 | `setjmp/longjmp`、または明示的なエラーコード返却 |
| `print()` | `printf()`（標準ライブラリ依存）または `write()` システムコール直叩き |

機械語から書き始める場合は、上記の C 標準ライブラリすらないところから、`write()` システムコールに対応するソフトウェア割込みを自分で書くことになる。

## minilang の立ち位置

minilang が「学習対象」としている範囲を明確にする：

| 層 | 範囲 | minilang はやる？ |
|---|---|---|
| 言語の意味論（評価規則、スコープ、制御フロー） | step 1〜4 | **やる**（本題） |
| 言語の構文解析（Lexer / Parser） | step 1〜4 | **やる**（本題） |
| AST のメモリ表現 | `@dataclass` | **やらない**（Python 任せ） |
| ホスト言語の演算 | `+ - * /` | **やらない**（Python に丸投げ） |
| メモリ管理 | GC | **やらない**（Python 任せ） |
| OS とのやりとり（I/O） | `print` / `input` | **やらない**（Python 任せ） |
| ハードウェア | CPU 命令 | **やらない**（CPython の C コードが下で動く） |

つまり minilang は **「言語処理の上半分」**だけを抜き出した教材。下半分（メモリ管理〜ハードウェア）を理解したいなら、別ルートで機械語からのアプローチが必要。

## ファイルごとの分担 — どこが minilang のオリジナルか

「あえてできないことにしている」ではなく、より正確には：

> Python のレベルでは既にできている（`eval()` で済む）。でも minilang の目的は「中身を理解する」ことなので、**結果より手順を、Python の内部を真似て自前で書く**。

「Python ができない」のではなく、「Python が内部でやっていることを、見えるところで自分でやり直す」。

### ファイルごとに分けると

| ファイル | minilang が**書いている**部分（アルゴリズム・設計） | Python が**提供している**部分（部品・基盤） |
|---|---|---|
| **tokens.py** | TokenKind の集合定義（NUMBER, PLUS, …）、Token の2フィールド設計 | `Enum`、`@dataclass`、`auto()` |
| **lexer.py** | 1文字ずつ進めて分岐するアルゴリズム、トークン列の組み立てロジック、キーワード判別 | `str.isdigit()` / `isalpha()`、`list.append()`、文字列スライス、`pos += 1` |
| **ast_nodes.py** | Num/BinOp/Var/Assign など、minilang 専用のノード型設計 | `@dataclass`、`Union`、`Optional` |
| **parser.py** | 再帰下降の文法対応、優先順位の階段、`_peek/_advance` の役割設計、`x = ...` や `if {...}` のような構文の認識ロジック | `list`、整数 index、メソッド呼び出し、Python の再帰スタック |
| **evaluator.py** | `isinstance` ディスパッチで「ノード型ごとに動きを変える」設計、env の概念、Function クラスとクロージャ設計、`ReturnValue` 例外で関数脱出 | `dict`、`int + int`、`==`、`try/except`、ガベージコレクション |
| **main.py** | REPL ループ設計、env を REPL ループ外で保持する設計、exit メタコマンド | `input()`、`print()`、`while`、例外捕捉 |

### 整理した境界線

| | 内容 | 担当 |
|---|---|---|
| **アルゴリズム** | 「文字列をどう切る」「トークン列をどう木にする」「木をどう評価する」 | minilang |
| **設計判断** | 「優先順位を呼び出し深さで表現する」「env を引数で渡す」「return を例外で実装」 | minilang |
| **部品** | リスト、辞書、整数、文字列、クラス機構 | Python |
| **演算の中身** | `1 + 2` → `3`、`a < b` → `bool` | Python |
| **メモリ管理** | Token/Node の解放、参照追跡 | Python（GC） |

ざっくり：**「何をやるか」と「どうやるか」の設計判断は minilang、「やる材料」は Python**。

### 具体例：`1 + 2` を評価する瞬間

[evaluator.py](../evaluator.py) の中：

```python
if node.op == "+":
    return left + right
```

- `node.op == "+"`：「足し算かどうか判定する」**設計**は minilang。`==` 演算子は Python
- `left + right`：「左右を足す」**設計**は minilang。**実際の足し算**は Python（最終的に CPU の add 命令）
- `return`：「関数の戻り値として返す」**設計**は minilang。スタック巻き戻しは Python

つまり minilang の Evaluator は **「何を、いつ、どう組み合わせるかの司令塔」**で、実際の作業（足す、比較する、メモリ確保する）は全部 Python に投げている。

### 料理に例えると

- minilang ＝ **「言語処理のレシピを書いている」**
- Python ＝ **「材料と調理器具を全部用意してくれている」**
- 私たちは料理人で、Python はスーパーと厨房

「あえてできないことにしている」ではなく、「**手順だけは自分で書く、材料は買う**」という分業。料理を学ぶときに小麦を育てるところから始めないのと同じ理屈。

## minilang と CPython の対比

minilang を理解すると、Python の `eval()` の中で何が起きているか想像できるようになる。ただし**精密には3点違う**：

### 違い1：実装言語が C（Python ではない）

CPython（Python 3 の標準実装）の `eval()` は **C で書かれている**。minilang は同じ概念を Python レベルで表現している。読みにくさは段違いだが、**やっている仕事の構造は同じ**。

### 違い2：CPython は4段構成（minilang は3段）

```
ソース文字列
   ↓ Lexer（Parser/tokenizer.c）
トークン列
   ↓ Parser（Parser/parser.c, PEG パーサ）
AST（Python の ast モジュールから見える）
   ↓ Compiler（Python/compile.c）
バイトコード（dis モジュールで見える）
   ↓ Evaluator/VM（Python/ceval.c）
実行結果
```

| | minilang | CPython |
|---|---|---|
| 段数 | **3段** | **4段**（AST とコードの間にバイトコードを挟む） |
| Evaluator の方式 | **tree-walking**（AST を直接歩いて実行） | **bytecode**（AST → バイトコードに翻訳して VM で実行） |

バイトコードを挟むのは**性能**のため（同じコードを何度も実行する場合に有利）。学習用には bytecode を省いた tree-walking のほうが分かりやすいので、minilang はそちらを採用。

### 違い3：扱う言語のサイズが桁違い

| | minilang | Python |
|---|---|---|
| 機能 | 四則演算、変数、`if`/`while`、関数（クロージャ） | + クラス、import、ジェネレータ、デコレータ、async/await、メタクラス、… |
| ソース規模 | 数百行 | 数十万行 |

CPython の `Parser/tokenizer.c` を開けば、minilang の `_number()` に対応する処理が見つかる。**「同じ仕事をしている」のは分かるが、規模は10倍以上**。

### 関係性のまとめ

> `eval()` の中身は「**同じ系統のアルゴリズムが、より大規模・より高速・別言語（C）で・段数を1つ増やして**実装されているもの」。

minilang は「**それを最短経路で、読み手が追える形に縮めたもの**」。学習で得たパターンは、CPython のソースを読むときの**地図**になる。

### CPython のソースを読みに行くなら

CPython の実際のソース：[https://github.com/python/cpython](https://github.com/python/cpython)

| ファイル | 役割 | minilang の対応 |
|---|---|---|
| `Parser/tokenizer.c` | Lexer | `lexer.py` |
| `Parser/` 配下 | Parser（PEG ベース） | `parser.py` |
| `Include/internal/pycore_ast.h` ほか | AST 定義 | `ast_nodes.py` |
| `Python/compile.c` | AST → バイトコード変換 | （minilang にはない段） |
| `Python/ceval.c` | バイトコードを実行するメインループ | `evaluator.py` |

minilang を理解した状態で `tokenizer.c` を覗くと、「あ、これは `_number()` 相当だな」「これはキーワード判別のテーブルだな」と**パターンが見えてくる**はず。

## 結論

「Python がどこまで肩代わりしているか」の答え：

- **データ構造、メモリ管理、I/O、基本演算、クラス機構**まで全部 Python 任せ
- minilang が書いているのは**「言語処理のアルゴリズム」だけ**（Lexer / Parser / Evaluator のロジック）
- 下の層（C ランタイム、OS、CPU）に降りずに**抽象の上で考えられる**のが Python を使う利点

「機械語から積み上げる」アプローチは minilang を**補完する別ルート**で、両方が揃って初めて「文字列が CPU 命令に変わるまで全部理解した」と言える状態になる。minilang はそのうちの**上半分**を、最短経路で組み立てる教材。

## 学習の順序として

- 1回で全部理解しようとすると挫折する
- minilang で**言語処理の本質**を先に掴む（このリポジトリ）
- 必要になったら**機械語〜OS の層**を別の教材で深掘りする（learning-log のアプローチ等）

両ルートを行ったり来たりすることで、**抽象の階段を上下にスライドできる**理解になる。
