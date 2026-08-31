"""Shared test doubles. Fixture values use coding-domain vocabulary (repos,
endpoints, commits) — never lorem/animals/recipes."""


class FakeBackend:
    """A Backend double driven by canned rows, for pure unit tests.

    `dim_rows` maps a lookup key to canned rows for dimensioned `run_report`
    calls (§5-12 fetchers). The key is `extra["row_key"]` when a fetcher sets
    one (needed when two calls share a dimension, e.g. content's current vs.
    previous-period WoW comparison), else it defaults to `tuple(dimensions)`.
    """

    def __init__(self, realtime_rows=None, exec_rows=None, activity_row=None, dim_rows=None, gsc_rows=None, gsc_site=None):
        self.realtime_rows = realtime_rows if realtime_rows is not None else []
        self.exec_rows = exec_rows if exec_rows is not None else []
        self.activity_row = activity_row if activity_row is not None else {}
        self.dim_rows = dim_rows if dim_rows is not None else {}
        self.gsc_rows = gsc_rows if gsc_rows is not None else []
        self.gsc_site = gsc_site
        self.calls = []

    def run_report(self, dimensions, metrics, days, extra=None):
        extra = extra or {}
        self.calls.append(("run_report", dimensions, metrics, days, extra))
        if "row_key" in extra:
            return self.dim_rows.get(extra["row_key"], [])
        if extra.get("compare_previous") and not dimensions:
            return self.exec_rows
        if not dimensions:
            return [self.activity_row] if self.activity_row else []
        return self.dim_rows.get(tuple(dimensions), [])

    def run_realtime(self, metrics):
        self.calls.append(("run_realtime", metrics))
        return self.realtime_rows

    def run_cohort(self, cohort_spec, dimensions, metrics):
        raise NotImplementedError("run_cohort not exercised by PART 1/2 sections")

    def gsc_query(self, dimensions, days, row_limit=25):
        self.calls.append(("gsc_query", dimensions, days, row_limit))
        return self.gsc_rows
