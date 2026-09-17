import time
import uuid
from typing import Dict, List, Optional

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QFont, QIcon, QKeySequence, QShortcut, QTextCursor, QTextDocument
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,

    QPlainTextDocumentLayout,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.components.buttons.icon_button import icon_button
from app.components.dialogs.confirm_delete import ConfirmDeleteDialog
from app.components.inputs.color_picker import ColorSelectorBar
from app.components.labels.animated_tooltip import attach_tooltip, set_tooltip
from app.components.navigation.vscode_tab_scroll import VSCodeTabScrollArea
from app.config.constants import BADGE_COLORS
from app.config.theme import ACCENT, BG_CARD, BG_INPUT, BORDER, BTN_HOVER, FONT_MONO, TEXT_DIM, TEXT_MAIN, font_css
from app.core.icons import render_pixmap
from app.utils.language_detector import detect_code_language



class InlineTabEdit(QLineEdit):
    """Inline editor for tab renaming with Enter to commit and Escape to cancel."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.btn = parent

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.btn:
                self.btn._commit_rename()
            event.accept()
            return
        elif event.key() == Qt.Key_Escape:
            if self.btn:
                self.btn._cancel_rename()
            event.accept()
            return
        super().keyPressEvent(event)

    def focusOutEvent(self, event):
        if self.btn and self.isVisible():
            self.btn._commit_rename()
        super().focusOutEvent(event)


class SnippetTabButton(QFrame):
    """
    VS Code-style tab button for code snippet language:
    - Tab name label (clicks activate tab)
    - In-place inline rename (double-click to rename right in the tab, Enter to commit)
    - Close button with x.svg (only shown on active tab; clicks trigger delete confirmation)
    - Active styling with accent color pill
    - Inactive styling with subtle hover
    """
    def __init__(self, name: str, is_active: bool = False, can_close: bool = True, on_click=None, on_close=None, on_rename=None, parent=None):
        super().__init__(parent)
        self.tab_name = name
        self.is_active = is_active
        self.can_close = can_close
        self.on_click = on_click
        self.on_close = on_close
        self.on_rename = on_rename
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(24)

        self.t_lay = QHBoxLayout(self)
        self.t_lay.setContentsMargins(8, 2, 4, 2)
        self.t_lay.setSpacing(5)

        self.name_lbl = QLabel(name)
        self.name_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.t_lay.addWidget(self.name_lbl)

        # Inline rename editor (hidden until double-clicked)
        self.name_edit = InlineTabEdit(self)
        self.name_edit.setFixedHeight(18)
        self.name_edit.hide()
        self.name_edit.textChanged.connect(self._adjust_edit_width)
        self.t_lay.addWidget(self.name_edit)

        self.close_btn = QToolButton(self)
        self.close_btn.setFixedSize(16, 16)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        attach_tooltip(self.close_btn, f"Delete '{name}' snippet", placement="top")
        if on_close:
            self.close_btn.clicked.connect(on_close)
        self.t_lay.addWidget(self.close_btn)

        self.update_style()

    def set_name(self, name: str):
        self.tab_name = name
        self.name_lbl.setText(name)
        set_tooltip(self.close_btn, f"Delete '{name}' snippet", placement="top")

    def _adjust_edit_width(self, text: str = ""):
        txt = self.name_edit.text() if not text else text
        fm = self.name_edit.fontMetrics()
        w = max(45, fm.horizontalAdvance(txt) + 14)
        self.name_edit.setFixedWidth(w)

    def start_rename(self):
        """Starts inline renaming right in the tab button like Windows file renaming."""
        if self.on_click and not self.is_active:
            self.on_click()

        self.name_lbl.hide()
        self.close_btn.hide()
        self.name_edit.setText(self.tab_name)
        self._adjust_edit_width(self.tab_name)
        self.name_edit.show()
        self.name_edit.selectAll()
        self.name_edit.setFocus()

    def _commit_rename(self):
        """Commits the inline rename when user presses Enter or clicks away."""
        if not self.name_edit.isVisible():
            return
        new_val = self.name_edit.text().strip()
        self.name_edit.hide()
        self.name_lbl.show()
        if self.is_active and self.can_close:
            self.close_btn.show()

        if new_val and new_val != self.tab_name:
            self.set_name(new_val)
            if self.on_rename:
                self.on_rename(new_val)
        elif not new_val:
            # Blank resets to auto-detection
            if self.on_rename:
                self.on_rename("")

    def _cancel_rename(self):
        """Cancels the inline rename when user presses Escape."""
        if not self.name_edit.isVisible():
            return
        self.name_edit.hide()
        self.name_lbl.show()
        if self.is_active and self.can_close:
            self.close_btn.show()

    def set_active(self, active: bool, can_close: bool = None):
        self.is_active = active
        if can_close is not None:
            self.can_close = can_close
        self.update_style()

    def update_style(self):
        if self.is_active:
            if self.can_close and not self.name_edit.isVisible():
                self.t_lay.setContentsMargins(8, 2, 4, 2)
            else:
                self.t_lay.setContentsMargins(8, 2, 8, 2)
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {ACCENT};
                    border-radius: 5px;
                }}
            """)
            self.name_lbl.setStyleSheet("""
                color: #0b0d10;
                font-weight: 700;
                font-size: 11.5px;
                background: transparent;
                border: none;
            """)
            self.name_edit.setStyleSheet("""
                QLineEdit {
                    background-color: #ffffff;
                    color: #0b0d10;
                    font-size: 11px;
                    font-weight: 700;
                    border: 1px solid #ffffff;
                    border-radius: 3px;
                    padding: 0px 3px;
                }
            """)
            pm = render_pixmap("x", (9, 9), color="#0b0d10")
            if pm:
                self.close_btn.setIcon(pm)
            self.close_btn.setStyleSheet("""
                QToolButton {
                    background: transparent;
                    border: none;
                    border-radius: 3px;
                }
                QToolButton:hover {
                    background: rgba(0, 0, 0, 0.20);
                }
                QToolButton:pressed {
                    background: rgba(0, 0, 0, 0.35);
                }
            """)
            if self.can_close and not self.name_edit.isVisible():
                self.close_btn.show()
            else:
                self.close_btn.hide()
        else:
            self.t_lay.setContentsMargins(8, 2, 8, 2)
            self.setStyleSheet("""
                QFrame {
                    background-color: transparent;
                    border-radius: 5px;
                }
                QFrame:hover {
                    background-color: #232938;
                }
            """)
            self.name_lbl.setStyleSheet("""
                color: #cbd5e1;
                font-weight: 600;
                font-size: 11.5px;
                background: transparent;
                border: none;
            """)
            self.name_edit.setStyleSheet("""
                QLineEdit {
                    background-color: #1a202c;
                    color: #ffffff;
                    font-size: 11px;
                    font-weight: 600;
                    border: 1px solid #ff773d;
                    border-radius: 3px;
                    padding: 0px 3px;
                }
            """)
            self.close_btn.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.on_click:
                self.on_click()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_rename()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

class AddSnippetTabButton(QToolButton):
    """Square + button to create a new language tab with SVG icon, matching tab height and dark box styling."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setAutoRaise(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)

        self._pm_normal = render_pixmap("plus", (12, 12), color="#cbd5e1")
        self._pm_hover = render_pixmap("plus", (12, 12), color="#ffffff")

        self.setIconSize(QSize(12, 12))
        attach_tooltip(self, "Add language snippet", placement="top")
        self._update_style(hovered=False)

    def _update_style(self, hovered: bool):
        pm = self._pm_hover if hovered else self._pm_normal
        if pm:
            self.setIcon(QIcon(pm))

        if hovered:
            self.setStyleSheet("""
                QToolButton {
                    background-color: #262f42;
                    border: 1px solid #445475;
                    border-radius: 5px;
                    padding: 0px;
                    margin: 0px;
                }
            """)
        else:
            self.setStyleSheet("""
                QToolButton {
                    background-color: #161b26;
                    border: 1px solid #283347;
                    border-radius: 5px;
                    padding: 0px;
                    margin: 0px;
                }
                QToolButton:pressed {
                    background-color: #0e121a;
                    border: 1px solid #ff773d;
                }
            """)

    def enterEvent(self, event):
        self._update_style(hovered=True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._update_style(hovered=False)
        super().leaveEvent(event)


class AIModelFormView(QWidget):
    """Add / Edit AI Model Form View with multi-language code snippets and auto-detection."""
    def __init__(self, win):
        super().__init__()
        self.win = win
        self.editing = None
        self.selected_color = BADGE_COLORS[0]
        self.color_buttons = {}

        # Snippets data in memory: list of dicts [{"name": "Python", "code": "...", "user_renamed": False, "doc": QTextDocument}]
        self.snippets_data: List[Dict] = []
        self.tab_buttons_list: List[SnippetTabButton] = []
        self._deleted_tabs_history: List[Dict] = []
        self.active_snippet_idx = 0
        self._block_auto_detect = False

        # Undo / Redo shortcuts
        QShortcut(QKeySequence.Undo, self, activated=self._handle_undo)
        QShortcut(QKeySequence.Redo, self, activated=self._handle_redo)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 10, 16, 10)
        root.setSpacing(5)

        # 1. Top Bar
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 2)
        top.setSpacing(10)
        back = icon_button(win.icons.get("back"), "←", "Back to list",
                           size=28, icon_size=15, object_name="SquareBtn")
        back.clicked.connect(win.show_list_view)
        top.addWidget(back)

        self.title_lbl = QLabel("Add AI Model")
        self.title_lbl.setStyleSheet(font_css("title-lg", color=TEXT_MAIN))
        top.addWidget(self.title_lbl)
        top.addStretch(1)
        root.addLayout(top)

        # 2. Model Name
        root.addSpacing(4)
        name_lbl = QLabel("Model Name")
        name_lbl.setStyleSheet(font_css("subtext", color=TEXT_DIM))
        root.addWidget(name_lbl)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Fable 5.1, GPT 6")
        self.name_edit.setFixedHeight(34)
        root.addWidget(self.name_edit)

        # 3. Code Snippets Section Header & Tabs Container
        root.addSpacing(9)
        snip_hdr_row = QHBoxLayout()
        snip_hdr_row.setContentsMargins(0, 2, 0, 0)
        snip_hdr_lbl = QLabel("Code Snippets")
        snip_hdr_lbl.setStyleSheet(font_css("subtext", color=TEXT_DIM))
        snip_hdr_row.addWidget(snip_hdr_lbl)
        snip_hdr_row.addStretch(1)
        root.addLayout(snip_hdr_row)

        # Container box wrapping Tabs + Code Text Area
        snippet_box = QFrame()
        snippet_box.setObjectName("SnippetBox")
        snippet_box.setStyleSheet(f"""
            QFrame#SnippetBox {{
                background-color: #0e121a;
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
        """)
        box_lay = QVBoxLayout(snippet_box)
        box_lay.setContentsMargins(6, 6, 6, 6)
        box_lay.setSpacing(6)

        # Horizontal Tab Scroll Area (VS Code style with mouse wheel support)
        self.tabs_scroll = VSCodeTabScrollArea(self)
        self.tabs_scroll.setFixedHeight(30)

        self.tabs_bar = QWidget()
        self.tabs_bar.setStyleSheet("background: transparent;")
        self.tabs_lay = QHBoxLayout(self.tabs_bar)
        self.tabs_lay.setContentsMargins(0, 0, 0, 0)
        self.tabs_lay.setSpacing(6)
        self.tabs_lay.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # Add '+' button to create new language tab
        self.add_tab_btn = AddSnippetTabButton()
        self.add_tab_btn.clicked.connect(self._add_snippet_tab)

        self.tabs_scroll.setWidget(self.tabs_bar)
        box_lay.addWidget(self.tabs_scroll)


        # Code Editor Text Area (increased height by 2 lines for clear visibility)
        self.code_edit = QPlainTextEdit()
        mono_font = QFont("JetBrains Mono", 10)
        mono_font.setStyleHint(QFont.Monospace)
        self.code_edit.setFont(mono_font)
        self.code_edit.setFixedHeight(134)
        self.code_edit.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: #090c12;
                color: #f1f5f9;
                border: 1px solid #1e2433;
                border-radius: 6px;
                padding: 6px 8px;
                font-family: {FONT_MONO};
                {font_css("code")}
                line-height: 1.45;
            }}
            QPlainTextEdit:focus {{
                border: 1px solid {ACCENT};
            }}
        """)
        self.code_edit.textChanged.connect(self._on_code_text_changed)
        box_lay.addWidget(self.code_edit)

        root.addWidget(snippet_box)

        # 4. Badge Color Picker (placed below the code snippets section)
        root.addSpacing(9)
        self.color_bar = ColorSelectorBar(
            initial_color=self.selected_color,
            on_color_changed=self._on_color_changed,
            win=self.win,
            parent=self
        )
        root.addWidget(self.color_bar)

        # Error / Validation hint
        self.hint = QLabel()
        self.hint.setProperty("cls", "error")
        self.hint.hide()
        root.addWidget(self.hint)

        root.addStretch(1)

        # 5. Cancel / Save Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.setContentsMargins(0, 4, 0, 0)

        cancel = QPushButton("Cancel")
        cancel.setStyleSheet(f"""
            QPushButton {{
                background: {BG_CARD};
                color: {TEXT_MAIN};
                border-radius: 8px;
                padding: 7px 16px;
                font-size: 13px;
                border: 1px solid {BORDER};
            }}
            QPushButton:hover {{ background: {BTN_HOVER}; }}
        """)
        cancel.setFixedHeight(34)
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.clicked.connect(win.show_list_view)
        btn_row.addWidget(cancel)

        save = QPushButton("Save Model")
        save.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT};
                color: #0b0d10;
                font-weight: 700;
                font-size: 13px;
                border-radius: 8px;
                padding: 7px 16px;
                border: none;
            }}
            QPushButton:hover {{ background: #d5693c; }}
            QPushButton:pressed {{ background: #b85a30; }}
        """)
        save.setFixedHeight(34)
        save.setCursor(Qt.PointingHandCursor)
        save.clicked.connect(self._save)
        btn_row.addWidget(save)

        root.addLayout(btn_row)

    def _create_snippet_doc(self, code: str = "") -> QTextDocument:
        """Creates a dedicated QTextDocument with monospace font, QPlainTextDocumentLayout, and undo/redo enabled."""
        doc = QTextDocument(self)
        doc.setDocumentLayout(QPlainTextDocumentLayout(doc))
        mono_font = QFont("Consolas", 10)
        mono_font.setStyleHint(QFont.Monospace)
        doc.setDefaultFont(mono_font)
        doc.setPlainText(code)
        doc.setUndoRedoEnabled(True)
        return doc


    def _default_snippet_name(self, idx: int) -> str:
        """Returns standard generic snippet label."""
        if len(self.snippets_data) <= 1:
            return "Snippet"
        return f"Snippet {idx + 1}"

    def _render_tabs(self):
        """Re-renders tab buttons inside the horizontal VS Code scroll area."""
        if self.active_snippet_idx >= len(self.snippets_data):
            self.active_snippet_idx = max(0, len(self.snippets_data) - 1)

        while self.tabs_lay.count():

            item = self.tabs_lay.takeAt(0)
            w = item.widget()
            if w is not None and w != self.add_tab_btn:
                w.hide()
                w.setParent(None)
                w.deleteLater()

        self.tab_buttons_list = []
        can_close_tabs = len(self.snippets_data) > 1
        for idx, snip in enumerate(self.snippets_data):
            is_active = (idx == self.active_snippet_idx)
            btn = SnippetTabButton(
                snip["name"],
                is_active=is_active,
                can_close=can_close_tabs,
                on_click=lambda _=False, i=idx: self._switch_to_tab(i),
                on_close=lambda _=False, i=idx: self._delete_snippet_tab(i),
                on_rename=lambda new_name, i=idx: self._on_tab_renamed(i, new_name),
            )
            self.tabs_lay.addWidget(btn, 0, Qt.AlignVCenter)
            self.tab_buttons_list.append(btn)

        self.tabs_lay.addWidget(self.add_tab_btn, 0, Qt.AlignVCenter)
        self.tabs_lay.addStretch(1)

        # Auto-scroll active tab into view
        if 0 <= self.active_snippet_idx < len(self.tab_buttons_list):
            active_btn = self.tab_buttons_list[self.active_snippet_idx]
            QTimer.singleShot(15, lambda b=active_btn: self.tabs_scroll.ensure_tab_visible(b))

        # Update text area placeholder
        current_name = self.snippets_data[self.active_snippet_idx]["name"] if self.snippets_data else "Snippet"
        if current_name in ("Code Snippet", "Snippet") or current_name.startswith("Snippet "):
            self.code_edit.setPlaceholderText("Paste your integration code snippet here (auto-detects language)...")
        else:
            self.code_edit.setPlaceholderText(f"Paste your {current_name} integration code snippet here")

    def _on_tab_renamed(self, idx: int, new_name: str):
        """Callback from in-place inline tab rename (no popups)."""
        if idx < 0 or idx >= len(self.snippets_data):
            return
        val = new_name.strip()
        if val:
            self.snippets_data[idx]["name"] = val
            self.snippets_data[idx]["user_renamed"] = True
            if 0 <= idx < len(self.tab_buttons_list):
                self.tab_buttons_list[idx].set_name(val)
        else:
            # Blank input resets to auto-detection
            self.snippets_data[idx]["user_renamed"] = False
            self._on_code_text_changed()


    def _delete_snippet_tab(self, idx: int):
        """Removes the snippet tab & code (prompts confirmation only if snippet contains code). Supports Ctrl+Z undo."""
        if idx < 0 or idx >= len(self.snippets_data):
            return

        snip = self.snippets_data[idx]
        snip_name = snip.get("name", "Snippet")
        code_content = snip["doc"].toPlainText().strip() if "doc" in snip and snip["doc"] else snip.get("code", "").strip()

        # Only prompt confirmation dialog if there is actual code to lose
        if code_content:
            dlg = ConfirmDeleteDialog(self.win, f"{snip_name} Snippet")
            if dlg.exec() != QDialog.Accepted:
                return

        # Save to history for Ctrl+Z undo
        self._deleted_tabs_history.append({
            "idx": idx,
            "data": snip,
        })

        # Remove snippet data
        self.snippets_data.pop(idx)

        # Handle active tab after deletion
        if not self.snippets_data:
            new_doc = self._create_snippet_doc("")
            self.snippets_data = [
                {"name": "Snippet", "code": "", "user_renamed": False, "doc": new_doc}
            ]
            self.active_snippet_idx = 0
        else:
            if idx == self.active_snippet_idx:
                self.active_snippet_idx = min(idx, len(self.snippets_data) - 1)
            elif idx < self.active_snippet_idx:
                self.active_snippet_idx -= 1

        self._switch_to_tab(self.active_snippet_idx)

    def _switch_to_tab(self, idx: int):
        if idx < 0 or idx >= len(self.snippets_data):
            return

        self.active_snippet_idx = idx
        snip = self.snippets_data[idx]

        if "doc" not in snip or snip["doc"] is None:
            snip["doc"] = self._create_snippet_doc(snip.get("code", ""))

        # Switch document without resetting undo stack
        self._block_auto_detect = True
        self.code_edit.setDocument(snip["doc"])
        self._block_auto_detect = False

        self._render_tabs()
        self.code_edit.setFocus()

    def _add_snippet_tab(self):
        # If single existing tab has generic name "Snippet", rename to "Snippet 1"
        if len(self.snippets_data) == 1 and not self.snippets_data[0].get("user_renamed", False):
            if self.snippets_data[0]["name"] == "Snippet":
                self.snippets_data[0]["name"] = "Snippet 1"

        num = len(self.snippets_data) + 1
        chosen = f"Snippet {num}"
        new_doc = self._create_snippet_doc("")

        self.snippets_data.append({
            "name": chosen,
            "code": "",
            "user_renamed": False,
            "doc": new_doc,
        })
        new_idx = len(self.snippets_data) - 1
        self._switch_to_tab(new_idx)
        QTimer.singleShot(25, lambda: self.tabs_scroll.ensure_tab_visible(self.add_tab_btn))

    def _on_code_text_changed(self):
        if self._block_auto_detect or not self.snippets_data:
            return

        if self.active_snippet_idx < 0 or self.active_snippet_idx >= len(self.snippets_data):
            return

        current_snip = self.snippets_data[self.active_snippet_idx]
        current_code = self.code_edit.toPlainText()
        current_snip["code"] = current_code

        # If user explicitly renamed this tab, do not auto-override
        if current_snip.get("user_renamed", False):
            return

        code_text = current_code.strip()
        detected = detect_code_language(code_text) if code_text else None
        target_name = detected if detected else self._default_snippet_name(self.active_snippet_idx)

        # Tab name changes to detected language on add, and quickly changes back to generic snippet on remove
        if current_snip["name"] != target_name:
            current_snip["name"] = target_name
            if 0 <= self.active_snippet_idx < len(self.tab_buttons_list):
                self.tab_buttons_list[self.active_snippet_idx].set_name(target_name)

            # Update text area placeholder
            if target_name in ("Snippet", "Code Snippet") or target_name.startswith("Snippet "):
                self.code_edit.setPlaceholderText("Paste your integration code snippet here (auto-detects language)...")
            else:
                self.code_edit.setPlaceholderText(f"Paste your {target_name} integration code snippet here")

    def _handle_undo(self):
        """Handles Ctrl+Z undo for both editor text changes and deleted tab recovery."""
        if self.code_edit.hasFocus():
            if self.code_edit.document().availableUndoSteps() > 0:
                self.code_edit.undo()
                return

        # Restore deleted tab if available
        if self._deleted_tabs_history:
            restored = self._deleted_tabs_history.pop()
            target_idx = min(restored["idx"], len(self.snippets_data))
            self.snippets_data.insert(target_idx, restored["data"])
            self._switch_to_tab(target_idx)
            return

        # Fallback undo in editor
        if self.code_edit.document().availableUndoSteps() > 0:
            self.code_edit.undo()

    def _handle_redo(self):
        """Handles Ctrl+Y redo for editor text changes."""
        if self.code_edit.document().availableRedoSteps() > 0:
            self.code_edit.redo()

    def edit(self, model_data: Optional[Dict] = None):
        self.editing = model_data
        self.title_lbl.setText("Edit AI Model" if model_data else "Add AI Model")
        self._deleted_tabs_history.clear()

        if model_data is not None:
            self.name_edit.setText(model_data.get("name", ""))
            self._pick_color(model_data.get("color", BADGE_COLORS[0]))

            snippets_dict = model_data.get("snippets", {})
            self.snippets_data = []
            for lang, code in snippets_dict.items():
                doc = self._create_snippet_doc(code)
                self.snippets_data.append({
                    "name": lang,
                    "code": code,
                    "user_renamed": True,
                    "doc": doc,
                })

            if not self.snippets_data:
                doc = self._create_snippet_doc("")
                self.snippets_data = [{"name": "Snippet", "code": "", "user_renamed": False, "doc": doc}]
        else:
            self.name_edit.clear()
            self._pick_color(BADGE_COLORS[0])
            doc = self._create_snippet_doc("")
            self.snippets_data = [
                {"name": "Snippet", "code": "", "user_renamed": False, "doc": doc}
            ]

        self.active_snippet_idx = 0
        self._switch_to_tab(0)
        self.hint.hide()
        self.name_edit.setFocus()

    def _pick_color(self, c: str):
        self.selected_color = c
        if hasattr(self, "color_bar"):
            self.color_bar.set_color(c)

    def _on_color_changed(self, c: str):
        self.selected_color = c

    def _save(self):
        name = self.name_edit.text().strip()

        if not name:
            self.hint.setText("Please enter a Model Name.")
            self.hint.show()
            return

        # Prepare snippets dict with latest text from documents
        snippets_dict = {}
        for s in self.snippets_data:
            s_name = s["name"].strip() or "Snippet"
            code_text = s["doc"].toPlainText() if "doc" in s and s["doc"] else s.get("code", "")
            snippets_dict[s_name] = code_text.strip()

        now_ms = int(time.time() * 1000)
        if self.editing is not None:
            self.editing["name"] = name
            self.editing["color"] = self.selected_color
            self.editing["snippets"] = snippets_dict
            self.editing["updatedAt"] = now_ms
        else:
            new_id = f"model_{now_ms}_{uuid.uuid4().hex[:5]}"
            self.win.ai_models.insert(0, {
                "id": new_id,
                "name": name,
                "color": self.selected_color,
                "snippets": snippets_dict,
                "createdAt": now_ms,
                "updatedAt": now_ms
            })

        self.win.save_ai_models()
        self.win.show_list_view()

