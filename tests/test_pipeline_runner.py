import unittest

from src.etl.pipeline_runner import PipelineStepError, run_pipeline, run_step


class PipelineRunnerTests(unittest.TestCase):
    def test_successful_steps_run_in_declared_order(self):
        observed = []
        extraction = [("extract one", lambda: observed.append("extract one"))]
        preparation = [
            ("prepare one", lambda: observed.append("prepare one")),
            ("prepare two", lambda: observed.append("prepare two")),
        ]

        run_pipeline(extraction, preparation)

        self.assertEqual(observed, ["extract one", "prepare one", "prepare two"])

    def test_failure_propagates_with_step_context(self):
        def fail():
            raise ValueError("source unavailable")

        with self.assertRaises(PipelineStepError) as context:
            run_step("ONS extraction", fail)

        self.assertIn("ONS extraction", str(context.exception))
        self.assertIn("source unavailable", str(context.exception))
        self.assertIsInstance(context.exception.__cause__, ValueError)

    def test_later_steps_do_not_run_after_failure(self):
        observed = []

        def fail():
            observed.append("failed")
            raise RuntimeError("boom")

        with self.assertRaises(PipelineStepError):
            run_pipeline(
                [("first", lambda: observed.append("first")), ("second", fail)],
                [("must not run", lambda: observed.append("late"))],
            )

        self.assertEqual(observed, ["first", "failed"])


if __name__ == "__main__":
    unittest.main()
