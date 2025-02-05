import os
import subprocess
from unittest import mock

import pytest

from datadog_checks.dev import docker_run
from datadog_checks.upbound_uxp import UpboundUxpCheck

from . import common


@pytest.fixture(scope='session')
def dd_environment():
    with docker_run(
        common.COMPOSE_FILE,
        endpoints=[
            'http://{}:{}/metrics'.format(common.HOST, common.PORT),
        ],
    ):
        yield {"openmetrics_endpoint": 'http://{}:{}/metrics'.format(common.HOST, common.PORT)}


@pytest.fixture(scope='session')
def dd_environment_k8s():
    print("conftest: dd_environment spinning up")
    cmd = ('kind', 'get', 'clusters')
    try:
        p = subprocess.run(cmd, timeout=600, capture_output=True, text=True)
        cluster_present = False
        for cluster in p.stdout.split('\n'):
            if cluster == "uxp":
                print("conftest: dd_environment using existing uxp cluster")
                cluster_present = True
                break
        if not cluster_present:
            print("conftest: dd_environment: creating new uxp cluster")
            os.system("tests/fixtures/k8s-uxp-agent-check.sh")
        yield
        print("conftest: dd_environment cleaning up")
    except subprocess.TimeoutExpired as ex:
        print(ex)


@pytest.fixture
def instance():
    print("conftest: instance")
    return {"verbose": False, "metrics_default": "min", "uxp_hosts": ["localhost"]}


@pytest.fixture
def check(instance):
    print("conftest: check")
    return UpboundUxpCheck({}, [instance])


@pytest.fixture()
def mock_metrics():
    print("conftest: mock_metrics")
    fixture_file = os.path.join(os.path.dirname(__file__), "fixtures", "metrics.txt")

    with open(fixture_file, "r") as f:
        content = f.read()

    with mock.patch(
        "requests.get",
        return_value=mock.MagicMock(
            status_code=200,
            iter_lines=lambda **kwargs: content.split("\n"),
            headers={"Content-Type": "text/plain"},
        ),
    ):
        yield
