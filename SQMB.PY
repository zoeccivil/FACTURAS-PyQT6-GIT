#!/usr/bin/env python3
"""
Busca llamadas a QMessageBox que usan keywords no válidos en PyQt6
(ej: parent=..., title=..., text=..., buttons=...) y muestra
la ubicación y una SUGERENCIA de reemplazo cuando es posible.

Uso:
    python search_qmessagebox.py            # lista ocurrencias (modo seguro)
    python search_qmessagebox.py --apply    # intenta corregir *algunas* líneas (haz backup antes)

NOTA: El modo --apply intenta hacer cambios automáticos solo en casos sencillos
(donde title y text son literales). Revisa los archivos antes de confirmar commit.
"""
import re
import sys
from pathlib import Path
import shutil

ROOT = Path(".").resolve()
PY_GLOB = ["**/*.py"]

# Pattern to find QMessageBox.*( ... parent= ... ) or title= or text= or buttons=
KW_PATTERN = re.compile(r"QMessageBox\.\w+\s*\(.*\b(parent|title|text|buttons|defaultButton)\s*=")

# Try to extract title and text string literals (very simple heuristic)
TITLE_RE = re.compile(r"title\s*=\s*([rR]?['\"]{1,3}.*?['\"]{1,3})")
TEXT_RE = re.compile(r"text\s*=\s*([rR]?['\"]{1,3}.*?['\"]{1,3})")
PARENT_RE = re.compile(r"parent\s*=\s*([^\s,)\]]+)")
BUTTONS_RE = re.compile(r"buttons\s*=\s*([^\s,)\]]+)")
DEFAULTBTN_RE = re.compile(r"defaultButton\s*=\s*([^\s,)\]]+)")

def suggest_replacement(line):
    """
    If title and text are present as string literals, return a suggested positional call.
    Otherwise return None.
    """
    m_title = TITLE_RE.search(line)
    m_text = TEXT_RE.search(line)
    # get function name
    m_func = re.search(r"(QMessageBox\.\w+)\s*\(", line)
    if not m_func:
        return None
    func = m_func.group(1)
    if m_title and m_text:
        title = m_title.group(1)
        text = m_text.group(1)
        # find buttons/defaultButton if present (keep as trailing args)
        buttons = ""
        m_buttons = BUTTONS_RE.search(line)
        if m_buttons:
            buttons = ", " + m_buttons.group(1)
        m_default = DEFAULTBTN_RE.search(line)
        if m_default:
            buttons += (", " + m_default.group(1)) if buttons else (", " + m_default.group(1))
        # construct suggestion: first arg should be the parent (we try to pick from parent=...)
        m_parent = PARENT_RE.search(line)
        parent = "self"
        if m_parent:
            parent = m_parent.group(1)
        suggestion = f"{func}({parent}, {title}, {text}{buttons})"
        return suggestion
    return None

def scan_repo(apply_fixes=False):
    py_files = []
    for g in PY_GLOB:
        py_files.extend(Path(ROOT).glob(g))
    py_files = [p for p in py_files if p.is_file()]

    findings = []
    for path in py_files:
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        lines = text.splitlines()
        changed = False
        new_lines = lines.copy()
        for idx, line in enumerate(lines, start=1):
            if KW_PATTERN.search(line):
                suggestion = suggest_replacement(line)
                findings.append({
                    "file": str(path),
                    "line_no": idx,
                    "line": line.rstrip(),
                    "suggestion": suggestion
                })
                # optional apply: attempt to replace simple cases where suggestion is not None
                if apply_fixes and suggestion:
                    # Replace the single line with suggestion
                    new_lines[idx-1] = suggestion
                    changed = True

        if apply_fixes and changed:
            # backup original file
            bak = path.with_suffix(path.suffix + ".bak")
            shutil.copy2(path, bak)
            path.write_text("\n".join(new_lines), encoding="utf-8")
            print(f"[FIXED] {path}  (backup: {bak})")

    return findings

def main():
    apply = "--apply" in sys.argv[1:]
    findings = scan_repo(apply_fixes=apply)
    if not findings:
        print("No se han encontrado llamadas problemáticas a QMessageBox con keywords.")
        return
    print(f"Se encontraron {len(findings)} llamadas problemáticas:")
    for f in findings:
        print(f"\nFile: {f['file']}  Line: {f['line_no']}")
        print("  Original:")
        print("    " + f['line'])
        if f['suggestion']:
            print("  Sugerencia:")
            print("    " + f['suggestion'])
        else:
            print("  Sugerencia: (no generada automáticamente — revisar manualmente)")
    if apply:
        print("\nModo --apply habilitado: se intentaron aplicar fixes automáticos en los casos simples.")
        print("Revisa los archivos .bak si algo no quedó correcto y deshaz los cambios si hace falta.")

if __name__ == "__main__":
    main()