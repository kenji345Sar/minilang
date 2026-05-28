# AST が使われている他の場面

minilang で自前に書いた **AST (Abstract Syntax Tree)** は、言語処理（インタプリタ・コンパイラ）だけのものではない。**「コードをテキストではなく構造として扱う」必要があるツールは、ほぼ全部 AST に行き着く**。この note は、AST が他にどこで再利用されるかの地図。

## AST がなぜ強いのか

ソースコードを **テキスト** として扱うと、すぐ限界が来る。例えば「`+` を `-` に書き換えたい」とき:

```python
result = a + b       # ← ここの + だけ書き換えたい
greeting = "1 + 2"   # ← ここの + は触りたくない（文字列リテラル）
total = a + b + c    # ← 演算子としての + のみ対象
# 加算処理: + が遅い   # ← コメントの + も触りたくない
```

テキスト置換では、コメントや文字列の中の `+` まで巻き込んでしまう。AST に変換すれば「**演算子としての `+` ノード**」だけを正確に取り出せる。

minilang で `BinOp(+, left, right)` のようなノードを定義したのと同じく、どの言語の AST にも「演算子」「リテラル」「変数参照」「関数呼び出し」などのノード種別が存在する。これに名前を付けて構造として扱えるのが AST の力。

## AST が出てくるツールの地図

| 用途 | 代表ツール | 何のために AST を使うか |
|---|---|---|
| **インタプリタ・コンパイラ** | minilang、CPython、TypeScript コンパイラ、Rustc | AST を **評価** または **機械語に翻訳** する |
| **Mutation Testing** | gomu（Go）、PIT（Java）、Stryker（JS）、mutmut（Python）| AST を **書き換えてバグを意図的に注入**、テストが検出できるか試す |
| **Linter** | ESLint、golangci-lint、Pylint、RuboCop | AST を走査して **コードスタイル違反やバグパターン** を検出 |
| **Formatter** | gofmt、Prettier、Black、rustfmt | AST にしてから **正規化された形でテキストに戻す**（パース → 整形 → 出力） |
| **静的解析・脆弱性検出** | CodeQL、Semgrep、SonarQube、go vet | AST + 制御フロー / データフロー解析で脆弱性を見つける |
| **コード自動修正・リファクタリング** | rector（PHP）、jscodeshift、go fix、IDE のリネーム | AST を **書き換えてから再度テキストに戻す** |
| **AI コード補完・LSP** | LSP サーバ、tree-sitter、GitHub Copilot 等 | カーソル位置の AST 文脈から補完候補を出す |
| **トランスパイラ** | Babel（JS）、TypeScript の JS 出力 | AST を **別の言語の AST に変換** してから出力 |

「コードをテキストではなく構造として扱う」必要があるなら、必ず AST が出てくる。

## minilang での AST と、他ツールでの AST の対応

| minilang で書いたもの | 他ツールでの対応 |
|---|---|
| `lexer.py`（文字列 → トークン列）| Go の `go/scanner`、Python の `tokenize`、JS の `acorn` の lexer |
| `parser.py`（トークン → 構文木）| `go/parser`、`ast` モジュール、`@babel/parser` |
| `ast_nodes.py`（AST ノード定義）| `go/ast`、Python の `ast.AST`、`@babel/types` |
| `evaluator.py`（AST を評価）| インタプリタの本体。コンパイラなら **代わりに** コード生成器が乗る |

Python では `import ast` だけで、Python ソースコードを AST にパースできる:

```python
import ast
tree = ast.parse("a + b")
print(ast.dump(tree))
# Module(body=[Expr(value=BinOp(left=Name(id='a'), op=Add(), right=Name(id='b')))])
```

minilang で自前に作った `BinOp` ノードと、Python 標準の `ast.BinOp` は **同じ概念**。

## なぜ標準パッケージで提供されているか

Go の `go/parser` や Python の `ast` モジュールが標準で入っているのは、**AST を扱う処理が言語エコシステム全体で頻繁に必要になる** から。

- gofmt / go vet / golangci-lint / gopls など Go のツール群は **すべて `go/ast` を共有して使っている**
- Python の linter（flake8、ruff、mypy）も `ast` モジュールを共有して使っている
- 「AST を扱うインフラ」が標準にあると、ツール作者は車輪の再発明をしなくて済む

minilang で自分で書いた経験があれば、これらの標準パッケージが **何を提供しているか** が想像できる ── これが minilang を自前で書いた価値のひとつ。

## 4 切り（[learning-by-slicing.md](../../infra-lessons/notes/learning-by-slicing.md)）に当てると

| 切り方 | AST まわりでの実体 |
|---|---|
| **A. プロトコル / 規格** | 言語仕様（Go 言語仕様、Python 言語リファレンス）。AST 構造はここから決まる |
| **B. パケット相当** | パース後のメモリ上のツリー。`ast.dump()` で観察可 |
| **C. 設定** | linter の設定ファイル（`.eslintrc`、`pyproject.toml` 等）でどの AST パターンを違反とするかを指定 |
| **D. 実装** | go/parser、Python の ast モジュール、tree-sitter、minilang の parser.py |

## まとめ

- AST は **「コードをテキストではなく構造として扱う」必要があるツールが共通して使う中間表現**
- minilang で自前に書いた AST と、Mutation Testing / Linter / Formatter / 静的解析が使う AST は **同じ概念**
- Go や Python では言語標準で AST 処理が提供されており、エコシステム全体で共有されている
- minilang で AST を自分で書いた経験は、これら全ツールの理解の土台になる

## 関連

- minilang の AST の実装本体: [../ast_nodes.py](../ast_nodes.py)、[../parser.py](../parser.py)
- 用語の定義は [glossary.md](glossary.md)
- 4 切りで切り口を整理: [../../infra-lessons/notes/learning-by-slicing.md](../../infra-lessons/notes/learning-by-slicing.md)
