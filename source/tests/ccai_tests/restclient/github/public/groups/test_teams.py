"""
    Wire tests for the generated ``TeamsApiGroup``.
"""

import unittest

from ccai.restclient.base.pagedlist import PagedList

from ccai.restclient.github.public.groups.teams import SimpleUser, Team, TeamFull

from ccai_tests.testshared.github.clientfactory import make_public_client
from ccai_tests.testshared.restclient.fakesession import assert_call, paged


TEAM = {
    "id": 1,
    "node_id": "MDQ6VGVhbTE=",
    "name": "Justice League",
    "slug": "justice-league",
    "privacy": "closed",
    "permission": "admin",
}


class TeamsGroupWireTests(unittest.TestCase):

    def test_get_by_name_hits_org_and_team_slug(self) -> None:
        client, session = make_public_client([(200, TEAM, {})])

        found = client.teams.get_by_name("octo-org", "justice-league")

        assert_call(
            session.last_call,
            method="GET",
            template="/orgs/{org}/teams/{team_slug}",
            path_params={"org": "octo-org", "team_slug": "justice-league"},
            params={},
        )
        self.assertIsInstance(found, TeamFull)
        self.assertEqual(found.slug, "justice-league")
        return

    def test_create_posts_body_and_expects_201(self) -> None:
        body = {"name": "Justice League", "privacy": "closed", "maintainers": ["octocat"]}
        client, session = make_public_client([(201, TEAM, {})])

        found = client.teams.create("octo-org", body)

        assert_call(
            session.last_call,
            method="POST",
            template="/orgs/{org}/teams",
            path_params={"org": "octo-org"},
            body=body,
        )
        self.assertEqual(found["name"], "Justice League")
        return

    def test_list_returns_paged_list_of_teams(self) -> None:
        teams = [TEAM, dict(TEAM, id=2, name="Avengers", slug="avengers")]
        client, session = make_public_client(paged(teams, 30))

        page = client.teams.list("octo-org")

        assert_call(
            session.last_call,
            method="GET",
            template="/orgs/{org}/teams",
            path_params={"org": "octo-org"},
            params={"per_page": 30, "page": 1},
        )
        self.assertIsInstance(page, PagedList)
        self.assertIsInstance(page[0], Team)
        self.assertEqual([team.slug for team in page], ["justice-league", "avengers"])
        return

    def test_list_members_in_org_sends_role_filter(self) -> None:
        members = [{"login": "octocat", "id": 1}]
        client, session = make_public_client(paged(members, 30))

        page = client.teams.list_members_in_org("octo-org", "justice-league", role="maintainer")

        assert_call(
            session.last_call,
            method="GET",
            template="/orgs/{org}/teams/{team_slug}/members",
            path_params={"org": "octo-org", "team_slug": "justice-league"},
            params={"role": "maintainer", "per_page": 30, "page": 1},
        )
        self.assertIsInstance(page[0], SimpleUser)
        self.assertEqual(page[0].login, "octocat")
        return


if __name__ == "__main__":
    unittest.main()
