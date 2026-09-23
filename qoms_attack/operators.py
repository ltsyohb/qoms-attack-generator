"""Recipe mutation and crossover operators used by QOMS generation."""

from __future__ import annotations

import random

from .schema import EvidenceChannel, Recipe, RelationOperator, StructureOperator


DEFAULT_OPERATORS = (
    "rephrase_for_writer",
    "add_retrieval_anchor",
    "strengthen_authority",
    "clarify_temporal_order",
    "add_bridge",
    "add_persistence_schedule",
    "channel_switch",
    "cross_channel_corroborate",
    "preserve_lineage",
)


class OperatorLibrary:
    def __init__(self, seed: int = 0) -> None:
        self.random = random.Random(seed)

    def mutate(self, recipe: Recipe, operator: str, child_id: str) -> Recipe:
        genes = recipe.genes
        base = {
            "id": child_id,
            "generation": recipe.generation + 1,
            "parent_ids": (recipe.id,),
            "mutation_history": recipe.mutation_history + (operator,),
        }
        claim = genes.get("claim", "")
        if operator == "rephrase_for_writer":
            genes["claim"] = "structured factual update: " + claim
        elif operator == "add_retrieval_anchor":
            genes["claim"] = f"retrieval anchor {recipe.source_topic}: {claim}"
        elif operator == "strengthen_authority":
            genes["claim"] = "verified registry authority amendment: " + claim
            genes.setdefault("authority", "independent-registry-board")
            return recipe.evolved(relation=RelationOperator.AMEND, content_genes=tuple(genes.items()), **base)
        elif operator == "clarify_temporal_order":
            genes["claim"] = "latest effective record superseding earlier entries: " + claim
            return recipe.evolved(relation=RelationOperator.CORRECT, content_genes=tuple(genes.items()), **base)
        elif operator == "add_bridge":
            bridge = recipe.bridge_topic or recipe.target_topics[0]
            return recipe.evolved(bridge_topic=bridge, structure=StructureOperator.BRIDGE_NOTE, **base)
        elif operator == "add_persistence_schedule":
            schedule = tuple(dict.fromkeys(recipe.schedule + ("ordinary_followups", "background_reconsolidation")))
            return recipe.evolved(structure=StructureOperator.RECONSOLIDATE, schedule=schedule, **base)
        elif operator == "channel_switch":
            order = (
                EvidenceChannel.OCR_TRANSCRIPT,
                EvidenceChannel.ASR_TRANSCRIPT,
                EvidenceChannel.AUTHORITY_RECORD,
                EvidenceChannel.TIMELINE,
            )
            try:
                channel = order[(order.index(recipe.evidence_channel) + 1) % len(order)]
            except ValueError:
                channel = order[0]
            genes["channel_transition"] = f"{recipe.evidence_channel.value}->{channel.value}"
            return recipe.evolved(evidence_channel=channel, content_genes=tuple(genes.items()), **base)
        elif operator == "cross_channel_corroborate":
            genes["claim"] = "independent cross-channel corroboration confirms: " + claim
            return recipe.evolved(evidence_channel=EvidenceChannel.CORROBORATED, content_genes=tuple(genes.items()), **base)
        elif operator == "preserve_lineage":
            genes["claim"] = "canonical scoped record: " + claim
        else:
            raise ValueError(f"unknown operator: {operator}")
        return recipe.evolved(content_genes=tuple(genes.items()), **base)

    def crossover(self, left: Recipe, right: Recipe, child_id: str) -> Recipe:
        return left.evolved(
            id=child_id,
            generation=max(left.generation, right.generation) + 1,
            bridge_topic=right.bridge_topic,
            structure=right.structure,
            schedule=right.schedule,
            parent_ids=(left.id, right.id),
            mutation_history=left.mutation_history + ("crossover",),
        )

    def sample(self, count: int) -> tuple[str, ...]:
        if count < 1:
            raise ValueError("count must be positive")
        return tuple(self.random.choice(DEFAULT_OPERATORS) for _ in range(count))

