import pytest
from expense_forecast.MemoMilestone import MemoMilestone
import re


class TestMemoMilestoneMethods:
    @pytest.mark.unit
    def test_MemoMilestone_constructor(self):
        MemoMilestone("milestone_name", "memo_regex")

        with pytest.raises(re.error):
            MemoMilestone("milestone_name", ")malformed_regex")

    @pytest.mark.unit
    def test_str(self):
        str(MemoMilestone("milestone_name", "memo_regex"))
