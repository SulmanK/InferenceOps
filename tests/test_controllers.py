import unittest

from controllers.policies import (
    Action,
    ScenarioHeuristicController,
    StaticPolicyController,
    observation_for_scenario,
)


class ControllerPolicyTest(unittest.TestCase):
    def test_invalid_action_is_rejected(self):
        with self.assertRaises(ValueError):
            Action("unsupported", "bad action")

    def test_static_controller_uses_fixed_policy(self):
        controller = StaticPolicyController("cache_aware")
        action = controller.choose(observation_for_scenario("mixed_short_long"))
        self.assertEqual(action.policy, "cache_aware")

    def test_scenario_heuristic_prefers_cache_for_shared_prefix(self):
        controller = ScenarioHeuristicController()
        action = controller.choose(observation_for_scenario("shared_prefix_burst"))
        self.assertEqual(action.policy, "cache_aware")

    def test_scenario_heuristic_prefers_power_of_two_for_degraded_worker(self):
        controller = ScenarioHeuristicController()
        action = controller.choose(observation_for_scenario("degraded_worker"))
        self.assertEqual(action.policy, "power_of_two")


if __name__ == "__main__":
    unittest.main()

