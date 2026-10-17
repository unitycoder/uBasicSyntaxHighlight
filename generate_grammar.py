#!/usr/bin/env python3
"""Generate the uBasic TextMate grammar from the compiler's own tables.

Reading the keyword set out of Lexer.cs and the builtin names out of Host.cs
means the highlighter cannot drift from the language. Add a keyword to the
lexer, re-run this, and the editors agree.

Emits the same grammar to both consumers:
  vscode/syntaxes/ubasic.tmLanguage.json   (VS Code extension)
  visualstudio/uBasic/Syntaxes/uBasic.json (Visual Studio loose grammar)

Usage:  python3 generate_grammar.py
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RUNTIME = os.path.normpath(os.path.join(HERE, "..", "Runtime"))

# ---------------------------------------------------------------- read source

def read(name):
    with open(os.path.join(RUNTIME, name), encoding="utf-8") as f:
        return f.read()

lexer = read("Lexer.cs")
host = read("Host.cs")

block = re.search(r"HashSet<string>\s+Keywords\s*=\s*new HashSet<string>\s*\{(.*?)\};",
                  lexer, re.S)
if not block:
    sys.exit("could not find the keyword table in Lexer.cs")
keywords = set(re.findall(r'"([^"]+)"', block.group(1)))

# Host.cs: Fn(...) entries are callable from uBasic; Proc("__...") ones are
# compiler-internal primitives and must not be highlighted.
builtins = set(n for n in re.findall(r'\bFn\("([^"]+)"', host) if not n.startswith("__"))

# Constants the compiler predefines (Compiler.DefinePredefinedConsts).
consts = set(n.rstrip("%!$") for n in
             re.findall(r'DefConst\("([^"]+)"', read("Compiler.cs")))

# ------------------------------------------------------------ categorise them

CONTROL = {"IF","THEN","ELSE","ELSEIF","END","FOR","TO","STEP","NEXT","WHILE","WEND",
           "DO","LOOP","UNTIL","SELECT","CASE","EXIT","GOTO","CALL","SUB","FUNCTION",
           "WAIT"}
DECL    = {"DIM","SHARED","CONST","LET","AS","RANDOMIZE"}
OPWORD  = {"AND","OR","NOT","XOR","MOD"}
TYPES   = {"INTEGER","SINGLE","STRING"}
STMTFN  = {"CLS","PSET","LINE","CIRCLE","PAINT","COLOR","LOCATE","PALETTE","SCREEN",
           "PRINT","BEEP","SOUND","PLAY"}
SHAPE   = {"B","BF","F"}          # LINE ... , B / BF  and  CIRCLE ... , F
NOISE   = {"REM"}                 # handled by the comment rule

leftover = keywords - CONTROL - DECL - OPWORD - TYPES - STMTFN - SHAPE - NOISE
if leftover:
    sys.exit("uncategorised keywords, update this script: " + ", ".join(sorted(leftover)))

def alt(words):
    """Longest-first alternation so END IF does not match a prefix first."""
    return "|".join(re.escape(w) for w in sorted(words, key=lambda w: (-len(w), w)))

# A keyword must not be followed by a letter, digit, underscore or sigil --
# otherwise `line%` would light up as the LINE statement.
TAIL = r"(?![A-Za-z0-9_%!$])"
# Builtins may end in '$', where \b does not behave, so use the same guard.
def kw(words):   return r"(?i)\b(?:" + alt(words) + r")" + TAIL

# ------------------------------------------------------------------- patterns

grammar = {
    "$schema": "https://raw.githubusercontent.com/martinring/tmlanguage/master/tmlanguage.json",
    "name": "uBasic",
    "scopeName": "source.ubasic",
    "fileTypes": ["ubas"],
    "patterns": [
        {"include": "#comment"},
        {"include": "#string"},
        {"include": "#procedure-name"},
        {"include": "#label"},
        {"include": "#number"},
        {"include": "#constant"},
        {"include": "#control"},
        {"include": "#declaration"},
        {"include": "#type"},
        {"include": "#operator-word"},
        {"include": "#statement-function"},
        {"include": "#shape-flag"},
        {"include": "#builtin"},
        {"include": "#variable"},
        {"include": "#operator"},
    ],
    "repository": {
        "comment": {
            "patterns": [
                {"name": "comment.line.apostrophe.ubasic", "match": r"'.*$"},
                {"name": "comment.line.rem.ubasic", "match": r"(?i)\bREM\b.*$"},
            ]
        },
        "string": {
            "name": "string.quoted.double.ubasic",
            "begin": '"',
            "end": '"(?!")',
            "patterns": [
                # "" is an embedded quote, the only escape QBasic has.
                {"name": "constant.character.escape.ubasic", "match": '""'}
            ]
        },
        # SUB Name(...) / FUNCTION Name%(...) -- colour the name being defined.
        "procedure-name": {
            "match": r"(?i)\b(SUB|FUNCTION)\s+([A-Za-z_][A-Za-z0-9_]*)([%!$]?)",
            "captures": {
                "1": {"name": "keyword.control.ubasic"},
                "2": {"name": "entity.name.function.ubasic"},
                "3": {"name": "storage.modifier.sigil.ubasic"},
            }
        },
        "label": {
            "match": r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(:)(?!=)",
            "captures": {
                "1": {"name": "entity.name.label.ubasic"},
                "2": {"name": "punctuation.separator.ubasic"},
            }
        },
        "number": {
            "patterns": [
                {"name": "constant.numeric.hex.ubasic", "match": r"(?i)&H[0-9A-F]+"},
                {"name": "constant.numeric.float.ubasic",
                 "match": r"(?i)\b\d+\.\d*(?:E[+-]?\d+)?[!#]?|\B\.\d+(?:E[+-]?\d+)?[!#]?"},
                {"name": "constant.numeric.integer.ubasic", "match": r"(?i)\b\d+[%&!]?\b"},
            ]
        },
        "constant":           {"name": "constant.language.ubasic",        "match": kw(consts)},
        "control":            {"name": "keyword.control.ubasic",          "match": kw(CONTROL)},
        "declaration":        {"name": "keyword.declaration.ubasic",      "match": kw(DECL)},
        "type":               {"name": "storage.type.ubasic",             "match": kw(TYPES)},
        "operator-word":      {"name": "keyword.operator.word.ubasic",    "match": kw(OPWORD)},
        "statement-function": {"name": "support.function.statement.ubasic","match": kw(STMTFN)},
        "builtin":            {"name": "support.function.builtin.ubasic", "match": kw(builtins)},
        # B / BF / F only mean something straight after a comma.
        "shape-flag": {
            "match": r"(?i)(,)\s*(BF|B|F)" + TAIL,
            "captures": {
                "1": {"name": "punctuation.separator.ubasic"},
                "2": {"name": "keyword.other.shape.ubasic"},
            }
        },
        # Trailing sigil gets its own scope so the type is visible at a glance.
        "variable": {
            "match": r"\b([A-Za-z_][A-Za-z0-9_]*)([%!$])?",
            "captures": {
                "1": {"name": "variable.other.ubasic"},
                "2": {"name": "storage.modifier.sigil.ubasic"},
            }
        },
        "operator": {
            "name": "keyword.operator.ubasic",
            "match": r"<>|<=|>=|[-+*/\\^=<>]"
        },
    }
}

# ------------------------------------------------------------------- emit

text = json.dumps(grammar, indent=2) + "\n"

targets = [
    os.path.join(HERE, "vscode", "syntaxes", "ubasic.tmLanguage.json"),
    os.path.join(HERE, "visualstudio", "uBasic", "Syntaxes", "uBasic.json"),
]
for t in targets:
    os.makedirs(os.path.dirname(t), exist_ok=True)
    with open(t, "w", encoding="utf-8") as f:
        f.write(text)
    print("wrote " + os.path.relpath(t, HERE))

print("%d keywords, %d builtins, %d constants" % (len(keywords), len(builtins), len(consts)))
