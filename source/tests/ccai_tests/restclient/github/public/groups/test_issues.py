"""
    Wire tests for the generated ``IssuesApiGroup``.
"""

import unittest

from ccai.restclient.base.pagedlist import PagedList

from ccai.restclient.github.public.groups.issues import Issue

from ccai_tests.testshared.github.clientfactory import make_public_client
from ccai_tests.testshared.restclient.fakesession import assert_call, paged


ISSUE = {
    "id": 1,
    "node_id": "MDU6SXNzdWUx",
    "number": 1347,
    "title": "Found a bug",
    "state": "open",
    "labels": [{"name": "bug"}],
}


class IssuesGroupWireTests(unittest.TestCase):

    def test_get_hits_issue_number_path(self) -> None:
        client, session = make_public_client([(200, ISSUE, {})])

        found = client.issues.get("octocat", "Hello-World", 1347)

        assert_call(
            session.last_call,
            method="GET",
            template="/repos/{owner}/{repo}/issues/{issue_number}",
            path_params={"owner": "octocat", "repo": "Hello-World", "issue_number": 1347},
            params={},
        )
        self.assertIsInstance(found, Issue)
        self.assertEqual(found.number, 1347)
        self.assertEqual(found.title, "Found a bug")
        return

    def test_list_for_repo_sends_filter_query_parameters(self) -> None:
        issues = [ISSUE, dict(ISSUE, id=2, number=1348, title="Another bug", state="closed")]
        client, session = make_public_client(paged(issues, 30))

        page = client.issues.list_for_repo("octocat", "Hello-World", state="closed", labels="bug", per_page=5)

        assert_call(
            session.last_call,
            method="GET",
            template="/repos/{owner}/{repo}/issues",
            path_params={"owner": "octocat", "repo": "Hello-World"},
            params={"state": "closed", "labels": "bug", "sort": "created", "direction": "desc", "per_page": 5, "page": 1},
        )
        self.assertIsInstance(page, PagedList)
        self.assertIsInstance(page[0], Issue)
        self.assertEqual([issue.number for issue in page], [1347, 1348])
        return

    def test_create_posts_body_and_expects_201(self) -> None:
        body = {"title": "Found a bug", "body": "It does not work.", "labels": ["bug"]}
        client, session = make_public_client([(201, ISSUE, {})])

        found = client.issues.create("octocat", "Hello-World", body)

        assert_call(
            session.last_call,
            method="POST",
            template="/repos/{owner}/{repo}/issues",
            path_params={"owner": "octocat", "repo": "Hello-World"},
            body=body,
        )
        self.assertEqual(found["number"], 1347)
        return

    def test_update_patches_body_and_parses_issue(self) -> None:
        body = {"state": "closed", "state_reason": "completed"}
        client, session = make_public_client([(200, dict(ISSUE, state="closed"), {})])

        found = client.issues.update("octocat", "Hello-World", 1347, body)

        assert_call(
            session.last_call,
            method="PATCH",
            template="/repos/{owner}/{repo}/issues/{issue_number}",
            path_params={"owner": "octocat", "repo": "Hello-World", "issue_number": 1347},
            body=body,
        )
        self.assertIsInstance(found, Issue)
        self.assertEqual(found.state, "closed")
        return


if __name__ == "__main__":
    unittest.main()
