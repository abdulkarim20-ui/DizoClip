"""
Design tokens, color constants, and QSS style sheet for DizoClip.
"""

from string import Template

# ---------- Colors (Midnight Slate) ----------
BG_MAIN = "#0f111a"       # Softer, deep slate background
BG_CARD = "#1a1d27"       # Slightly elevated card background
BG_INPUT = "#14161f"      # Differentiated input field depth
ACCENT = "#ff8c5a"        # Brighter, punchier coral/orange
TEXT_MAIN = "#e2e8f0"     # Softer white to reduce eye strain
TEXT_DIM = "#7a8292"      # Subdued / masked text
BORDER = "#2a2f3d"        # Cleaner structural lines
CARD_BORDER = "#252b38"    # Card chip border
BTN_HOVER = "#242938"      # Action button hover
BTN_ACTIVE = "#2d3345"     # 3-dot active background
DANGER = "#e84a4a"
SUCCESS = "#4ae87c"

# ---------- Typography System ----------
FONT_UI = '"Inter", "Segoe UI Variable", "Segoe UI", -apple-system, "Helvetica Neue", Arial, sans-serif'
FONT_MONO = '"JetBrains Mono", "Cascadia Code", "Consolas", "Courier New", monospace'

TYPE = {
    "title-lg":     dict(size=15,   weight=700, spacing="0px"),
    "title":        dict(size=13,   weight=700, spacing="0px"),
    "body-strong":  dict(size=13,   weight=600, spacing="0px"),
    "body":         dict(size=13,   weight=400, spacing="0px"),
    "subtext":      dict(size=11.5, weight=500, spacing="0px"),
    "caption":      dict(size=11.5, weight=600, spacing="0px"),
    "caption-dim":  dict(size=11,   weight=400, spacing="0px"),
    "eyebrow":      dict(size=10,   weight=700, spacing="0.8px"),
    "micro":        dict(size=10,   weight=700, spacing="0px"),
    "code":         dict(size=11.5, weight=500, spacing="0px"),
    "error":        dict(size=12,   weight=500, spacing="0px"),
}


def font_css(token: str, color: str = "", extra: str = "") -> str:
    """Generate inline stylesheet font rules for a typography token."""
    spec = TYPE.get(token, TYPE["body"])
    sz = spec["size"]
    size_str = f"{int(sz)}px" if isinstance(sz, (int, float)) and sz == int(sz) else f"{sz}px"
    rules = [
        f"font-size: {size_str};",
        f"font-weight: {spec['weight']};",
    ]
    if spec.get("spacing") and spec["spacing"] != "0px":
        rules.append(f"letter-spacing: {spec['spacing']};")
    if color:
        rules.append(f"color: {color};")
    if extra:
        rules.append(extra.strip())
    return " ".join(rules)


APP_QSS = Template("""
QMainWindow { background: $BG_MAIN; }
QDialog { background: $BG_CARD; }

QWidget {
    color: $TEXT_MAIN;
    font-family: $FONT_UI;
    font-size: 13px;              /* body */
    font-weight: 400;
}

QLabel { background: transparent; border: none; }
QLabel[cls="dim"]     { color: $TEXT_DIM; }
QLabel[cls="title"]   { font-size: 13px; font-weight: 700; }     /* was: 13/700, unchanged */
QLabel[cls="h2"]      { font-size: 13px; font-weight: 700; }
QLabel[cls="caption"] { color: $TEXT_DIM; font-size: 11.5px; font-weight: 500; }  /* was 12px */
QLabel[cls="masked"]  { color: $TEXT_DIM; font-size: 11px;  font-weight: 400; }
QLabel[cls="error"]   { color: $DANGER;   font-size: 12px;  font-weight: 500; }

QLabel#CountBadge {
    background: transparent;
    border: none;
    color: $ACCENT;
    font-size: 12.5px;
    font-weight: 600;
    padding: 0px;
}

QLineEdit {
    background: $BG_INPUT;
    border: 1px solid $BORDER;
    border-radius: 8px;
    padding: 6px 10px;
    color: $TEXT_MAIN;
    selection-background-color: $ACCENT;
    selection-color: #ffffff;
    lineedit-password-character: 42;
}
QLineEdit:focus { border: 1px solid $ACCENT; }

QPlainTextEdit, QTextEdit {
    background: $BG_INPUT;
    border: 1px solid $BORDER;
    border-radius: 8px;
    padding: 8px 10px;
    color: $TEXT_MAIN;
    selection-background-color: $ACCENT;
    selection-color: #ffffff;
    font-size: 12px;
    line-height: 1.4;
}
QPlainTextEdit:focus, QTextEdit:focus {
    border: 1px solid $ACCENT;
}

QFrame#Card {
    background: #141722;
    border: 1px solid #222838;
    border-radius: 12px;
}
QFrame#Card:hover {
    background: #181c2b;
    border: 1px solid #2d354b;
}
QFrame#Card[dragging="true"] {
    background: #202536;
    border: 1px solid #ff8c5a;
}

QPushButton {
    background: $BG_CARD;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    color: $TEXT_MAIN;
}
QPushButton:hover   { background: $BTN_HOVER; }
QPushButton:pressed { background: $BTN_ACTIVE; }

QPushButton#Primary {
    background: $ACCENT;
    color: #0b0d10;
    font-weight: 700;
}
QPushButton#Primary:hover   { background: #d5693c; }
QPushButton#Primary:pressed { background: #b85a30; }

QPushButton#Danger {
    background: $DANGER;
    color: #ffffff;
    font-weight: 700;
}
QPushButton#Danger:hover { background: #c83838; }

QPushButton[cls="neutral"]         { background: $BG_MAIN; }
QPushButton[cls="neutral"]:hover   { background: $BTN_HOVER; }

QToolButton[cls="icon"] {
    background: transparent;
    border: none;
    border-radius: 6px;
    color: $TEXT_DIM;
}
QToolButton[cls="icon"]:hover   { background: $BTN_HOVER; color: $TEXT_MAIN; }
QToolButton[cls="icon"]:pressed { background: $BTN_ACTIVE; }

QPushButton#SquareBtn, QToolButton#SquareBtn {
    background: #191c28;
    border: 1px solid #282f42;
    border-radius: 6px;
    color: $TEXT_DIM;
    padding: 0;
}
QPushButton#SquareBtn:hover, QToolButton#SquareBtn:hover {
    background: #242b3d;
    border: 1px solid #3b445c;
    color: $TEXT_MAIN;
}
QPushButton#SquareBtn:pressed, QToolButton#SquareBtn:pressed {
    background: #161924;
}

QPushButton#FieldBtn, QToolButton#FieldBtn {
    background: #191c28;
    border: 1px solid #282f42;
    border-radius: 8px;
    color: $TEXT_DIM;
    padding: 0;
}
QPushButton#FieldBtn:hover, QToolButton#FieldBtn:hover {
    background: #242b3d;
    border: 1px solid #3b445c;
    color: $TEXT_MAIN;
}
QPushButton#FieldBtn:pressed, QToolButton#FieldBtn:pressed {
    background: #161924;
}

QScrollArea {
    background: transparent;
    border: none;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}

QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #2b3144;
    min-height: 20px;
    border-radius: 3px;
}
QScrollBar::handle:vertical:hover {
    background: #3e4661;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
    background: none;
    border: none;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
    border: none;
}
QScrollBar:horizontal {
    height: 0px;
}

QToolTip {
    background-color: #141722;
    color: $TEXT_MAIN;
    font-family: $FONT_UI;
    font-size: 11.5px;
    font-weight: 500;
    border: 1px solid #282f42;
    border-radius: 6px;
    padding: 4px 8px;
}

/* Monospace targets: code snippet panels, key/command value fields */
QLabel[cls="code"], QLineEdit[cls="code"] {
    font-family: $FONT_MONO;
    font-size: 11.5px;
    font-weight: 500;
    line-height: 1.45;
}
""").substitute(
    BG_MAIN=BG_MAIN, BG_CARD=BG_CARD, BG_INPUT=BG_INPUT, ACCENT=ACCENT,
    TEXT_MAIN=TEXT_MAIN, TEXT_DIM=TEXT_DIM, BORDER=BORDER,
    CARD_BORDER=CARD_BORDER, BTN_HOVER=BTN_HOVER, BTN_ACTIVE=BTN_ACTIVE,
    DANGER=DANGER, SUCCESS=SUCCESS,
    FONT_UI=FONT_UI, FONT_MONO=FONT_MONO,
)
