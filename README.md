# Editor support for `.ubas`

Syntax highlighting for uBasic in **Visual Studio**, **VS Code** and **Rider**.
All three read the same TextMate grammar, so there is one file to maintain.

Pick your editor below and follow the steps. Nothing needs building — these are
just files to copy.

## What is in this folder

```
EditorSupport~/
├── generate_grammar.py                     regenerates the grammar (see "Updating")
├── visualstudio/
│   └── uBasic/
│       └── Syntaxes/
│           └── uBasic.json                 ← Visual Studio reads this
└── vscode/                                 ← VS Code and Rider read this folder
    ├── package.json
    ├── language-configuration.json
    └── syntaxes/
        └── ubasic.tmLanguage.json
```

---

# Visual Studio

## Option A — quick, no files (about 10 seconds)

Good enough if you just want keywords to stop being black.

1. **Tools → Options → Text Editor → File Extension**
2. In **Extension**, type `ubas` (no dot)
3. In **Editor**, choose **Microsoft Visual Basic** from the dropdown
4. Click **Add**, then **OK**
5. Close and reopen any `.ubas` file you already have open

Visual Basic's editor already knows `DIM`, `IF`, `THEN`, `FOR`, `SUB` and
friends, so uBasic comes out mostly right. It will not know `PSET`, `CIRCLE`,
`PLAY` or the sigils. If Visual Basic is not in the dropdown, that workload is
not installed — use Option B instead.

## Option B — the real grammar

1. Open the folder `%userprofile%\.vs\Extensions` in Explorer.
   - Paste that path straight into the address bar.
   - `.vs` is a **hidden** folder, so you will not see it by browsing.
   - **`Extensions` usually does not exist yet — create it.**
2. Copy the `visualstudio\uBasic` folder into it.

   You should end up with exactly this:

   ```
   C:\Users\<you>\.vs\Extensions\uBasic\Syntaxes\uBasic.json
   ```

3. **Restart Visual Studio.**
4. Close and reopen any `.ubas` file that was already open — otherwise it keeps
   its old colouring and it looks like nothing happened.

Or, from PowerShell in this folder:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.vs\Extensions" | Out-Null
Copy-Item -Recurse -Force .\visualstudio\uBasic "$env:USERPROFILE\.vs\Extensions\"
```

**If it still is not coloured**, also do Option A (steps 1–4) and pick any
editor. Visual Studio normally reads the file extension from the `fileTypes`
array inside the grammar, but the two settings work together.

---

# VS Code

1. Copy the whole `vscode` folder into your extensions directory, **renaming it
   to `ubasic-0.2.0`**:

   | OS | Destination |
   |----|-------------|
   | Windows | `%USERPROFILE%\.vscode\extensions\ubasic-0.2.0\` |
   | macOS / Linux | `~/.vscode/extensions/ubasic-0.2.0/` |

   You should end up with `…\ubasic-0.2.0\package.json`, not
   `…\ubasic-0.2.0\vscode\package.json`.

2. Reload the window: **Ctrl+Shift+P** → *Developer: Reload Window*.

That is all — no build step, no `npm install`.

One line, from inside this folder:

```powershell
# Windows PowerShell
Copy-Item -Recurse -Force .\vscode "$env:USERPROFILE\.vscode\extensions\ubasic-0.2.0"
```

```bash
# macOS / Linux
cp -r vscode ~/.vscode/extensions/ubasic-0.2.0
```

Besides colouring you also get:

- `'` as the comment character, so **Ctrl+/** works
- bracket matching and auto-closing quotes
- auto-indent after `IF … THEN`, `FOR`, `WHILE`, `DO`, `SELECT CASE`, `SUB`,
  `FUNCTION`; dedent on `END …`, `NEXT`, `WEND`, `LOOP`, `ELSE`
- double-clicking `count%` selects the sigil too

---

# Rider

1. **File → Settings → Editor → TextMate Bundles**
2. Click **+**
3. Select the `vscode` folder from this directory
4. **OK**

Rider reads VS Code extension layouts directly, so the same folder serves both.

---

# Check that it worked

Save this as `test.ubas` and open it. Every line below should pick up a
different colour:

```basic
' a comment
DIM count%, speed!, name$
CONST MAXW% = 320
count% = &HFF
name$ = "hello " + STR$(42)
IF count% > 10 AND NOT speed! = 0 THEN PRINT MID$(name$, 1, 5)
LINE (0, 0)-(100, 50), 14, BF
PLAY "T120 O4 CDEFG"

FUNCTION Double%(n%)
  Double% = n% * 2
END FUNCTION
```

Things to look for specifically:

- `count`, `speed`, `name` are variables, and the `%`, `!`, `$` are a
  **different** colour
- `MID$` and `STR$` are builtins, including the `$`
- `BF` after the comma is a keyword, not a variable
- `Double` on the `FUNCTION` line is a function name

---

# Updating the grammar

The grammar is **generated** from the compiler's own tables:

| Comes from | Supplies |
|------------|----------|
| `Runtime/Lexer.cs` | the keyword set |
| `Runtime/Host.cs` | the builtin function names |
| `Runtime/Compiler.cs` | the predefined constants |

So after adding a keyword to the lexer:

```bash
python3 generate_grammar.py
```

That rewrites both `vscode/syntaxes/ubasic.tmLanguage.json` and
`visualstudio/uBasic/Syntaxes/uBasic.json`, then repeat the copy step for your
editor.

**Do not hand-edit the generated `.json` files** — the next run overwrites them.
If a keyword is uncategorised the script stops and tells you, rather than
quietly leaving it uncoloured.

## Sharing the VS Code extension as a `.vsix`

```bash
npm install -g @vscode/vsce
cd vscode && vsce package
```

---

# Reference: what gets coloured

| Scope | Covers |
|-------|--------|
| `keyword.control` | `IF THEN ELSE ELSEIF END FOR TO STEP NEXT WHILE WEND DO LOOP UNTIL SELECT CASE EXIT GOTO CALL SUB FUNCTION WAIT` |
| `keyword.declaration` | `DIM SHARED CONST LET AS RANDOMIZE` |
| `keyword.operator.word` | `AND OR NOT XOR MOD` |
| `storage.type` | `INTEGER SINGLE STRING` |
| `support.function.statement` | `CLS PSET LINE CIRCLE PAINT COLOR LOCATE PALETTE SCREEN PRINT BEEP SOUND PLAY` |
| `support.function.builtin` | `ABS SIN COS SQR CINT LEN MID$ STR$ KEY …` (39 of them) |
| `constant.language` | `TRUE FALSE PI KEY_LEFT KEY_RIGHT KEY_UP KEY_DOWN KEY_ESC KEY_SPACE KEY_ENTER` |
| `entity.name.function` | the name in `SUB Foo` / `FUNCTION Bar%` |
| `entity.name.label` | `cont:` at the start of a line |
| `storage.modifier.sigil` | the trailing `%`, `!` or `$`, scoped separately so the type reads at a glance |
| `keyword.other.shape` | `B` / `BF` after `LINE`, `F` after `CIRCLE` — only straight after a comma |
| `comment.line` | `'` to end of line, and `REM` |
| `string.quoted.double` | `"…"`, with `""` as an embedded quote |
| `constant.numeric` | decimals, floats with exponents, and `&HFF` hex |

Keywords match case-insensitively, and are guarded against matching an
identifier that merely starts the same way — `line% = 1` is a variable, not the
`LINE` statement.

# Limitation

This is **colouring only**. A loose TextMate grammar gives no IntelliSense, no
go-to-definition and no error squiggles in any of these editors.

For errors, rely on the `.ubas` importer in Unity: it compile-checks on every
save and reports with line numbers, so mistakes surface without entering play
mode.

Source: [Add Visual Studio editor support for other languages](https://learn.microsoft.com/en-us/visualstudio/ide/adding-visual-studio-editor-support-for-other-languages?view=vs-2022)
