"""
    .. module:: githubrestclientgenerator
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Github REST client generator with GitHub specific configuration.
    
    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

from __future__ import annotations

import os

from automojo.restclient.base.restclientgenerator import RestClientGenerator

from automojo.restclient.github.public.githubrestclientbase import GithubRestClientBase


class GithubRestClientGenerator(RestClientGenerator):
    """
        GitHub REST client generator configured for the public API client.
    """

    REST_CLIENT_BASE_CLASS = GithubRestClientBase

    CLIENT_MODULE_ROOT = "automojo.restclient.github.public"

    SCHEMA_MODULE_ROOT = "automojo.restclient.github.public.schemas"
    GROUP_MODULE_ROOT = "automojo.restclient.github.public.groups"


def rest_client_generator_main():
    """
        Entry point used to generate REST client code from the OpenAPI specification.
    """

    THIS_FILE = __file__
    THIS_DIR = os.path.dirname(THIS_FILE)
    CLIENT_ROOT = os.path.dirname(os.path.join(THIS_DIR))

    SPECS_DIR = os.path.join(THIS_DIR, "specs")
    OPENAPI_SPECFILE = os.path.join(SPECS_DIR, "api-public.json")

    generator = GithubRestClientGenerator(
        openapi_spec_file=OPENAPI_SPECFILE,
        clients_root=CLIENT_ROOT,
        client_class_name="GithubPublicRestClient"
    )
    generator.generate()
    return


if __name__ == "__main__":
    rest_client_generator_main()


    