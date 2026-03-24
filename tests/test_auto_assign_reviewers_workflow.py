import pathlib
import unittest


WORKFLOW_PATH = pathlib.Path(__file__).resolve().parent.parent / '.github' / 'workflows' / 'auto-assign-reviewers.yml'


class AutoAssignReviewersWorkflowTests(unittest.TestCase):
    def test_workflow_configuration(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding='utf-8')

        with self.subTest(msg="Permissions are correctly configured"):
            self.assertIn('contents: read', workflow)
            self.assertIn('pull-requests: write', workflow)

        with self.subTest(msg="Checkout step is present and correctly ordered"):
            checkout_ref = 'uses: actions/checkout@v4'
            require_call = "require('./.github/scripts/utils.js')"
            self.assertIn(checkout_ref, workflow)
            self.assertIn(require_call, workflow)
            self.assertLess(workflow.index(checkout_ref), workflow.index(require_call))

        with self.subTest(msg="Explanatory comment for checkout is present"):
            self.assertIn(
                '# Checkout is required so github-script can load ./.github/scripts/utils.js',
                workflow,
            )


if __name__ == '__main__':
    unittest.main()
