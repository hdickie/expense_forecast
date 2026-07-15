import pytest
import pandas as pd
from datetime import date

from expense_forecast.AccountMilestone import AccountMilestone
from expense_forecast.MilestoneSet import MilestoneSet


class TestAccountMilestoneMethods:

    @pytest.mark.unit
    def test_AccountMilestone_constructor__valid_inputs(self):
        AccountMilestone("Milestone_Name", "Account_Name", 0, 100)

    @pytest.mark.unit
    def test_AccountMilestone_constructor__invalid_inputs(self):
        with pytest.raises(TypeError):
            AccountMilestone(
                "Milestone_Name", "Account_Name", "X", 100
            )

        with pytest.raises(TypeError):
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

    @pytest.mark.unit
    def test_MilestoneSet_AccountMilestone_summary_column(self):
        forecast_df = pd.DataFrame(
            {
                "Date": [date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)],
                "Checking": [100, 50, 0],
                "Net Worth": [100, 50, 0],
            }
        )

        success_date = MilestoneSet.evaluateAccountMilestone(
            forecast_df,
            "Net Worth",
            0,
            0,
            log_stack_depth=0,
        )

        assert success_date == date(2026, 1, 3)
