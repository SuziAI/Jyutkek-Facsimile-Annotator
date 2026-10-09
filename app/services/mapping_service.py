from __future__ import annotations

from app.models.document import (
    Document,
    Surface,
    Zone,
    BodyQupai,
    BodyMetadata,
    BodyRecitativo,
    ProlongationDotCell,
    SylCell,
    GongcheCell,
    BeatCell,
    CellBlock,
    RoleAnnotBlock,
    DirectionBlock,
    LineBlock,
    TitleBlock,
    ParagraphBlock,
)
from app.viewmodels.content_cell_viewmodel import (
    ProlongationDotCellViewModel,
    SylCellViewModel,
    GongcheCellViewModel,
    BeatCellViewModel,
)
from app.viewmodels.content_viewmodel import (
    BodyQupaiViewModel,
    BodyMetadataViewModel,
    BodyRecitativoViewModel,
)
from app.viewmodels.document_viewmodel import DocumentViewModel
from app.viewmodels.surface_viewmodel import SurfaceViewModel
from app.viewmodels.zone_viewmodel import ZoneViewModel
from app.viewmodels.content_block_viewmodel import (
    TitleBlockViewModel,
    ParagraphBlockViewModel,
    CellBlockViewModel,
    RoleAnnotBlockViewModel,
    DirectionBlockViewModel,
    LineBlockViewModel,
)

# ---------------------------------------------------------------------------
# Cell-level mappers
# ---------------------------------------------------------------------------

def prolongation_dot_cell_to_viewmodel(
    prolongation_dot_cell: ProlongationDotCell,
    vm: ProlongationDotCellViewModel,
) -> None:
    """
    Set the ProlongationDotCellViewModel parameters according to the
    ProlongationDotCell model properties.
    """
    vm.content = prolongation_dot_cell.content


def viewmodel_to_prolongation_dot_cell(vm: ProlongationDotCellViewModel) -> ProlongationDotCell:
    """
    Persists the ProlongationDotCellViewModel parameters into a
    ProlongationDotCell model.
    """
    return ProlongationDotCell(
        content=vm.content,
    )


def syl_cell_to_viewmodel(syl_cell: SylCell, vm: SylCellViewModel) -> None:
    """
    Set the SylCellViewModel parameters according to the SylCell model properties.
    """
    vm.con = syl_cell.con
    vm.content = syl_cell.content


def viewmodel_to_syl_cell(vm: SylCellViewModel) -> SylCell:
    """
    Persists the SylCellViewModel parameters into a SylCell model.
    """
    return SylCell(
        con=vm.con,
        content=vm.content,
    )


def gongche_cell_to_viewmodel(gongche_cell: GongcheCell, vm: GongcheCellViewModel) -> None:
    """
    Set the GongcheCellViewModel parameters according to the GongcheCell model
    properties.
    """
    vm.pname = gongche_cell.pname
    vm.content = gongche_cell.content


def viewmodel_to_gongche_cell(vm: GongcheCellViewModel) -> GongcheCell:
    """
    Persists the GongcheCellViewModel parameters into a GongcheCell model.
    """
    return GongcheCell(
        pname=vm.pname,
        content=vm.content,
    )


def beat_cell_to_viewmodel(beat_cell: BeatCell, vm: BeatCellViewModel) -> None:
    """
    Set the BeatCellViewModel parameters according to the BeatCell model
    properties.
    """
    vm.beat = beat_cell.beat
    vm.content = beat_cell.content


def viewmodel_to_beat_cell(vm: BeatCellViewModel) -> BeatCell:
    """
    Persists the BeatCellViewModel parameters into a BeatCell model.
    """
    return BeatCell(
        beat=vm.beat,
        content=vm.content,
    )


def cell_block_to_viewmodel(cell_block: CellBlock, vm: CellBlockViewModel) -> None:
    """
    Set the CellBlockViewModel parameters according to the CellBlock model
    properties.
    """
    # Beat
    if cell_block.beat is not None:
        beat_vm = vm.beat
        if beat_vm is None:
            beat_vm = BeatCellViewModel(parent=vm)
        beat_cell_to_viewmodel(cell_block.beat, beat_vm)
        vm.beat = beat_vm
    else:
        vm.beat = None

    # Gongche
    if cell_block.gongche is not None:
        gongche_vm = vm.gongche
        if gongche_vm is None:
            gongche_vm = GongcheCellViewModel(parent=vm)
        gongche_cell_to_viewmodel(cell_block.gongche, gongche_vm)
        vm.gongche = gongche_vm
    else:
        vm.gongche = None

    # Syl
    if cell_block.syl is not None:
        syl_vm = vm.syl
        if syl_vm is None:
            syl_vm = SylCellViewModel(parent=vm)
        syl_cell_to_viewmodel(cell_block.syl, syl_vm)
        vm.syl = syl_vm
    else:
        vm.syl = None

    # Prolongation dot
    if cell_block.prolongation_dot is not None:
        pd_vm = vm.prolongation_dot
        if pd_vm is None:
            pd_vm = ProlongationDotCellViewModel(parent=vm)
        prolongation_dot_cell_to_viewmodel(cell_block.prolongation_dot, pd_vm)
        vm.prolongation_dot = pd_vm
    else:
        vm.prolongation_dot = None


def viewmodel_to_cell_block(vm: CellBlockViewModel) -> CellBlock:
    """
    Persists the CellBlockViewModel parameters into a CellBlock model.
    """
    beat_model = viewmodel_to_beat_cell(vm.beat) if vm.beat is not None else None
    gongche_model = (
        viewmodel_to_gongche_cell(vm.gongche) if vm.gongche is not None else None
    )
    syl_model = viewmodel_to_syl_cell(vm.syl) if vm.syl is not None else None
    prolongation_dot_model = (
        viewmodel_to_prolongation_dot_cell(vm.prolongation_dot)
        if vm.prolongation_dot is not None
        else None
    )

    return CellBlock(
        beat=beat_model,
        gongche=gongche_model,
        syl=syl_model,
        prolongation_dot=prolongation_dot_model,
    )

# ---------------------------------------------------------------------------
# Block-level mappers
# ---------------------------------------------------------------------------

def title_block_to_viewmodel(title_block: TitleBlock, vm: TitleBlockViewModel) -> None:
    """
    Set the TitleBlockViewModel parameters according to the TitleBlock model
    properties.
    """
    vm.title = title_block.title


def viewmodel_to_title_block(vm: TitleBlockViewModel) -> TitleBlock:
    """
    Persists the TitleBlockViewModel parameters into a TitleBlock model.
    """
    return TitleBlock(
        title=vm.title,
    )


def paragraph_block_to_viewmodel(
    paragraph_block: ParagraphBlock,
    vm: ParagraphBlockViewModel,
) -> None:
    """
    Set the ParagraphBlockViewModel parameters according to the ParagraphBlock
    model properties.
    """
    vm.paragraph = paragraph_block.paragraph


def viewmodel_to_paragraph_block(vm: ParagraphBlockViewModel) -> ParagraphBlock:
    """
    Persists the ParagraphBlockViewModel parameters into a ParagraphBlock model.
    """
    return ParagraphBlock(
        paragraph=vm.paragraph,
    )


def role_annot_block_to_viewmodel(
    role_annot_block: RoleAnnotBlock,
    vm: RoleAnnotBlockViewModel,
) -> None:
    """
    Set the RoleAnnotBlockViewModel parameters according to the RoleAnnotBlock
    model properties.
    """
    # RoleAnnotBlock.plist is a tuple[RoleAnnot]; VM uses tuple[str]
    vm.plist = tuple(role_annot_block.plist)
    vm.content = role_annot_block.content


def viewmodel_to_role_annot_block(vm: RoleAnnotBlockViewModel) -> RoleAnnotBlock:
    """
    Persists the RoleAnnotBlockViewModel parameters into a RoleAnnotBlock model.
    """
    return RoleAnnotBlock(
        plist=tuple(vm.plist),
        content=vm.content,
    )


def direction_block_to_viewmodel(
    direction_block: DirectionBlock,
    vm: DirectionBlockViewModel,
) -> None:
    """
    Set the DirectionBlockViewModel parameters according to the DirectionBlock
    model properties.
    """
    # DirectionBlock.plist is tuple[Direction]; VM uses tuple[str]
    vm.plist = tuple(direction_block.plist)
    vm.content = direction_block.content


def viewmodel_to_direction_block(vm: DirectionBlockViewModel) -> DirectionBlock:
    """
    Persists the DirectionBlockViewModel parameters into a DirectionBlock model.
    """
    return DirectionBlock(
        plist=tuple(vm.plist),
        content=vm.content,
    )


def line_block_to_viewmodel(line_block: LineBlock, vm: LineBlockViewModel) -> None:
    """
    Set the LineBlockViewModel parameters according to the LineBlock model
    properties.
    """
    vm.content = line_block.content


def viewmodel_to_line_block(vm: LineBlockViewModel) -> LineBlock:
    """
    Persists the LineBlockViewModel parameters into a LineBlock model.
    """
    return LineBlock(
        content=vm.content,
    )

# ---------------------------------------------------------------------------
# Body mappers
# ---------------------------------------------------------------------------

def body_metadata_to_viewmodel(body_metadata: BodyMetadata, vm: BodyMetadataViewModel) -> None:
    """
    Set the BodyMetadataViewModel parameters according to the BodyMetadata model
    properties.
    """
    content_vms: list[TitleBlockViewModel | ParagraphBlockViewModel] = []

    for block in body_metadata.content:
        if isinstance(block, TitleBlock):
            block_vm = TitleBlockViewModel(parent=vm)
            title_block_to_viewmodel(block, block_vm)
        elif isinstance(block, ParagraphBlock):
            block_vm = ParagraphBlockViewModel(parent=vm)
            paragraph_block_to_viewmodel(block, block_vm)
        else:
            raise TypeError(f"Unsupported BodyMetadata block type: {type(block)!r}")
        content_vms.append(block_vm)

    vm.content = tuple(content_vms)


def viewmodel_to_body_metadata(vm: BodyMetadataViewModel) -> BodyMetadata:
    """
    Persists the BodyMetadataViewModel parameters into a BodyMetadata model.
    """
    content_models: list[TitleBlock | ParagraphBlock] = []

    for block_vm in vm.content:
        if isinstance(block_vm, TitleBlockViewModel):
            content_models.append(viewmodel_to_title_block(block_vm))
        elif isinstance(block_vm, ParagraphBlockViewModel):
            content_models.append(viewmodel_to_paragraph_block(block_vm))
        else:
            raise TypeError(
                f"Unsupported BodyMetadata block viewmodel type: {type(block_vm)!r}"
            )

    return BodyMetadata(
        content=tuple(content_models),
    )


def body_recitativo_to_viewmodel(
    body_recitativo: BodyRecitativo,
    vm: BodyRecitativoViewModel,
) -> None:
    """
    Set the BodyRecitativoViewModel parameters according to the BodyRecitativo
    model properties.
    """
    content_vms: list[RoleAnnotBlock | DirectionBlock | LineBlock] = []

    for block in body_recitativo.content:
        if isinstance(block, RoleAnnotBlock):
            block_vm = RoleAnnotBlockViewModel(parent=vm)
            role_annot_block_to_viewmodel(block, block_vm)
        elif isinstance(block, DirectionBlock):
            block_vm = DirectionBlockViewModel(parent=vm)
            direction_block_to_viewmodel(block, block_vm)
        elif isinstance(block, LineBlock):
            block_vm = LineBlockViewModel(parent=vm)
            line_block_to_viewmodel(block, block_vm)
        else:
            raise TypeError(
                f"Unsupported BodyRecitativo block type: {type(block)!r}"
            )
        content_vms.append(block_vm)

    # Note: type hint in BodyRecitativoViewModel currently uses model types,
    # but we store the corresponding block *viewmodels* here.
    vm.content = tuple(content_vms)  # type: ignore[assignment]


def viewmodel_to_body_recitativo(vm: BodyRecitativoViewModel) -> BodyRecitativo:
    """
    Persists the BodyRecitativoViewModel parameters into a BodyRecitativo model.
    """
    content_models: list[RoleAnnotBlock | DirectionBlock | LineBlock] = []

    for block_vm in vm.content:
        if isinstance(block_vm, RoleAnnotBlockViewModel):
            content_models.append(viewmodel_to_role_annot_block(block_vm))
        elif isinstance(block_vm, DirectionBlockViewModel):
            content_models.append(viewmodel_to_direction_block(block_vm))
        elif isinstance(block_vm, LineBlockViewModel):
            content_models.append(viewmodel_to_line_block(block_vm))
        else:
            raise TypeError(
                f"Unsupported BodyRecitativo block viewmodel type: {type(block_vm)!r}"
            )

    return BodyRecitativo(
        content=tuple(content_models),
    )


def body_qupai_to_viewmodel(body_qupai: BodyQupai, vm: BodyQupaiViewModel) -> None:
    """
    Set the BodyQupaiViewModel parameters according to the BodyQupai model
    properties.
    """
    content_vms: list[RoleAnnotBlock | DirectionBlock | CellBlock] = []

    for block in body_qupai.content:
        if isinstance(block, RoleAnnotBlock):
            block_vm = RoleAnnotBlockViewModel(parent=vm)
            role_annot_block_to_viewmodel(block, block_vm)
        elif isinstance(block, DirectionBlock):
            block_vm = DirectionBlockViewModel(parent=vm)
            direction_block_to_viewmodel(block, block_vm)
        elif isinstance(block, CellBlock):
            block_vm = CellBlockViewModel(parent=vm)
            cell_block_to_viewmodel(block, block_vm)
        else:
            raise TypeError(f"Unsupported BodyQupai block type: {type(block)!r}")
        content_vms.append(block_vm)

    # As with BodyRecitativoViewModel, we actually store the viewmodels here.
    vm.content = tuple(content_vms)  # type: ignore[assignment]


def viewmodel_to_body_qupai(vm: BodyQupaiViewModel) -> BodyQupai:
    """
    Persists the BodyQupaiViewModel parameters into a BodyQupai model.
    """
    content_models: list[RoleAnnotBlock | DirectionBlock | CellBlock] = []

    for block_vm in vm.content:
        if isinstance(block_vm, RoleAnnotBlockViewModel):
            content_models.append(viewmodel_to_role_annot_block(block_vm))
        elif isinstance(block_vm, DirectionBlockViewModel):
            content_models.append(viewmodel_to_direction_block(block_vm))
        elif isinstance(block_vm, CellBlockViewModel):
            content_models.append(viewmodel_to_cell_block(block_vm))
        else:
            raise TypeError(
                f"Unsupported BodyQupai block viewmodel type: {type(block_vm)!r}"
            )

    return BodyQupai(
        content=tuple(content_models),
    )


def zone_to_viewmodel(zone: Zone, vm: ZoneViewModel) -> None:
    """
    Set the ZoneViewModel parameters according to the Zone model properties.

    :param zone: Model from which the parameters are loaded.
    :param vm: Viewmodel whose properties should be updated.
    """
    # Geometry
    vm.set_rect(zone.ulx, zone.uly, zone.lrx, zone.lry)

    # Content
    if zone.content is None:
        vm.content = None
        return

    if isinstance(zone.content, BodyMetadata):
        body_metadata_to_viewmodel(zone.content, vm.content)
    elif isinstance(zone.content, BodyRecitativo):
        body_recitativo_to_viewmodel(zone.content, vm.content)
    elif isinstance(zone.content, BodyQupai):
        body_qupai_to_viewmodel(zone.content, vm.content)
    else:
        raise TypeError(f"Unsupported zone content type: {type(zone.content)!r}")


def viewmodel_to_zone(vm: ZoneViewModel) -> Zone:
    """
    Persists the ZoneViewModel parameters into a Zone model.

    :param vm: Viewmodel to persist.
    :return: Model.
    """
    content_model = None

    if vm.content is not None:
        if isinstance(vm.content, BodyMetadataViewModel):
            content_model = viewmodel_to_body_metadata(vm.content)
        elif isinstance(vm.content, BodyRecitativoViewModel):
            content_model = viewmodel_to_body_recitativo(vm.content)
        elif isinstance(vm.content, BodyQupaiViewModel):
            content_model = viewmodel_to_body_qupai(vm.content)
        else:
            raise TypeError(f"Unsupported body viewmodel type: {type(vm.content)!r}")

    return Zone(
        ulx=vm.ulx,
        uly=vm.uly,
        lrx=vm.lrx,
        lry=vm.lry,
        content=content_model,
    )


def surface_to_viewmodel(surface: Surface, vm: SurfaceViewModel) -> None:
    """
    Set the SurfaceViewModel parameters according to the Surface model properties.

    :param surface: Model from which the parameters are loaded.
    :param vm: Viewmodel whose properties should be updated.
    """
    zones = []
    for zone in surface.zones:
        zone_vm = ZoneViewModel(parent=vm)
        zone_to_viewmodel(zone, zone_vm)
        zones.append(zone_vm)
    vm.image = surface.image
    vm.image_path = surface.image_path
    vm.zones = tuple(zones)


def viewmodel_to_surface(vm: SurfaceViewModel) -> Surface:
    """
    Persists the SurfaceViewModel parameters into a Surface model.

    :param vm: Viewmodel to persist.
    :return: Model.
    """
    return Surface(
        image=vm.image,
        image_path=vm.image_path,
        zones=tuple(viewmodel_to_zone(zone_vm) for zone_vm in vm.zones),
    )


def document_to_viewmodel(doc: Document, vm: DocumentViewModel) -> None:
    """
    Set the DocumentViewModel parameters according to the Document model properties.

    :param doc: Model from which the parameters are loaded.
    :param vm: Viewmodel whose properties should be updated.
    """
    surfaces = []
    for surface in doc.surfaces:
        surface_vm = SurfaceViewModel(parent=vm)
        surface_to_viewmodel(surface, surface_vm)
        surfaces.append(surface_vm)
    vm.surfaces = tuple(surfaces)
    vm.document_type = doc.document_type
    vm.current_page_index = doc.current_page_index


def viewmodel_to_document(vm: DocumentViewModel) -> Document:
    """
    Persists the DocumentViewModel parameters into a Document model.

    :param vm: Viewmodel to persist.
    :return: Model.
    """
    return Document(
        surfaces=tuple(viewmodel_to_surface(surface_vm) for surface_vm in vm.surfaces),
        document_type=vm.document_type,
        current_page_index=vm.current_page_index,
    )
