"""Regression checks for configuration and transcript compatibility."""

import pytest

from runner import report
from runner.allocations import allocations


def test_zero_budget_unequal_allocation():
    assert allocations("A.2", 3, 1, 0) == [0, 0, 0]


def test_unequal_allocations_are_reproducible_and_bounded():
    values = allocations("A.2", 100, 7, 1000)
    assert values == allocations("A.2", 100, 7, 1000)
    assert len(set(values)) > 1
    assert all(100 <= value <= 1900 for value in values)


@pytest.mark.parametrize(
    "experiment,count,tokens", [("bad", 2, 10), ("A.1", 0, 10), ("A.2", 1, -1)]
)
def test_invalid_allocations(experiment, count, tokens):
    with pytest.raises(ValueError):
        allocations(experiment, count, 1, tokens)


def test_report_recognizes_agent_prefix():
    assert report.MARKER.search("[pi-0] AGENT_BEGIN")[1] == "0"


def test_report_template_keeps_embedded_data_inside_script():
    output = report.render_report({"text": "</script><script>bad()</script>"})
    assert "__DATA__" not in output
    assert "</script><script>bad()" not in output
    assert "<\\/script>" in output
