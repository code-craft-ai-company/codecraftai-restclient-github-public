"""
    Wire tests for the generated ``OrgsApiGroup``.
"""

import unittest

from ccai.restclient.base.pagedlist import PagedList

from ccai.restclient.github.public.groups.orgs import OrganizationFull, OrgMembership, SimpleUser

from ccai_tests.testshared.github.clientfactory import make_public_client
from ccai_tests.testshared.restclient.fakesession import assert_call, paged


ORGANIZATION = {
    "login": "octo-org",
    "id": 1,
    "node_id": "MDEyOk9yZ2FuaXphdGlvbjE=",
    "description": "A great organization",
    "public_repos": 2,
}


class OrgsGroupWireTests(unittest.TestCase):

    def test_get_hits_orgs_org(self) -> None:
        client, session = make_public_client([(200, ORGANIZATION, {})])

        found = client.orgs.get("octo-org")

        assert_call(
            session.last_call,
            method="GET",
            template="/orgs/{org}",
            path_params={"org": "octo-org"},
            params={},
        )
        self.assertIsInstance(found, OrganizationFull)
        self.assertEqual(found.login, "octo-org")
        self.assertEqual(found.public_repos, 2)
        return

    def test_update_patches_body_and_parses_organization(self) -> None:
        body = {"description": "Updated description", "billing_email": "billing@example.test"}
        payload = dict(ORGANIZATION)
        payload["description"] = "Updated description"
        client, session = make_public_client([(200, payload, {})])

        found = client.orgs.update("octo-org", body)

        assert_call(
            session.last_call,
            method="PATCH",
            template="/orgs/{org}",
            path_params={"org": "octo-org"},
            body=body,
        )
        self.assertIsInstance(found, OrganizationFull)
        self.assertEqual(found.description, "Updated description")
        return

    def test_get_membership_for_user_hits_two_path_parameters(self) -> None:
        membership = {"url": "https://api.github.test/orgs/octo-org/memberships/octocat", "state": "active", "role": "admin"}
        client, session = make_public_client([(200, membership, {})])

        found = client.orgs.get_membership_for_user("octo-org", "octocat")

        assert_call(
            session.last_call,
            method="GET",
            template="/orgs/{org}/memberships/{username}",
            path_params={"org": "octo-org", "username": "octocat"},
        )
        self.assertIsInstance(found, OrgMembership)
        self.assertEqual(found.role, "admin")
        return

    def test_list_members_filters_by_role_and_returns_paged_list(self) -> None:
        members = [{"login": "octocat", "id": 1}, {"login": "hubot", "id": 2}]
        client, session = make_public_client(paged(members, 30))

        page = client.orgs.list_members("octo-org", role="admin")

        assert_call(
            session.last_call,
            method="GET",
            template="/orgs/{org}/members",
            path_params={"org": "octo-org"},
            params={"filter": "all", "role": "admin", "per_page": 30, "page": 1},
        )
        self.assertIsInstance(page, PagedList)
        self.assertIsInstance(page[0], SimpleUser)
        self.assertEqual([member.login for member in page], ["octocat", "hubot"])
        self.assertFalse(page.has_next)
        return


if __name__ == "__main__":
    unittest.main()
