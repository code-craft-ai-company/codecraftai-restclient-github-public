"""
    Tests for :class:`GithubPublicRestClient` and its
    :class:`GithubRestClientBase` parent: authentication headers, group
    binding, the error mapping a generated call surfaces, and a property
    check that path parameters land in the generated template.
"""

import unittest

from base64 import b64encode
from typing import Optional

from ccai.credentials.basiccredential import BasicCredential

from ccai.errors.exceptions import (
    HttpForbiddenError,
    HttpNotFoundError,
    HttpUnprocessableContentError,
)

from ccai.restclient.github.public.githubpublicrestclient import GithubPublicRestClient
from ccai.restclient.github.public.groups.repos import ReposApiGroup

from ccai_tests.testshared.github.clientfactory import (
    TEST_HOST,
    TEST_HOST_URL,
    TEST_TOKEN,
    make_public_client,
    make_token_credential,
)
from ccai_tests.testshared.restclient.fakesession import assert_call


class _NoAuthCredential:
    """
        A credential carrying none of the attributes the GitHub client can
        authenticate with.
    """
    identifier = "nothing"


class GithubPublicRestClientAuthTests(unittest.TestCase):

    def test_token_credential_authenticates_with_bearer_header(self) -> None:
        client = GithubPublicRestClient(host=TEST_HOST, credential=make_token_credential())

        client.authenticate()

        self.assertIsNotNone(client._session)
        self.assertEqual(client._session.headers["Authorization"], "Bearer " + TEST_TOKEN)
        self.assertEqual(client._session.headers["Content-Type"], "application/json")
        return

    def test_basic_credential_authenticates_with_basic_header(self) -> None:
        credential = BasicCredential(identifier="basic", categories=["basic"], username="octocat", password="secret")
        client = GithubPublicRestClient(host=TEST_HOST, credential=credential)

        client.authenticate()

        expected = "Basic " + b64encode(b"octocat:secret").decode("utf-8")
        self.assertEqual(client._session.headers["Authorization"], expected)
        return

    def test_unsupported_credential_raises_runtime_error(self) -> None:
        client = GithubPublicRestClient(host=TEST_HOST, credential=_NoAuthCredential())

        with self.assertRaises(RuntimeError) as context:
            client.authenticate()

        self.assertIn("_NoAuthCredential", str(context.exception))
        return

    def test_default_accept_header_targets_github_v3(self) -> None:
        client = GithubPublicRestClient(host=TEST_HOST, credential=make_token_credential())
        self.assertEqual(client.headers["Accept"], "application/vnd.github.v3+json")
        self.assertEqual(client.host, TEST_HOST)
        return


class GithubPublicRestClientGroupTests(unittest.TestCase):

    def test_group_properties_are_bound_to_the_client(self) -> None:
        client, session = make_public_client([])

        repos = client.repos

        self.assertIsInstance(repos, ReposApiGroup)
        self.assertIs(client.repos, repos)
        self.assertIs(repos.client, client)
        return

    def test_generated_call_targets_the_client_host(self) -> None:
        client, session = make_public_client([(200, {"id": 1}, {})])

        client.repos.get("octocat", "Hello-World")

        self.assertEqual(session.last_call.url, TEST_HOST_URL + "/repos/octocat/Hello-World")
        return


class GithubPublicRestClientErrorMappingTests(unittest.TestCase):

    def test_404_raises_not_found_with_response_body(self) -> None:
        body = {"message": "Not Found", "documentation_url": "https://docs.github.com/rest/repos/repos#get-a-repository"}
        client, session = make_public_client([(404, body, {})])

        with self.assertRaises(HttpNotFoundError) as context:
            client.repos.get("octocat", "missing")

        message = str(context.exception)
        self.assertIn("code=404", message)
        self.assertIn("Not Found", message)
        self.assertIn(TEST_HOST_URL + "/repos/octocat/missing", message)
        return

    def test_422_raises_unprocessable_content_with_validation_errors(self) -> None:
        body = {
            "message": "Validation Failed",
            "errors": [
                {"resource": "Repository", "code": "custom", "field": "name", "message": "name already exists on this account"}
            ],
            "documentation_url": "https://docs.github.com/rest/repos/repos#create-an-organization-repository",
        }
        client, session = make_public_client([(422, body, {})])

        with self.assertRaises(HttpUnprocessableContentError) as context:
            client.repos.create_in_org("octo-org", {"name": "dup"})

        message = str(context.exception)
        self.assertIn("code=422", message)
        self.assertIn("Validation Failed", message)
        self.assertIn("name already exists on this account", message)
        return

    def test_403_rate_limit_raises_forbidden_with_response_body(self) -> None:
        body = {
            "message": "API rate limit exceeded for 203.0.113.7. (But here's the good news: Authenticated requests get a higher rate limit.)",
            "documentation_url": "https://docs.github.com/rest/overview/resources-in-the-rest-api#rate-limiting",
        }
        headers = {"X-RateLimit-Limit": "60", "X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1700000000"}
        client, session = make_public_client([(403, body, headers)])

        with self.assertRaises(HttpForbiddenError) as context:
            client.repos.get("octocat", "Hello-World")

        message = str(context.exception)
        self.assertIn("code=403", message)
        self.assertIn("API rate limit exceeded", message)
        return


class GithubPublicRestClientPathParameterTests(unittest.TestCase):

    # Representative owner and repository names over the characters GitHub
    # allows: case, digits, hyphens, underscores, dots, single characters and
    # the maximum lengths (39 for an owner, 100 for a repository).
    NAME_CASES = [
        ("octocat", "Hello-World"),
        ("a", "b"),
        ("octo-org", "my_repo.v2"),
        ("Octo1234", "1234"),
        ("under_score", "trailing-dash-"),
        ("dotted.owner", ".github"),
        ("x" * 39, "y" * 100),
        ("MiXeD-CaSe_9", "UPPER.lower-mixed_09"),
    ]

    def test_repos_get_places_each_owner_and_repo_name_in_the_template(self) -> None:
        """
            For each representative owner and repository name,
            ``repos.get(owner, repo)`` hits ``GET /repos/{owner}/{repo}`` with
            exactly those values and parses the response.
        """
        for owner, repo in self.NAME_CASES:
            with self.subTest(owner=owner, repo=repo):
                client, session = make_public_client([(200, {"id": 1, "name": repo}, {})])

                found = client.repos.get(owner, repo)

                extracted = assert_call(
                    session.last_call,
                    method="GET",
                    template="/repos/{owner}/{repo}",
                    path_params={"owner": owner, "repo": repo},
                )
                self.assertEqual(extracted, {"owner": owner, "repo": repo})
                self.assertEqual(found.name, repo)
        return


if __name__ == "__main__":
    unittest.main()
