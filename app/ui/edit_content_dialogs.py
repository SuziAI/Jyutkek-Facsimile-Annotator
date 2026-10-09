from __future__ import annotations
from PySide6.QtWidgets import QWidget, QFormLayout, QLineEdit, QLabel, QHBoxLayout, QPushButton, \
    QComboBox, QGroupBox, QTextEdit, QTableWidget, QTableWidgetItem

from app.viewmodels.content_block_viewmodel import CellBlockViewModel, TitleBlockViewModel, ParagraphBlockViewModel, \
    RoleAnnotBlockViewModel, DirectionBlockViewModel, LineBlockViewModel
from app.viewmodels.content_cell_viewmodel import BeatCellViewModel, SylCellViewModel, ProlongationDotCellViewModel, \
    GongcheCellViewModel
from app.viewmodels.content_viewmodel import BodyMetadataViewModel, BodyQupaiViewModel, BodyRecitativoViewModel
from app.viewmodels.zone_viewmodel import ZoneViewModel

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QDialogButtonBox,
    QListWidget,
    QListWidgetItem,
)


class DialogSelectBlockType(QDialog):
    """
    Dialog for selecting a block type when adding a new content block.
    """

    def __init__(self, block_types: list[str], parent=None) -> None:
        """
        Initializes a dialog that lets the user select one of the given block types.

        :param block_types: List of human-readable block type names (e.g. ["Title", "Paragraph"]).
        :param parent: Parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Select Block Type")
        self._selected_type: str | None = None

        layout = QVBoxLayout(self)

        self._list = QListWidget(self)
        for bt in block_types:
            item = QListWidgetItem(bt, self._list)
            item.setData(Qt.ItemDataRole.UserRole, bt)
        self._list.itemDoubleClicked.connect(self._accept_current)
        layout.addWidget(self._list)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            Qt.Orientation.Horizontal,
            self,
        )
        buttons.accepted.connect(self._accept_current)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if self._list.count() > 0:
            self._list.setCurrentRow(0)

    def _accept_current(self) -> None:
        item = self._list.currentItem()
        if item is None:
            return
        self._selected_type = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    @property
    def selected_type(self) -> str | None:
        """
        Returns the selected block type name or None if the dialog was cancelled.
        """
        return self._selected_type


class CellBlockDialog(QDialog):
    """
    CellBlockDialog allows editing of a CellBlockViewModel and its nested
    BeatCellViewModel, GongcheCellViewModel, SylCellViewModel and
    ProlongationDotCellViewModel instances.
    """

    def __init__(self, cell_vm: CellBlockViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Cell Block")
        self._cell_vm = cell_vm

        layout = QVBoxLayout(self)

        form = QFormLayout()
        layout.addLayout(form)

        # Beat cell
        self._beat_beat = QLineEdit(self)
        self._beat_content = QLineEdit(self)
        form.addRow(QLabel("Beat ID:", self), self._beat_beat)
        form.addRow(QLabel("Beat Content:", self), self._beat_content)

        # Gongche cell
        self._gongche_pname = QLineEdit(self)
        self._gongche_content = QLineEdit(self)
        form.addRow(QLabel("Gongche Pitch:", self), self._gongche_pname)
        form.addRow(QLabel("Gongche Content:", self), self._gongche_content)

        # Syl cell
        self._syl_con = QLineEdit(self)
        self._syl_content = QLineEdit(self)
        form.addRow(QLabel("Syl Con:", self), self._syl_con)
        form.addRow(QLabel("Syl Content:", self), self._syl_content)

        # Prolongation dot
        self._pd_content = QLineEdit(self)
        form.addRow(QLabel("Prolongation Dot Content:", self), self._pd_content)

        # Buttons
        button_box = QHBoxLayout()
        ok_btn = QPushButton("OK", self)
        cancel_btn = QPushButton("Cancel", self)
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        button_box.addStretch(1)
        button_box.addWidget(ok_btn)
        button_box.addWidget(cancel_btn)
        layout.addLayout(button_box)

        self._load_from_viewmodel()

    def _load_from_viewmodel(self) -> None:
        """
        Loads the values from the CellBlockViewModel into the dialog widgets.
        """
        if self._cell_vm.beat is not None:
            self._beat_beat.setText(str(self._cell_vm.beat.beat))
            self._beat_content.setText(self._cell_vm.beat.content)
        if self._cell_vm.gongche is not None:
            self._gongche_pname.setText(str(self._cell_vm.gongche.pname))
            self._gongche_content.setText(self._cell_vm.gongche.content)
        if self._cell_vm.syl is not None:
            self._syl_con.setText(str(self._cell_vm.syl.con))
            self._syl_content.setText(self._cell_vm.syl.content)
        if self._cell_vm.prolongation_dot is not None:
            self._pd_content.setText(self._cell_vm.prolongation_dot.content)

    def accept(self) -> None:
        """
        Writes the dialog values back into the CellBlockViewModel and closes the dialog.
        """
        # Beat
        beat_text = self._beat_beat.text().strip()
        beat_content = self._beat_content.text()
        if beat_text or beat_content:
            if self._cell_vm.beat is None:
                self._cell_vm.beat = BeatCellViewModel(parent=self._cell_vm)
            self._cell_vm.beat.beat = beat_text
            self._cell_vm.beat.content = beat_content
        else:
            self._cell_vm.beat = None

        # Gongche
        pname_text = self._gongche_pname.text().strip()
        gongche_content = self._gongche_content.text()
        if pname_text or gongche_content:
            if self._cell_vm.gongche is None:
                self._cell_vm.gongche = GongcheCellViewModel(parent=self._cell_vm)
            self._cell_vm.gongche.pname = pname_text
            self._cell_vm.gongche.content = gongche_content
        else:
            self._cell_vm.gongche = None

        # Syl
        syl_con = self._syl_con.text().strip()
        syl_content = self._syl_content.text()
        if syl_con or syl_content:
            if self._cell_vm.syl is None:
                self._cell_vm.syl = SylCellViewModel(parent=self._cell_vm)
            self._cell_vm.syl.con = syl_con
            self._cell_vm.syl.content = syl_content
        else:
            self._cell_vm.syl = None

        # Prolongation dot
        pd_content = self._pd_content.text().strip()
        if pd_content:
            if self._cell_vm.prolongation_dot is None:
                self._cell_vm.prolongation_dot = ProlongationDotCellViewModel(parent=self._cell_vm)
            self._cell_vm.prolongation_dot.content = pd_content
        else:
            self._cell_vm.prolongation_dot = None

        super().accept()


class ZoneContentEditor(QWidget):
    """
    ZoneContentEditor displays and edits the content of a single ZoneViewModel.
    It provides
        * a combo box to select the content type (None, Metadata, Recitativo, Qupai),
        * a list of content blocks,
        * buttons to add, remove and edit content blocks.

    Depending on the selected content type, it manages
        BodyMetadataViewModel, BodyRecitativoViewModel or BodyQupaiViewModel
    and the corresponding block viewmodels.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._zone: ZoneViewModel | None = None

        main_layout = QVBoxLayout(self)

        # Content type selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Content type:", self))
        self._type_combo = QComboBox(self)
        self._type_combo.addItems(["None", "Metadata", "Recitativo", "Qupai"])
        self._type_combo.currentIndexChanged.connect(self._content_type_changed)
        type_layout.addWidget(self._type_combo)
        type_layout.addStretch(1)
        main_layout.addLayout(type_layout)

        # Block list as a 3-column table: Type, Content, Attributes
        block_group = QGroupBox("Blocks", self)
        block_layout = QVBoxLayout(block_group)

        self._block_list = QTableWidget(self)
        self._block_list.setColumnCount(3)
        self._block_list.setHorizontalHeaderLabels(["Type", "Content", "Attributes"])
        self._block_list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._block_list.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._block_list.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._block_list.horizontalHeader().setStretchLastSection(True)

        self._block_list.cellDoubleClicked.connect(self._edit_block)
        block_layout.addWidget(self._block_list)

        # Block buttons
        btn_layout = QHBoxLayout()
        self._add_block_btn = QPushButton("Add Block", self)
        self._remove_block_btn = QPushButton("Remove Block", self)
        self._edit_block_btn = QPushButton("Edit Block", self)

        self._add_block_btn.clicked.connect(self._add_block)
        self._remove_block_btn.clicked.connect(self._remove_block)
        self._edit_block_btn.clicked.connect(self._edit_block_clicked)

        btn_layout.addWidget(self._add_block_btn)
        btn_layout.addWidget(self._remove_block_btn)
        btn_layout.addWidget(self._edit_block_btn)
        btn_layout.addStretch(1)
        block_layout.addLayout(btn_layout)

        block_group.setLayout(block_layout)
        main_layout.addWidget(block_group)

        self._update_enabled_state()

    def set_zone(self, zone: ZoneViewModel | None) -> None:
        """
        Sets the zone whose content should be displayed and edited.
        """
        self._zone = zone
        self._reload_from_zone()

    def _reload_from_zone(self) -> None:
        """
        Loads the current zone content into the widgets.
        """
        self._block_list.clear()

        if self._zone is None:
            self._type_combo.setCurrentText("None")
            self._update_enabled_state()
            return

        content = self._zone.content
        if content is None:
            self._type_combo.setCurrentText("None")
        elif isinstance(content, BodyMetadataViewModel):
            self._type_combo.setCurrentText("Metadata")
        elif isinstance(content, BodyRecitativoViewModel):
            self._type_combo.setCurrentText("Recitativo")
        elif isinstance(content, BodyQupaiViewModel):
            self._type_combo.setCurrentText("Qupai")
        else:
            self._type_combo.setCurrentText("None")

        self._populate_block_list()
        self._update_enabled_state()

    def _block_row_data(self, block: object) -> tuple[str, str, str]:
        """
        Returns (Type, Content, Attributes) strings for display in the 3-column table.
        """
        # Metadata blocks
        if isinstance(block, TitleBlockViewModel):
            return "Title", block.title, ""

        if isinstance(block, ParagraphBlockViewModel):
            return "Paragraph", block.paragraph, ""

        # Role annotation
        if isinstance(block, RoleAnnotBlockViewModel):
            roles = ", ".join(block.plist) if block.plist else ""
            return "RoleAnnot", block.content, f"plist=[{roles}]" if roles else "plist=[]"

        # Direction
        if isinstance(block, DirectionBlockViewModel):
            plist = ", ".join(block.plist) if block.plist else ""
            attr = f"plist=[{plist}]" if plist else "plist=[]"
            return "Direction", block.content, attr

        # Line
        if isinstance(block, LineBlockViewModel):
            return "Line", block.content, ""

        # CellBlock
        if isinstance(block, CellBlockViewModel):
            content = ""
            parts = []
            if block.beat is not None:
                parts.append(f"beat={block.beat.beat} ({block.beat.content})")
            if block.gongche is not None:
                parts.append(f"gongche={block.gongche.pname} ({block.gongche.content})")
            if block.syl is not None:
                parts.append(f"syl={block.syl.con} ({block.syl.content})")
            if block.prolongation_dot is not None:
                parts.append(f"dot={block.prolongation_dot.content}")
            attr = ", ".join(parts) if parts else "empty"
            return "CellBlock", content, attr

        # Fallback
        return type(block).__name__, repr(block), ""

    def _populate_block_list(self) -> None:
        """
        Populates the table widget according to the current body viewmodel.
        """
        self._block_list.clearContents()
        self._block_list.setRowCount(0)

        if self._zone is None or self._zone.content is None:
            return

        blocks = list(self._zone.content.content)
        self._block_list.setRowCount(len(blocks))

        for row, block in enumerate(blocks):
            type_str, content_str, attr_str = self._block_row_data(block)

            # Type
            type_item = QTableWidgetItem(type_str)
            type_item.setData(Qt.ItemDataRole.UserRole, block)
            self._block_list.setItem(row, 0, type_item)

            # Content
            content_item = QTableWidgetItem(content_str)
            self._block_list.setItem(row, 1, content_item)

            # Attributes
            attr_item = QTableWidgetItem(attr_str)
            self._block_list.setItem(row, 2, attr_item)

    def _current_body(self) -> BodyMetadataViewModel | BodyRecitativoViewModel | BodyQupaiViewModel | None:
        """
        Convenience getter for the body viewmodel of the current zone.
        """
        if self._zone is None:
            return None
        return self._zone.content

    def _set_body_content(self, blocks: tuple[object, ...]) -> None:
        """
        Writes the given blocks back into the underlying body viewmodel.
        """
        body = self._current_body()
        if body is None:
            return
        body.content = blocks  # type: ignore[assignment]
        self._zone.content = body  # type: ignore[arg-type]

    def _content_type_changed(self, _index: int) -> None:
        """
        Called when the content type combo box value changes.
        Creates or clears the ZoneViewModel.content accordingly.
        """
        if self._zone is None:
            return

        text = self._type_combo.currentText()
        if text == "None":
            self._zone.content = None
        elif text == "Metadata":
            if not isinstance(self._zone.content, BodyMetadataViewModel):
                self._zone.content = BodyMetadataViewModel(parent=self._zone)
        elif text == "Recitativo":
            if not isinstance(self._zone.content, BodyRecitativoViewModel):
                self._zone.content = BodyRecitativoViewModel(parent=self._zone)
        elif text == "Qupai":
            if not isinstance(self._zone.content, BodyQupaiViewModel):
                self._zone.content = BodyQupaiViewModel(parent=self._zone)

        self._populate_block_list()
        self._update_enabled_state()

    def _update_enabled_state(self) -> None:
        """
        Enables or disables the editor widgets based on selection and type.
        """
        enabled = self._zone is not None and self._zone.content is not None
        self._block_list.setEnabled(enabled)
        self._add_block_btn.setEnabled(enabled)
        self._remove_block_btn.setEnabled(enabled)
        self._edit_block_btn.setEnabled(enabled)

    def _add_block(self) -> None:
        """
        Adds a block of a type suitable for the current body.
        Now uses DialogSelectBlockType so the user can choose the block type.
        """
        body = self._current_body()
        if body is None:
            return

        if isinstance(body, BodyMetadataViewModel):
            choices = ["Title", "Paragraph"]
        elif isinstance(body, BodyRecitativoViewModel):
            choices = ["RoleAnnot", "Direction", "Line"]
        elif isinstance(body, BodyQupaiViewModel):
            choices = ["RoleAnnot", "Direction", "CellBlock"]
        else:
            return

        dlg = DialogSelectBlockType(choices, parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        selected = dlg.selected_type
        if selected is None:
            return

        blocks = list(body.content)

        if isinstance(body, BodyMetadataViewModel):
            if selected == "Title":
                new_block = TitleBlockViewModel(title="", parent=body)
            elif selected == "Paragraph":
                new_block = ParagraphBlockViewModel(paragraph="", parent=body)
            else:
                return

        elif isinstance(body, BodyRecitativoViewModel):
            if selected == "RoleAnnot":
                new_block = RoleAnnotBlockViewModel(parent=body)
            elif selected == "Direction":
                new_block = DirectionBlockViewModel(parent=body)
            elif selected == "Line":
                new_block = LineBlockViewModel(content="", parent=body)
            else:
                return

        elif isinstance(body, BodyQupaiViewModel):
            if selected == "RoleAnnot":
                new_block = RoleAnnotBlockViewModel(parent=body)
            elif selected == "Direction":
                new_block = DirectionBlockViewModel(parent=body)
            elif selected == "CellBlock":
                new_block = CellBlockViewModel(parent=body)
            else:
                return

        else:
            return

        blocks.append(new_block)
        self._set_body_content(tuple(blocks))
        self._populate_block_list()

    def _remove_block(self) -> None:
        """
        Removes the currently selected block from the body content.
        """
        body = self._current_body()
        if body is None:
            return

        row = self._block_list.currentRow()
        if row < 0:
            return

        blocks = list(body.content)
        if 0 <= row < len(blocks):
            del blocks[row]
        self._set_body_content(tuple(blocks))
        self._populate_block_list()

    def _edit_block_clicked(self) -> None:
        """
        Slot for the 'Edit Block' button.
        """
        row = self._block_list.currentRow()
        if row < 0:
            return
        self._edit_block(row, 0)

    def _edit_block(self, row: int, _column: int) -> None:
        """
        Opens an editor for the double-clicked or selected block.
        Called by cellDoubleClicked(row, column).
        """
        item = self._block_list.item(row, 0)
        if item is None:
            return

        block = item.data(Qt.ItemDataRole.UserRole)

        if isinstance(block, (TitleBlockViewModel, ParagraphBlockViewModel,
                              RoleAnnotBlockViewModel, DirectionBlockViewModel,
                              LineBlockViewModel)):
            self._edit_text_block(block)
        elif isinstance(block, CellBlockViewModel):
            self._edit_cell_block(block)

        # Refresh row display
        type_str, content_str, attr_str = self._block_row_data(block)

        # Update type item (and boldness)
        type_item = self._block_list.item(row, 0)
        if type_item is None:
            type_item = QTableWidgetItem()
            self._block_list.setItem(row, 0, type_item)
        type_item.setText(type_str)
        font = type_item.font()
        font.setBold(isinstance(block, TitleBlockViewModel))
        type_item.setFont(font)
        type_item.setData(Qt.ItemDataRole.UserRole, block)

        # Update content
        content_item = self._block_list.item(row, 1)
        if content_item is None:
            content_item = QTableWidgetItem()
            self._block_list.setItem(row, 1, content_item)
        content_item.setText(content_str)

        # Update attributes
        attr_item = self._block_list.item(row, 2)
        if attr_item is None:
            attr_item = QTableWidgetItem()
            self._block_list.setItem(row, 2, attr_item)
        attr_item.setText(attr_str)

    def _edit_text_block(self, block: object) -> None:
        """
        Simple dialog for editing one of the text based blocks.
        """
        dialog = QDialog(self)
        if isinstance(block, TitleBlockViewModel):
            dialog.setWindowTitle("Edit Title Block")
        elif isinstance(block, ParagraphBlockViewModel):
            dialog.setWindowTitle("Edit Paragraph Block")
        elif isinstance(block, RoleAnnotBlockViewModel):
            dialog.setWindowTitle("Edit RoleAnnot Block")
        elif isinstance(block, DirectionBlockViewModel):
            dialog.setWindowTitle("Edit Direction Block")
        elif isinstance(block, LineBlockViewModel):
            dialog.setWindowTitle("Edit Line Block")
        else:
            dialog.setWindowTitle("Edit Block")

        layout = QVBoxLayout(dialog)

        form = QFormLayout()
        layout.addLayout(form)

        plist_edit: QLineEdit | None = None
        if isinstance(block, (RoleAnnotBlockViewModel, DirectionBlockViewModel)):
            plist_edit = QLineEdit(dialog)
            plist_edit.setText(", ".join(block.plist))
            form.addRow(QLabel("plist (comma-separated):", dialog), plist_edit)

        text_edit = QTextEdit(dialog)
        if isinstance(block, TitleBlockViewModel):
            text_edit.setPlainText(block.title)
        elif isinstance(block, ParagraphBlockViewModel):
            text_edit.setPlainText(block.paragraph)
        elif isinstance(block, (RoleAnnotBlockViewModel, DirectionBlockViewModel, LineBlockViewModel)):
            text_edit.setPlainText(block.content)
        form.addRow(QLabel("Text:", dialog), text_edit)

        button_box = QHBoxLayout()
        ok_btn = QPushButton("OK", dialog)
        cancel_btn = QPushButton("Cancel", dialog)
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        button_box.addStretch(1)
        button_box.addWidget(ok_btn)
        button_box.addWidget(cancel_btn)
        layout.addLayout(button_box)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        if plist_edit is not None and isinstance(block, (RoleAnnotBlockViewModel, DirectionBlockViewModel)):
            raw = plist_edit.text()
            block.plist = tuple(s.strip() for s in raw.split(",") if s.strip())

        text = text_edit.toPlainText()
        if isinstance(block, TitleBlockViewModel):
            block.title = text
        elif isinstance(block, ParagraphBlockViewModel):
            block.paragraph = text
        elif isinstance(block, (RoleAnnotBlockViewModel, DirectionBlockViewModel, LineBlockViewModel)):
            block.content = text

    def _edit_cell_block(self, cell_block: CellBlockViewModel) -> None:
        """
        Opens a dialog to edit a CellBlockViewModel and its nested cells.
        """
        dialog = CellBlockDialog(cell_block, parent=self)
        dialog.exec()