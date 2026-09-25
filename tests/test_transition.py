import importlib.util
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parent.parent / "src/mango_performance_modes/controller.py"
spec = importlib.util.spec_from_file_location("mango_controller", SOURCE)
power = importlib.util.module_from_spec(spec)
spec.loader.exec_module(power)


class TransitionTests(unittest.TestCase):
    def test_sober_auto_and_close(self):
        state = power.initial_state()
        state = power.transition(state, True)
        self.assertEqual((state["mode"], state["manual"]), ("balanced", False))
        state = power.transition(state, False)
        self.assertEqual((state["mode"], state["manual"]), ("eco", False))

    def test_manual_max_never_automatic(self):
        state = power.transition(power.initial_state(), False, "max")
        self.assertEqual((state["mode"], state["manual"]), ("max", True))
        state = power.transition(state, True)
        self.assertEqual(state["mode"], "max")
        state = power.transition(state, False)
        self.assertEqual((state["mode"], state["manual"]), ("eco", False))

    def test_manual_eco_during_sober_until_close(self):
        state = power.transition(power.initial_state(), True)
        state = power.transition(state, True, "eco")
        self.assertTrue(state["manual"])
        self.assertEqual(power.transition(state, True)["mode"], "eco")
        self.assertEqual(power.transition(state, False)["mode"], "eco")

    def test_eco_outside_sober_restores_automation(self):
        state = power.transition(power.initial_state(), False, "balanced")
        state = power.transition(state, False, "eco")
        self.assertFalse(state["manual"])
        self.assertEqual(power.transition(state, True)["mode"], "balanced")

    def test_unknown_mode_rejected(self):
        with self.assertRaises(ValueError):
            power.transition(power.initial_state(), False, "turbo")

    def test_initial_state_shape(self):
        state = power.initial_state()
        self.assertEqual(state["mode"], "eco")
        self.assertFalse(state["manual"])
        self.assertFalse(state["sober"])


if __name__ == "__main__":
    unittest.main()
