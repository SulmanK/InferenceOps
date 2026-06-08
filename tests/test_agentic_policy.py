import unittest

from controllers.agentic_policy import (
    AgenticPolicyController,
    ScriptedAgentClient,
    parse_agent_action,
)
from controllers.policies import observation_for_scenario


class BadAgentClient:
    def __init__(self, response: str):
        self.response = response

    def complete(self, prompt: str) -> str:
        return self.response


class AgenticPolicyTest(unittest.TestCase):
    def test_parse_valid_json_action(self):
        action = parse_agent_action('{"policy": "cache_aware", "reason": "hot prefixes"}')
        self.assertEqual(action.policy, "cache_aware")
        self.assertEqual(action.reason, "hot prefixes")

    def test_parse_rejects_unsupported_policy(self):
        with self.assertRaises(ValueError):
            parse_agent_action('{"policy": "shell_exec", "reason": "bad"}')

    def test_invalid_agent_response_uses_fallback(self):
        controller = AgenticPolicyController(BadAgentClient("not json"), fallback_policy="cache_aware")
        decision = controller.decide(observation_for_scenario("mixed_short_long"))
        self.assertFalse(decision.valid)
        self.assertTrue(decision.fallback_used)
        self.assertEqual(decision.action.policy, "cache_aware")

    def test_scripted_agent_is_deterministic(self):
        controller = AgenticPolicyController(ScriptedAgentClient())
        action = controller.choose(observation_for_scenario("shared_prefix_burst"))
        self.assertEqual(action.policy, "cache_aware")
        action = controller.choose(observation_for_scenario("mixed_short_long"))
        self.assertEqual(action.policy, "power_of_two")


if __name__ == "__main__":
    unittest.main()

