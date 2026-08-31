"""Shared test doubles. Fixture values use coding-domain vocabulary (repos,
endpoints, commits) — never lorem/animals/recipes."""


class FakeBackend:
    """A Backend double driven by canned rows, for pure unit tests."""

    def __init__(self, realtime_rows=None, exec_rows=None, activity_row=None):
        self.realtime_rows = realtime_rows if realtime_rows is not None else []
        self.exec_rows = exec_rows if exec_rows is not None else []
        self.activity_row = activity_row if activity_row is not None else {}
        self.calls = []

    def run_report(self, dimensions, metrics, days, extra=None):
        extra = extra or {}
        self.calls.append(("run_report", dimensions, metrics, days, extra))
        if extra.get("compare_previous"):
            return self.exec_rows
        return [self.activity_row] if self.activity_row else []

    def run_realtime(self, metrics):
        self.calls.append(("run_realtime", metrics))
        return self.realtime_rows

    def run_cohort(self, cohort_spec, dimensions, metrics):
        raise NotImplementedError("run_cohort not exercised by PART 1 sections 1-4")

    def gsc_query(self, dimensions, days, row_limit=25):
        raise NotImplementedError("gsc_query not exercised by PART 1 sections 1-4")
