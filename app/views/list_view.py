import os

from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QSize,
    Qt,
    QTimer,
)
from PySide6.QtGui import QAction, QColor, QIcon, QPainter
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.components.buttons.icon_button import icon_button
from app.components.buttons.nav_tab import NavTabButton
from app.components.cards.ai_model_card import AIModelCard
from app.components.cards.card_drag_controller import CardDragController
from app.components.cards.command_card import CommandCard
from app.components.cards.key_card import KeyCard
from app.components.cards.link_card import LinkCard
from app.components.cards.prompt_card import PromptCard
from app.components.navigation.vscode_tab_scroll import VSCodeTabScrollArea
from app.config.paths import ASSETS_DIR
from app.config.sections import SECTION_DEFINITIONS
from app.config.theme import ACCENT, BG_MAIN, TEXT_DIM, TEXT_MAIN
from app.core.icons import render_padded_pixmap, render_pixmap
from app.sections.registry import SECTION_REGISTRY
from app.views.controllers.search_controller import SearchController


class HeaderActionButton(QToolButton):
    """Borderless header action button with dim normal tint and white hover state."""
    def __init__(self, icon_name: str, tooltip: str = "", parent=None):
        super().__init__(parent)
        self.icon_name = icon_name
        self.setFixedSize(28, 28)
        self.setCursor(Qt.PointingHandCursor)
        self._hovered = False

        self._pm_dim = render_pixmap(self.icon_name, (15, 15), color=TEXT_DIM)
        self._pm_white = render_pixmap(self.icon_name, (15, 15), color="#ffffff")

        self.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: none;
                border-radius: 6px;
                padding: 0px;
            }
            QToolButton:hover {
                color: #ffffff;
                background: #1f2533;
            }
            QToolButton:pressed {
                background: #2a3245;
            }
        """)

        if tooltip:
            self.setToolTip(tooltip)

    def setToolTip(self, text: str):
        from app.components.labels.animated_tooltip import set_tooltip
        set_tooltip(self, text, placement="bottom")
        self._update_icon()

    def enterEvent(self, event):
        self._hovered = True
        self._update_icon()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self._update_icon()
        super().leaveEvent(event)

    def _update_icon(self):
        pm = self._pm_white if self._hovered else self._pm_dim
        if pm and not pm.isNull():
            self.setIcon(QIcon(pm))
            self.setIconSize(QSize(15, 15))


# Backwards compatibility alias
HeaderSearchButton = HeaderActionButton


class ListView(QWidget):
    """Primary list view with modular search controller and smooth transitions."""
    def __init__(self, win):
        super().__init__()
        self.win = win
        self.expanded_card = None
        self.active_tab = "key-round"
        self._section_animating = False
        self._section_animation = None
        self._search_rebuild_timer = QTimer(self)
        self._search_rebuild_timer.setSingleShot(True)
        self._search_rebuild_timer.setInterval(60)
        self._search_rebuild_timer.timeout.connect(self.rebuild)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 10, 12)
        root.setSpacing(10)

        # 1. Top Navigation Bar (Tabs + Settings)
        self.top_bar = QWidget()
        self.top_lay = QHBoxLayout(self.top_bar)
        self.top_lay.setContentsMargins(0, 0, 6, 2)
        self.top_lay.setSpacing(6)

        # VS Code style horizontal tab scroll for section buttons
        self.nav_scroll = VSCodeTabScrollArea(self)
        self.nav_scroll.setFixedHeight(38)

        self.tabs_container = QWidget()
        self.tabs_container.setStyleSheet("background: transparent;")
        self.tabs_container_lay = QHBoxLayout(self.tabs_container)
        self.tabs_container_lay.setContentsMargins(0, 0, 0, 0)
        self.tabs_container_lay.setSpacing(10)
        self.tabs_container_lay.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.nav_scroll.setWidget(self.tabs_container)

        self.top_lay.addWidget(self.nav_scroll, 1)

        self._reorder_mode = False
        self.tab_buttons = {}
        self.settings_btn = NavTabButton("settings", is_active=False, tooltip="Settings", is_fixed=True)
        self.settings_btn.clicked.connect(self._on_settings_clicked)
        self.top_lay.addWidget(self.settings_btn, 0, Qt.AlignVCenter)

        self.refresh_nav_tabs()
        root.addWidget(self.top_bar)


        # 2. Section Header: Title & Count | Underline Search | Add Button
        self.header_widget = QWidget()
        header = QHBoxLayout(self.header_widget)
        header.setContentsMargins(2, 2, 6, 0)
        header.setSpacing(8)

        # Left: Section Title + Count Badge
        self.title_lbl = QLabel("API Keys")
        self.title_lbl.setProperty("cls", "h2")
        self.count = QLabel("0")
        self.count.setObjectName("CountBadge")
        self.count.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        header.addWidget(self.title_lbl, 0, Qt.AlignVCenter)
        header.addWidget(self.count, 0, Qt.AlignVCenter)
        header.addStretch(1)

        # Minimalist Underline Search LineEdit
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search keys")
        self.search.setFixedHeight(28)
        self.search.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.search.hide()
        self.search.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: none;
                border-bottom: 2px solid #ff773d;
                border-radius: 0px;
                padding: 0px 4px 2px 2px;
                color: {TEXT_MAIN};
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-bottom: 2px solid #ff8c5a;
            }}
        """)

        # Custom clear action inside the search bar using x.svg (only visible when text is entered)
        self.clear_action = QAction(self)
        pm_x = render_pixmap("x", (12, 12), color="#8f97a8")
        if pm_x:
            self.clear_action.setIcon(QIcon(pm_x))
            self.clear_action.setToolTip("Clear search")
        self.clear_action.setVisible(False)
        self.search.addAction(self.clear_action, QLineEdit.TrailingPosition)
        self.clear_action.triggered.connect(self._on_clear_search)
        self.search.textChanged.connect(self._on_search_text_changed)

        header.addWidget(self.search, 1, Qt.AlignVCenter)

        # Search Trigger / Close Button (shows 🔍, toggles search)
        self.search_btn = HeaderActionButton("search", tooltip="Search", parent=self)
        self.search_btn.setFixedSize(28, 28)
        header.addWidget(self.search_btn, 0, Qt.AlignVCenter)

        # Add New Item Button
        self.add_btn = HeaderActionButton("plus", tooltip="Add new item", parent=self)
        self.add_btn.setFixedSize(28, 28)
        self.add_btn.clicked.connect(self._on_add_clicked)
        header.addWidget(self.add_btn, 0, Qt.AlignVCenter)

        root.addWidget(self.header_widget)

        # 3. Dedicated Search Controller
        self.search_controller = SearchController(self)
        self.search_btn.clicked.connect(self._on_search_btn_clicked)

        # 4. Scrollable Cards Container
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setStyleSheet(f"QScrollArea {{ background-color: {BG_MAIN}; border: none; }}")

        self.body = QWidget()
        self.body.setAutoFillBackground(True)
        self.body.setStyleSheet(f"background-color: {BG_MAIN};")

        self.cards = QVBoxLayout(self.body)
        self.cards.setContentsMargins(0, 2, 6, 2)
        self.cards.setSpacing(8)
        self.cards.setAlignment(Qt.AlignTop)
        self.card_drag = None
        self.scroll.setWidget(self.body)
        root.addWidget(self.scroll, 1)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(event.rect(), QColor(BG_MAIN))
        p.end()

    def refresh_nav_tabs(self):
        """Rebuilds navigation tab buttons according to user-defined order and enabled sections."""
        # Clear container layout items
        while self.tabs_container_lay.count():
            item = self.tabs_container_lay.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        self.tab_buttons.clear()

        all_possible = ["key-round", "prompt", "ai_model", "link", "command"]
        order = list(self.win.settings.get("section_order", all_possible))
        for item in all_possible:
            if item not in order:
                order.append(item)

        enabled = set(self.win.settings.get("enabled_sections", all_possible))
        visible = [sid for sid in order if sid in enabled]
        if not visible:
            visible = [all_possible[0]]

        if self.active_tab not in visible:
            self.active_tab = visible[0]

        for sid in visible:
            sec_meta = SECTION_REGISTRY.get(sid, SECTION_REGISTRY["key-round"])
            btn = NavTabButton(
                sid,
                is_active=(sid == self.active_tab),
                tooltip=sec_meta.get("title", sid),
                is_fixed=False,
            )
            btn.clicked.connect(lambda _, tid=sid: self._on_tab_button_clicked(tid))
            btn.drag_moved.connect(self._on_tab_drag_moved)
            btn.drag_released.connect(self._on_tab_drag_released)
            self.tab_buttons[sid] = btn
            self.tabs_container_lay.addWidget(btn)

        self.tabs_container_lay.addStretch(1)
        self.settings_btn.set_active(False)

    def _rebuild_tab_layout_order(self):
        """Rearranges tab widgets in tabs_container_lay according to section_order without destroying them."""
        all_possible = ["key-round", "prompt", "ai_model", "link", "command"]
        order = list(self.win.settings.get("section_order", all_possible))
        enabled = set(self.win.settings.get("enabled_sections", all_possible))
        visible = [sid for sid in order if sid in enabled and sid in self.tab_buttons]

        # Re-insert into layout
        while self.tabs_container_lay.count():
            self.tabs_container_lay.takeAt(0)

        for sid in visible:
            self.tabs_container_lay.addWidget(self.tab_buttons[sid])

        self.tabs_container_lay.addStretch(1)

    def _on_tab_drag_moved(self, btn, dx: int):
        """Real-time tab slot swapping during hold-and-drag."""
        all_possible = ["key-round", "prompt", "ai_model", "link", "command"]
        order = list(self.win.settings.get("section_order", all_possible))
        enabled = set(self.win.settings.get("enabled_sections", order))
        current_visible = [sid for sid in order if sid in enabled and sid in self.tab_buttons]

        if btn.icon_name not in current_visible:
            return

        idx = current_visible.index(btn.icon_name)

        if dx > 18 and idx < len(current_visible) - 1:
            next_key = current_visible[idx + 1]
            pos1 = order.index(btn.icon_name)
            pos2 = order.index(next_key)
            order[pos1], order[pos2] = order[pos2], order[pos1]
            self.win.settings["section_order"] = order
            btn._drag_start_x += 38
            self._rebuild_tab_layout_order()

        elif dx < -18 and idx > 0:
            prev_key = current_visible[idx - 1]
            pos1 = order.index(btn.icon_name)
            pos2 = order.index(prev_key)
            order[pos1], order[pos2] = order[pos2], order[pos1]
            self.win.settings["section_order"] = order
            btn._drag_start_x -= 38
            self._rebuild_tab_layout_order()

    def _on_tab_drag_released(self, btn):
        """Persists tab order to DC_Settings.json on drag release."""
        self.win.save_settings()
        if hasattr(self.win, "settings_view") and self.win.settings_view:
            self.win.settings_view.refresh_nav_tabs()

    def _on_tab_button_clicked(self, tab_id: str):
        self.select_tab(tab_id)

    def _on_search_btn_clicked(self):
        self.search_controller.toggle()

    def _on_search_text_changed(self, text: str):
        self.clear_action.setVisible(bool(text.strip()))
        self._search_rebuild_timer.start()

    def _on_clear_search(self):
        self.search.clear()
        self.clear_action.setVisible(False)
        self.search.setFocus()

    @property
    def _search_open(self) -> bool:
        return self.search_controller.is_open

    def open_search(self):
        self.search_controller.open()

    def close_search(self):
        self.search_controller.close()

    def select_tab(self, tab_id: str, animate: bool = True):
        if tab_id not in self.tab_buttons:
            # If tab is disabled or missing, fallback to first available
            if self.tab_buttons:
                tab_id = next(iter(self.tab_buttons.keys()))
            else:
                return

        if tab_id == self.active_tab:
            for btn_id, btn in self.tab_buttons.items():
                btn.set_active(btn_id == tab_id)
            if tab_id in self.tab_buttons:
                self.nav_scroll.ensure_tab_visible(self.tab_buttons[tab_id])
            return

        def _apply_section(tid):
            self._section_animating = True
            self.active_tab = tid
            self.expanded_card = None

            for btn_id, btn in self.tab_buttons.items():
                btn.set_active(btn_id == tid)

            section = SECTION_REGISTRY.get(tid, SECTION_REGISTRY["key-round"])
            self.title_lbl.setText(section["title"])
            self.search.setPlaceholderText(
                section.get("search_placeholder", "Type to search")
            )
            if animate:
                self._animate_section_change()
            else:
                self.rebuild(animate_resize=False)
                self._section_animating = False
            if tid in self.tab_buttons:
                self.nav_scroll.ensure_tab_visible(self.tab_buttons[tid])

        if animate:
            self.search_controller.switch_section(tab_id, _apply_section)
        else:
            _apply_section(tab_id)


    def _animate_section_change(self):
        """Smoothly replace section cards without layout flicker or black glitches."""
        # Guard: don't stack effects/animations if this fires again mid-transition
        if self._section_animation is not None:
            self._section_animation.stop()
            try:
                self._section_animation.finished.disconnect()
            except (TypeError, RuntimeError):
                pass
            self._section_animation = None

        # Clear any stale effect before creating a new one
        if self.body.graphicsEffect() is not None:
            self.body.setGraphicsEffect(None)

        # Freeze repainting of body while tearing down/rebuilding cards
        self.body.setUpdatesEnabled(False)
        self.rebuild(animate_resize=True)
        self.body.setUpdatesEnabled(True)

        effect = QGraphicsOpacityEffect(self.body)
        self.body.setGraphicsEffect(effect)

        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(120)
        animation.setStartValue(0.8)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.OutCubic)

        def finish():
            self.body.setGraphicsEffect(None)
            self._section_animating = False
            self._section_animation = None

        animation.finished.connect(finish)
        self._section_animation = animation
        animation.start()

    def _on_settings_clicked(self):
        """Safely transitions to settings view."""
        if self.search_controller.is_open:
            self.search_controller.leave_list_view(on_finished=self.win.show_settings_view)
        else:
            self.win.show_settings_view()

    def _on_add_clicked(self):
        """Safely navigates to add form for the current section through SearchController."""
        def open_form():
            if self.active_tab == "key-round":
                self.win.show_add_view()
            elif self.active_tab == "prompt":
                self.win.show_add_prompt_view()
            elif self.active_tab in ("ai_model", "sparkles-2"):
                self.win.show_add_ai_model_view()
            elif self.active_tab == "link":
                self.win.show_add_link_view()
            else:
                self.win.show_add_command_view()

        if self.search_controller.is_open:
            self.search_controller.leave_list_view(on_finished=open_form)
        else:
            open_form()

    def _empty_widget(self, searching: bool = False) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setAlignment(Qt.AlignCenter)
        v.setContentsMargins(0, 8, 0, 8)
        v.setSpacing(6)

        if searching:
            icon_lbl = QLabel()
            icon_lbl.setAlignment(Qt.AlignCenter)
            search_pm = render_pixmap("search", (36, 36), TEXT_DIM)
            if search_pm:
                icon_lbl.setPixmap(search_pm)
            else:
                icon_lbl.setText("🔍")
                icon_lbl.setStyleSheet("font-size: 26px;")
            v.addWidget(icon_lbl)
            v.addSpacing(4)

            t = QLabel("No results found")
            t.setAlignment(Qt.AlignCenter)
            t.setStyleSheet(f"color: {TEXT_MAIN}; font-size: 15px; font-weight: 700;")
            v.addWidget(t)

            s = QLabel("Try searching with a different term.")
            s.setAlignment(Qt.AlignCenter)
            s.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px;")
            v.addWidget(s)
            return w

        meta = SECTION_REGISTRY.get(self.active_tab, SECTION_REGISTRY["key-round"])
        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignCenter)

        if self.active_tab == "key-round":
            key_pm = render_pixmap("key-round", (38, 38), TEXT_DIM)
            if key_pm:
                icon_lbl.setPixmap(key_pm)
            else:
                icon_lbl.setText("🔑")
                icon_lbl.setStyleSheet("font-size: 26px;")
        elif self.active_tab == "prompt":
            pm_prompt = render_pixmap("prompt", (38, 38), TEXT_DIM)
            if pm_prompt:
                icon_lbl.setPixmap(pm_prompt)
            else:
                icon_lbl.setText("💬")
                icon_lbl.setStyleSheet("font-size: 28px;")
        elif self.active_tab in ("ai_model", "sparkles-2"):
            pm_ai = render_pixmap("ai_model", (38, 38), TEXT_DIM)
            if pm_ai is None or pm_ai.isNull():
                pm_ai = render_pixmap("sparkles-2", (38, 38), TEXT_DIM)
            if pm_ai:
                icon_lbl.setPixmap(pm_ai)
            else:
                icon_lbl.setText("🧠")
                icon_lbl.setStyleSheet("font-size: 28px;")
        elif self.active_tab == "link":
            link_pm = render_pixmap("link", (38, 38), TEXT_DIM)
            if link_pm:
                icon_lbl.setPixmap(link_pm)
            else:
                icon_lbl.setText("🔗")
                icon_lbl.setStyleSheet("font-size: 28px;")
        else:
            cmd_svg_path = os.path.join(ASSETS_DIR, "command.svg")
            cmd_pm = render_pixmap("command", (38, 38), TEXT_DIM) if os.path.exists(cmd_svg_path) else None
            if cmd_pm and not cmd_pm.isNull():
                icon_lbl.setPixmap(cmd_pm)
            else:
                icon_lbl.setText(">_")
                icon_lbl.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {TEXT_DIM}; font-family: monospace;")

        v.addWidget(icon_lbl)
        v.addSpacing(4)

        t = QLabel(meta["empty_title"])
        t.setAlignment(Qt.AlignCenter)
        t.setStyleSheet(f"color: {TEXT_MAIN}; font-size: 15px; font-weight: 700;")
        v.addWidget(t)

        s = QLabel(meta["empty_subtitle"])
        s.setAlignment(Qt.AlignCenter)
        s.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px;")
        v.addWidget(s)
        v.addSpacing(8)

        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignCenter)
        # Use QToolButton for better icon+text horizontal alignment
        add_btn = QToolButton()
        add_btn.setText(meta["add_btn_text"])
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        plus_pm = render_pixmap("plus", (12, 12), color="#0b0d10")
        if plus_pm and not plus_pm.isNull():
            add_btn.setIcon(QIcon(plus_pm))
            add_btn.setIconSize(QSize(12, 12))

        add_btn.setStyleSheet(f"""
            QToolButton {{
                background: {ACCENT};
                color: #0b0d10;
                font-weight: 700;
                font-size: 13px;
                border-radius: 8px;
                padding: 8px 20px;
                border: none;
            }}
            QToolButton:hover {{ background: #d5693c; }}
            QToolButton:pressed {{ background: #b85a30; }}
        """)
        add_btn.clicked.connect(self._on_add_clicked)
        btn_row.addWidget(add_btn)
        v.addLayout(btn_row)

        return w

    def _add_reorderable_card(self, card, data, save_callback) -> None:
        """Add one card and attach the shared reorder controller (active when not filtering by search)."""
        self.cards.addWidget(card)
        if not self.search.text().strip():
            if self.card_drag is None:
                self.card_drag = CardDragController(
                    parent=self,
                    layout=self.cards,
                    data_provider=lambda data=data: data,
                    save_callback=save_callback,
                    scroll_area=self.scroll,
                )
            self.card_drag.attach(card)

    def rebuild(self, animate_resize: bool = True):
        if hasattr(self, "_search_rebuild_timer"):
            self._search_rebuild_timer.stop()

        if self.card_drag is not None:
            self.card_drag.cancel()
            self.card_drag = None

        self.expanded_card = None

        # Block paint while tearing down old cards so nothing paints mid-deletion
        self.body.setUpdatesEnabled(False)
        while self.cards.count():
            item = self.cards.takeAt(0)
            w = item.widget()
            if w is not None:
                w.hide()
                w.setParent(None)
                w.deleteLater()
        self.body.setUpdatesEnabled(True)

        text = self.search.text().strip().lower()

        if self.active_tab == "key-round":
            items = ([k for k in self.win.keys if text in k["label"].lower()]
                     if text else self.win.keys)
            self.count.setText(str(len(self.win.keys)))
            self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded if len(items) > 3 else Qt.ScrollBarAlwaysOff)

            if not items:
                self.cards.addStretch(1)
                self.cards.addWidget(self._empty_widget(searching=bool(text)))
                self.cards.addStretch(1)
                self.win.update_size_for_count(0, is_prompt=False, animate=animate_resize)
                return

            self.win.update_size_for_count(len(items), is_prompt=False, animate=animate_resize)
            for k in items:
                card = KeyCard(
                    k, self.win,
                    on_copy=self.win.copy_key,
                    on_edit=self.win.show_edit_view,
                    on_delete=self.win.confirm_delete_key,
                    on_toggle=self.toggle_card,
                )
                self._add_reorderable_card(card, self.win.keys, self.win.save_keys)
            if len(items) < 3:
                self.cards.addStretch(1)

        elif self.active_tab == "prompt":
            items = ([p for p in self.win.prompts if (text in (p.get("name") or p.get("title", "")).lower() or text in (p.get("prompt") or p.get("content", "")).lower())]
                     if text else self.win.prompts)
            self.count.setText(str(len(self.win.prompts)))
            self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded if len(items) > 3 else Qt.ScrollBarAlwaysOff)

            if not items:
                self.cards.addStretch(1)
                self.cards.addWidget(self._empty_widget(searching=bool(text)))
                self.cards.addStretch(1)
                self.win.update_size_for_count(0, is_prompt=True, animate=animate_resize)
                return

            self.win.update_size_for_count(len(items), is_prompt=True, animate=animate_resize)
            for p in items:
                card = PromptCard(
                    p, self.win,
                    on_copy=self.win.copy_prompt,
                    on_edit=self.win.show_edit_prompt_view,
                    on_delete=self.win.confirm_delete_prompt,
                    on_toggle=self.toggle_card,
                )
                self._add_reorderable_card(card, self.win.prompts, self.win.save_prompts)
            if len(items) < 3:
                self.cards.addStretch(1)

        elif self.active_tab in ("ai_model", "sparkles-2"):
            def match_model(m):
                if not text:
                    return True
                if text in m.get("name", "").lower():
                    return True
                if text in m.get("provider", "").lower():
                    return True
                for s_code in m.get("snippets", {}).values():
                    if text in s_code.lower():
                        return True
                return False

            items = [m for m in self.win.ai_models if match_model(m)]
            self.count.setText(str(len(self.win.ai_models)))
            self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded if len(items) > 3 else Qt.ScrollBarAlwaysOff)

            if not items:
                self.cards.addStretch(1)
                self.cards.addWidget(self._empty_widget(searching=bool(text)))
                self.cards.addStretch(1)
                self.win.update_size_for_count(0, is_prompt=True, animate=animate_resize)
                return

            self.win.update_size_for_count(len(items), is_prompt=True, animate=animate_resize)
            for m in items:
                card = AIModelCard(
                    m, self.win,
                    on_copy=self.win.copy_ai_model,
                    on_edit=self.win.show_edit_ai_model_view,
                    on_delete=self.win.confirm_delete_ai_model,
                )
                self._add_reorderable_card(card, self.win.ai_models, self.win.save_ai_models)
            if len(items) < 3:
                self.cards.addStretch(1)

        elif self.active_tab == "link":
            items = ([l for l in self.win.links if (text in l.get("title", "").lower() or text in l.get("url", "").lower())]
                     if text else self.win.links)
            self.count.setText(str(len(self.win.links)))
            self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded if len(items) > 3 else Qt.ScrollBarAlwaysOff)

            if not items:
                self.cards.addStretch(1)
                self.cards.addWidget(self._empty_widget(searching=bool(text)))
                self.cards.addStretch(1)
                self.win.update_size_for_count(0, is_prompt=False, animate=animate_resize)
                return

            self.win.update_size_for_count(len(items), is_prompt=False, animate=animate_resize)
            for l in items:
                card = LinkCard(
                    l, self.win,
                    on_copy=self.win.copy_link,
                    on_edit=self.win.show_edit_link_view,
                    on_delete=self.win.confirm_delete_link,
                    on_open=self.win.open_link,
                )
                self._add_reorderable_card(card, self.win.links, self.win.save_links)
            if len(items) < 3:
                self.cards.addStretch(1)

        else:  # "command"
            items = ([c for c in self.win.commands if (text in c.get("title", "").lower() or text in c.get("command", "").lower())]
                     if text else self.win.commands)
            self.count.setText(str(len(self.win.commands)))
            self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded if len(items) > 3 else Qt.ScrollBarAlwaysOff)

            if not items:
                self.cards.addStretch(1)
                self.cards.addWidget(self._empty_widget(searching=bool(text)))
                self.cards.addStretch(1)
                self.win.update_size_for_count(0, is_prompt=True, animate=animate_resize)
                return

            self.win.update_size_for_count(len(items), is_prompt=True, animate=animate_resize)
            for c in items:
                card = CommandCard(
                    c, self.win,
                    on_copy=self.win.copy_command,
                    on_edit=self.win.show_edit_command_view,
                    on_delete=self.win.confirm_delete_command,
                )
                self._add_reorderable_card(card, self.win.commands, self.win.save_commands)
            if len(items) < 3:
                self.cards.addStretch(1)

    def toggle_card(self, card):
        if self.expanded_card is card:
            card.set_expanded(False)
            self.expanded_card = None
            return
        if self.expanded_card is not None:
            self.expanded_card.set_expanded(False)
        card.set_expanded(True)
        self.expanded_card = card
