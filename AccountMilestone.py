import pandas as pd
import jsonpickle

class AccountMilestone:

    def __init__(self,Milestone_Name,Account_Name,Min_Balance,Max_Balance):
        self.milestone_name = Milestone_Name
        self.account_name = Account_Name
        self.min_balance = float(Min_Balance)
        self.max_balance = float(Max_Balance)

        #assert isinstance(Min_Balance, (int, float, complex)) and not isinstance(Min_Balance, bool)
        #assert isinstance(Max_Balance, (int, float, complex)) and not isinstance(Max_Balance, bool)
        assert Min_Balance <= Max_Balance


    #this is not shoqing as executed inthe coverage report but it is.... not sure whats going on there
    def __str__(self):

        return pd.DataFrame({
            'Milestone_Name': [self.milestone_name],
            'Account_Name': [self.account_name],
            'Min_Balance': [self.min_balance],
            'Max_Balance': [self.max_balance]
        }).to_string()


    def to_json(self):

        return jsonpickle.encode(self, indent=4)
