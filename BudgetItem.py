import pandas as pd, datetime

import jsonpickle

class BudgetItem:

    def __init__(self,
                 start_date_YYYYMMDD,
                 end_date_YYYYMMDD,
                 priority,
                 cadence,
                 amount,
                 memo,
                 deferrable=False,
                 partial_payment_allowed=False,
                 print_debug_messages=True,
                 raise_exceptions=True):
        """
        Creates a BudgetItem object. Input validation is performed.

        :param str start_date_YYYYMMDD: A string that indicates the start date with format %Y%m%d.
        :param str end_date_YYYYMMDD: A string that indicates the end date with format %Y%m%d.
        :param int priority: An integer >= 1 that indicates priority. See below for priority level meanings.
        :param str cadence: One of: 'once', 'daily', 'weekly', 'semiweekly', 'monthly', 'quarterly', 'yearly'
        :param float amount: A dollar value for the amount of the transaction.
        :param str memo: A label for the transaction.
        :param bool deferrable: True if the transaction can be delayed. False if it is time-sensitive.
        :param bool partial_payment_allowed: True if partial payments are allowed.
        :param bool print_debug_messages: If True, prints debug messages.
        :param bool raise_exceptions: If True, raises exceptions on errors.
        :raises ValueError: if input parameters are invalid.
        :rtype: BudgetItem

        Comment on Priority levels:
        This code executes transactions starting at priority 1 and moving up. Level 1 indicates non-negotiable, and the code will
        break if non-negotiable budget items cause account boundaries to be violated. Higher level priorities have no
        hard-coded meaning, but here is how they can be used:

        1. Non-negotiable (Income, Rent, Minimum credit card payments, Minimum loan payments, essential expenses)
        2. Non-deferrable items willing to incur interest
        3. Deferrable items willing to incur interest
        4. Additional payments on credit card debt
        5. Non-deferrable items not willing to incur interest
        6. Deferrable items not willing to incur interest
        7. Additional loan payments
        8. Savings
        9. Investments

        """

        self.print_debug_messages = print_debug_messages
        self.raise_exceptions = raise_exceptions

        errors = []

        # Validate and parse dates
        try:
            self.start_date = datetime.datetime.strptime(start_date_YYYYMMDD.replace('-', ''), '%Y%m%d').date()
        except ValueError:
            errors.append(f"Invalid start date format: '{start_date_YYYYMMDD}'. Expected format is YYYYMMDD.")

        try:
            self.end_date = datetime.datetime.strptime(end_date_YYYYMMDD.replace('-', ''), '%Y%m%d').date()
        except ValueError:
            errors.append(f"Invalid end date format: '{end_date_YYYYMMDD}'. Expected format is YYYYMMDD.")

        self.cadence = cadence

        if hasattr(self, 'start_date') and hasattr(self, 'end_date'):
            if self.start_date > self.end_date:
                errors.append(f"Start date ({self.start_date}) must be on or before end date ({self.end_date}).")
            if self.cadence.lower() == 'once' and self.start_date != self.end_date:
                errors.append("If cadence is 'once', then start_date must equal end_date.")

        # Validate priority
        try:
            self.priority = int(priority)
            if self.priority < 1:
                errors.append("Priority must be an integer greater than or equal to 1.")
        except ValueError:
            errors.append(f"Priority must be an integer. Value provided: '{priority}'.")

        # Validate cadence
        valid_cadences = ['once', 'daily', 'weekly', 'semiweekly', 'monthly', 'quarterly', 'yearly']
        self.cadence = str(cadence).lower()
        if self.cadence not in valid_cadences:
            errors.append(f"Cadence must be one of: {', '.join(valid_cadences)}. Value provided: '{cadence}'.")

        # Validate amount
        try:
            self.amount = float(amount)
        except ValueError:
            errors.append(f"Amount must be a number. Value provided: '{amount}'.")

        # Validate memo
        self.memo = str(memo)

        # Validate deferrable and partial_payment_allowed
        self.deferrable = bool(deferrable)
        self.partial_payment_allowed = bool(partial_payment_allowed)

        # Additional validations
        if self.memo.lower() == 'income' and self.priority != 1:
            errors.append("If memo is 'income', then priority must be 1.")

        if self.priority == 1 and self.deferrable:
            errors.append("If priority is 1, then deferrable must be False.")

        if self.priority == 1 and self.partial_payment_allowed:
            errors.append("If priority is 1, then partial_payment_allowed must be False.")

        # Handle errors
        if errors:
            error_message = '\n'.join(errors)
            if self.print_debug_messages:
                print("Errors in BudgetItem initialization:")
                print(error_message)
            if self.raise_exceptions:
                raise ValueError(error_message)

        # Set attributes if no errors occurred
        if not errors:
            self.start_date_YYYYMMDD = start_date_YYYYMMDD
            self.end_date_YYYYMMDD = end_date_YYYYMMDD
            # self.priority, self.cadence, self.amount, self.memo, self.deferrable, and self.partial_payment_allowed
            # are already set during validation

    def __str__(self):
        return pd.DataFrame({
            'Start_Date': [self.start_date_YYYYMMDD],
            'End_Date': [self.end_date_YYYYMMDD],
            'Priority': [self.priority],
            'Cadence': [self.cadence],
            'Amount': [self.amount],
            'Memo': [self.memo],
            'Deferrable': [self.deferrable],
            'Partial_Payment_Allowed': [self.partial_payment_allowed]
        }).to_string()

    def to_json(self):
        """
        Get a <string> representing the <BudgetItem> object.

        """
        return jsonpickle.encode(self, indent=4)
        # return pd.DataFrame({
        #     'Start_Date': [self.start_date_YYYYMMDD],
        #     'End_Date': [self.end_date_YYYYMMDD],
        #     'Priority': [self.priority],
        #     'Cadence': [self.cadence],
        #     'Amount': [self.amount],
        #     'Memo': [self.memo],
        #     'Deferrable': [self.deferrable],
        #     'Partial_Payment_Allowed': [self.partial_payment_allowed]
        # }).to_json(orient="records")

    # def fromJSON(self,JSON_string):
    #     pass

if __name__ == "__main__": import doctest ; doctest.testmod()


#before gpt: 11 passed, 222 deselected in 15.38s

#after gpt: