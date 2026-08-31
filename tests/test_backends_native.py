import pytest

from gadeepdive.backends.native import NativeBackend


@pytest.fixture
def backend():
    return NativeBackend(ga4_property_id="900100200", gsc_site="sc-domain:repo-atlas.dev")


def test_run_report_raises_not_implemented(backend):
    with pytest.raises(NotImplementedError, match="native"):
        backend.run_report([], ["sessions"], 7)


def test_run_realtime_raises_not_implemented(backend):
    with pytest.raises(NotImplementedError, match="native"):
        backend.run_realtime(["activeUsers"])


def test_run_cohort_raises_not_implemented(backend):
    with pytest.raises(NotImplementedError, match="native"):
        backend.run_cohort({}, ["cohort"], ["cohortActiveUsers"])


def test_gsc_query_raises_not_implemented(backend):
    with pytest.raises(NotImplementedError, match="native"):
        backend.gsc_query(["query"], 7)
