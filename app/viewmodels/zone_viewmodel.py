from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from app.viewmodels.content_viewmodel import BodyMetadataViewModel, BodyRecitativoViewModel, BodyQupaiViewModel


class ZoneViewModel(QObject):
    """
    Zone viewmodel.

    Signals:
        rect_changed (Signal(float, float, float, float)): Emitted when the zone rectangle coordinates are changed.
        content_changed (Signal()): Emitted when the zone content is changed.
    """
    rect_changed = Signal(float, float, float, float)
    content_changed = Signal()

    def __init__(
        self,
        ulx: int = 0,
        uly: int = 0,
        lrx: int = 0,
        lry: int = 0,
        content: BodyMetadataViewModel | BodyRecitativoViewModel | BodyQupaiViewModel | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._ulx = int(ulx)
        self._uly = int(uly)
        self._lrx = int(lrx)
        self._lry = int(lry)
        self._content = content

    @property
    def ulx(self) -> int:
        return self._ulx

    @ulx.setter
    def ulx(self, value: int) -> None:
        self._set_rect(int(value), self._uly, self._lrx, self._lry)

    @property
    def uly(self) -> int:
        return self._uly

    @uly.setter
    def uly(self, value: int) -> None:
        self._set_rect(self._ulx, int(value), self._lrx, self._lry)

    @property
    def lrx(self) -> int:
        return self._lrx

    @lrx.setter
    def lrx(self, value: int) -> None:
        self._set_rect(self._ulx, self._uly, int(value), self._lry)

    @property
    def lry(self) -> int:
        return self._lry

    @lry.setter
    def lry(self, value: int) -> None:
        self._set_rect(self._ulx, self._uly, self._lrx, int(value))

    def set_rect(self, ulx: int, uly: int, lrx: int, lry: int) -> None:
        self._set_rect(int(ulx), int(uly), int(lrx), int(lry))

    def _set_rect(self, ulx: int, uly: int, lrx: int, lry: int) -> None:
        if (ulx, uly, lrx, lry) == (self._ulx, self._uly, self._lrx, self._lry):
            return
        self._ulx = ulx
        self._uly = uly
        self._lrx = lrx
        self._lry = lry
        self.rect_changed.emit(self._ulx, self._uly, self._lrx, self._lry)

    @property
    def content(self) -> BodyMetadataViewModel | BodyRecitativoViewModel | BodyQupaiViewModel | None:
        return self._content

    @content.setter
    def content(self, value: BodyMetadataViewModel | BodyRecitativoViewModel | BodyQupaiViewModel | None) -> None:
        self._content = value
        self.content_changed.emit()
