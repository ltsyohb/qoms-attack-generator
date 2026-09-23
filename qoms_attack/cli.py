"""Generate candidates from a JSON seed without running an experiment or audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import CandidateGenerator, GenerationConfig
from .schema import EvidenceChannel, Modality, Recipe, RelationOperator, StructureOperator


def load_recipe(path: Path) -> Recipe:
    value = json.loads(path.read_text(encoding="utf-8"))
    return Recipe(
        id=value["id"], generation=int(value.get("generation", 0)),
        source_topic=value["source_topic"], bridge_topic=value.get("bridge_topic"),
        target_topics=tuple(value["target_topics"]), relation=RelationOperator(value["relation"]),
        structure=StructureOperator(value["structure"]), schedule=tuple(value.get("schedule", ())),
        content_genes=tuple((str(k), str(v)) for k, v in value["content_genes"].items()),
        modality=Modality(value.get("modality", "text")),
        evidence_channel=EvidenceChannel(value.get("evidence_channel", "plain_text")),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate QOMS attack candidates for an authorized local target")
    parser.add_argument("seed", type=Path)
    parser.add_argument("--budget", type=int, default=20)
    parser.add_argument("--seed-value", type=int, default=0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = CandidateGenerator(GenerationConfig(budget=args.budget, seed=args.seed_value)).generate((load_recipe(args.seed),))
    payload = {"schema": "qoms-attack-candidates-v1", "candidates": [item.to_dict() for item in result.candidates]}
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()

