from __future__ import annotations

from PySide6.QtGui import QIcon, QKeyEvent
from PySide6.QtWidgets import QWidget, QFormLayout, QLineEdit, QLabel, QHBoxLayout, QPushButton, \
    QComboBox, QGroupBox, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView, QGridLayout
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QDialogButtonBox,
    QListWidget,
    QListWidgetItem,
)
from typing import get_args, override

from app.models.document import Beat, Pitch
from app.services.document_service import DocumentService
from app.services.mapping_service import viewmodel_to_cell_block, cell_block_to_viewmodel, viewmodel_to_line_block, \
    line_block_to_viewmodel, viewmodel_to_title_block, title_block_to_viewmodel, viewmodel_to_paragraph_block, \
    paragraph_block_to_viewmodel, viewmodel_to_role_annot_block, role_annot_block_to_viewmodel, \
    viewmodel_to_direction_block, direction_block_to_viewmodel
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

PUNCTUATION_CHARS = set("。，“”、…？！：；—,.!?;:")


def group_lyrics_with_punctuation(lyrics: str) -> tuple[str, ...]:
    """
    Groups a lyrics string into units where punctuation characters are
    attached to the preceding character, e.g.:

        "我爱你，爸爸。" -> ("我", "爱", "你，", "爸。")

    Punctuation is defined in PUNCTUATION_CHARS.
    """
    units: list[str] = []
    current: str | None = None

    for ch in lyrics:
        if ch in PUNCTUATION_CHARS:
            # Append punctuation to the current unit if there is one
            if current is not None:
                current += ch
            else:
                # If punctuation starts the string (rare), treat as its own unit
                current = ch
        else:
            # Non-punctuation: start a new unit
            if current is not None:
                units.append(current)
            current = ch

    # Flush last unit
    if current is not None:
        units.append(current)

    return tuple(units)


class DialogMultipleCells(QDialog):
    """
    Dialog for adding multiple CellBlocks at once.

    It offers two modes:
        1) Lyrics mode: user enters a text; each character becomes one cell.
        2) Count mode: user enters a number; that many empty cells are created.

    Only one mode is active at a time:
        - When lyrics text is non-empty, the number field is disabled.
        - When number > 0, the lyrics box is cleared and disabled.

    On accept, `cell_contents` returns a tuple[str, ...]:
        - Lyrics mode: each character in the text (one per cell).
        - Count mode: N empty strings (""), where N is the entered number.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add Multiple Cells")

        self._cell_contents: tuple[str, ...] = ()

        layout = QVBoxLayout(self)

        form = QFormLayout()
        layout.addLayout(form)

        # Lyrics input
        self._lyrics_edit = QLineEdit(self)
        self._lyrics_edit.setPlaceholderText("Enter lyrics (one character per cell)")
        form.addRow(QLabel("Lyrics:", self), self._lyrics_edit)

        # Number of cells input
        self._count_edit = QLineEdit(self)
        self._count_edit.setPlaceholderText("Enter number of empty cells")
        form.addRow(QLabel("Number of cells:", self), self._count_edit)

        # Connect signals to enforce mutual exclusivity
        self._lyrics_edit.textChanged.connect(self._on_lyrics_changed)
        self._count_edit.textChanged.connect(self._on_count_changed)

        # Buttons
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK", self)
        cancel_btn = QPushButton("Cancel", self)
        ok_btn.clicked.connect(self._on_accept)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addStretch(1)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        self._update_enabled_state()

    @property
    def cell_contents(self) -> tuple[str, ...]:
        """
        Returns the tuple of strings representing the requested cells.

        - Lyrics mode: one character per entry, e.g. ("我", "要", "唱").
        - Count mode: N entries of "", e.g. ("", "", "", "").
        """
        return self._cell_contents

    # --- Internal helpers ---

    def _on_lyrics_changed(self, text: str) -> None:
        """
        Called when the lyrics text changes.
        If lyrics is non-empty, disable the count field.
        """
        text = text or ""
        if text:
            # Disable count, clear it
            self._count_edit.blockSignals(True)
            self._count_edit.clear()
            self._count_edit.blockSignals(False)
        self._update_enabled_state()

    def _on_count_changed(self, text: str) -> None:
        """
        Called when the count text changes.
        If count > 0, disable the lyrics field.
        """
        text = text.strip()
        # Basic validation: only treat as count if it's a positive integer
        count_valid = False
        if text:
            try:
                n = int(text)
                count_valid = n > 0
            except ValueError:
                count_valid = False

        if count_valid:
            # Disable lyrics, clear it
            self._lyrics_edit.blockSignals(True)
            self._lyrics_edit.clear()
            self._lyrics_edit.blockSignals(False)

        self._update_enabled_state()

    def _update_enabled_state(self) -> None:
        """
        Updates enabled/disabled state of the two inputs based on current content.
        """
        lyrics = self._lyrics_edit.text() or ""
        count_text = self._count_edit.text().strip()

        # Check if count is valid
        count_valid = False
        if count_text:
            try:
                n = int(count_text)
                count_valid = n > 0
            except ValueError:
                count_valid = False

        if lyrics:
            # Lyrics mode active
            self._lyrics_edit.setEnabled(True)
            self._count_edit.setEnabled(False)
        elif count_valid:
            # Count mode active
            self._lyrics_edit.setEnabled(False)
            self._count_edit.setEnabled(True)
        else:
            # Neither active yet: both enabled to allow input
            self._lyrics_edit.setEnabled(True)
            self._count_edit.setEnabled(True)

    def _on_accept(self) -> None:
        """
        Builds `self._cell_contents` according to the current mode and closes if valid.
        """
        lyrics = (self._lyrics_edit.text() or "").strip()
        count_text = self._count_edit.text().strip()

        # Lyrics mode
        if lyrics:
            # Group punctuation with preceding characters
            self._cell_contents = group_lyrics_with_punctuation(lyrics)
            self.accept()
            return

        # Count mode
        if count_text:
            try:
                n = int(count_text)
            except ValueError:
                n = 0
        else:
            n = 0

        if n > 0:
            self._cell_contents = tuple("" for _ in range(n))
            self.accept()
            return


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
            self._cell_vm.syl.con = syl_con if syl_con != "" else None
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
        * buttons to add, remove and edit content blocks,
        * a tools panel with shortcut buttons for Qupai cells, Qupai roles/directions,
          and Recitativo roles/directions.
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
        self._document_service.undo_redo_changed.connect(self._update_enabled_state)
        self._document_vm.selected_block_index_changed.connect(self._update_enabled_state)

        # main layout
        main_layout = QVBoxLayout(self)

        # --- Content type selection + tools toggle ---
        type_layout = QHBoxLayout()

        type_layout.addWidget(QLabel("Content type:", self))

        self._type_combo = QComboBox(self)
        self._type_combo.addItems(["None", "Metadata", "Recitativo", "Qupai"])
        self._type_combo.currentIndexChanged.connect(self._content_type_changed)
        type_layout.addWidget(self._type_combo)

        # Toggle button for shortcuts/tools panel
        self._toggle_tools_btn = QPushButton("Show Shortcuts", self)
        self._toggle_tools_btn.setCheckable(True)
        self._toggle_tools_btn.setToolTip("Show/hide the shortcut tools panel")
        self._toggle_tools_btn.clicked.connect(self._toggle_tools_visibility)
        type_layout.addWidget(self._toggle_tools_btn)

        type_layout.addStretch(1)
        main_layout.addLayout(type_layout)

        # --- Blocks + Tools side by side ---
        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout)

        # Left: Blocks group
        block_group = QGroupBox("Blocks", self)
        block_layout = QVBoxLayout(block_group)

        self._block_list = QTableWidget(self)
        self._block_list.setColumnCount(5)
        self._block_list.setHorizontalHeaderLabels(["Type", "", "", "", "Attributes"])
        self._block_list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._block_list.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._block_list.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        header = self._block_list.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Type
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Beat (L)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Text
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Beat (R)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)           # Attributes

        self._block_list.cellDoubleClicked.connect(self._edit_block)
        self._block_list.itemClicked.connect(self._block_selection_changed)
        block_layout.addWidget(self._block_list)

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
        content_layout.addWidget(block_group, stretch=3)

        # Right: Tools panel
        self._tools_group = QGroupBox("Shortcuts", self)
        self._tools_layout = QVBoxLayout(self._tools_group)

        # Build all tool groups
        self._build_recitativo_direction_tools()
        self._build_recitativo_role_tools()
        self._build_qupai_direction_tools()
        self._build_qupai_role_tools()
        self._build_qupai_cell_tools()
        self._build_qupai_beat_tools()
        self._build_qupai_prolongation_tools()

        self._tools_layout.addStretch(1)
        self._tools_group.setLayout(self._tools_layout)
        content_layout.addWidget(self._tools_group, stretch=2)

        self._update_enabled_state()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @override
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Delete:
            # Only delete if a block is selected and the block list has focus
            if self._block_list.hasFocus() and self._remove_block_btn.isEnabled():
                self._remove_block()
                event.accept()
                return
        super().keyPressEvent(event)

    @property
    def shortcuts_visible(self) -> bool:
        return self._toggle_tools_btn.isChecked()

    @shortcuts_visible.setter
    def shortcuts_visible(self, value: bool) -> None:
        self._toggle_tools_btn.setChecked(value)
        self._toggle_tools_btn.setText("Hide Shortcuts" if value else "Show Shortcuts")
        self._toggle_tools_btn.setIcon(
            QIcon.fromTheme(QIcon.ThemeIcon.GoPrevious) if value else QIcon.fromTheme(QIcon.ThemeIcon.GoNext)
        )
        self._tools_group.setVisible(value)

    def set_zone(self, zone: ZoneViewModel | None) -> None:
        """
        Sets the zone whose content should be displayed and edited.
        """
        self._zone = zone
        self._reload_from_zone()

    # ------------------------------------------------------------------
    # Internal: loading / populating
    # ------------------------------------------------------------------

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
            return "Role", None, block.content, None, attr

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
            text_display = block.syl.content if block.syl is not None else ""
            gongche_display = block.gongche.content if block.gongche is not None else ""
            beat_display = block.beat.content if block.beat is not None else ""

            if block.prolongation_dot is not None and gongche_display is not None:
                gongche_display += block.prolongation_dot.content

            parts = []
            if block.beat is not None:
                parts.append(f'type="{block.beat.beat}"')
            if block.gongche is not None:
                parts.append(f'pname="{block.gongche.pname}"')
            if block.syl is not None and block.syl.con is not None:
                parts.append(f'con="{block.syl.con}"')
            attr = ", ".join(parts) if parts else ""

            return "Cell", text_display, gongche_display, beat_display, attr

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

            # Column 0: Type (UserRole stores block)
            type_item = QTableWidgetItem(type_str)
            type_item.setData(Qt.ItemDataRole.UserRole, block)
            self._block_list.setItem(row, 0, type_item)

            # Column 1: Beat (left)
            beat_left_item = QTableWidgetItem(beat_left or "")
            self._block_list.setItem(row, 1, beat_left_item)

            # Column 2: Text (vertical)
            text_widget = VerticalTextWidget(text_str, parent=self._block_list)
            self._block_list.setCellWidget(row, 2, text_widget)

            # Column 3: Beat (right)
            beat_right_item = QTableWidgetItem(beat_right or "")
            self._block_list.setItem(row, 3, beat_right_item)

            # Column 4: Attributes
            attr_item = QTableWidgetItem(attr_str)
            self._block_list.setItem(row, 4, attr_item)

        if self._document_vm.selected_block_index is not None:
            self._block_list.selectRow(self._document_vm.selected_block_index)
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

    # ------------------------------------------------------------------
    # Content type / enabled state
    # ------------------------------------------------------------------

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
        zone_selected = self._zone is not None
        self._type_combo.setEnabled(zone_selected)

        body = self._current_body()
        has_body = zone_selected and body is not None

        self._block_list.setEnabled(has_body)
        self._add_block_btn.setEnabled(has_body)

        selected_index = self._document_vm.selected_block_index
        block_selected = has_body and selected_index is not None

        self._remove_block_btn.setEnabled(block_selected)
        self._edit_block_btn.setEnabled(block_selected)
        self._move_block_up_button.setEnabled(block_selected)
        self._move_block_down_button.setEnabled(block_selected)

        self._update_tools_enabled()

    def _update_tools_enabled(self) -> None:
        """
        Enables/disables all shortcut buttons based on body type and selected block type.
        Buttons remain visible at all times.
        """
        body = self._current_body()
        index = self._document_vm.selected_block_index
        zone_has_body = body is not None
        block_selected = index is not None and zone_has_body

        # Disable everything by default
        for btn in getattr(self, "_gongche_buttons", []):
            btn.setEnabled(False)
        for btn in getattr(self, "_beat_buttons", []):
            btn.setEnabled(False)
        for btn in getattr(self, "_recit_dir_buttons", []):
            btn.setEnabled(False)
        for btn in getattr(self, "_recit_role_buttons", []):
            btn.setEnabled(False)
        for btn in getattr(self, "_qupai_dir_buttons", []):
            btn.setEnabled(False)
        for btn in getattr(self, "_qupai_role_buttons", []):
            btn.setEnabled(False)
        if hasattr(self, "_btn_no_dot"):
            self._btn_no_dot.setEnabled(False)
        if hasattr(self, "_btn_with_dot"):
            self._btn_with_dot.setEnabled(False)

        if not block_selected:
            return

        type_item = self._block_list.item(index, 0)
        if type_item is None:
            return
        block = type_item.data(Qt.ItemDataRole.UserRole)

        # Enable Qupai Cell tools
        if isinstance(body, BodyQupaiViewModel) and isinstance(block, CellBlockViewModel):
            for btn in self._gongche_buttons:
                btn.setEnabled(True)
            for btn in self._beat_buttons:
                btn.setEnabled(True)
            self._btn_no_dot.setEnabled(True)
            self._btn_with_dot.setEnabled(True)

        # Recitativo Direction
        if isinstance(body, BodyRecitativoViewModel) and isinstance(block, DirectionBlockViewModel):
            for btn in self._recit_dir_buttons:
                btn.setEnabled(True)

        # Recitativo RoleAnnot
        if isinstance(body, BodyRecitativoViewModel) and isinstance(block, RoleAnnotBlockViewModel):
            for btn in self._recit_role_buttons:
                btn.setEnabled(True)

        # Qupai Direction
        if isinstance(body, BodyQupaiViewModel) and isinstance(block, DirectionBlockViewModel):
            for btn in self._qupai_dir_buttons:
                btn.setEnabled(True)

        # Qupai RoleAnnot
        if isinstance(body, BodyQupaiViewModel) and isinstance(block, RoleAnnotBlockViewModel):
            for btn in self._qupai_role_buttons:
                btn.setEnabled(True)

    # ------------------------------------------------------------------
    # Block operations
    # ------------------------------------------------------------------

    def _add_block(self) -> None:
        """
        Adds a block of a type suitable for the current body.
        Uses DialogSelectBlockType so the user can choose the block type.
        """
        surface_index = self._document_vm.current_page_index
        zone_index = self._document_vm.selected_zone_index
        if zone_index is None:
            return

        body = self._current_body()
        if body is None:
            return

        if isinstance(body, BodyMetadataViewModel):
            choices = ["Title", "Paragraph"]
        elif isinstance(body, BodyRecitativoViewModel):
            choices = ["RoleAnnot", "Direction", "Line"]
        elif isinstance(body, BodyQupaiViewModel):
            choices = ["RoleAnnot", "Direction", "Cell", "Multiple Cells..."]
        else:
            return

        dlg = DialogSelectBlockType(choices, parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        selected = dlg.selected_type

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
            elif selected == "Cell":
                new_block = CellBlockViewModel(parent=body)
            elif selected == "Multiple Cells...":
                dlg = DialogMultipleCells(parent=self)
                if dlg.exec() != QDialog.DialogCode.Accepted:
                    return

                contents = dlg.cell_contents

                surface_index = self._document_vm.current_page_index
                zone_index = self._document_vm.selected_zone_index
                if zone_index is None:
                    return

                zone_vm = self._document_vm.surfaces[surface_index].zones[zone_index]

                for offset, text in enumerate(contents):
                    cb = CellBlockViewModel(parent=body)
                    if text:
                        cb.syl = SylCellViewModel(parent=cb)
                        cb.syl.content = text
                        cb.syl.con = None
                    self._document_service.add_block(
                        surface_index=surface_index,
                        zone_index=zone_index,
                        block=cb,
                    )

                return
            else:
                return

        else:
            return

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

        selected_block = self._document_vm.selected_block_index
        if selected_block is None:
            return

        self._document_service.remove_block(
            surface_index=surface_index,
            zone_index=zone_index,
            block_index=selected_block
        )

    def _edit_block_clicked(self) -> None:
        """
        Slot for the 'Edit Block' button.
        """
        selected_block = self._document_vm.selected_block_index
        if selected_block is None:
            return
        self._edit_block(selected_block, 0)

    def _move_block_up(self) -> None:
        """
        Moves the currently selected block one position up.
        """
        self._document_service.change_block_order(
            self._document_vm.current_page_index,
            self._document_vm.selected_zone_index,
            self._document_vm.selected_block_index,
            self._document_vm.selected_block_index - 1,
        )

    def _move_block_down(self) -> None:
        """
        Moves the currently selected block one position down.
        """
        self._document_service.change_block_order(
            self._document_vm.current_page_index,
            self._document_vm.selected_zone_index,
            self._document_vm.selected_block_index,
            self._document_vm.selected_block_index + 1,
        )

    def _edit_block(self, row: int, _column: int) -> None:
        """
        Opens an editor for the double-clicked or selected block.
        """
        type_item = self._block_list.item(row, 0)
        if type_item is None:
            return

        block = type_item.data(Qt.ItemDataRole.UserRole)

        if isinstance(block, TitleBlockViewModel):
            edited_block = TitleBlockViewModel(parent=block.parent())
            title_block_to_viewmodel(viewmodel_to_title_block(block), edited_block)
            editing_accepted = self._edit_text_block(edited_block)
        elif isinstance(block, ParagraphBlockViewModel):
            edited_block = ParagraphBlockViewModel(parent=block.parent())
            paragraph_block_to_viewmodel(viewmodel_to_paragraph_block(block), edited_block)
            editing_accepted = self._edit_text_block(edited_block)
        elif isinstance(block, RoleAnnotBlockViewModel):
            edited_block = RoleAnnotBlockViewModel(parent=block.parent())
            role_annot_block_to_viewmodel(viewmodel_to_role_annot_block(block), edited_block)
            editing_accepted = self._edit_text_block(edited_block)
        elif isinstance(block, DirectionBlockViewModel):
            edited_block = DirectionBlockViewModel(parent=block.parent())
            direction_block_to_viewmodel(viewmodel_to_direction_block(block), edited_block)
            editing_accepted = self._edit_text_block(edited_block)
        elif isinstance(block, LineBlockViewModel):
            edited_block = LineBlockViewModel(parent=block.parent())
            line_block_to_viewmodel(viewmodel_to_line_block(block), edited_block)
            editing_accepted = self._edit_text_block(edited_block)
        elif isinstance(block, CellBlockViewModel):
            edited_block = CellBlockViewModel(parent=block.parent())
            cell_block_to_viewmodel(viewmodel_to_cell_block(block), edited_block)
            editing_accepted = self._edit_cell_block(edited_block)
        else:
            return

        if editing_accepted:
            self._document_service.edit_block(
                self._document_vm.current_page_index,
                self._document_vm.selected_zone_index,
                self._document_vm.selected_block_index,
                edited_block
            )
        self._block_list.resizeRowsToContents()

    def _edit_text_block(self, block: object) -> bool:
        """
        Simple dialog for editing one of the text based blocks.
        Returns True if the editing was accepted.
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
            return False

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

        return True

    def _edit_cell_block(self, cell_block: CellBlockViewModel) -> bool:
        """
        Opens a dialog to edit a CellBlockViewModel and its nested cells.
        """
        dialog = CellBlockDialog(cell_block, parent=self)
        result = dialog.exec()
        return result == QDialog.DialogCode.Accepted

    def _block_selection_changed(self) -> None:
        selected_block = self._block_list.currentRow()
        if selected_block < 0:
            self._document_service.select_block(None)
            return
        self._document_service.select_block(selected_block)

    # ------------------------------------------------------------------
    # Tools: creation
    # ------------------------------------------------------------------

    def _build_qupai_cell_tools(self) -> None:
        gongche_group = QGroupBox("Qupai (Pitch)", self)
        grid = QGridLayout(gongche_group)

        rows = [
            [
                ("lower_he", "佮"),
                ("lower_shi", "仕"),
                ("lower_yi", "亿"),
                ("lower_shang", "仩"),
                ("lower_che", "伬"),
                ("lower_gong", "仜"),
                ("lower_fan", "仮")
            ],
            [
                ("he", "合"),
                ("shi", "士"),
                ("yi", "乙"),
                ("shang", "上"),
                ("che", "尺"),
                ("gong", "工"),
                ("fan", "反"),
            ],
            [
                ("liu", "六"),
                ("wu", "五"),
                ("higher_yi", "𢒼"),
                ("sheng", "生"),
                ("higher_che", "鿈"),
                ("higher_gong", "𢓁"),
                ("higher_fan", "𢓉"),
            ],
            [
                ("higher_liu", "𢓌"),
                ("higher_wu", "鿉")
            ]
        ]

        self._gongche_buttons: list[QPushButton] = []

        for row_idx, row_data in enumerate(rows):
            for col_idx, (pname, content) in enumerate(row_data):
                btn = QPushButton(content, self)
                btn.setToolTip(f"Set gongche to {content} ({pname})")
                btn.clicked.connect(
                    lambda checked=False, pn=pname, ct=content: self._apply_qupai_cell_gongche(pn, ct)
                )
                grid.addWidget(btn, row_idx, col_idx)
                self._gongche_buttons.append(btn)

        gongche_group.setLayout(grid)
        self._tools_layout.addWidget(gongche_group)

    def _build_qupai_beat_tools(self) -> None:
        beat_group = QGroupBox("Qupai (Beat)", self)
        layout = QHBoxLayout(beat_group)

        specs = [
            ("strong", "×", "Strong beat on syllable"),
            ("strong", "⨱", "Strong beat without syllable"),
            ("weak", "、", "Weak beat on syllable"),
            ("weak", "⌞", "Weak beat without syllable"),
        ]

        self._beat_buttons: list[QPushButton] = []

        for beat, content, tooltip in specs:
            btn = QPushButton(content, self)
            btn.setToolTip(tooltip)
            btn.clicked.connect(
                lambda checked=False, b=beat, ct=content: self._apply_qupai_cell_beat(b, ct)
            )
            layout.addWidget(btn)
            self._beat_buttons.append(btn)

        beat_group.setLayout(layout)
        self._tools_layout.addWidget(beat_group)

    def _build_qupai_prolongation_tools(self) -> None:
        pd_group = QGroupBox("Qupai (Prolongation Dot)", self)
        layout = QHBoxLayout(pd_group)

        self._btn_no_dot = QPushButton("No Dot", self)
        self._btn_with_dot = QPushButton("·", self)

        self._btn_no_dot.setToolTip("Remove prolongation dot")
        self._btn_with_dot.setToolTip("Add prolongation dot ·")

        self._btn_no_dot.clicked.connect(lambda checked=False: self._apply_qupai_prolongation_dot(False))
        self._btn_with_dot.clicked.connect(lambda checked=False: self._apply_qupai_prolongation_dot(True))

        layout.addWidget(self._btn_no_dot)
        layout.addWidget(self._btn_with_dot)

        pd_group.setLayout(layout)
        self._tools_layout.addWidget(pd_group)

    def _build_recitativo_direction_tools(self) -> None:
        group = QGroupBox("Recitativo (Direction)", self)
        layout = QHBoxLayout(group)

        specs = [
            ("#recitativo", "詩白", "Start recitativo"),
            (None, "接白", "Continue recitativo"),
        ]

        self._recit_dir_buttons: list[QPushButton] = []

        for plist, content, tooltip in specs:
            btn = QPushButton(content, self)
            btn.setToolTip(tooltip)
            btn.clicked.connect(
                lambda checked=False, pl=plist, ct=content: self._apply_recitativo_direction(pl, ct)
            )
            layout.addWidget(btn)
            self._recit_dir_buttons.append(btn)

        group.setLayout(layout)
        self._tools_layout.addWidget(group)

    def _build_recitativo_role_tools(self) -> None:
        group = QGroupBox("Recitativo (Role)", self)
        layout = QHBoxLayout(group)

        specs = [
            ("singer_sheng", "生"),
            ("#singer_dan", "旦"),
        ]

        self._recit_role_buttons: list[QPushButton] = []

        for plist, content in specs:
            btn = QPushButton(content, self)
            btn.setToolTip(f"Recitativo role: {content}")
            btn.clicked.connect(
                lambda checked=False, pl=plist, ct=content: self._apply_recitativo_role(pl, ct)
            )
            layout.addWidget(btn)
            self._recit_role_buttons.append(btn)

        group.setLayout(layout)
        self._tools_layout.addWidget(group)

    def _build_qupai_direction_tools(self) -> None:
        group = QGroupBox("Qupai (Direction)", self)
        layout = QHBoxLayout(group)

        specs = [
            ("#accompanied", "!TODO!", "（曲牌）", "Start of Qupai"),   # accompanied, empty content
            (None, "接唱", "接唱", "Continue Qupai"),                   # plain "接唱"
        ]

        self._qupai_dir_buttons: list[QPushButton] = []

        for plist, content, label, tooltip in specs:
            btn = QPushButton(label, self)
            btn.setToolTip(tooltip)
            btn.clicked.connect(
                lambda checked=False, pl=plist, ct=content: self._apply_qupai_direction(pl, ct)
            )
            layout.addWidget(btn)
            self._qupai_dir_buttons.append(btn)

        group.setLayout(layout)
        self._tools_layout.addWidget(group)

    def _build_qupai_role_tools(self) -> None:
        group = QGroupBox("Qupai (Role)", self)
        layout = QGridLayout(group)

        specs = [
            ("#singer_sheng", "生", "生", "Annotated 生, start with 生"),
            ("#singer_dan", "旦", "旦", "Annotated 旦, start with 旦"),
            ("#orchestra", "生", "生 (orchestra)", "Annotated 生, start with orchestra-only"),
            ("#orchestra", "旦", "旦 (orchestra)", "Annotated 旦, start with orchestra-only"),
            (None, "（", "（", "Start of orchestra-only, already annotated"),
            ("#orchestra", "（", "（ (orchestra)", "After singing, start with orchestra-only"),
            ("#singer_sheng", "）", "）(生)", "After orchestra-only, start with 生"),
            ("#singer_dan", "）", "）(旦)", "After orchestra-only, start with 旦"),
        ]

        self._qupai_role_buttons: list[QPushButton] = []

        for idx, (plist, content, label, tooltip) in enumerate(specs):
            btn = QPushButton(label, self)
            btn.setToolTip(tooltip)
            btn.clicked.connect(
                lambda checked=False, pl=plist, ct=content: self._apply_qupai_role(pl, ct)
            )
            row, col = divmod(idx, 4)
            layout.addWidget(btn, row, col)
            self._qupai_role_buttons.append(btn)

        group.setLayout(layout)
        self._tools_layout.addWidget(group)

    # ------------------------------------------------------------------
    # Tools: mutation handlers
    # ------------------------------------------------------------------

    def _apply_qupai_cell_gongche(self, pname: str, content: str) -> None:
        index = self._document_vm.selected_block_index
        if index is None or self._zone is None:
            return

        if not isinstance(self._zone.content, BodyQupaiViewModel):
            return

        type_item = self._block_list.item(index, 0)
        if type_item is None:
            return
        block = type_item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(block, CellBlockViewModel):
            return

        edited_block = CellBlockViewModel(parent=block.parent())
        cell_block_to_viewmodel(viewmodel_to_cell_block(block), edited_block)

        if edited_block.gongche is None:
            edited_block.gongche = GongcheCellViewModel(parent=edited_block)
        edited_block.gongche.pname = pname
        edited_block.gongche.content = content

        self._document_service.edit_block(
            self._document_vm.current_page_index,
            self._document_vm.selected_zone_index,
            index,
            edited_block,
        )

    def _apply_qupai_cell_beat(self, beat: str, content: str) -> None:
        index = self._document_vm.selected_block_index
        if index is None or self._zone is None:
            return

        if not isinstance(self._zone.content, BodyQupaiViewModel):
            return

        type_item = self._block_list.item(index, 0)
        if type_item is None:
            return
        block = type_item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(block, CellBlockViewModel):
            return

        edited_block = CellBlockViewModel(parent=block.parent())
        cell_block_to_viewmodel(viewmodel_to_cell_block(block), edited_block)

        if edited_block.beat is None:
            edited_block.beat = BeatCellViewModel(parent=edited_block)
        edited_block.beat.beat = beat
        edited_block.beat.content = content

        self._document_service.edit_block(
            self._document_vm.current_page_index,
            self._document_vm.selected_zone_index,
            index,
            edited_block,
        )

    def _apply_qupai_prolongation_dot(self, use_dot: bool) -> None:
        index = self._document_vm.selected_block_index
        if index is None or self._zone is None:
            return

        if not isinstance(self._zone.content, BodyQupaiViewModel):
            return

        type_item = self._block_list.item(index, 0)
        if type_item is None:
            return
        block = type_item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(block, CellBlockViewModel):
            return

        edited_block = CellBlockViewModel(parent=block.parent())
        cell_block_to_viewmodel(viewmodel_to_cell_block(block), edited_block)

        if use_dot:
            if edited_block.prolongation_dot is None:
                edited_block.prolongation_dot = ProlongationDotCellViewModel(parent=edited_block)
            edited_block.prolongation_dot.content = "·"
        else:
            edited_block.prolongation_dot = None

        self._document_service.edit_block(
            self._document_vm.current_page_index,
            self._document_vm.selected_zone_index,
            index,
            edited_block,
        )

    def _apply_recitativo_direction(self, plist: str | None, content: str) -> None:
        index = self._document_vm.selected_block_index
        if index is None or self._zone is None:
            return

        if not isinstance(self._zone.content, BodyRecitativoViewModel):
            return

        type_item = self._block_list.item(index, 0)
        if type_item is None:
            return
        block = type_item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(block, DirectionBlockViewModel):
            return

        edited_block = DirectionBlockViewModel(parent=block.parent())
        direction_block_to_viewmodel(viewmodel_to_direction_block(block), edited_block)

        if plist is None:
            edited_block.plist = ()
        else:
            edited_block.plist = (plist,)
        edited_block.content = content

        self._document_service.edit_block(
            self._document_vm.current_page_index,
            self._document_vm.selected_zone_index,
            index,
            edited_block,
        )

    def _apply_recitativo_role(self, plist: str, content: str) -> None:
        index = self._document_vm.selected_block_index
        if index is None or self._zone is None:
            return

        if not isinstance(self._zone.content, BodyRecitativoViewModel):
            return

        type_item = self._block_list.item(index, 0)
        if type_item is None:
            return
        block = type_item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(block, RoleAnnotBlockViewModel):
            return

        edited_block = RoleAnnotBlockViewModel(parent=block.parent())
        role_annot_block_to_viewmodel(viewmodel_to_role_annot_block(block), edited_block)

        edited_block.plist = (plist,)
        edited_block.content = content

        self._document_service.edit_block(
            self._document_vm.current_page_index,
            self._document_vm.selected_zone_index,
            index,
            edited_block,
        )

    def _apply_qupai_direction(self, plist: str | None, content: str) -> None:
        index = self._document_vm.selected_block_index
        if index is None or self._zone is None:
            return

        if not isinstance(self._zone.content, BodyQupaiViewModel):
            return

        type_item = self._block_list.item(index, 0)
        if type_item is None:
            return
        block = type_item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(block, DirectionBlockViewModel):
            return

        edited_block = DirectionBlockViewModel(parent=block.parent())
        direction_block_to_viewmodel(viewmodel_to_direction_block(block), edited_block)

        if plist is None:
            edited_block.plist = ()
        else:
            edited_block.plist = (plist,)
        edited_block.content = content

        self._document_service.edit_block(
            self._document_vm.current_page_index,
            self._document_vm.selected_zone_index,
            index,
            edited_block,
        )

    def _apply_qupai_role(self, plist: str | None, content: str) -> None:
        index = self._document_vm.selected_block_index
        if index is None or self._zone is None:
            return

        if not isinstance(self._zone.content, BodyQupaiViewModel):
            return

        type_item = self._block_list.item(index, 0)
        if type_item is None:
            return
        block = type_item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(block, RoleAnnotBlockViewModel):
            return

        edited_block = RoleAnnotBlockViewModel(parent=block.parent())
        role_annot_block_to_viewmodel(viewmodel_to_role_annot_block(block), edited_block)

        if plist is None:
            edited_block.plist = ()
        else:
            edited_block.plist = (plist,)
        edited_block.content = content

        self._document_service.edit_block(
            self._document_vm.current_page_index,
            self._document_vm.selected_zone_index,
            index,
            edited_block,
        )

    def _toggle_tools_visibility(self) -> None:
        """
        Show or hide the tools (shortcuts) panel, controlled by the toggle button.
        """
        # Checked => show; unchecked => hide
        visible = self._toggle_tools_btn.isChecked()

        if visible:
            self._tools_group.show()
            self._toggle_tools_btn.setText("Hide Shortcuts")
            self._toggle_tools_btn.setIcon(QIcon.fromTheme(QIcon.ThemeIcon.GoPrevious))
        else:
            self._tools_group.hide()
            self._toggle_tools_btn.setText("Show Shortcuts")
            self._toggle_tools_btn.setIcon(QIcon.fromTheme(QIcon.ThemeIcon.GoNext))