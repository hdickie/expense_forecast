import pytest

import AccountMilestone

class TestAccountMilestoneMethods:

    @pytest.mark.unit
    def test_AccountMilestone_constructor__valid_inputs(self):
        AccountMilestone.AccountMilestone('Milestone_Name','Account_Name',0,100)

    @pytest.mark.unit
    def test_AccountMilestone_constructor__invalid_inputs(self):
        with pytest.raises(ValueError):
            AccountMilestone.AccountMilestone('Milestone_Name', 'Account_Name', 'X', 100)

        with pytest.raises(ValueError):
            AccountMilestone.AccountMilestone('Milestone_Name', 'Account_Name', 0, 'X')

    @pytest.mark.unit
    def test_str(self):
        assert str(AccountMilestone.AccountMilestone('Milestone_Name','Account_Name',0,100)) is not None
