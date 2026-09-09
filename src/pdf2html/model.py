from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class TextBlock:
    text: str
    bbox: tuple[float, float, float, float]
    kind: str = "paragraph"
    level: int | None = None


@dataclass(slots=True)
class Page:
    number: int
    width: float
    height: float
    image: str
    blocks: list[TextBlock] = field(default_factory=list)
    needs_ocr: bool = False


@dataclass(slots=True)
class Document:
    source_name: str
    title: str
    page_count: int
    pages: list[Page]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ConversionResult:
    output_dir: Path
    html_path: Path
    document_path: Path
    report_path: Path
    page_count: int
    ocr_candidates: list[int]

