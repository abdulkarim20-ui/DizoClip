from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPainter, QPalette
from PySide6.QtWidgets import QLabel, QSizePolicy


class ElidedLabel(QLabel):
    """Crash-proof label that renders elided text directly in paintEvent without painter conflicts."""
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self._raw_text = text
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setMinimumWidth(0)

    def setText(self, text):
        self._raw_text = text
        self.update()
        self.updateGeometry()

    def setToolTip(self, text: str):
        from app.components.labels.animated_tooltip import set_tooltip
        set_tooltip(self, text, placement="top")

    def text(self):
        return self._raw_text

    def sizeHint(self):
        fm = self.fontMetrics()
        tw = fm.horizontalAdvance(self._raw_text)
        th = fm.height()
        return QSize(tw + 20, max(18, th + 4))

    def minimumSizeHint(self):
        fm = self.fontMetrics()
        return QSize(20, max(18, fm.height() + 4))

    def paintEvent(self, event):
        # Do NOT call super().paintEvent(event) when manually painting text 
        # to avoid double-painting/painter collision errors on the same paint device.
        p = QPainter(self)
        if not p.isActive():
            return

        p.setRenderHint(QPainter.Antialiasing)

        rect = self.contentsRect()
        if rect.isEmpty():
            rect = self.rect()
        
        avail_width = max(0, rect.width())
        fm = self.fontMetrics()
        elided = fm.elidedText(self._raw_text, Qt.ElideRight, avail_width)

        p.setFont(self.font())
        p.setPen(self.palette().color(QPalette.WindowText))
        
        align = self.alignment()
        if not (align & (Qt.AlignLeft | Qt.AlignRight | Qt.AlignHCenter | Qt.AlignCenter)):
            align = Qt.AlignLeft | Qt.AlignVCenter
            
        p.drawText(rect, align, elided)
        p.end()
