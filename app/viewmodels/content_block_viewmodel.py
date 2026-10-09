from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from app.viewmodels.content_cell_viewmodel import BeatCellViewModel, GongcheCellViewModel, SylCellViewModel, \
    ProlongationDotCellViewModel


class TitleBlockViewModel(QObject):
    """
    TitleBlock viewmodel.

    Signals:
        title_changed (Signal(str)): Emitted when the title block content is changed.
    """
    title_changed = Signal(str)

    def __init__(
        self,
        title: str = "",
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._title = title

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        self._title = value
        self.title_changed.emit(value)


class ParagraphBlockViewModel(QObject):
    """
    ParagraphBlock viewmodel.

    Signals:
        paragraph_changed (Signal(str)): Emitted when the paragraph block content is changed.
    """
    paragraph_changed = Signal(str)

    def __init__(
        self,
        paragraph: str = "",
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._paragraph = paragraph

    @property
    def paragraph(self) -> str:
        return self._paragraph

    @paragraph.setter
    def paragraph(self, value: str) -> None:
        self._paragraph = value
        self.paragraph_changed.emit(value)


class RoleAnnotBlockViewModel(QObject):
    """
    RoleAnnotBlock viewmodel.

    Signals:
        role_annot_changed (Signal()): Emitted when the role annot block content is changed.
    """
    role_annot_changed = Signal()

    def __init__(
        self,
        plist: (tuple[str]) = tuple([""]),
        content: str = "",
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._plist = plist
        self._content = content

    @property
    def plist(self) -> tuple[str]:
        return self._plist

    @plist.setter
    def plist(self, value: tuple[str]) -> None:
        self._plist = value
        self.role_annot_changed.emit()

    @property
    def content(self) -> str:
        return self._content

    @content.setter
    def content(self, value: str) -> None:
        self._content = value
        self.role_annot_changed.emit()


class LineBlockViewModel(QObject):
    """
    LineBlockViewModel viewmodel.

    Signals:
        content_changed (Signal(str)): Emitted when the line block content is changed.
    """
    content_changed = Signal(str)

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
        self.content_changed.emit(value)


class DirectionBlockViewModel(QObject):
    """
    DirectionBlock viewmodel.

    Signals:
        direction_changed (Signal()): Emitted when the direction block content is changed.
    """
    direction_changed = Signal()

    def __init__(
        self,
        plist: (tuple[str]) = tuple([""]),
        content: str = "",
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._plist = plist
        self._content = content

    @property
    def plist(self) -> tuple[str]:
        return self._plist

    @plist.setter
    def plist(self, value: tuple[str]) -> None:
        self._plist = value
        self.direction_changed.emit()

    @property
    def content(self) -> str:
        return self._content

    @content.setter
    def content(self, value: str) -> None:
        self._content = value
        self.direction_changed.emit()


class CellBlockViewModel(QObject):
    """
    CellBlock viewmodel.

    Signals:
        cell_changed (Signal()): Emitted when the cell block content is changed.
    """
    cell_changed = Signal()

    def __init__(
        self,
        beat: BeatCellViewModel | None = None,
        gongche: GongcheCellViewModel | None = None,
        syl: SylCellViewModel | None = None,
        prolongation_dot: ProlongationDotCellViewModel | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._beat = beat
        self._gongche = gongche
        self._syl = syl
        self._prolongation_dot = prolongation_dot

    @property
    def beat(self) -> BeatCellViewModel | None:
        return self._beat

    @beat.setter
    def beat(self, value: BeatCellViewModel | None) -> None:
        self._beat = value
        self.cell_changed.emit()

    @property
    def gongche(self) -> GongcheCellViewModel | None:
        return self._gongche

    @gongche.setter
    def gongche(self, value: GongcheCellViewModel | None) -> None:
        self._gongche = value
        self.cell_changed.emit()

    @property
    def syl(self) -> SylCellViewModel | None:
        return self._syl

    @syl.setter
    def syl(self, value: SylCellViewModel | None) -> None:
        self._syl = value
        self.cell_changed.emit()

    @property
    def prolongation_dot(self) -> ProlongationDotCellViewModel | None:
        return self._prolongation_dot

    @prolongation_dot.setter
    def prolongation_dot(self, value: ProlongationDotCellViewModel | None) -> None:
        self._prolongation_dot = value
        self.cell_changed.emit()