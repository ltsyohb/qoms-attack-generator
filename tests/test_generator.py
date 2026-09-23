import unittest

from qoms_attack import CandidateGenerator, GenerationConfig, Recipe, RelationOperator, StructureOperator


def seed() -> Recipe:
    return Recipe(
        id="seed", generation=0, source_topic="registry", target_topics=("policy",),
        relation=RelationOperator.AMEND, structure=StructureOperator.SINGLE_NOTE,
        schedule=("submit",), content_genes=(("claim", "value is TARGET 1234"),),
    )


class GeneratorTests(unittest.TestCase):
    def test_generation_is_bounded_and_deterministic(self):
        config = GenerationConfig(budget=6, population_size=2, elite_size=1, seed=7)
        left = CandidateGenerator(config).generate((seed(),))
        right = CandidateGenerator(config).generate((seed(),))
        self.assertGreater(len(left.candidates), 1)
        self.assertLessEqual(len(left.candidates), 6)
        self.assertEqual(
            [item.payload for item in left.candidates],
            [item.payload for item in right.candidates],
        )

    def test_black_box_score_selects_best(self):
        result = CandidateGenerator(GenerationConfig(budget=4, population_size=2, elite_size=1)).generate(
            (seed(),), score=lambda payload, recipe: float(len(payload))
        )
        self.assertEqual(result.best.score, max(item.score for item in result.candidates))


if __name__ == "__main__":
    unittest.main()
