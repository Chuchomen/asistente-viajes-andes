import unittest

from agent_core import (
    build_full_knowledge_block,
    fallback_answer,
    load_knowledge_base,
    retrieve_context,
)


class AgentCoreTest(unittest.TestCase):
    def test_retrieves_cartagena_package(self):
        results = retrieve_context("Cuanto cuesta el viaje a Cartagena?")
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["id"], "cartagena")

    def test_retrieves_japan_package(self):
        results = retrieve_context("Cuanto cuesta un viaje a Japon?")
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["id"], "japon")

    def test_unknown_topic_has_no_context(self):
        results = retrieve_context("Hay descuentos para grupos grandes?")
        self.assertEqual(results, [])
        self.assertIn("No tengo ese dato", fallback_answer())

    def test_full_knowledge_block_covers_all_items(self):
        knowledge_base = load_knowledge_base()
        block = build_full_knowledge_block(knowledge_base)
        self.assertGreaterEqual(len(knowledge_base), 10)
        for item in knowledge_base:
            self.assertIn(item["title"], block)


if __name__ == "__main__":
    unittest.main()
