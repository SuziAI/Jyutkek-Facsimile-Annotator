from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Union

"""
Holds whether the document is in TEI or MEI XML format.
"""
DocumentType = Literal["TEI", "MEI"]

"""
Holds the reciting role, i.e., Sheng or Dan.
"""
RoleAnnot = Literal["orchestra", "singer_sheng", "singer_dan"]


"""
Holds the direction, i.e., recitativo or accompanied.
"""
Direction = Literal["recitativo", "accompanied"]


"""
Holds the beat type, i.e., weak or strong.
"""
Beat = Literal["weak", "strong"]


"""
Holds the pitch type.
"""
Pitch = Literal[
    "lower_he",
    "lower_shi",
    "lower_yi",
    "lower_shang",
    "lower_che",
    "lower_gong",
    "lower_fan",
    "he",
    "shi",
    "yi",
    "shang",
    "che",
    "gong",
    "fan",
    "liu",
    "wu",
    "higher_yi",
    "sheng",
    "higher_che",
    "higher_gong",
    "higher_fan",
    "higher_liu",
    "higher_wu"
]

"""
Holds the approval state.
"""
Approval = Literal[
    "approved",
    "pending"
]

"""
Holds the syllable continuation type.
"""
Con = Literal["u"]


@dataclass(frozen=True, kw_only=True)
class ApprovalMixin:
    """
    Allows for different annotations regarding approval, e.g.,
    if it has to be checked by another person.

    Properties:
        approval_state (str): The state of the approval, e.g., "approved" or "pending".
        approval_note (str): Note or remark accompanying the approval state.
    """
    approval_state: Approval = "approved"
    approval_note: str = ""


@dataclass(frozen=True, kw_only=True)
class TitleBlock(ApprovalMixin):
    """
    Holds the piece's title

    Properties:
        title (str): The piece's title.
    """
    title: str


@dataclass(frozen=True, kw_only=True)
class ParagraphBlock(ApprovalMixin):
    """
    Holds the piece's introductory information

    Properties:
        paragraph (str): Holds an introductory paragraph.
    """
    paragraph: str


@dataclass(frozen=True, kw_only=True)
class RoleAnnotBlock(ApprovalMixin):
    """
    Holds role annotation data.

    Properties:
        plist (tuple[str]): List of role references separated by space,
                           e.g., #singer_dan.
        content (str): The block's text content.
    """
    plist: tuple[RoleAnnot]
    content: str


@dataclass(frozen=True, kw_only=True)
class LineBlock(ApprovalMixin):
    """
    Holds line annotation data.

    Properties:
        content (str): The block's text content.
    """
    content: str


@dataclass(frozen=True, kw_only=True)
class DirectionBlock(ApprovalMixin):
    """
    Holds direction data.

    Properties:
        plist (tuple[str]): List of role references separated by space,
                           e.g., #singer_dan.
        content (str): The block's text content.
    """
    plist: tuple[Direction]
    content: str


@dataclass(frozen=True)
class BeatCell:
    """
    Holds beat data.

    Properties:
        beat (Beat): The beat information.
        content (str): The block's text content.
    """
    beat: Beat
    content: str


@dataclass(frozen=True)
class GongcheCell:
    """
    Holds pitch data.

    Properties:
        pname (Pitch): The pitch information.
        content (str): The block's text content.
    """
    pname: Pitch
    content: str


@dataclass(frozen=True)
class SylCell:
    """
    Holds syllable data.

    Properties:
        con (Con): The syllable continuation information.
        content (str): The block's text content.
    """
    con: Con | None
    content: str


@dataclass(frozen=True)
class ProlongationDotCell:
    """
    Holds prolongation dot data.

    Properties:
        content (str): The block's text content.
    """
    content: str


@dataclass(frozen=True, kw_only=True)
class CellBlock(ApprovalMixin):
    """
    Holds a Jyutkek cell annotation.

    Properties:
        beat (BeatCell): Beat information.
        gongche (GongcheCell): Pitch information.
        syl (SylCell): Syllable information.
        prolongation_dot (ProlongationDotCell): Prolongation information.
    """
    beat: BeatCell | None
    gongche: GongcheCell | None
    syl: SylCell | None
    prolongation_dot: ProlongationDotCell | None


ContentBlock = Union[
    TitleBlock,
    ParagraphBlock,
    RoleAnnotBlock,
    DirectionBlock,
    LineBlock,
    CellBlock,
]

@dataclass(frozen=True)
class BodyMetadata:
    """
    Holds the piece's metadata (title, describing paragraphs).

    Properties:
        content (tuple): List of individual content blocks.
    """
    content: tuple[TitleBlock | ParagraphBlock, ...]


@dataclass(frozen=True)
class BodyRecitativo:
    """
    Holds one of the piece's recitativo line.

    Properties:
        content (tuple): List of individual content blocks.
    """
    content: tuple[RoleAnnotBlock | DirectionBlock | LineBlock, ...]


@dataclass(frozen=True)
class BodyQupai:
    """
    Holds one of the piece's qupai lines.

    Properties:
        content (tuple): List of individual content blocks.
    """
    content: tuple[RoleAnnotBlock | DirectionBlock | CellBlock, ...]


@dataclass(frozen=True)
class Zone:
    """
    Holds the coordinates of a single zone.

    Properties:
        ulx (int): Upper left x coordinate.
        uly (int): Upper left y coordinate.
        lrx (int): Lower right x coordinate.
        lry (int): Lower right y coordinate.
    """
    ulx: int
    uly: int
    lrx: int
    lry: int
    content: BodyMetadata | BodyRecitativo | BodyQupai | None = None


@dataclass(frozen=True)
class Surface:
    """
    Holds the state of a surface.

    Properties:
        image (bytes): Bytestring containing the raw image data.
        image_path (str): Path to the image file.
        zones (tuple[Zone, ...]): The zones associated with this surface.
    """
    image: bytes
    image_path: str
    zones: tuple[Zone, ...]


@dataclass(frozen=True)
class Document:
    """
    Holds the state of a document.

    Properties:
        surfaces (tuple[Surface, ...]): The surfaces associated with this document.
        document_type (DocumentType): Type of the document.
        current_page_index (int): The index of the page currently being edited.
    """
    surfaces: tuple[Surface, ...]
    document_type: DocumentType
    current_page_index: int
