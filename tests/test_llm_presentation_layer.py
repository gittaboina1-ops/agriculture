"""
Unit tests for LLM presentation layer and fallback requirements.
Tests:
1. Normal LLM response (when LLM works, reformats outcome)
2. LLM failure (simulating API error/exception -> returns original outcome)
3. Empty LLM response (simulating empty LLM response -> returns original outcome)
4. Context & outcome payload (verifying LLM receives retrieved info & original outcome)
5. Preservation of original system outcome fields
"""

import os
import unittest
from unittest.mock import patch, MagicMock
from backend.services.llm_service import LLMAnswerService
from backend.retrieval.service import retrieval_service

class TestLLMPresentationLayer(unittest.TestCase):
    def setUp(self):
        self.llm_service = LLMAnswerService()
        self.query = "What soil conditions are suitable for tomato?"
        self.intent = "SOIL_SUITABILITY"
        self.context = {
            "matched_crop": "Tomato",
            "entities": [{"id": "CROP_001", "name": "Tomato", "label": "Crop"}],
            "graph_evidence": [],
            "sources": [{"source_id": "DOC_005", "title": "Soil Physical Characteristics", "source_type": "Bulletin", "summary": "Soil details"}],
            "conflicts": [],
            "data_quality_warnings": [],
            "soil_records": [{"name": "Loamy Sand", "properties": {"ph_range": "6.0–7.0"}}]
        }

    def test_original_system_outcome_generation(self):
        outcome = self.llm_service._generate_original_system_outcome(self.query, self.intent, self.context)
        self.assertIn("agricultural_insight", outcome)
        self.assertIn("relevant_factors", outcome)
        self.assertIn("Loamy Sand", outcome["agricultural_insight"])
        self.assertEqual(outcome["mode"], "grounded_rule_engine")

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake_gemini_key"})
    @patch.object(LLMAnswerService, "_call_gemini")
    def test_normal_llm_response(self, mock_gemini):
        mock_gemini.return_value = {
            "agricultural_insight": "Tomatoes grow exceptionally well in fertile, well-drained loamy sand with a pH between 6.0 and 7.0.",
            "relevant_factors": ["Soil type: Loamy Sand", "Optimal pH: 6.0–7.0"]
        }

        res = self.llm_service.generate_grounded_answer(self.query, self.intent, self.context)

        self.assertEqual(res["mode"], "llm")
        self.assertEqual(res["provider"], "gemini")
        self.assertTrue("gemini" in res["model"])
        self.assertIn("Tomatoes grow exceptionally well", res["agricultural_insight"])
        self.assertEqual(len(res["relevant_factors"]), 2)

        # Verify system prompt and user prompt passed to _call_gemini contain anti-hallucination instruction
        call_args = mock_gemini.call_args
        system_inst = call_args[0][0]
        user_prompt = call_args[0][1]

        self.assertIn("response generation layer for an existing retrieval system", system_inst)
        self.assertIn("Do not add facts from your own knowledge", system_inst)
        self.assertIn("Existing System Outcome", user_prompt)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "fake_openai_key", "GEMINI_API_KEY": ""})
    @patch.object(LLMAnswerService, "_call_openai")
    def test_llm_failure_returns_original_outcome(self, mock_openai):
        # Simulate API error / Exception
        mock_openai.side_effect = Exception("API connection error")

        original_outcome = self.llm_service._generate_original_system_outcome(self.query, self.intent, self.context)
        res = self.llm_service.generate_grounded_answer(self.query, self.intent, self.context)

        # Verify fallback to original system outcome
        self.assertEqual(res["agricultural_insight"], original_outcome["agricultural_insight"])
        self.assertEqual(res["relevant_factors"], original_outcome["relevant_factors"])
        self.assertIn("LLM exception", res["fallback_reason"])

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake_gemini_key"})
    @patch.object(LLMAnswerService, "_call_gemini")
    def test_empty_llm_response_returns_original_outcome(self, mock_gemini):
        # Simulate empty response from LLM
        mock_gemini.return_value = {"agricultural_insight": "", "relevant_factors": []}

        original_outcome = self.llm_service._generate_original_system_outcome(self.query, self.intent, self.context)
        res = self.llm_service.generate_grounded_answer(self.query, self.intent, self.context)

        self.assertEqual(res["agricultural_insight"], original_outcome["agricultural_insight"])
        self.assertEqual(res["relevant_factors"], original_outcome["relevant_factors"])
        self.assertEqual(res["fallback_reason"], "Empty or malformed LLM response")

    def test_retrieval_service_preserves_all_response_fields(self):
        # Verify that execute_farmer_query returns all expected fields without breaking contract
        res = retrieval_service.execute_farmer_query("What soil conditions are suitable for tomato?")
        expected_keys = [
            "query", "intent", "matched_crop", "entities", "agricultural_insight",
            "relevant_factors", "evidence", "sources", "conflicts", "data_quality_warnings",
            "subgraph", "evaluation_metrics", "generation_mode", "provider", "model", "fallback_reason"
        ]
        for key in expected_keys:
            self.assertIn(key, res)

if __name__ == "__main__":
    unittest.main()
