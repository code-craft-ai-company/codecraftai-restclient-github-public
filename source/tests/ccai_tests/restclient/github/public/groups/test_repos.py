"""
    Wire tests for the generated ``ReposApiGroup``: what a call puts on the
    wire, that the canned response parses into the declared schema type, and
    ``PagedList`` pagination through ``list_for_org``.
"""

import unittest

from typing import Any, Dict, List

from ccai.restclient.base.pagedlist import PagedList

from ccai.restclient.github.public.groups.repos import FullRepository, MinimalRepository

from ccai_tests.testshared.github.clientfactory import make_public_client
from ccai_tests.testshared.restclient.fakesession import assert_call, paged


ORG_REPOS_URL = "https://api.github.test/orgs/octo-org/repos?per_page=2"


def _repo(number: int, name: str) -> Dict[str, Any]:
    """
        Builds the subset of a GitHub repository payload the tests read.
    """
    rtnval = {
        "id": number,
        "node_id": "MDEwOlJlcG9zaXRvcnk{}".format(number),
        "name": name,
        "full_name": "octo-org/{}".format(name),
        "private": False,
        "owner": {"login": "octo-org", "id": 1},
    }
    return rtnval


class ReposGroupWireTests(unittest.TestCase):

    def test_get_hits_repos_owner_repo(self) -> None:
        client, session = make_public_client([(200, _repo(1296269, "Hello-World"), {})])

        found = client.repos.get("octocat", "Hello-World")

        assert_call(
            session.last_call,
            method="GET",
            template="/repos/{owner}/{repo}",
            path_params={"owner": "octocat", "repo": "Hello-World"},
            params={},
        )
        self.assertIsNone(session.last_call.body)
        self.assertIsInstance(found, FullRepository)
        self.assertEqual(found.id, 1296269)
        self.assertEqual(found.full_name, "octo-org/Hello-World")
        return

    def test_create_in_org_posts_json_body(self) -> None:
        body = {"name": "new-repo", "private": True, "auto_init": True}
        client, session = make_public_client([(201, _repo(42, "new-repo"), {})])

        found = client.repos.create_in_org("octo-org", body)

        assert_call(
            session.last_call,
            method="POST",
            template="/orgs/{org}/repos",
            path_params={"org": "octo-org"},
            body=body,
        )
        self.assertEqual(found["name"], "new-repo")
        return

    def test_update_patches_body_and_parses_full_repository(self) -> None:
        body = {"description": "renamed", "has_wiki": False}
        payload = _repo(1296269, "Hello-World")
        payload["description"] = "renamed"
        client, session = make_public_client([(200, payload, {})])

        found = client.repos.update("octocat", "Hello-World", body)

        assert_call(
            session.last_call,
            method="PATCH",
            template="/repos/{owner}/{repo}",
            path_params={"owner": "octocat", "repo": "Hello-World"},
            body=body,
        )
        self.assertIsInstance(found, FullRepository)
        self.assertEqual(found.description, "renamed")
        return

    def test_get_sends_client_default_headers(self) -> None:
        client, session = make_public_client([(200, _repo(1, "a"), {})])

        client.repos.get("octocat", "a")

        self.assertEqual(session.last_call.headers, client.headers)
        self.assertEqual(session.last_call.headers["Accept"], "application/vnd.github.v3+json")
        return

    def test_get_uses_explicit_headers_instead_of_defaults(self) -> None:
        client, session = make_public_client([(200, _repo(1, "a"), {})])
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}

        client.repos.get("octocat", "a", headers=headers)

        self.assertEqual(session.last_call.headers, headers)
        return


class ReposListForOrgPaginationTests(unittest.TestCase):

    def setUp(self) -> None:
        self.repos = [_repo(1, "alpha"), _repo(2, "beta"), _repo(3, "gamma")]
        self.pages = paged(self.repos, 2, url=ORG_REPOS_URL)
        return

    def test_first_page_parses_items_and_links_to_next(self) -> None:
        client, session = make_public_client(self.pages)

        page = client.repos.list_for_org("octo-org", per_page=2)

        assert_call(
            session.last_call,
            method="GET",
            template="/orgs/{org}/repos",
            path_params={"org": "octo-org"},
            params={"type": "all", "sort": "created", "per_page": 2, "page": 1},
        )
        self.assertIsInstance(page, PagedList)
        self.assertEqual(len(page), 2)
        self.assertIsInstance(page[0], MinimalRepository)
        self.assertEqual([item.name for item in page], ["alpha", "beta"])
        self.assertTrue(page.has_next)
        self.assertEqual(page.next_page, 2)
        self.assertEqual(page.last_page, 2)
        return

    def test_last_page_has_no_next(self) -> None:
        client, session = make_public_client(self.pages[1:])

        page = client.repos.list_for_org("octo-org", per_page=2, page=2)

        self.assertEqual(session.last_call.params["page"], 2)
        self.assertEqual([item.name for item in page], ["gamma"])
        self.assertFalse(page.has_next)
        self.assertIsNone(page.next_page)
        self.assertTrue(page.has_prev)
        self.assertEqual(page.prev_page, 1)
        return

    def test_walking_next_page_until_exhausted_visits_every_repo_once(self) -> None:
        client, session = make_public_client(self.pages)

        names: List[str] = []
        page_number = 1
        while True:
            page = client.repos.list_for_org("octo-org", per_page=2, page=page_number)
            names.extend([item.name for item in page])
            if not page.has_next:
                break
            page_number = page.next_page

        self.assertEqual(names, ["alpha", "beta", "gamma"])
        self.assertEqual([call.params["page"] for call in session.calls], [1, 2])
        session.assert_exhausted()
        return

    def test_empty_org_returns_empty_page_without_links(self) -> None:
        client, session = make_public_client(paged([], 30, url=ORG_REPOS_URL))

        page = client.repos.list_for_org("octo-org")

        self.assertEqual(len(page), 0)
        self.assertEqual(page.items, [])
        self.assertEqual(page.links, {})
        self.assertFalse(page.has_next)
        return


if __name__ == "__main__":
    unittest.main()
