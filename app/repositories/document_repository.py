from __future__ import annotations

from pathlib import Path
from typing import Any

import msgpack

from app.models.document import (
    Document,
    DocumentType,
    Surface,
    Zone,
    BodyMetadata,
    BodyRecitativo,
    BodyQupai,
    TitleBlock,
    ParagraphBlock,
    RoleAnnotBlock,
    LineBlock,
    DirectionBlock,
    CellBlock,
    BeatCell,
    GongcheCell,
    SylCell,
    ProlongationDotCell,
    RoleAnnot,
    Direction,
    Beat,
    Pitch,
    Con,
)


class DocumentRepository:
    """
    Repository for loading/saving documents from/to the file system.

    Methods:
        load (Path): Loads the serialized document data from the file system into the Document model.
        save (Path, Document): Saves the Document model data into a serialized file on the file system.

    Private Methods:
        _surface_from_dict (dict[str, Any]): Creates a Surface model from the serialized document data.
        _document_type (object): Checks the document type for validity and returns it.
    """

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    @classmethod
    def load(cls, path: Path) -> Document:
        """
        Loads the serialized document data from the file system into the Document model.

        :param path: Path to the serialized document file.
        :return: Document model.
        """
        with path.open("rb") as f:
            data = msgpack.unpackb(f.read(), raw=False)

        document_type = cls._document_type(data["document_type"])
        current_page_index = int(data["current_page_index"])

        surfaces = tuple(cls._surface_from_dict(s) for s in data["surfaces"])

        return Document(
            surfaces=surfaces,
            document_type=document_type,
            current_page_index=current_page_index,
        )

    @classmethod
    def save(cls, path: Path, document: Document) -> None:
        """
        Saves the Document model data into a serialized file on the file system.

        :param path: Path to the serialized document file.
        :param document: Document model.
        """
        data: dict[str, Any] = {
            "document_type": document.document_type,
            "current_page_index": document.current_page_index,
            "surfaces": [cls._surface_to_dict(s) for s in document.surfaces],
        }

        packed = msgpack.packb(data, use_bin_type=True)
        with path.open("wb") as f:
            f.write(packed)

    # ---------------------------------------------------------------------
    # Surface <-> dict
    # ---------------------------------------------------------------------

    @classmethod
    def _surface_from_dict(cls, data: dict[str, Any]) -> Surface:
        """
        Creates a Surface model from the serialized document data.

        :param data: Serialized Surface data.
        :return: Surface model.
        """
        zones = tuple(
            Zone(
                ulx=int(zone["ulx"]),
                uly=int(zone["uly"]),
                lrx=int(zone["lrx"]),
                lry=int(zone["lry"]),
                content=cls._zone_content_from_serialized(zone.get("content")),
            )
            for zone in data["zones"]
        )

        return Surface(
            image=bytes(data["image"]),
            image_path=str(data["image_path"]),
            zones=zones,
        )

    @classmethod
    def _surface_to_dict(cls, surface: Surface) -> dict[str, Any]:
        """
        Serializes a Surface model into a dict that can be msgpack'ed.

        :param surface: Surface model.
        :return: Dict representation.
        """
        return {
            "image": surface.image,
            "image_path": surface.image_path,
            "zones": [cls._zone_to_dict(z) for z in surface.zones],
        }

    @classmethod
    def _zone_to_dict(cls, zone: Zone) -> dict[str, Any]:
        """
        Serializes a Zone model into a dict, including its content.

        :param zone: Zone model.
        :return: Dict representation.
        """
        return {
            "ulx": zone.ulx,
            "uly": zone.uly,
            "lrx": zone.lrx,
            "lry": zone.lry,
            "content": cls._zone_content_to_serialized(zone.content),
        }

    # ---------------------------------------------------------------------
    # Zone.content (Body*) <-> dict
    # ---------------------------------------------------------------------

    @classmethod
    def _zone_content_to_serialized(
        cls, content: BodyMetadata | BodyRecitativo | BodyQupai | None
    ) -> dict[str, Any] | None:
        """
        Serializes the zone content (BodyMetadata / BodyRecitativo / BodyQupai)
        into a plain dict that msgpack can handle.

        We store a 'kind' field so we can reconstruct the correct Body* type.
        """
        if content is None:
            return None

        if isinstance(content, BodyMetadata):
            return {
                "kind": "body_metadata",
                "content": [cls._block_to_dict(block) for block in content.content],
            }

        if isinstance(content, BodyRecitativo):
            return {
                "kind": "body_recitativo",
                "content": [cls._block_to_dict(block) for block in content.content],
            }

        if isinstance(content, BodyQupai):
            return {
                "kind": "body_qupai",
                "content": [cls._block_to_dict(block) for block in content.content],
            }

        raise TypeError(f"Unsupported zone content type: {type(content)!r}")

    @classmethod
    def _zone_content_from_serialized(
        cls, data: dict[str, Any] | None
    ) -> BodyMetadata | BodyRecitativo | BodyQupai | None:
        """
        Deserializes zone content from a dict into one of the Body* types.
        """
        if data is None:
            return None

        kind = data.get("kind")
        blocks_data = data.get("content", [])

        blocks = tuple(cls._block_from_dict(b) for b in blocks_data)

        if kind == "body_metadata":
            # content: tuple[TitleBlock | ParagraphBlock, ...]
            return BodyMetadata(content=blocks)  # type: ignore[arg-type]
        if kind == "body_recitativo":
            # content: tuple[RoleAnnotBlock | DirectionBlock | LineBlock, ...]
            return BodyRecitativo(content=blocks)  # type: ignore[arg-type]
        if kind == "body_qupai":
            # content: tuple[RoleAnnotBlock | DirectionBlock | CellBlock, ...]
            return BodyQupai(content=blocks)  # type: ignore[arg-type]

        raise ValueError(f"Unknown body kind: {kind!r}")

    # ---------------------------------------------------------------------
    # Block <-> dict
    # ---------------------------------------------------------------------

    @classmethod
    def _block_to_dict(
        cls,
        block: (
            TitleBlock
            | ParagraphBlock
            | RoleAnnotBlock
            | LineBlock
            | DirectionBlock
            | CellBlock
        ),
    ) -> dict[str, Any]:
        """
        Serializes any block type into a tagged dict.
        """
        if isinstance(block, TitleBlock):
            return {"type": "title", "title": block.title}

        if isinstance(block, ParagraphBlock):
            return {"type": "paragraph", "paragraph": block.paragraph}

        if isinstance(block, RoleAnnotBlock):
            return {
                "type": "role_annot",
                "plist": list(block.plist),
                "content": block.content,
            }

        if isinstance(block, LineBlock):
            return {"type": "line", "content": block.content}

        if isinstance(block, DirectionBlock):
            return {
                "type": "direction",
                "plist": list(block.plist),
                "content": block.content,
            }

        if isinstance(block, CellBlock):
            return {
                "type": "cell",
                "beat": cls._beat_cell_to_dict(block.beat),
                "gongche": cls._gongche_cell_to_dict(block.gongche),
                "syl": cls._syl_cell_to_dict(block.syl),
                "prolongation_dot": cls._prolongation_dot_cell_to_dict(
                    block.prolongation_dot
                ),
            }

        raise TypeError(f"Unsupported block type: {type(block)!r}")

    @classmethod
    def _block_from_dict(
        cls, data: dict[str, Any]
    ) -> (
        TitleBlock
        | ParagraphBlock
        | RoleAnnotBlock
        | LineBlock
        | DirectionBlock
        | CellBlock
    ):
        """
        Deserializes a tagged dict into the appropriate block dataclass.
        """
        type_ = data.get("type")

        if type_ == "title":
            return TitleBlock(title=str(data["title"]))

        if type_ == "paragraph":
            return ParagraphBlock(paragraph=str(data["paragraph"]))

        if type_ == "role_annot":
            plist = tuple(data.get("plist", []))  # type: ignore[assignment]
            return RoleAnnotBlock(
                plist=plist,  # tuple[RoleAnnot]
                content=str(data.get("content", "")),
            )

        if type_ == "line":
            return LineBlock(content=str(data.get("content", "")))

        if type_ == "direction":
            plist = tuple(data.get("plist", []))  # type: ignore[assignment]
            return DirectionBlock(
                plist=plist,  # tuple[Direction]
                content=str(data.get("content", "")),
            )

        if type_ == "cell":
            return CellBlock(
                beat=cls._beat_cell_from_dict(data.get("beat")),
                gongche=cls._gongche_cell_from_dict(data.get("gongche")),
                syl=cls._syl_cell_from_dict(data.get("syl")),
                prolongation_dot=cls._prolongation_dot_cell_from_dict(
                    data.get("prolongation_dot")
                ),
            )

        raise ValueError(f"Unknown block type: {type_!r}")

    # ---------------------------------------------------------------------
    # Cell <-> dict
    # ---------------------------------------------------------------------

    @classmethod
    def _beat_cell_to_dict(cls, cell: BeatCell | None) -> dict[str, Any] | None:
        if cell is None:
            return None
        return {
            "beat": cell.beat,
            "content": cell.content,
        }

    @classmethod
    def _beat_cell_from_dict(cls, data: dict[str, Any] | None) -> BeatCell | None:
        if data is None:
            return None
        beat: Beat = data.get("beat")
        return BeatCell(
            beat=beat,
            content=str(data.get("content", "")),
        )

    @classmethod
    def _gongche_cell_to_dict(
        cls, cell: GongcheCell | None
    ) -> dict[str, Any] | None:
        if cell is None:
            return None
        return {
            "pname": cell.pname,
            "content": cell.content,
        }

    @classmethod
    def _gongche_cell_from_dict(
        cls, data: dict[str, Any] | None
    ) -> GongcheCell | None:
        if data is None:
            return None
        pname: Pitch = data.get("pname")
        return GongcheCell(
            pname=pname,
            content=str(data.get("content", "")),
        )

    @classmethod
    def _syl_cell_to_dict(cls, cell: SylCell | None) -> dict[str, Any] | None:
        if cell is None:
            return None
        return {
            "con": cell.con,
            "content": cell.content,
        }

    @classmethod
    def _syl_cell_from_dict(cls, data: dict[str, Any] | None) -> SylCell | None:
        if data is None:
            return None
        con_raw = data.get("con", None)
        con: Con | None = con_raw if con_raw is not None else None
        return SylCell(
            con=con,
            content=str(data.get("content", "")),
        )

    @classmethod
    def _prolongation_dot_cell_to_dict(
        cls, cell: ProlongationDotCell | None
    ) -> dict[str, Any] | None:
        if cell is None:
            return None
        return {
            "content": cell.content,
        }

    @classmethod
    def _prolongation_dot_cell_from_dict(
        cls, data: dict[str, Any] | None
    ) -> ProlongationDotCell | None:
        if data is None:
            return None
        return ProlongationDotCell(
            content=str(data.get("content", "")),
        )

    # ---------------------------------------------------------------------
    # DocumentType validation
    # ---------------------------------------------------------------------

    @classmethod
    def _document_type(cls, value: object) -> DocumentType:
        """
        Checks the document type for validity and returns it.

        :param value: Document type value.
        :raise ValueError: If document type is invalid.
        :return: Document type value if valid.
        """
        if value not in ("TEI", "MEI"):
            raise ValueError(f"Unsupported document type: {value!r}")
        # For now you can decide to enforce MEI or keep what is stored.
        # Here we simply return the stored value as a valid DocumentType.
        return value  # type: ignore[return-value]