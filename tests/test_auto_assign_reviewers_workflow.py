import pathlib
import unittest


WORKFLOW_PATH = pathlib.Path(__file__).resolve().parent.parent / '.github' / 'workflows' / 'auto-assign-reviewers.yml'


class AutoAssignReviewersWorkflowTests(unittest.TestCase):
    def test_checkout_step_has_required_permissions_and_ordering(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding='utf-8')

        self.assertIn('contents: read', workflow)
        self.assertIn('pull-requests: write', workflow)
        self.assertLess(workflow.index('contents: read'), workflow.index('pull-requests: write'))

        checkout_ref = 'uses: actions/checkout@v4.0.4'
        self.assertIn(checkout_ref, workflow)
        self.assertIn("require('./.github/scripts/utils.js')", workflow)
        self.assertLess(workflow.index(checkout_ref), workflow.index("require('./.github/scripts/utils.js')"))
        self.assertIn(
            '# Checkout is required so github-script can load ./.github/scripts/utils.js',
            workflow,
        )


if __name__ == '__main__':
    unittest.main()
