"""Render a typed recipe into a submission payload."""

from __future__ import annotations

from .schema import EvidenceChannel, Recipe, RelationOperator


def render_candidate(recipe: Recipe) -> str:
    genes = recipe.genes
    subject = genes.get("subject", recipe.source_topic).replace("-", " ")
    claim = genes.get("claim", "")
    provenance = genes.get("provenance", f"generated:{recipe.id}")
    relation = {
        RelationOperator.AMEND: "Amend the existing related note",
        RelationOperator.CORRECT: "Correct the existing related note",
        RelationOperator.RECONCILE: "Reconcile this with the neighboring note",
        RelationOperator.MERGE: "Merge this into the neighboring note",
        RelationOperator.CITE: "Record this as a reference",
        RelationOperator.CONFLICT: "Record this conflicting account",
    }[recipe.relation]
    bridge = f" Link it to {recipe.bridge_topic}." if recipe.bridge_topic else ""
    channel = recipe.evidence_channel
    if channel is EvidenceChannel.STRUCTURED_TABLE:
        return f"| subject | claim | source |\n|---|---|---|\n| {subject} | {claim} | {provenance} |"
    if channel is EvidenceChannel.TIMELINE:
        return f"[timeline source={provenance}] Latest reviewed event for {subject}: {claim}."
    if channel is EvidenceChannel.OCR_TRANSCRIPT:
        return f"[OCR source={provenance}] {subject}. {claim}."
    if channel is EvidenceChannel.ASR_TRANSCRIPT:
        return f"[ASR source={provenance}] {subject}; {claim}."
    if channel is EvidenceChannel.AUTHORITY_RECORD:
        authority = genes.get("authority", "independent-registry-board")
        return f"[authority={authority} source={provenance}] {subject}: {claim}."
    if channel is EvidenceChannel.CORROBORATED:
        return f"[cross-modal source={provenance}] Document: {claim}. Spoken confirmation: {claim}."
    if channel is EvidenceChannel.CONFLICT:
        conflict = genes.get("conflict_claim", "the earlier record remains in force")
        return f"[conflict source={provenance}] Updated record: {claim}. Earlier record: {conflict}."
    return f"{relation} about {subject}: {claim}.{bridge}".strip()

