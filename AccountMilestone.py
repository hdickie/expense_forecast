
class AccountMilestone:

    def __init__(self,Milestone_Name,Account_Name,Min_Balance,Max_Balance):
        self.milestone_name = Milestone_Name
        self.account_name = Account_Name
        self.min_balance = Min_Balance
        self.max_balance = Max_Balance

        assert Min_Balance <= Max_Balance


    def __str__(self):

        return_string = ""

        return_string += "Milestone_Name:"+self.milestone_name+"\n"
        return_string += "Account_Name:" + self.account_name + "\n"
        return_string += "Min_Balance:" + self.min_balance + "\n"
        return_string += "Max_Balance:" + self.max_balance + "\n"

        return return_string