import pytest
from expense_forecast.MemoMilestone import MemoMilestone
from expense_forecast.MilestoneSet import MilestoneSet
import re


class TestMemoMilestoneMethods:
    def test_mapping_constructor_supplies_milestone_name(self):
        milestones = MilestoneSet(
            {"Get job as RN": MemoMilestone(memo_regex=r"RN Year 1 Income")}
        )

        assert milestones.memo_milestones[0].milestone_name == "Get job as RN"
    @pytest.mark.unit
    def test_MemoMilestone_constructor(self):
        MemoMilestone("milestone_name", "memo_regex")

        with pytest.raises(re.error):
            MemoMilestone("milestone_name", ")malformed_regex")

    @pytest.mark.unit
    def test_str(self):
        str(MemoMilestone("milestone_name", "memo_regex"))
