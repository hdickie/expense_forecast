import datetime
import pandas as pd
import jsonpickle


class Account:

    @staticmethod
    def _validate_balances(min_balance, balance, max_balance):
        if min_balance > balance:
            raise ValueError(
                f"Account.balance ({balance}) cannot be less than min_balance ({min_balance})"
            )

        if max_balance < balance:
            raise ValueError(
                f"Account.balance ({balance}) cannot be greater than max_balance ({max_balance})"
            )

        if max_balance < min_balance:
            raise ValueError(
                f"Account.max_balance ({max_balance}) cannot be less than min_balance ({min_balance})"
            )

    @staticmethod
    def _validate_account_type(account_type):
        valid_account_types = [
            "checking",
            "credit prev stmt bal",
            "credit curr stmt bal",
            "savings",
            "principal balance",
            "interest",
            "credit billing cycle payment bal",
            "loan billing cycle payment bal",
            "loan end of prev cycle bal",
            "credit end of prev cycle bal",
        ]
        assert account_type == account_type.lower()
        if account_type not in valid_account_types:
            raise ValueError(
                f"Invalid account_type: {account_type}. Must be one of {', '.join(valid_account_types)}"
            )

    @staticmethod
    def _validate_account_name(account_type, account_name):
        account_types_that_require_colon_in_name = [
            "credit curr stmt bal",
            "credit prev stmt bal",
            "principal balance",
            "credit billing cycle payment bal",
            "loan billing cycle payment bal",
            "loan prev end of cycle balance",
            "credit prev end of cycle balance",
        ]
        if account_type in account_types_that_require_colon_in_name:
            if ":" not in account_name:
                raise ValueError(
                    "Accounts of these types: [" + ', '.join(
                        account_types_that_require_colon_in_name) + "] require colon char in the account name. Got: "+account_name
                )

    @staticmethod
    def _validate_apr(account_type, apr):
        account_types_that_require_apr = [
            "credit prev stmt bal",
            "principal balance",
            "savings",
        ]
        if account_type in account_types_that_require_apr and apr is not None:
            assert apr >= 0
        elif account_type in account_types_that_require_apr and apr is None:
            raise ValueError(
                f"Account.apr is required for account_type '{account_type}'"
            )
        elif account_type not in account_types_that_require_apr and apr is not None:
            raise ValueError(
                f"Account.apr should be None for account_type '{account_type}'"
            )

    @staticmethod
    def _validate_interest_cadence(account_type, interest_cadence):
        account_types_that_require_interest_cadence = [
            "credit prev stmt bal",
            "principal balance",
            "savings",
        ]
        if account_type in account_types_that_require_interest_cadence and interest_cadence not in ['daily','monthly']: #todo more strict
            raise ValueError(
                f"Account.interest_cadence should be daily or monthly for account_type '{account_type}'"
            )
        elif account_type not in account_types_that_require_interest_cadence and interest_cadence is not None:
            raise ValueError(
                f"Account.interest_cadence should be None for account_type '{account_type}'"
            )

    @staticmethod
    def _validate_interest_type(account_type, interest_type):
        if account_type in ["principal balance", "savings"] and interest_type is None:
            raise ValueError(
                f"Account.interest_type is required for account_type '{account_type}'"
            )
        elif account_type in ["principal balance", "savings"] and interest_type not in ["simple", "compound"]:
            raise ValueError(
                f"Account.interest_type should be simple or compound for account_type '{account_type}'"
            )
        elif account_type not in ["principal balance", "savings"] and interest_type is not None:
            raise ValueError(
                f"Account.interest_type should be None for account_type '{account_type}'"
            )

    @staticmethod
    def _validate_billing_start_date(account_type, billing_start_date):
        account_types_that_require_billing_start_date = [
            "credit billing cycle payment bal",
            "loan billing cycle payment bal",
            "credit prev stmt bal",
            "principal balance",
            "savings",
            "loan end of prev cycle bal",
            "credit end of prev cycle bal",
        ]

        if account_type in account_types_that_require_billing_start_date and billing_start_date is not None:
            assert isinstance(billing_start_date, datetime.datetime)
        elif account_type in account_types_that_require_billing_start_date and billing_start_date is None:
            raise ValueError(
                f"Account.billing_start_date is required for account_type '{account_type}'"
            )
        elif account_type not in account_types_that_require_billing_start_date and billing_start_date is not None:
            raise ValueError(
                f"Account.billing_start_date should be None for account_type '{account_type}'"
            )

    @staticmethod
    def _validate_minimum_payment(account_type, minimum_payment):
        account_types_that_require_minimum_payment = ["credit prev stmt bal", "principal balance"]
        if account_type in account_types_that_require_minimum_payment and minimum_payment is not None:
            assert minimum_payment >= 0
        elif account_type in account_types_that_require_minimum_payment and minimum_payment is None:
            raise ValueError(
                f"Account.minimum_payment is required for account_type '{account_type}'"
            )
        elif account_type not in account_types_that_require_minimum_payment and minimum_payment is not None:
            raise ValueError(
                f"Account.minimum_payment should be None for account_type '{account_type}'"
            )

    @staticmethod
    def _validate_primary_checking_ind(account_type, primary_checking_ind):
        if account_type != 'checking' and primary_checking_ind is not None:
            raise ValueError(
                f"Account.primary_checking_ind should be None for account_type '{account_type}'"
            )
        elif account_type == 'checking' and primary_checking_ind is None:
            raise TypeError(
                f"Account.primary_checking_ind must be a bool Value was: {primary_checking_ind}"
            )
        elif account_type == 'checking' and primary_checking_ind is not None:
            assert isinstance(primary_checking_ind,bool)

    def __init__(self, name, balance, min_balance, max_balance, account_type, **kwargs):
        # checking, credit, principal balance, interest, investment
        # parameters are expected to be correctly typed. wont cast but will error

        allowed_kwargs = ['billing_start_date', 'interest_type', 'apr', 'interest_cadence', 'minimum_payment', 'primary_checking_ind']
        for key in kwargs:
            if key not in allowed_kwargs:
                raise TypeError(f"Unexpected keyword argument '{key}'")

        self.name = name
        self._validate_account_name(account_type, self.name)

        self.balance = balance
        self.min_balance = min_balance
        self.max_balance = max_balance
        self._validate_balances(self.min_balance, self.balance, self.max_balance)

        self.account_type = account_type
        self._validate_account_type(self.account_type)

        self.billing_start_date = kwargs.get('billing_start_date',None)
        self._validate_billing_start_date(self.account_type, self.billing_start_date)

        self.interest_type = kwargs.get('interest_type', None)
        self._validate_interest_type(self.account_type, self.interest_type)

        self.apr = kwargs.get('apr', None)
        self._validate_apr(self.account_type,self.apr)

        self.interest_cadence = kwargs.get('interest_cadence', None)
        self._validate_interest_cadence(self.account_type,self.interest_cadence)

        self.minimum_payment = kwargs.get('minimum_payment', None)
        self._validate_minimum_payment(self.account_type,self.minimum_payment)

        self.primary_checking_ind = kwargs.get('primary_checking_ind', None)
        self._validate_primary_checking_ind(self.account_type,self.primary_checking_ind)

    def to_json(self):
        """
        :rtype: string
        """
        return jsonpickle.encode(self, indent=4)

    def __str__(self):
        bsd = [ bsd.strftime('%Y%m%d') for bsd in [self.billing_start_date] if self.billing_start_date ]

        return pd.DataFrame(
            {
                "Name": [self.name],
                "Balance": [self.balance],
                "Min_Balance": [self.min_balance],
                "Max_Balance": [self.max_balance],
                "Account_Type": [self.account_type],
                "Billing_Start_Date": [bsd],
                "Interest_Type": [self.interest_type],
                "APR": [self.apr],
                "Interest_Cadence": [self.interest_cadence],
                "Minimum_Payment": [self.minimum_payment],
                "Primary_Checking_Ind": [self.primary_checking_ind],
            }
        ).to_string()


# written in one line so that test coverage can reach 100%
if __name__ == "__main__":
    import doctest

    doctest.testmod()
