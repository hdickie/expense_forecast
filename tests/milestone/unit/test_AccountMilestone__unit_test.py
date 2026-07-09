import pytest

from expense_forecast.AccountMilestone import AccountMilestone


class TestAccountMilestoneMethods:

    @pytest.mark.unit
    def test_AccountMilestone_constructor__valid_inputs(self):
        AccountMilestone("Milestone_Name", "Account_Name", 0, 100)

    @pytest.mark.unit
    def test_AccountMilestone_constructor__invalid_inputs(self):
        with pytest.raises(ValueError):
            AccountMilestone(
                "Milestone_Name", "Account_Name", "X", 100
            )

        with pytest.raises(ValueError):
            AccountMilestone("Milestone_Name", "Account_Name", 0, "X")

    @pytest.mark.unit
    def test_str(self):
        assert (
            str(
                AccountMilestone(
                    "Milestone_Name", "Account_Name", 0, 100
                )
            )
            is not None
        )

    # TODO implement test_MilestoneSet_AccountMilestone_summary_column
    @pytest.mark.unit
    def test_MilestoneSet_AccountMilestone_summary_column(self):
        pass