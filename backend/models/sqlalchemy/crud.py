from core import Account

def create_account(db_session, forecast_id, account_name, balance, min_balance, max_balance, account_type):
    new_account = Account(
        forecast_id=forecast_id,
        account_name=account_name,
        balance=balance,
        min_balance=min_balance,
        max_balance=max_balance,
        account_type=account_type,
    )
    db_session.add(new_account)
    db_session.commit()
    db_session.refresh(new_account)
    return new_account
