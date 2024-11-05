import pytest
import MemoMilestone
import re

class TestMemoMilestoneMethods:
    def test_MemoMilestone_constructor(self):
        MemoMilestone.MemoMilestone('milestone_name','memo_regex')

        with pytest.raises(re.error):
            MemoMilestone.MemoMilestone('milestone_name', ')malformed_regex')

    def test_str(self):
        str(MemoMilestone.MemoMilestone('milestone_name','memo_regex'))


