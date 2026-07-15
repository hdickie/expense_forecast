import pytest
import pandas as pd

from expense_forecast.MemoMilestone import MemoMilestone
from expense_forecast.MilestoneSet import MilestoneSet
import re


class TestMemoMilestoneMethods:
    def test_mapping_constructor_supplies_milestone_name(self):
        milestones = MilestoneSet(
            {"Get job as RN": MemoMilestone(memo_regex=r"RN Year 1 Income")}
        )

        assert milestones.memo_milestones[0].milestone_name == "Get job as RN"

    def test_missing_memo_milestone_returns_none(self):
        forecast = pd.DataFrame(
            {"Date": [pd.Timestamp("2026-07-01")], "Memo": ["CNA income"]}
        )

        result = MilestoneSet.evaulateMemoMilestone(
            forecast, r"RN Year 1 income", log_stack_depth=0
        )

        assert result is None

    @pytest.mark.unit
    def test_MemoMilestone_constructor(self):
        MemoMilestone("milestone_name", "memo_regex")

        with pytest.raises(re.error):
            MemoMilestone("milestone_name", ")malformed_regex")

    @pytest.mark.unit
    def test_str(self):
        str(MemoMilestone("milestone_name", "memo_regex"))
