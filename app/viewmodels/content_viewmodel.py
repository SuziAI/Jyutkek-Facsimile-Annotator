from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from app.models.document import RoleAnnotBlock, DirectionBlock, LineBlock, CellBlock
from app.viewmodels.content_block_viewmodel import TitleBlockViewModel, ParagraphBlockViewModel


class BodyMetadataViewModel(QObject):
    """
    BodyMetadata viewmodel.

    Signals:
        content_changed (Signal()): Emitted when the body metadata content is changed.
    """
    content_changed = Signal()

    def __init__(
        self,
        content: tuple[TitleBlockViewModel | ParagraphBlockViewModel, ...] = (),
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._content = content

    @property
    def content(self) -> tuple[TitleBlockViewModel | ParagraphBlockViewModel, ...]:
        return self._content

    @content.setter
    def content(self, value: tuple[TitleBlockViewModel | ParagraphBlockViewModel, ...]) -> None:
        self._content = value
        self.content_changed.emit()


class BodyRecitativoViewModel(QObject):
    """
    BodyRecitativo viewmodel.

    Signals:
        content_changed (Signal()): Emitted when the body recitativo content is changed.
    """
    content_changed = Signal()

    def __init__(
        self,
        content: tuple[RoleAnnotBlock | DirectionBlock | LineBlock, ...] = (),
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._content = content

    @property
    def content(self) -> tuple[RoleAnnotBlock | DirectionBlock | LineBlock, ...]:
        return self._content

    @content.setter
    def content(self, value: tuple[RoleAnnotBlock | DirectionBlock | LineBlock, ...]) -> None:
        self._content = value
        self.content_changed.emit()


class BodyQupaiViewModel(QObject):
    """
    BodyQupai viewmodel.

    Signals:
        content_changed (Signal()): Emitted when the body qupai content is changed.
    """
    content_changed = Signal()

    def __init__(
        self,
        content: tuple[RoleAnnotBlock | DirectionBlock | CellBlock, ...] = (),
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._content = content

    @property
    def content(self) -> tuple[RoleAnnotBlock | DirectionBlock | CellBlock, ...]:
        return self._content

    @content.setter
    def content(self, value: tuple[RoleAnnotBlock | DirectionBlock | CellBlock, ...]) -> None:
        self._content = value
        self.content_changed.emit()