"""
evchart_helper.boto3_manager

A helper module that manages connecting to the AWS API endpoints via boto3 in order to ensure the
DOE proxy information is used as well as FIPS being enabled.  Also provides some simple caching of
service clients/resources for reuse.
"""
import os

import boto3
from botocore.config import Config
from evchart_helper.boto3_manager.exceptions import (
    Boto3ManagerClientTypeError
)


class Boto3Manager:

    def __init__(self):
        self._clients = {}
        self._config = Config(
            proxies={
                "http": os.environ["NETWORKPROXY"],
                "https": os.environ["NETWORKPROXY"]
            } if os.environ.get("NETWORKPROXY") else None,
            use_fips_endpoint=True
        )
        self._resources = {}
        self._session = None

    def __instantiate(
        self,
        service_id,
        endpoint_url,
        region_name,
        client_type="client"
    ):
        """
            Instantiate the boto3 module for the requested AWS service "client" or "resource".
        """
        if client_type not in ["client", "resource"]:
            raise Boto3ManagerClientTypeError

        if not self._session:
            self._session = boto3.session.Session()

        collection = getattr(self, f"_{client_type}s")
        if not collection.get(service_id):
            collection[service_id] = {}

        region_name = region_name if region_name else "us-east-1"
        if not collection[service_id].get(region_name):
            if service_id == "s3":
                self._config = self._config.merge(Config(signature_version="s3v4"))

            collection[service_id][region_name] = getattr(self._session, client_type)(
                service_id,
                config=self._config,
                endpoint_url=(
                    f"https://{service_id}-fips.{region_name}.amazonaws.com"
                ) if service_id in ["sts"] else endpoint_url
            )

        return collection[service_id][region_name]

    def client(self, service_id, endpoint_url=None, region_name=None):
        """
            Returns a boto3 AWS service "client".
        """
        return self.__instantiate(service_id, endpoint_url, region_name)

    def resource(self, service_id, endpoint_url=None, region_name=None):
        """
            Returns a boto3 AWS service "resource".
        """
        return self.__instantiate(service_id, endpoint_url, region_name, "resource")

boto3_manager = Boto3Manager()
