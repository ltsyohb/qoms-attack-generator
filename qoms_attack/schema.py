"""Typed attack recipe schemas."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import Enum
from typing import Any


class Modality(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"


class EvidenceChannel(str, Enum):
    PLAIN_TEXT = "plain_text"
    STRUCTURED_TABLE = "structured_table"
    TIMELINE = "timeline"
    OCR_TRANSCRIPT = "ocr_transcript"
    ASR_TRANSCRIPT = "asr_transcript"
    AUTHORITY_RECORD = "authority_record"
    CORROBORATED = "cross_modal_corroboration"
    CONFLICT = "cross_modal_conflict"


class RelationOperator(str, Enum):
    AMEND = "amend"
    CORRECT = "correct"
    RECONCILE = "reconcile"
    MERGE = "merge"
    CITE = "cite"
    CONFLICT = "conflict"


class StructureOperator(str, Enum):
    SINGLE_NOTE = "single_note"
    BRIDGE_NOTE = "bridge_note"
    SEQUENCE = "sequence"
    RECONSOLIDATE = "reconsolidate"


@dataclass(frozen=True)
class Recipe:
    id: str
    generation: int
    source_topic: str
    target_topics: tuple[str, ...]
    relation: RelationOperator
    structure: StructureOperator
    schedule: tuple[str, ...]
    content_genes: tuple[tuple[str, str], ...]
    modality: Modality = Modality.TEXT
    evidence_channel: EvidenceChannel = EvidenceChannel.PLAIN_TEXT
    bridge_topic: str | None = None
    parent_ids: tuple[str, ...] = ()
    mutation_history: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.target_topics:
            raise ValueError("recipe needs at least one target topic")
        keys = [key for key, _ in self.content_genes]
        if len(set(keys)) != len(keys):
            raise ValueError("content gene keys must be unique")

    @property
    def genes(self) -> dict[str, str]:
        return dict(self.content_genes)

    def evolved(self, **changes: Any) -> "Recipe":
        return replace(self, **changes)

    def canonical_key(self) -> tuple[Any, ...]:
        return (
            self.source_topic,
            self.bridge_topic,
            self.target_topics,
            self.relation.value,
            self.structure.value,
            self.schedule,
            tuple(sorted(self.content_genes)),
            self.modality.value,
            self.evidence_channel.value,
        )

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["relation"] = self.relation.value
        value["structure"] = self.structure.value
        value["modality"] = self.modality.value
        value["evidence_channel"] = self.evidence_channel.value
        return value


@dataclass(frozen=True)
class Candidate:
    recipe: Recipe
    payload: str
    score: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"recipe": self.recipe.to_dict(), "payload": self.payload, "score": self.score}

