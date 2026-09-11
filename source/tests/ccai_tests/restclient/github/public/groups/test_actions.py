"""
    Wire tests for the generated ``ActionsApiGroup``.
"""

import unittest

from ccai.restclient.github.public.groups.actions import Workflow, WorkflowRun

from ccai_tests.testshared.github.clientfactory import make_public_client
from ccai_tests.testshared.restclient.fakesession import assert_call


WORKFLOW = {
    "id": 161335,
    "node_id": "MDg6V29ya2Zsb3cxNjEzMzU=",
    "name": "CI",
    "path": ".github/workflows/blank.yaml",
    "state": "active",
}

WORKFLOW_RUN = {
    "id": 30433642,
    "name": "Build",
    "workflow_id": 161335,
    "status": "completed",
    "conclusion": "success",
    "head_branch": "main",
}


class ActionsGroupWireTests(unittest.TestCase):

    def test_get_workflow_hits_workflow_path(self) -> None:
        client, session = make_public_client([(200, WORKFLOW, {})])

        found = client.actions.get_workflow("octocat", "Hello-World", 161335)

        assert_call(
            session.last_call,
            method="GET",
            template="/repos/{owner}/{repo}/actions/workflows/{workflow_id}",
            path_params={"owner": "octocat", "repo": "Hello-World", "workflow_id": 161335},
            params={},
        )
        self.assertIsInstance(found, Workflow)
        self.assertEqual(found.name, "CI")
        self.assertEqual(found.state, "active")
        return

    def test_list_workflow_runs_sends_query_parameters(self) -> None:
        payload = {"total_count": 1, "workflow_runs": [WORKFLOW_RUN]}
        client, session = make_public_client([(200, payload, {})])

        found = client.actions.list_workflow_runs(
            "octocat", "Hello-World", "blank.yaml", branch="main", status="completed", per_page=5
        )

        assert_call(
            session.last_call,
            method="GET",
            template="/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs",
            path_params={"owner": "octocat", "repo": "Hello-World", "workflow_id": "blank.yaml"},
            params={"branch": "main", "status": "completed", "per_page": 5, "page": 1, "exclude_pull_requests": False},
        )
        self.assertEqual(found["total_count"], 1)
        self.assertEqual(found["workflow_runs"][0]["id"], 30433642)
        return

    def test_get_workflow_run_passes_exclude_pull_requests_flag(self) -> None:
        client, session = make_public_client([(200, WORKFLOW_RUN, {})])

        found = client.actions.get_workflow_run("octocat", "Hello-World", 30433642, exclude_pull_requests=True)

        assert_call(
            session.last_call,
            method="GET",
            template="/repos/{owner}/{repo}/actions/runs/{run_id}",
            path_params={"owner": "octocat", "repo": "Hello-World", "run_id": 30433642},
            params={"exclude_pull_requests": True},
        )
        self.assertIsInstance(found, WorkflowRun)
        self.assertEqual(found.conclusion, "success")
        return

    def test_create_workflow_dispatch_posts_body_and_returns_none_on_204(self) -> None:
        body = {"ref": "main", "inputs": {"environment": "staging"}}
        client, session = make_public_client([(204, None, {})])

        found = client.actions.create_workflow_dispatch("octocat", "Hello-World", "blank.yaml", body)

        assert_call(
            session.last_call,
            method="POST",
            template="/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches",
            path_params={"owner": "octocat", "repo": "Hello-World", "workflow_id": "blank.yaml"},
            body=body,
        )
        self.assertIsNone(found)
        return


if __name__ == "__main__":
    unittest.main()
