"""
    .. module:: githubrestclientbase
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Github REST client base with token and basic auth support.
    
    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""


from __future__ import annotations

from base64 import b64encode
from typing import Dict, Optional

from requests import Session

from ccai.credentials.basecredential import BaseCredential
from ccai.credentials.basiccredential import BasicCredential

from ccai.restclient.base.aspectsrest import AspectsRest, DEFAULT_REST_ASPECTS
from ccai.restclient.base.restclientbase import RestClientBase

from ccai.credentials.githubtokencredential import GithubTokenCredential


class GithubRestClientBase(RestClientBase):
    """
        The :class:`GithubRestClientBase` object provides GitHub specific authentication
        logic for both password based and token based credentials.
    """

    def __init__(self, host: str, credential: BaseCredential, port: Optional[int] = None, scheme: Optional[str] = "https", headers: Optional[Dict[str, str]] = None, verify_certificate: Optional[bool] = None, aspects: AspectsRest = DEFAULT_REST_ASPECTS):
        """
            Initialize the GitHub REST client base.

            :param host: Hostname for the REST service.
            :param credential: Credential used for authentication.
            :param port: Optional port for the service.
            :param scheme: URL scheme, default is ``https``.
            :param headers: Optional default headers applied to every request.
            :param verify_certificate: Optional flag to enable or disable TLS verification.
            :param aspects: Default REST aspects.

            :returns: None
        """
        super().__init__(host, credential, port, scheme=scheme, headers=headers, verify_certificate=verify_certificate, aspects=aspects)
        self._headers.setdefault("Accept", "application/vnd.github.v3+json")
        return

    def authenticate(self):
        """
            Authenticate with GitHub using the provided credential.

            :raises: RuntimeError if the credential type is not supported.
        """
        credential = self._credential
        headers = self._build_auth_headers(credential)

        session = Session()
        session.verify = self._verify_certificate

        if headers:
            session.headers.update(headers)

        self._session = session
        return

    def _build_auth_headers(self, credential: BaseCredential) -> Dict[str, str]:
        """
            Build the Authorization header for the given credential.

            :param credential: The credential used to authenticate.

            :returns: Dictionary containing Authorization header.
            :raises: RuntimeError if the credential type is not supported.
        """
        if isinstance(credential, BasicCredential):
            return self._build_basic_auth_headers(credential.username, credential.password)

        if GithubTokenCredential is not None and isinstance(credential, GithubTokenCredential):
            token_value = getattr(credential, "token", None)
            if token_value:
                return self._build_token_auth_headers(token_value)

        token_value = self._get_token_value(credential)
        if token_value:
            return self._build_token_auth_headers(token_value)

        username = getattr(credential, "username", None)
        password = getattr(credential, "password", None)
        if username is not None and password is not None:
            return self._build_basic_auth_headers(username, password)

        errmsg = f"Unsupported credential type '{type(credential).__name__}' for GitHub authentication."
        raise RuntimeError(errmsg)

    def _build_basic_auth_headers(self, username: str, password: str) -> Dict[str, str]:
        authbytes = f"{username}:{password}".encode("utf-8")
        passwd_encoded = b64encode(authbytes).decode("utf-8")
        return {
            "Content-Type": "application/json",
            "Authorization": f"Basic {passwd_encoded}"
        }

    def _build_token_auth_headers(self, token_value: str) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token_value}"
        }

    def _get_token_value(self, credential: BaseCredential) -> Optional[str]:
        token_value = getattr(credential, "token", None)
        if token_value:
            return token_value

        token_value = getattr(credential, "access_token", None)
        if token_value:
            return token_value

        return None
