from __future__ import annotations

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QFormLayout, QLineEdit, QLabel, QHBoxLayout, QPushButton, \
    QComboBox, QGroupBox, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QDialogButtonBox,
    QListWidget,
    QListWidgetItem,
)
from typing import get_args

from app.models.document import Beat, Pitch
from app.services.document_service import DocumentService
from app.ui.widgets import VerticalTextWidget
from app.viewmodels.content_block_viewmodel import CellBlockViewModel, TitleBlockViewModel, ParagraphBlockViewModel, \
    RoleAnnotBlockViewModel, DirectionBlockViewModel, LineBlockViewModel
from app.viewmodels.content_cell_viewmodel import BeatCellViewModel, SylCellViewModel, ProlongationDotCellViewModel, \
    GongcheCellViewModel
from app.viewmodels.content_viewmodel import BodyMetadataViewModel, BodyQupaiViewModel, BodyRecitativoViewModel
from app.viewmodels.document_viewmodel import DocumentViewModel
from app.viewmodels.zone_viewmodel import ZoneViewModel

BEAT_CHOICES: tuple[str, ...] = get_args(Beat)
PITCH_CHOICES: tuple[str, ...] = get_args(Pitch)


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

        # --- Beat cell ---
        # _beat_beat: None / weak / strong
        self._beat_beat = QComboBox(self)
        self._beat_beat.addItem("")
        self._beat_beat.addItems(list(BEAT_CHOICES))  # from Literal Beat
        self._beat_content = QLineEdit(self)
        form.addRow(QLabel("Beat @type:", self), self._beat_beat)
        form.addRow(QLabel("Beat Content:", self), self._beat_content)

        # --- Gongche cell ---
        # _gongche_pname: None + all Pitch values
        self._gongche_pname = QComboBox(self)
        self._gongche_pname.addItem("")
        self._gongche_pname.addItems(list(PITCH_CHOICES))  # from Literal Pitch
        self._gongche_content = QLineEdit(self)
        form.addRow(QLabel("Gongche @pname:", self), self._gongche_pname)
        form.addRow(QLabel("Gongche Content:", self), self._gongche_content)

        # --- Syl cell ---
        # _syl_con: None / u
        self._syl_con = QComboBox(self)
        self._syl_con.addItems(["", "u"])
        self._syl_content = QLineEdit(self)
        form.addRow(QLabel("Syl @con:", self), self._syl_con)
        form.addRow(QLabel("Syl Content:", self), self._syl_content)

        # --- Prolongation dot ---
        self._pd_content = QLineEdit(self)
        form.addRow(QLabel("ProlongationDot Content:", self), self._pd_content)

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
        # Beat
        if self._cell_vm.beat is not None:
            beat_type = (self._cell_vm.beat.beat or "").strip()
            if beat_type in ("weak", "strong"):
                self._beat_beat.setCurrentText(beat_type)
            else:
                self._beat_beat.setCurrentText("None")
            self._beat_content.setText(self._cell_vm.beat.content)
        else:
            self._beat_beat.setCurrentText("None")
            self._beat_content.clear()

        # Gongche
        if self._cell_vm.gongche is not None:
            pname = (self._cell_vm.gongche.pname or "").strip()
            if pname in [self._gongche_pname.itemText(i) for i in range(self._gongche_pname.count())]:
                self._gongche_pname.setCurrentText(pname)
            else:
                self._gongche_pname.setCurrentText("None")
            self._gongche_content.setText(self._cell_vm.gongche.content)
        else:
            self._gongche_pname.setCurrentText("None")
            self._gongche_content.clear()

        # Syl
        if self._cell_vm.syl is not None:
            con = (self._cell_vm.syl.con or "").strip()
            if con == "u":
                self._syl_con.setCurrentText("u")
            else:
                self._syl_con.setCurrentText("None")
            self._syl_content.setText(self._cell_vm.syl.content)
        else:
            self._syl_con.setCurrentText("None")
            self._syl_content.clear()

        # Prolongation dot
        if self._cell_vm.prolongation_dot is not None:
            self._pd_content.setText(self._cell_vm.prolongation_dot.content)
        else:
            self._pd_content.clear()

    def accept(self) -> None:
        """
        Writes the dialog values back into the CellBlockViewModel and closes the dialog.
        """
        # Beat
        beat_text = self._beat_beat.currentText().strip()
        beat_content = self._beat_content.text()
        if beat_text or beat_content:
            if self._cell_vm.beat is None:
                self._cell_vm.beat = BeatCellViewModel(parent=self._cell_vm)
            self._cell_vm.beat.beat = beat_text
            self._cell_vm.beat.content = beat_content
        else:
            self._cell_vm.beat = None

        # Gongche
        pname_text = self._gongche_pname.currentText().strip()
        gongche_content = self._gongche_content.text()
        if pname_text or gongche_content:
            if self._cell_vm.gongche is None:
                self._cell_vm.gongche = GongcheCellViewModel(parent=self._cell_vm)
            self._cell_vm.gongche.pname = pname_text
            self._cell_vm.gongche.content = gongche_content
        else:
            self._cell_vm.gongche = None

        # Syl
        syl_con = self._syl_con.currentText().strip()
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

    def __init__(self,
                 document_vm: DocumentViewModel,
                 document_service: DocumentService,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._document_vm = document_vm
        self._document_service = document_service
        self._zone: ZoneViewModel | None = None

        self._document_service.undo_redo_changed.connect(self._populate_block_list)

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

        # Block list as a 5-column table:
        # 0: Type, 1: Beat (left), 2: Text, 3: Beat (right), 4: Attributes
        block_group = QGroupBox("Blocks", self)
        block_layout = QVBoxLayout(block_group)

        self._block_list = QTableWidget(self)
        self._block_list.setColumnCount(5)
        self._block_list.setHorizontalHeaderLabels(["Type", "", "", "", "Attributes"])
        self._block_list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._block_list.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._block_list.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Column sizing
        header = self._block_list.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Type
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Beat (L)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Text
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Beat (R)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Attributes

        self._block_list.cellDoubleClicked.connect(self._edit_block)
        self._block_list.itemSelectionChanged.connect(self._update_enabled_state)
        block_layout.addWidget(self._block_list)

        # --- Button rows ---

        # Row 1: Add / Remove / Edit
        row1_layout = QHBoxLayout()
        self._add_block_btn = QPushButton("Add", self)
        self._remove_block_btn = QPushButton("Remove", self)
        self._edit_block_btn = QPushButton("Edit", self)

        self._add_block_btn.clicked.connect(self._add_block)
        self._remove_block_btn.clicked.connect(self._remove_block)
        self._edit_block_btn.clicked.connect(self._edit_block_clicked)

        self._add_block_btn.setIcon(QIcon.fromTheme(QIcon.ThemeIcon.WindowNew))
        self._remove_block_btn.setIcon(QIcon.fromTheme(QIcon.ThemeIcon.EditClear))
        self._edit_block_btn.setIcon(QIcon.fromTheme(QIcon.ThemeIcon.ToolsCheckSpelling))

        row1_layout.addWidget(self._add_block_btn)
        row1_layout.addWidget(self._remove_block_btn)
        row1_layout.addWidget(self._edit_block_btn)
        row1_layout.addStretch(1)
        block_layout.addLayout(row1_layout)

        # Row 2: Move Up / Move Down
        row2_layout = QHBoxLayout()
        self._move_block_up_button = QPushButton("Move Up", self)
        self._move_block_down_button = QPushButton("Move Down", self)

        self._move_block_up_button.clicked.connect(self._move_block_up)
        self._move_block_down_button.clicked.connect(self._move_block_down)

        self._move_block_up_button.setIcon(QIcon.fromTheme(QIcon.ThemeIcon.GoUp))
        self._move_block_down_button.setIcon(QIcon.fromTheme(QIcon.ThemeIcon.GoDown))

        row2_layout.addWidget(self._move_block_up_button)
        row2_layout.addWidget(self._move_block_down_button)
        row2_layout.addStretch(1)
        block_layout.addLayout(row2_layout)

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
        self._block_list.clearContents()

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

    def _block_row_data(
            self,
            block: object,
    ) -> tuple[str, str | None, str, str | None, str]:
        """
        Returns (Type, BeatLeft, Text, BeatRight, Attributes) for display.

        BeatLeft/BeatRight can be None when not applicable.
        Text is the main text shown in the vertical Text column.
        """
        # Title
        if isinstance(block, TitleBlockViewModel):
            return "Title", None, block.title, None, ""

        # Paragraph
        if isinstance(block, ParagraphBlockViewModel):
            return "Paragraph", None, block.paragraph, None, ""

        # Role annotation
        if isinstance(block, RoleAnnotBlockViewModel):
            roles = " ".join(block.plist) if block.plist else ""
            attr = f"plist={roles}" if roles else ""
            return "RoleAnnot", None, block.content, None, attr

        # Direction
        if isinstance(block, DirectionBlockViewModel):
            plist = " ".join(block.plist) if block.plist else ""
            attr = f"plist={plist}" if plist else ""
            return "Direction", None, f"▲{block.content}▼", None, attr

        # Line
        if isinstance(block, LineBlockViewModel):
            return "Line", None, block.content, None, ""

        # CellBlock
        if isinstance(block, CellBlockViewModel):
            text_display = block.syl.content if block.syl is not None else None
            gongche_display = block.gongche.content if block.gongche is not None else None
            beat_display = block.beat.content if block.beat is not None else None

            if block.prolongation_dot is not None:
                gongche_display += block.prolongation_dot.content

            # Attributes: more detailed summary
            parts = []
            if block.beat is not None:
                parts.append(f'type="{block.beat.beat}"')
            if block.gongche is not None:
                parts.append(f'pname="{block.gongche.pname}"')
            if block.syl is not None:
                parts.append(f'con="{block.syl.con}"')
            attr = ", ".join(parts) if parts else ""

            return "CellBlock", text_display, gongche_display, beat_display, attr

        # Fallback
        type_name = type(block).__name__
        return type_name, None, repr(block), None, ""

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
            type_str, beat_left, text_str, beat_right, attr_str = self._block_row_data(block)

            # --- Column 0: Type (QTableWidgetItem, UserRole stores block) ---
            type_item = QTableWidgetItem(type_str)
            type_item.setData(Qt.ItemDataRole.UserRole, block)

            self._block_list.setItem(row, 0, type_item)

            # --- Column 1: Beat (L) ---
            beat_left_item = QTableWidgetItem(beat_left or "")
            self._block_list.setItem(row, 1, beat_left_item)

            # --- Column 2: Text (VerticalTextWidget) ---
            text_widget = VerticalTextWidget(text_str, parent=self._block_list)
            self._block_list.setCellWidget(row, 2, text_widget)

            # --- Column 3: Beat (R) ---
            beat_right_item = QTableWidgetItem(beat_right or "")
            self._block_list.setItem(row, 3, beat_right_item)

            # --- Column 4: Attributes ---
            attr_item = QTableWidgetItem(attr_str)
            self._block_list.setItem(row, 4, attr_item)

        self._block_list.resizeRowsToContents()

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
        enabled = self._zone is not None
        self._type_combo.setEnabled(enabled)

        # allow adding and removing blocks only with actual content types
        enabled = enabled and self._zone.content is not None
        self._block_list.setEnabled(enabled)
        self._add_block_btn.setEnabled(enabled)
        self._remove_block_btn.setEnabled(enabled)

        # editing, moving up/down is only possible when a block is selected
        enabled = enabled and self._block_list.currentRow() >= 0
        self._edit_block_btn.setEnabled(enabled)
        self._move_block_up_button.setEnabled(enabled)
        self._move_block_down_button.setEnabled(enabled)

    def _add_block(self) -> None:
        """
        Adds a block of a type suitable for the current body.
        Now uses DialogSelectBlockType so the user can choose the block type.
        """
        surface_index = self._document_vm.current_page_index
        zone_index = self._document_vm.selected_zone_index
        if zone_index is None:
            return

        body = self._current_body()
        if body is None:
            return

        # 1) Determine allowed choices based on body type
        if isinstance(body, BodyMetadataViewModel):
            choices = ["Title", "Paragraph"]
        elif isinstance(body, BodyRecitativoViewModel):
            choices = ["RoleAnnot", "Direction", "Line"]
        elif isinstance(body, BodyQupaiViewModel):
            choices = ["RoleAnnot", "Direction", "CellBlock"]
        else:
            return

        # 2) Show dialog to pick the type
        dlg = DialogSelectBlockType(choices, parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        selected = dlg.selected_type  # or whatever attribute your dialog exposes

        # 3) Construct the new block based on `body` and the selected type
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

        # 4) Delegate the *mutation* to DocumentService so it becomes undoable
        self._document_service.add_block(
            surface_index=surface_index,
            zone_index=zone_index,
            block=new_block,
        )

    def _remove_block(self) -> None:
        """
        Removes the currently selected block from the body content.
        """
        surface_index = self._document_vm.current_page_index
        zone_index = self._document_vm.selected_zone_index

        body = self._current_body()
        if body is None:
            return

        row = self._block_list.currentRow()
        if row < 0:
            return

        self._document_service.remove_block(
            surface_index=surface_index,
            zone_index=zone_index,
            block_index=row
        )

    def _edit_block_clicked(self) -> None:
        """
        Slot for the 'Edit Block' button.
        """
        row = self._block_list.currentRow()
        if row < 0:
            return
        self._edit_block(row, 0)

    def _move_block_up(self) -> None:
        """
        Moves the currently selected block one position up.
        """
        body = self._current_body()
        if body is None:
            return

        row = self._block_list.currentRow()
        if row <= 0:  # nothing selected or already at top
            return

        blocks = list(body.content)
        if row >= len(blocks):
            return

        # swap row with row-1
        blocks[row - 1], blocks[row] = blocks[row], blocks[row - 1]

        # write back and repopulate
        self._set_body_content(tuple(blocks))
        self._populate_block_list()

        # restore selection on the new row
        self._block_list.selectRow(row - 1)

    def _move_block_down(self) -> None:
        """
        Moves the currently selected block one position down.
        """
        body = self._current_body()
        if body is None:
            return

        row = self._block_list.currentRow()
        if row < 0:
            return

        blocks = list(body.content)
        if row >= len(blocks) - 1:  # already at the bottom
            return

        # swap row with row+1
        blocks[row], blocks[row + 1] = blocks[row + 1], blocks[row]

        # write back and repopulate
        self._set_body_content(tuple(blocks))
        self._populate_block_list()

        # restore selection on the new row
        self._block_list.selectRow(row + 1)

    def _edit_block(self, row: int, _column: int) -> None:
        """
        Opens an editor for the double-clicked or selected block.
        Called by cellDoubleClicked(row, column).
        """
        type_item = self._block_list.item(row, 0)
        if type_item is None:
            return

        block = type_item.data(Qt.ItemDataRole.UserRole)

        if isinstance(block, (TitleBlockViewModel, ParagraphBlockViewModel,
                              RoleAnnotBlockViewModel, DirectionBlockViewModel,
                              LineBlockViewModel)):
            self._edit_text_block(block)
        elif isinstance(block, CellBlockViewModel):
            self._edit_cell_block(block)
        else:
            return

        # After editing, recompute row data
        type_str, beat_left, text_str, beat_right, attr_str = self._block_row_data(block)

        # --- Column 0: Type ---
        type_item.setText(type_str)
        type_item.setData(Qt.ItemDataRole.UserRole, block)

        # --- Column 1: Beat (L) ---
        beat_left_item = self._block_list.item(row, 1)
        if beat_left_item is None:
            beat_left_item = QTableWidgetItem()
            self._block_list.setItem(row, 1, beat_left_item)
        beat_left_item.setText(beat_left or "")

        # --- Column 2: Text (VerticalTextWidget) ---
        old_text_widget = self._block_list.cellWidget(row, 2)
        if old_text_widget is not None:
            old_text_widget.setParent(None)
        new_text_widget = VerticalTextWidget(text_str, parent=self._block_list)
        self._block_list.setCellWidget(row, 2, new_text_widget)

        # --- Column 3: Beat (R) ---
        beat_right_item = self._block_list.item(row, 3)
        if beat_right_item is None:
            beat_right_item = QTableWidgetItem()
            self._block_list.setItem(row, 3, beat_right_item)
        beat_right_item.setText(beat_right or "")

        # --- Column 4: Attributes ---
        attr_item = self._block_list.item(row, 4)
        if attr_item is None:
            attr_item = QTableWidgetItem()
            self._block_list.setItem(row, 4, attr_item)
        attr_item.setText(attr_str)

        self._block_list.resizeRowsToContents()

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