from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from app.models.document import Beat, Pitch, Con


class BeatCellViewModel(QObject):
    """
    BeatCell viewmodel.

    Signals:
        cell_changed (Signal(str, str)): Emitted when the beat cell content is changed.
    """
    cell_changed = Signal(str, str)

    def __init__(
        self,
        beat: Beat = "",
        content: str = "",
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._beat = beat
        self._content = content

    @property
    def beat(self) -> Beat:
        return self._beat

    @beat.setter
    def beat(self, value: Beat) -> None:
        self._beat = value
        self.cell_changed.emit(value, self._content)

    @property
    def content(self) -> str:
        return self._content

    @content.setter
    def content(self, value: str) -> None:
        self._content = value
        self.cell_changed.emit(self._beat, value)


class GongcheCellViewModel(QObject):
    """
    GongcheCell viewmodel.

    Signals:
        cell_changed (Signal(str, str)): Emitted when the gongche cell content is changed.
    """
    cell_changed = Signal(str, str)

    def __init__(
        self,
        pname: Pitch = "",
        content: str = "",
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._pname = pname
        self._content = content

    @property
    def pname(self) -> Pitch:
        return self._pname

    @pname.setter
    def pname(self, value: Pitch) -> None:
        self._pname = value
        self.cell_changed.emit(value, self._content)

    @property
    def content(self) -> str:
        return self._content

    @content.setter
    def content(self, value: str) -> None:
        self._content = value
        self.cell_changed.emit(self._pname, value)


class SylCellViewModel(QObject):
    """
    SylCell viewmodel.

    Signals:
        cell_changed (Signal(object, str)): Emitted when the syl cell content is changed.
    """
    cell_changed = Signal(object, str)

    def __init__(
        self,
        con: Con | None = None,
        content: str = "",
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._con = con
        self._content = content

    @property
    def con(self) -> Con | None:
        return self._con

    @con.setter
    def con(self, value: Con | None) -> None:
        self._con = value
        self.cell_changed.emit(value, self._content)

    @property
    def content(self) -> str:
        return self._content

    @content.setter
    def content(self, value: str) -> None:
        self._content = value
        self.cell_changed.emit(self._con, value)


class ProlongationDotCellViewModel(QObject):
    """
    ProlongationDot viewmodel.

    Signals:
        cell_changed (Signal(str)): Emitted when the prolongation dot cell content is changed.
    """
    cell_changed = Signal(str)

    def __init__(
        self,
        content: str = "",
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._content = content

    @property
    def content(self) -> str:
        return self._content

    @content.setter
    def content(self, value: str) -> None:
        self._content = value
        self.cell_changed.emit(value)