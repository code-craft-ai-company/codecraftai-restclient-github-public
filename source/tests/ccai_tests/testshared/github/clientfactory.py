"""
    .. module:: clientfactory
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Builds :class:`GithubPublicRestClient` instances whose HTTP
        session is a recording :class:`FakeSession`, so group methods can be
        exercised at the wire level without a network.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""


__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import Any, Optional, Sequence, Tuple

from ccai.credentials.githubtokencredential import GithubTokenCredential

from ccai.restclient.github.public.githubpublicrestclient import GithubPublicRestClient

from ccai_tests.testshared.restclient.fakesession import FakeSession


TEST_HOST = "api.github.test"
TEST_HOST_URL = "https://" + TEST_HOST
TEST_TOKEN = "ghp_testtoken"


def make_token_credential() -> GithubTokenCredential:
    """
        Builds the token credential the test clients authenticate with.

        :returns: A :class:`GithubTokenCredential`.
    """
    credential = GithubTokenCredential(
        identifier="github-test",
        categories=["github-token"],
        token=TEST_TOKEN,
    )
    return credential


def make_public_client(responses: Optional[Sequence[Any]] = None) -> Tuple[GithubPublicRestClient, FakeSession]:
    """
        Builds a :class:`GithubPublicRestClient` over a :class:`FakeSession`
        holding ``responses``.

        The session is installed directly on the client's ``_session``
        attribute, which :meth:`RestClientBase._get_session` returns without
        calling ``authenticate``, so no real :class:`requests.Session` is
        created.

        :param responses: The canned responses, in call order.

        :returns: The client and the session that records its calls.
    """
    session = FakeSession(responses)
    credential = make_token_credential()
    client = GithubPublicRestClient(host=TEST_HOST, credential=credential)
    client._session = session
    return client, session
