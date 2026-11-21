import datetime

from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, QRectF, QSize, Qt, QUrl
from PySide6.QtGui import QBrush, QColor, QDesktopServices, QIcon, QPainter
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app import __version__
from app.components.buttons.nav_tab import NavTabButton
from app.components.navigation.module_selector import (
    StartupModuleSelector,
    VisibleModulesSelector,
)
from app.components.labels.animated_tooltip import attach_tooltip, set_tooltip
from app.config.sections import SECTION_DEFINITIONS
from app.config.theme import ACCENT, CARD_BORDER, FONT_MONO, TEXT_DIM, TEXT_MAIN, font_css
from app.core.data_manager import DataError
from app.core.export_import import (
    MAX_IMPORT_BYTES,
    ExportError,
    WrongPassphrase,
    is_encrypted_bundle,
    read_bundle,
)
from app.core.icons import render_pixmap
from app.sections.registry import SECTION_REGISTRY


class ToggleSwitch(QWidget):
    """Clean iOS/macOS-style switch button without borders or neon glow."""
    def __init__(self, checked=False, on_toggle=None, parent=None):
        super().__init__(parent)
        self.setFixedSize(36, 20)
        self.setCursor(Qt.PointingHandCursor)
        self._checked = checked
        self._on_toggle = on_toggle
        self._thumb_pos = 18.0 if checked else 2.0

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            self._animate()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._checked = not self._checked
            self._animate()
            if self._on_toggle:
                self._on_toggle(self._checked)
        super().mousePressEvent(event)

    def _animate(self):
        self._anim = QPropertyAnimation(self, b"thumb_pos")
        self._anim.setDuration(140)
        self._anim.setStartValue(self._thumb_pos)
        self._anim.setEndValue(18.0 if self._checked else 2.0)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.start()

    def get_thumb_pos(self):
        return self._thumb_pos

    def set_thumb_pos(self, pos):
        self._thumb_pos = pos
        self.update()

    thumb_pos = Property(float, get_thumb_pos, set_thumb_pos)

    def paintEvent(self, event):
        p = QPainter(self)
        if not p.isActive():
            return
        p.setRenderHint(QPainter.Antialiasing)

        w, h = float(self.width()), float(self.height())
        r = h / 2.0

        bg_color = QColor("#ff8c5a") if self._checked else QColor("#2a2f3d")
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(bg_color))
        p.drawRoundedRect(QRectF(0, 0, w, h), r, r)

        p.setBrush(QBrush(QColor("#ffffff")))
        p.drawEllipse(QRectF(self._thumb_pos, 2.0, 16.0, 16.0))
        p.end()


class AboutSocialButton(QToolButton):
    """Social icon button for GitHub and LinkedIn in the About section."""
    def __init__(self, icon_name: str, url: str, tooltip: str, parent=None):
        super().__init__(parent)
        self.url = url
        self.setFixedSize(28, 28)
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setAutoRaise(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)

        self._pm_normal = render_pixmap(icon_name, (15, 15), color="#94a3b8")
        self._pm_hover = render_pixmap(icon_name, (15, 15), color="#ffffff")

        self.setIconSize(QSize(15, 15))
        attach_tooltip(self, tooltip, placement="top")
        self._update_style(hovered=False)
        self.clicked.connect(self._open)

    def _update_style(self, hovered: bool):
        pm = self._pm_hover if hovered else self._pm_normal
        if pm:
            self.setIcon(QIcon(pm))

        if hovered:
            self.setStyleSheet("""
                QToolButton {
                    background-color: #222a3b;
                    border: 1px solid #3b4862;
                    border-radius: 6px;
                    padding: 0px;
                }
            """)
        else:
            self.setStyleSheet("""
                QToolButton {
                    background-color: #171d2b;
                    border: 1px solid #252f42;
                    border-radius: 6px;
                    padding: 0px;
                }
            """)

    def enterEvent(self, event):
        self._update_style(hovered=True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._update_style(hovered=False)
        super().leaveEvent(event)

    def _open(self):
        url_str = self.url.strip()
        if not url_str.startswith(("http://", "https://")):
            url_str = "https://" + url_str
        QDesktopServices.openUrl(QUrl(url_str))



class SettingsView(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 10, 12)
        root.setSpacing(10)

        # Top navigation bar
        self.top_bar = QWidget()
        self.top_lay = QHBoxLayout(self.top_bar)
        self.top_lay.setContentsMargins(0, 0, 6, 2)
        self.top_lay.setSpacing(10)

        self.tab_buttons = {}
        self.settings_btn = NavTabButton("settings", is_active=True, tooltip="Settings", is_fixed=True)
        self.refresh_nav_tabs()
        root.addWidget(self.top_bar)

        title_lbl = QLabel("Settings")
        title_lbl.setStyleSheet(font_css("title-lg", color=TEXT_MAIN, extra="margin-left: 2px; margin-top: 2px; margin-bottom: 2px;"))
        root.addWidget(title_lbl)

        # Scrollable Settings Container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        body = QWidget()
        body.setStyleSheet("background: transparent;")
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(0, 2, 6, 2)
        body_lay.setSpacing(8)
        body_lay.setAlignment(Qt.AlignTop)

        # 1. Section: General
        sec_gen = QLabel("General")
        sec_gen.setStyleSheet(font_css("eyebrow", color="#7a8292", extra="margin-top: 2px; margin-left: 2px;"))
        body_lay.addWidget(sec_gen)

        # 1. Always on Top Card
        card_top = QFrame()
        card_top.setObjectName("Card")
        card_top.setFixedHeight(66)
        lay_top = QVBoxLayout(card_top)
        lay_top.setContentsMargins(14, 9, 14, 9)
        lay_top.setSpacing(4)

        row_top = QHBoxLayout()
        row_top.setContentsMargins(0, 0, 0, 0)
        row_top.setSpacing(8)
        lbl1 = QLabel("Always on Top")
        lbl1.setStyleSheet(font_css("body-strong", color="#ffffff"))
        row_top.addWidget(lbl1, 0, Qt.AlignVCenter)
        row_top.addStretch(1)

        self.sw_top = ToggleSwitch(
            checked=self.win.settings.get("always_on_top", False),
            on_toggle=self._on_toggle_top
        )
        row_top.addWidget(self.sw_top, 0, Qt.AlignVCenter)
        lay_top.addLayout(row_top)

        sub1 = QLabel("Keep DizoClip pinned above all other windows")
        sub1.setStyleSheet(font_css("subtext", color="#7a8292"))
        sub1.setWordWrap(True)
        lay_top.addWidget(sub1)
        body_lay.addWidget(card_top)

        # 2. Confirm Before Delete Card
        card_del = QFrame()
        card_del.setObjectName("Card")
        card_del.setFixedHeight(66)
        lay_del = QVBoxLayout(card_del)
        lay_del.setContentsMargins(14, 9, 14, 9)
        lay_del.setSpacing(4)

        row_del = QHBoxLayout()
        row_del.setContentsMargins(0, 0, 0, 0)
        row_del.setSpacing(8)
        lbl2 = QLabel("Confirm Before Delete")
        lbl2.setStyleSheet(font_css("body-strong", color="#ffffff"))
        row_del.addWidget(lbl2, 0, Qt.AlignVCenter)
        row_del.addStretch(1)

        self.sw_del = ToggleSwitch(
            checked=self.win.settings.get("confirm_delete", True),
            on_toggle=self._on_toggle_del
        )
        row_del.addWidget(self.sw_del, 0, Qt.AlignVCenter)
        lay_del.addLayout(row_del)

        sub2 = QLabel("Ask for confirmation before deleting any item")
        sub2.setStyleSheet(font_css("subtext", color="#7a8292"))
        sub2.setWordWrap(True)
        lay_del.addWidget(sub2)
        body_lay.addWidget(card_del)

        card_clip, self.sw_clip = self._toggle_card(
            "Auto-Clear Clipboard",
            "Clear copied API keys after 30 seconds",
            self.win.settings.get("auto_clear_clipboard", True),
            self._on_toggle_clip,
        )
        body_lay.addWidget(card_clip)

        card_enc, self.sw_enc = self._toggle_card(
            "Encrypt All Data",
            "Also protect prompts, commands and snippets on disk",
            self.win.settings.get("encrypt_all_data", True),
            self._on_toggle_encrypt,
        )
        body_lay.addWidget(card_enc)

        # 2. Section: Modules
        sec_mod = QLabel("Modules")
        sec_mod.setStyleSheet(font_css("eyebrow", color="#7a8292", extra="margin-top: 6px; margin-left: 2px;"))
        body_lay.addWidget(sec_mod)

        # 3. Startup Module Card
        card_mod = QFrame()
        card_mod.setObjectName("Card")
        card_mod.setFixedHeight(66)
        lay_mod = QVBoxLayout(card_mod)
        lay_mod.setContentsMargins(14, 9, 14, 9)
        lay_mod.setSpacing(4)

        row_mod = QHBoxLayout()
        row_mod.setContentsMargins(0, 0, 0, 0)
        row_mod.setSpacing(8)
        lbl3 = QLabel("Startup Module")
        lbl3.setStyleSheet(font_css("body-strong", color="#ffffff"))
        row_mod.addWidget(lbl3, 0, Qt.AlignVCenter)
        row_mod.addStretch(1)

        self.module_selector = StartupModuleSelector(
            win=self.win,
            on_changed=self._on_module_changed
        )
        row_mod.addWidget(self.module_selector, 0, Qt.AlignVCenter)
        lay_mod.addLayout(row_mod)

        sub3 = QLabel("Choose which module opens when DizoClip starts")
        sub3.setStyleSheet(font_css("subtext", color="#7a8292"))
        sub3.setWordWrap(True)
        lay_mod.addWidget(sub3)
        body_lay.addWidget(card_mod)

        # 4. Visible Modules Card (Dropdown Selector with Checklist)
        card_vis = QFrame()
        card_vis.setObjectName("Card")
        card_vis.setFixedHeight(66)
        lay_vis = QVBoxLayout(card_vis)
        lay_vis.setContentsMargins(14, 9, 14, 9)
        lay_vis.setSpacing(4)

        row_vis = QHBoxLayout()
        row_vis.setContentsMargins(0, 0, 0, 0)
        row_vis.setSpacing(8)
        lbl4 = QLabel("Visible Modules")
        lbl4.setStyleSheet(font_css("body-strong", color="#ffffff"))
        row_vis.addWidget(lbl4, 0, Qt.AlignVCenter)
        row_vis.addStretch(1)

        self.visible_modules_selector = VisibleModulesSelector(
            win=self.win,
            on_changed=self._on_visible_modules_changed
        )
        row_vis.addWidget(self.visible_modules_selector, 0, Qt.AlignVCenter)
        lay_vis.addLayout(row_vis)

        sub4 = QLabel("Choose which sections appear in the navigation bar")
        sub4.setStyleSheet(font_css("subtext", color="#7a8292"))
        sub4.setWordWrap(True)
        lay_vis.addWidget(sub4)
        body_lay.addWidget(card_vis)

        # 3. Section: Interaction
        sec_interaction = QLabel("Interaction")
        sec_interaction.setStyleSheet(font_css("eyebrow", color="#7a8292", extra="margin-top: 6px; margin-left: 2px;"))
        body_lay.addWidget(sec_interaction)

        # Interaction Guide Card (Module Reorder, Card Reorder & Link Interaction)
        card_interaction = QFrame()
        card_interaction.setObjectName("Card")
        card_interaction.setFixedHeight(215)
        lay_inter = QVBoxLayout(card_interaction)
        lay_inter.setContentsMargins(14, 12, 14, 12)
        lay_inter.setSpacing(4)

        # 01 · Reorder modules
        row_reorder = QHBoxLayout()
        row_reorder.setContentsMargins(0, 0, 0, 0)
        row_reorder.setSpacing(6)
        lbl_reorder = QLabel("01 · Reorder modules")
        lbl_reorder.setStyleSheet(font_css("body-strong", color="#ffffff"))
        row_reorder.addWidget(lbl_reorder)

        ico_reorder = QLabel()
        pm_reorder = render_pixmap("arrow-left-right", (13, 13), color="#7a8292")
        if pm_reorder:
            ico_reorder.setPixmap(pm_reorder)
        row_reorder.addWidget(ico_reorder, 0, Qt.AlignVCenter)
        row_reorder.addStretch(1)
        lay_inter.addLayout(row_reorder)

        sub_reorder = QLabel("Hold and drag any module tab at the top to reorder it. Release to save its position.")
        sub_reorder.setStyleSheet(font_css("subtext", color="#7a8292"))
        sub_reorder.setWordWrap(True)
        lay_inter.addWidget(sub_reorder)

        # Subtle divider 1
        lay_inter.addSpacing(3)
        div_inter1 = QFrame()
        div_inter1.setFixedHeight(1)
        div_inter1.setStyleSheet("background-color: #1e2433;")
        lay_inter.addWidget(div_inter1)
        lay_inter.addSpacing(3)

        # 02 · Reorder cards
        row_cards = QHBoxLayout()
        row_cards.setContentsMargins(0, 0, 0, 0)
        row_cards.setSpacing(6)
        lbl_cards = QLabel("02 · Reorder cards")
        lbl_cards.setStyleSheet(font_css("body-strong", color="#ffffff"))
        row_cards.addWidget(lbl_cards)

        ico_cards = QLabel()
        pm_cards = render_pixmap("chevrons-up-down", (12, 12), color="#7a8292")
        if pm_cards:
            ico_cards.setPixmap(pm_cards)
        row_cards.addWidget(ico_cards, 0, Qt.AlignVCenter)
        row_cards.addStretch(1)
        lay_inter.addLayout(row_cards)

        sub_cards = QLabel("Hold and drag any card within a module to rearrange your items. Release to save your custom order.")
        sub_cards.setStyleSheet(font_css("subtext", color="#7a8292"))
        sub_cards.setWordWrap(True)
        lay_inter.addWidget(sub_cards)

        # Subtle divider 2
        lay_inter.addSpacing(3)
        div_inter2 = QFrame()
        div_inter2.setFixedHeight(1)
        div_inter2.setStyleSheet("background-color: #1e2433;")
        lay_inter.addWidget(div_inter2)
        lay_inter.addSpacing(3)

        # 03 · Open links
        row_links = QHBoxLayout()
        row_links.setContentsMargins(0, 0, 0, 0)
        row_links.setSpacing(6)
        lbl_links = QLabel("03 · Open links")
        lbl_links.setStyleSheet(font_css("body-strong", color="#ffffff"))
        row_links.addWidget(lbl_links)

        ico_links = QLabel()
        pm_links = render_pixmap("square-arrow-out-up-right", (12, 12), color="#7a8292")
        if pm_links:
            ico_links.setPixmap(pm_links)
        row_links.addWidget(ico_links, 0, Qt.AlignVCenter)
        row_links.addStretch(1)
        lay_inter.addLayout(row_links)

        sub_links = QLabel("Hover over a link to preview it. Click to open it in your browser, or click Copy to copy the link.")
        sub_links.setStyleSheet(font_css("subtext", color="#7a8292"))
        sub_links.setWordWrap(True)
        lay_inter.addWidget(sub_links)

        body_lay.addWidget(card_interaction)

        # 4. Section: Data
        sec_data = QLabel("Data")
        sec_data.setStyleSheet(font_css("eyebrow", color="#7a8292", extra="margin-top: 6px; margin-left: 2px;"))
        body_lay.addWidget(sec_data)
        body_lay.addWidget(self._action_card(
            "Restore from Backup", "Roll a data file back to an earlier backup",
            "Restore", self._on_restore_clicked))
        body_lay.addWidget(self._action_card(
            "Data Folder", "Open the folder where DizoClip stores your data",
            "Open", self._on_open_folder_clicked))
        body_lay.addWidget(self._action_card(
            "Export Data", "Choose what to share, as encrypted or plain JSON",
            "Export", self._on_export_clicked))
        body_lay.addWidget(self._action_card(
            "Import Data", "Preview a file, then add only what you want",
            "Import", self._on_import_clicked))

        # 5. Section: About
        sec_about = QLabel("About")
        sec_about.setStyleSheet(font_css("eyebrow", color="#7a8292", extra="margin-top: 6px; margin-left: 2px;"))
        body_lay.addWidget(sec_about)

        # About Card: (Left: DizoClip + Version badge, Creator below; Right: Social buttons)
        card_about = QFrame()
        card_about.setObjectName("Card")
        card_about.setFixedHeight(64)
        lay_about = QHBoxLayout(card_about)
        lay_about.setContentsMargins(14, 10, 14, 10)
        lay_about.setSpacing(12)

        # Left Column: App Name + Version on top row, Creator on bottom row
        left_about = QVBoxLayout()
        left_about.setContentsMargins(0, 0, 0, 0)
        left_about.setSpacing(4)
        left_about.setAlignment(Qt.AlignVCenter)

        top_name_row = QHBoxLayout()
        top_name_row.setContentsMargins(0, 0, 0, 0)
        top_name_row.setSpacing(8)
        top_name_row.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        lbl_app_name = QLabel("DizoClip")
        lbl_app_name.setStyleSheet(font_css("title", color="#ffffff"))
        top_name_row.addWidget(lbl_app_name)

        lbl_version = QLabel(__version__)
        lbl_version.setStyleSheet(
            f"color: {ACCENT}; font-weight: 700; font-family: {FONT_MONO}; "
            f"font-size: 11.5px; letter-spacing: 0.5px; background: transparent; border: none;"
        )
        top_name_row.addWidget(lbl_version)
        top_name_row.addStretch(1)
        left_about.addLayout(top_name_row)

        lbl_creator = QLabel("<span style='color: #7a8292; font-size: 11px;'>Creator:</span> <span style='color: #ffffff; font-weight: 600; font-size: 11px;'>AbdulKarim</span>")
        left_about.addWidget(lbl_creator)
        lay_about.addLayout(left_about, 1)

        # Right Column: Social Links
        social_row = QHBoxLayout()
        social_row.setContentsMargins(0, 0, 0, 0)
        social_row.setSpacing(8)
        social_row.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        gh_btn = AboutSocialButton("github", "https://github.com/abdulkarim20-ui", "GitHub: abdulkarim20-ui")
        li_btn = AboutSocialButton("linkedin", "https://www.linkedin.com/in/abdulkarim27", "LinkedIn: abdulkarim27")
        social_row.addWidget(gh_btn)
        social_row.addWidget(li_btn)
        lay_about.addLayout(social_row)

        body_lay.addWidget(card_about)

        scroll.setWidget(body)
        root.addWidget(scroll, 1)

    def _action_card(self, title: str, subtitle: str, button_text: str, on_click) -> QFrame:
        """Settings card with a title, a one-line subtitle and a small button on the right."""
        card = QFrame()
        card.setObjectName("Card")
        card.setFixedHeight(66)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 9, 14, 9)
        lay.setSpacing(4)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        lbl = QLabel(title)
        lbl.setStyleSheet(font_css("body-strong", color="#ffffff"))
        row.addWidget(lbl, 0, Qt.AlignVCenter)
        row.addStretch(1)

        btn = QPushButton(button_text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(26)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: #161821; border: 1px solid {CARD_BORDER}; border-radius: 6px;
                color: #ffffff; font-size: 11.5px; font-weight: 600; padding: 0 12px;
            }}
            QPushButton:hover {{ background: #1a1e2a; border-color: #3b4354; }}
        """)
        btn.clicked.connect(on_click)
        row.addWidget(btn, 0, Qt.AlignVCenter)
        lay.addLayout(row)

        sub = QLabel(subtitle)
        sub.setStyleSheet(font_css("subtext", color="#7a8292"))
        sub.setWordWrap(True)
        lay.addWidget(sub)
        return card

    def _toggle_card(self, title: str, subtitle: str, checked: bool, on_toggle):
        """Settings card with a ToggleSwitch. Returns (card, switch)."""
        card = QFrame()
        card.setObjectName("Card")
        card.setFixedHeight(66)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 9, 14, 9)
        lay.setSpacing(4)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        lbl = QLabel(title)
        lbl.setStyleSheet(font_css("body-strong", color="#ffffff"))
        row.addWidget(lbl, 0, Qt.AlignVCenter)
        row.addStretch(1)
        switch = ToggleSwitch(checked=checked, on_toggle=on_toggle)
        row.addWidget(switch, 0, Qt.AlignVCenter)
        lay.addLayout(row)

        sub = QLabel(subtitle)
        sub.setStyleSheet(font_css("subtext", color="#7a8292"))
        sub.setWordWrap(True)
        lay.addWidget(sub)
        return card, switch

    def _on_toggle_clip(self, checked):
        self.win.settings["auto_clear_clipboard"] = checked
        self.win.save_settings()

    def _on_toggle_encrypt(self, checked):
        self.win.settings["encrypt_all_data"] = checked
        self.win.save_settings()       # DataManager learns the new value here
        self.win.rewrite_all_datasets()

    def _on_restore_clicked(self):
        from app.components.dialogs.restore_backup import RestoreBackupDialog
        RestoreBackupDialog(self.win).exec()

    def _on_open_folder_clicked(self):
        try:
            self.win.data_manager.open_data_folder()
        except (DataError, OSError) as exc:
            QMessageBox.information(self, "DizoClip", str(exc))

    def _ask_passphrase(self, title: str, label: str):
        text, ok = QInputDialog.getText(self, title, label, QLineEdit.Password)
        return text if ok and text else None

    def _on_export_clicked(self):
        from app.components.dialogs.export_dialog import ExportDialog
        ExportDialog(self.win).exec()

    def _on_import_clicked(self):
        import os
        from app.components.dialogs.import_dialog import ImportDialog

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import DizoClip data",
            "",
            "DizoClip files (*.dizoclip *.json *.env *.txt);;Environment files (*.env *.txt);;All files (*)",
        )
        if not path:
            return

        try:
            if os.path.getsize(path) > MAX_IMPORT_BYTES:
                raise ExportError("This file is too large to be a DizoClip export.")
            with open(path, "rb") as fh:
                blob = fh.read()

            payload = None
            if is_encrypted_bundle(blob):
                while payload is None:  # wrong passphrase -> ask again, Cancel leaves
                    pw = self._ask_passphrase("Import data", "Passphrase for this file:")
                    if not pw:
                        return
                    try:
                        payload = read_bundle(blob, pw)
                    except WrongPassphrase as exc:
                        QMessageBox.warning(self, "DizoClip", str(exc))
            else:
                payload = read_bundle(blob)

            plan = self.win.plan_import(payload)
        except (ExportError, OSError) as exc:
            QMessageBox.critical(self, "DizoClip", f"Import failed:\n\n{exc}")
            return

        if not plan.items:
            QMessageBox.information(self, "DizoClip", "This file has nothing to import.")
            return

        dlg = ImportDialog(self.win, plan, os.path.basename(path))
        if dlg.exec() != QDialog.Accepted:
            return

        try:
            added = self.win.import_selected(plan, dlg.chosen_indexes())
        except DataError as exc:
            QMessageBox.critical(self, "DizoClip", f"Import could not be saved. Nothing was added.\n\n{exc}")
            return

        total = sum(added.values())
        QMessageBox.information(self, "DizoClip", f"Imported {total} item(s). Existing items were not changed.")

    def refresh_nav_tabs(self):
        """Rebuilds navigation tab buttons according to section_order and enabled_sections."""
        while self.top_lay.count():
            item = self.top_lay.takeAt(0)
            w = item.widget()
            if w is not None and w is not self.settings_btn:
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

        for sid in visible:
            sec_meta = SECTION_REGISTRY.get(sid, SECTION_REGISTRY["key-round"])
            btn = NavTabButton(
                sid,
                is_active=False,
                tooltip=sec_meta.get("title", sid),
                is_fixed=False,
            )
            btn.clicked.connect(lambda _, tid=sid: self._goto_tab(tid))
            self.tab_buttons[sid] = btn
            self.top_lay.addWidget(btn)

        self.top_lay.addStretch(1)
        self.settings_btn.set_active(True)
        self.top_lay.addWidget(self.settings_btn)

    def _goto_tab(self, tab_id):
        self.win.show_list_view()
        self.win.list_view.select_tab(tab_id)

    def _on_toggle_top(self, checked):
        self.win.settings["always_on_top"] = checked
        self.win.save_settings()
        self.win.apply_always_on_top(checked)

    def _on_toggle_del(self, checked):
        self.win.settings["confirm_delete"] = checked
        self.win.save_settings()

    def _on_module_changed(self, selected_mod):
        self.win.settings["startup_module"] = selected_mod
        self.win.save_settings()

    def _on_visible_modules_changed(self, enabled_list):
        # If startup_module is no longer enabled, update to the first enabled one
        if self.win.settings.get("startup_module") not in enabled_list:
            self.win.settings["startup_module"] = enabled_list[0]

        self.win.save_settings()

        # Update navigation bars and module selector across views
        self.refresh_nav_tabs()
        self.win.list_view.refresh_nav_tabs()
        self.module_selector._refresh()
        if hasattr(self, "visible_modules_selector"):
            self.visible_modules_selector._refresh()

        # If currently active tab in ListView was disabled, switch to first enabled
        if self.win.list_view.active_tab not in enabled_list:
            self.win.list_view.select_tab(enabled_list[0])
