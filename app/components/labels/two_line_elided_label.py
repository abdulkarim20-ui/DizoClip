from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSizePolicy


class TwoLineElidedLabel(QLabel):
    """Clean multi-line label that fits up to 2 lines of snippet preview."""
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self._raw_text = text
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(30)

    def setText(self, text):
        self._raw_text = text
        self._update_text()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_text()

    def _update_text(self):
        w = self.width()
        if w <= 10:
            return
        fm = self.fontMetrics()
        clean = " ".join(self._raw_text.split())
        if not clean:
            super().setText("")
            return

        if fm.horizontalAdvance(clean) <= w:
            super().setText(clean)
            return

        words = clean.split(" ")
        line1 = ""
        rem_idx = len(words)
        for i, word in enumerate(words):
            candidate = (line1 + " " + word).strip()
            if fm.horizontalAdvance(candidate) <= w:
                line1 = candidate
            else:
                rem_idx = i
                break

        if not line1:
            line1 = fm.elidedText(words[0], Qt.ElideRight, w)
            rem_idx = 1

        rem_text = " ".join(words[rem_idx:]).strip()
        if rem_text:
            line2 = fm.elidedText(rem_text, Qt.ElideRight, w)
            super().setText(f"{line1}\n{line2}")
        else:
            super().setText(line1)
