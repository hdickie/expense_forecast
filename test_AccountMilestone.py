import pytest

import AccountMilestone

class TestAccountMilestoneMethods:

    def test_AccountMilestone_constructor__valid_inputs(self):
        AccountMilestone.AccountMilestone('Milestone_Name','Account_Name',0,100)

    def test_AccountMilestone_constructor__invalid_inputs(self):
        with pytest.raises(AssertionError):
            AccountMilestone.AccountMilestone('Milestone_Name', 'Account_Name', 'X', 100)

        with pytest.raises(AssertionError):
            AccountMilestone.AccountMilestone('Milestone_Name', 'Account_Name', 0, 'X')

    def test_str(self):
        str(AccountMilestone.AccountMilestone('Milestone_Name','Account_Name',0,100))

    def test_to_json(self):
        AccountMilestone.AccountMilestone('Milestone_Name','Account_Name',0,100).to_json()
