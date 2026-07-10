import pandas as pd
import jsonpickle


class AccountMilestone:
    """
    Represents a financial condition which is satisfied by account balance
    for one account staying within bounds from the milestone date to the
    end of the forecast.

    An AccountMilestone evaluates one account value against a user-defined 
    range of balances. When the condition becomes true, the milestone
    is considered achieved and may trigger changes to forecast behavior.

    AccountMilestones are intended to describe meaningful financial events
    rather than specific dates. Examples include paying off a loan,
    reaching a savings goal, accumulating a target investment balance, or
    reducing a credit card below a specified threshold.

    Responsibilities
    ----------------
    - Describe a financial milestone.
    - Evaluate whether the milestone has been achieved.
    - Expose milestone state to the forecasting engine.
    - Support serialization and deserialization.

    Examples
    --------
    - Credit card balance reaches $0.
    - Emergency fund exceeds $15,000.
    - Investment portfolio reaches $500,000.
    - Student loan principal falls below $10,000.

    Invariants
    ----------
    - A milestone represents a declarative condition rather than an action.
    - Evaluation depends only on the forecast state supplied to it.
    - Identical financial states always produce identical evaluation
      results.

    Notes
    -----
    AccountMilestone determines *when* a significant financial condition
    has been reached. The actions that occur after a milestone is achieved
    are defined elsewhere by the forecasting engine.
    """
    def __init__(self, 
                 Milestone_Name: str, 
                 Account_Name: str, 
                 Min_Balance: float, 
                 Max_Balance: float):
        """
        Initialize an AccountMilestone.

        Construct a milestone by defining the boundaries the balance for the 
        specified account must stay in. The supplied arguments completely 
        describe the milestone's evaluation criteria.

        Parameters
        ----------
        Milestone_Name : str

        Account_Name : str

        Min_Balance : float

        Max_Balance : float

        Returns
        -------
        None

        @interface-report: show
        """

        # TODO DEFER extract validator methods
        if Milestone_Name is None:
            raise ValueError("Milestone_Name in AccountMilestone() must not be None")
        self.milestone_name = Milestone_Name

        if Milestone_Name is None:
            raise ValueError("Account_Name in AccountMilestone() must not be None")
        self.account_name = Account_Name
        
        if Milestone_Name is None:
            raise ValueError("Account_Name in AccountMilestone() must not be None")
        
        if ';' in self.account_name:
            raise ValueError("Account_Name must not contain ';' in AccountMilestone() ")

        if Min_Balance > Max_Balance:
            raise ValueError(f"Min_Balance ({Min_Balance}) must must be <= Max_Balance ({Max_Balance}) in AccountMilestone() ")

        self.min_balance = float(Min_Balance)
        self.max_balance = float(Max_Balance)

    def __str__(self):
        """
        Returns human-readable representation of AccountMilestone.

        @interface-report: show
        """
        return pd.DataFrame(
            {
                "Milestone_Name": [self.milestone_name],
                "Account_Name": [self.account_name],
                "Min_Balance": [self.min_balance],
                "Max_Balance": [self.max_balance],
            }
        ).to_string()

    def to_json(self):
        """
        Returns json string.

        @interface-report: show
        """
        return jsonpickle.encode(self, indent=4)
