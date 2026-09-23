"""Budgeted candidate generation with optional black-box scores."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .operators import OperatorLibrary
from .render import render_candidate
from .schema import Candidate, Recipe


ScoreFunction = Callable[[str, Recipe], float]


@dataclass(frozen=True)
class GenerationConfig:
    budget: int = 20
    population_size: int = 4
    elite_size: int = 2
    seed: int = 0

    def __post_init__(self) -> None:
        if min(self.budget, self.population_size, self.elite_size) < 1:
            raise ValueError("generation counts must be positive")
        if self.elite_size > self.population_size:
            raise ValueError("elite_size cannot exceed population_size")


@dataclass(frozen=True)
class GenerationResult:
    candidates: tuple[Candidate, ...]

    @property
    def best(self) -> Candidate:
        if not self.candidates:
            raise ValueError("no candidates generated")
        if any(item.score is not None for item in self.candidates):
            return max(self.candidates, key=lambda item: float("-inf") if item.score is None else item.score)
        return self.candidates[0]


class CandidateGenerator:
    def __init__(self, config: GenerationConfig | None = None) -> None:
        self.config = config or GenerationConfig()
        self.operators = OperatorLibrary(self.config.seed)

    def generate(self, seeds: tuple[Recipe, ...], score: ScoreFunction | None = None) -> GenerationResult:
        if not seeds:
            raise ValueError("at least one seed recipe is required")
        pending = list(self._deduplicate(seeds))
        seen = {item.canonical_key() for item in pending}
        generated: list[Candidate] = []
        generation = 0
        while pending and len(generated) < self.config.budget:
            generation += 1
            batch = pending[: self.config.population_size]
            pending = pending[self.config.population_size :]
            for recipe in batch:
                if len(generated) >= self.config.budget:
                    break
                payload = render_candidate(recipe)
                generated.append(Candidate(recipe, payload, score(payload, recipe) if score else None))
            ranked = sorted(generated, key=lambda item: (item.score is not None, item.score or 0.0), reverse=True)
            parents = ranked[: self.config.elite_size]
            for index, parent in enumerate(parents):
                operator = self.operators.sample(1)[0]
                child = self.operators.mutate(parent.recipe, operator, f"g{generation + 1}-{parent.recipe.id}-{index + 1}")
                if child.canonical_key() not in seen:
                    seen.add(child.canonical_key())
                    pending.append(child)
            if len(parents) >= 2:
                child = self.operators.crossover(parents[0].recipe, parents[1].recipe, f"g{generation + 1}-cross")
                if child.canonical_key() not in seen:
                    seen.add(child.canonical_key())
                    pending.append(child)
        return GenerationResult(tuple(generated))

    @staticmethod
    def _deduplicate(recipes: tuple[Recipe, ...]) -> tuple[Recipe, ...]:
        unique = {}
        for recipe in recipes:
            unique.setdefault(recipe.canonical_key(), recipe)
        return tuple(unique.values())

