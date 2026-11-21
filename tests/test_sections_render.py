import sys

import pytest
from PySide6.QtWidgets import QApplication

from app.components.cards.base_card import BaseCard
from app.window.main_window import MainWindow


def _card_count(win):
    lay = win.list_view.cards
    return sum(1 for i in range(lay.count()) if isinstance(lay.itemAt(i).widget(), BaseCard))


@pytest.fixture
def win():
    QApplication.instance() or QApplication(sys.argv)
    w = MainWindow()
    w.settings["welcome_seen"] = True
    c = "#e8794a"
    w.keys[:] = [{"label": f"key{i}", "full_key": "x" * 24, "color": c} for i in range(4)]
    w.prompts[:] = [{"id": f"p{i}", "name": f"prompt{i}", "prompt": "hello world " * 5, "color": c} for i in range(4)]
    w.ai_models[:] = [{"id": f"m{i}", "name": f"model{i}", "snippets": {"Python": "print(1)"}, "color": c} for i in range(4)]
    w.links[:] = [{"id": f"l{i}", "title": f"link{i}", "url": "https://x.example", "color": c} for i in range(4)]
    w.commands[:] = [{"id": f"c{i}", "title": f"cmd{i}", "command": "git status", "color": c} for i in range(4)]
    yield w
    w.close()


@pytest.mark.parametrize("tab", ["key-round", "prompt", "ai_model", "link", "command"])
def test_every_section_renders_its_cards_and_search_filters(win, tab):
    win.list_view.select_tab(tab, animate=False)
    win.list_view.rebuild(animate_resize=False)
    assert _card_count(win) == 4

    win.list_view.search.setText("zzz-no-match")
    win.list_view.rebuild(animate_resize=False)
    assert _card_count(win) == 0
