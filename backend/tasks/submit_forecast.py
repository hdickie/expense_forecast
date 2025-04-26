import datetime
from core.AccountSet import AccountSet
import logging
from os import getenv
import sys
from core.ExpenseForecast import ExpenseForecast
from core.LineItem import LineItem
from core.LineItemSet import LineItemSet
from core.DecisionRule import DecisionRule
from core.DecisionRuleSet import DecisionRuleSet
from core.MilestoneSet import MilestoneSet

from models.expenseforecast.params import ExpenseForecastParams

from datetime import datetime

from models.sqlalchemy.database import SessionLocal
from models.sqlalchemy.models import User
from models.sqlalchemy.models import Parameter
from models.sqlalchemy.models import AccountSet
from models.sqlalchemy.models import InvestmentAccount
from models.sqlalchemy.models import LoanAccount
from models.sqlalchemy.models import CreditAccount
from models.sqlalchemy.models import CheckingAccount
from models.sqlalchemy.models import LineItemSet
from models.sqlalchemy.models import LineItem
from models.sqlalchemy.models import DecisionRuleSet
from models.sqlalchemy.models import DecisionRule
from models.sqlalchemy.models import AccountMilestone
from models.sqlalchemy.models import MemoMilestone
from models.sqlalchemy.models import CompositeMilestone
from models.sqlalchemy.models import MilestoneSet
from models.sqlalchemy.models import ExpenseForecast
from models.sqlalchemy.models import ForecastStage

from models.account.params import CheckingAccountParams
from models.account.params import CreditCardAccountParams
from models.account.params import LoanAccountParams
from models.account.params import InvestmentAccountParams
from models.lineitem.params import LineItemParams
from models.decisionrule.params import DecisionRuleParams
from models.milestone.params import AccountMilestoneParams
from models.milestone.params import MemoMilestoneParams
from models.milestone.params import CompositeMilestoneParams
from models.expenseforecast.schemas import DraftSubmission

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert


# from celery import shared_task

from celery_main import celery_app

import logging
logger = logging.getLogger("tasks.submit_forecast")
logger.setLevel(logging.INFO)  # Or DEBUG if you want more noise

# Create console handler
handler = logging.StreamHandler(sys.stdout)  # Important! stdout not stderr
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)

# Avoid duplicate handlers if code reloads
if not logger.handlers:
    logger.addHandler(handler)














def validate_draft_submission(draft: DraftSubmission):
    logger.info('ENTER validate_draft_submission')
    errors = []

    # Business rule: Only one account can be marked as primary checking
    primary_count = sum(1 for a in draft.accounts if a.primary_checking)
    if primary_count > 1:
        errors.append({
            "section": "accounts",
            "field": "primary_checking",
            "message": "Only one account can be set as primary checking"
        })

    # Example: No account can have negative balance
    for i, account in enumerate(draft.accounts):
        if account.balance < 0:
            errors.append({
                "section": "accounts",
                "row": i,
                "field": "balance",
                "message": "Balance cannot be negative"
            })

    # Example: Line item amounts must be positive
    for i, item in enumerate(draft.line_items):
        if item.amount < 0:
            errors.append({
                "section": "line_items",
                "row": i,
                "field": "amount",
                "message": "Amount must be non-negative"
            })

    try:
        list_of_AccountParams = []
        list_of_LineItemParams = []
        list_of_DecisionRuleParams = []
        lists_of_MilestoneSetParams = []

        logger.info('BEGIN AccountSet business logic validation')
        for account_params in draft.accounts:
            logger.info(account_params)
            if account_params.account_type == 'checking':
                list_of_AccountParams.append(CheckingAccountParams(name=account_params.account_name,
                                                                   balance=account_params.balance,
                                                                   min_balance=account_params.min_balance,
                                                                   max_balance=account_params.max_balance,
                                                                   primary_checking_ind=account_params.primary_checking
                                                                   ))
            elif account_params.account_type == 'credit':
                list_of_AccountParams.append(CreditCardAccountParams(account_params))
            elif account_params.account_type == 'loan':
                list_of_AccountParams.append(LoanAccountParams(account_params))
            elif account_params.account_type == 'investment':
                list_of_AccountParams.append(InvestmentAccountParams(account_params))
            else:
                raise NotImplementedError
        A = AccountSet.from_params(list_of_AccountParams)

        logger.info('BEGIN LineItem business logic validation')
        for lineitem_params in draft.line_items:
            list_of_LineItemParams.append(LineItemParams(lineitem_params))
        if len(list_of_LineItemParams) > 0:
            L = LineItemSet.from_params(list_of_LineItemParams)
        else:
            L = LineItemSet([])

        logger.info('BEGIN DecisionRule business logic validation')
        for decisionrule_params in draft.decision_rules:
            list_of_DecisionRuleParams.append(DecisionRuleParams(decisionrule_params))
        if len(list_of_DecisionRuleParams) > 0:
            D = DecisionRuleSet.from_params(list_of_DecisionRuleParams)
        else:
            D = DecisionRuleSet([])
        start_date = datetime.strptime(draft.parameters[0].start_date[0:10],'%Y-%m-%d') #e.g. 2025-04-24T00:00:00.000Z
        end_date = datetime.strptime(draft.parameters[0].end_date[0:10],'%Y-%m-%d') #e.g. 2025-05-01T00:00:00.000Z

        logger.info('BEGIN MilestoneSet business logic validation')
        #todo
        # for milestoneset_params in draft.milestones:
        #     # AccountMilestoneParams, 
        #     # todo MemoMilestoneParams, CompositeMilestoneParams
        #     # if milestoneset_params.mileston
        #     # new_milestone_params = 
        #     lists_of_MilestoneSetParams.append(None)
        if len(lists_of_MilestoneSetParams) > 0:
            M = MilestoneSet.from_params(lists_of_MilestoneSetParams)
        else:
            M = MilestoneSet([])
        approximate_flag = draft.parameters[0].approximate
        forecast_name = draft.parameters[0].forecast_name

        logger.info('BEGIN ExpenseForecast business logic validation')
        args = ExpenseForecastParams(account_set=A,
                                     lineitem_set=L,
                                     decisionrule_set=D,
                                     start_date=start_date,
                                     end_date=end_date,
                                     milestone_set=M,
                                     approximate_flag=approximate_flag,
                                     forecast_name=forecast_name)
        E = ExpenseForecast.from_params(args)
        logger.info('VALIDATION COMPLETE. FORECAST PREPARED TO RUN')
        logger.info('unique_id:'+str(E.unique_id))
    except Exception as e:
        errors.append(e.args)

    if errors:
        rv = {
            "status": "rejected",
            "errors": errors
        }
        logger.error(rv)
        logger.info('EXIT validate_draft_submission (FAIL)')
        return rv
    logger.info('EXIT validate_draft_submission (SUCCESS)')

@celery_app.task
def submit_draft(draft_dict: dict):
    logger.info('ENTER submit_draft')
    # logger.info(draft_dict)

    logger.info('Parameters')
    logger.info(draft_dict.parameters)
    logger.info('Accounts')
    logger.info(draft_dict.accounts)
    logger.info('Line Items')
    logger.info(draft_dict.line_items)
    logger.info('Decision Rules')
    logger.info(draft_dict.decision_rules)
    logger.info('Milestones')
    logger.info(draft_dict.milestones)

    test_user_email = 'hume.dickie@live.com'
    

    # Step 1: Create DB session
    db = SessionLocal()
    # todo assert user exists

    select_stmt = select(User.id).where(
                User.email == test_user_email,
            )
    result = db.execute(select_stmt)
    fief_uuid = result.scalar_one()

    # insert parameters
    new_parameter_row_ids = []
    for parameter_row in draft_dict.parameters:
        # new_parameter = Parameter(
        #     user_ud = fief_uuid,
        #     start_date=parameter_row.start_date,
        #     end_date=parameter_row.end_date,
        #     forecast_name=parameter_row.forecast_name,
        #     approximate=parameter_row.approximate,
        # )
        # db.add(new_parameter)
        stmt = insert(Parameter).values(
            user_id=fief_uuid,
            start_date=parameter_row.start_date,
            end_date=parameter_row.end_date,
            forecast_name=parameter_row.forecast_name,
            approximate=parameter_row.approximate,
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=['user_id', 'start_date', 'end_date', 'forecast_name', 'approximate'])
        stmt = stmt.returning(Parameter.id)
        logger.info(stmt)
        result = db.execute(stmt)
        new_id = result.scalar() 
        if new_id is None: #the row already existed, we have to select for it
            select_stmt = select(Parameter.id).where(
                Parameter.user_id == fief_uuid,
                Parameter.start_date == parameter_row.start_date,
                Parameter.end_date == parameter_row.end_date,
                Parameter.forecast_name == parameter_row.forecast_name,
                Parameter.approximate == parameter_row.approximate,
            )
            result = db.execute(select_stmt)
            new_id = result.scalar_one()
        new_parameter_row_ids.append(new_id)

    new_account_row_ids = []
    for account_row in draft_dict.accounts:
        if account_row.account_type == 'checking':
            stmt = insert(CheckingAccount).values(
                user_id=fief_uuid,
                account_name=account_row.account_name,
                balance=account_row.balance,
                min_balance=account_row.min_balance,
                max_balance=account_row.max_balance,
                primary_checking=account_row.primary_checking,
            )
            stmt = stmt.on_conflict_do_nothing(index_elements=['user_id', 'account_name', 'balance','min_balance',
                                                               'max_balance','primary_checking'])
            stmt = stmt.returning(CheckingAccount.id)
            logger.info(stmt)
            result = db.execute(stmt)
            new_id = result.scalar() 
            if new_id is None: 
                select_stmt = select(CheckingAccount.id).where(
                    CheckingAccount.user_id == fief_uuid,
                    CheckingAccount.account_name == account_row.account_name,
                    CheckingAccount.balance == account_row.balance,
                    CheckingAccount.min_balance == account_row.min_balance,
                    CheckingAccount.max_balance == account_row.max_balance,
                    CheckingAccount.primary_checking == account_row.primary_checking
                )
                result = db.execute(select_stmt)
                new_id = result.scalar_one()
        elif account_row.account_type == 'credit':
            stmt = insert(CreditAccount).values(
                account_name=account_row.account_name,
                balance=account_row.balance,
                min_balance=account_row.min_balance,
                max_balance=account_row.max_balance,
                billing_start_date=account_row.billing_start_date,
                apr=account_row.apr,
                minimum_payment=account_row.minimum_payment,
                prev_cycle_balance=account_row.prev_cycle_balance
            )
            stmt = stmt.on_conflict_do_nothing(index_elements=['user_id', 'account_name', 'balance','min_balance',
                                                               'max_balance', 'billing_start_date', 'apr','minimum_payment',
                                                               'prev_cycle_balance'
                                                               ])
            stmt = stmt.returning(CreditAccount.id)
            result = db.execute(stmt)
            logger.info(stmt)
            new_id = result.scalar() 
            if new_id is None: 
                select_stmt = select(CreditAccount.id).where(
                    CreditAccount.user_id == fief_uuid,
                    CreditAccount.account_name == account_row.account_name,
                    CreditAccount.balance == account_row.balance,
                    CreditAccount.min_balance == account_row.min_balance,
                    CreditAccount.max_balance == account_row.max_balance,
                    CreditAccount.billing_start_date == account_row.billing_start_date,
                    CreditAccount.apr == account_row.apr,
                    CreditAccount.minimum_payment == account_row.minimum_payment,
                    CreditAccount.prev_cycle_balance == account_row.prev_cycle_balance
                )
                result = db.execute(select_stmt)
                new_id = result.scalar_one()
        elif account_row.account_type == 'loan':
            stmt = insert(LoanAccount).values(
                account_name=account_row.account_name,
                balance=account_row.balance,
                min_balance=account_row.min_balance,
                max_balance=account_row.max_balance,
                interest_type=account_row.interest_type,
                interest_cadence=account_row.interest_cadence,
                billing_start_date=account_row.billing_start_date,
                apr=account_row.apr,
                minimum_payment=account_row.minimum_payment,
                prev_cycle_balance=account_row.prev_cycle_balance
            )
            stmt = stmt.on_conflict_do_nothing(index_elements=['user_id', 'account_name', 'balance','min_balance',
                                                               'max_balance', 'interest_type', 'interest_cadence','billing_start_date',
                                                               'apr', 'minimum_payment', 'prev_cycle_balance'
                                                               ])
            stmt = stmt.returning(LoanAccount.id)
            result = db.execute(stmt)
            logger.info(stmt)
            new_id = result.scalar() 
            if new_id is None: 
                select_stmt = select(LoanAccount.id).where(
                    LoanAccount.user_id == fief_uuid,
                    LoanAccount.account_name == account_row.account_name,
                    LoanAccount.balance == account_row.balance,
                    LoanAccount.min_balance == account_row.min_balance,
                    LoanAccount.max_balance == account_row.max_balance,
                    LoanAccount.interest_type == account_row.interest_type,
                    LoanAccount.interest_cadence == account_row.interest_cadence,
                    LoanAccount.billing_start_date == account_row.billing_start_date,
                    LoanAccount.apr == account_row.apr,
                    LoanAccount.minimum_payment == account_row.minimum_payment,
                    LoanAccount.prev_cycle_balance == account_row.prev_cycle_balance
                )
                result = db.execute(select_stmt)
                new_id = result.scalar_one()   
        elif account_row.account_type == 'investment':
            stmt = insert(InvestmentAccount).values(
                account_name=account_row.account_name,
                balance=account_row.balance,
                min_balance=account_row.min_balance,
                max_balance=account_row.max_balance,
                interest_type=account_row.interest_type,
                interest_cadence=account_row.interest_cadence,
                billing_start_date=account_row.billing_start_date,
                apr=account_row.apr,
                minimum_payment=account_row.minimum_payment,
                prev_cycle_balance=account_row.prev_cycle_balance
            )
            stmt = stmt.on_conflict_do_nothing(index_elements=['user_id', 'account_name', 'balance','min_balance',
                                                               'max_balance', 'interest_type', 'interest_cadence','billing_start_date',
                                                               'apr', 'minimum_payment', 'prev_cycle_balance'
                                                               ])
            stmt = stmt.returning(InvestmentAccount.id)
            logger.info(stmt)
            result = db.execute(stmt)
            new_id = result.scalar() 
            if new_id is None: 
                select_stmt = select(InvestmentAccount.id).where(
                    InvestmentAccount.user_id == fief_uuid,
                    InvestmentAccount.account_name == account_row.account_name,
                    InvestmentAccount.balance == account_row.balance,
                    InvestmentAccount.min_balance == account_row.min_balance,
                    InvestmentAccount.max_balance == account_row.max_balance,
                    InvestmentAccount.interest_type == account_row.interest_type,
                    InvestmentAccount.interest_cadence == account_row.interest_cadence,
                    InvestmentAccount.billing_start_date == account_row.billing_start_date,
                    InvestmentAccount.apr == account_row.apr,
                    InvestmentAccount.minimum_payment == account_row.minimum_payment,
                    InvestmentAccount.prev_cycle_balance == account_row.prev_cycle_balance
                )
                result = db.execute(select_stmt)
                new_id = result.scalar_one()
        
        new_account_row_ids.append(new_id)
        
    # insert line items
    new_line_item_row_ids = []
    for line_item_row in draft_dict.line_items:

        stmt = insert(LineItem).values(
            user_id=fief_uuid,
            name=line_item_row.name,
            amount=line_item_row.amount,
            priority=line_item_row.priority,
            cadence=line_item_row.cadence,
            start_date=line_item_row.start_date,
            end_date=line_item_row.end_date,
            deferrable=line_item_row.deferrable,
            partial_payment_allowed=line_item_row.partial_payment_allowed
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=['user_id', 'name', 'amount', 'priority', 'cadence',
                                                           'start_date','end_date','deferrable','partial_payment_allowed'])
        stmt = stmt.returning(LineItem.id)
        logger.info(stmt)
        result = db.execute(stmt)
        new_id = result.scalar() 
        if new_id is None: #the row already existed, we have to select for it
            select_stmt = select(LineItem.id).where(
                LineItem.user_id == fief_uuid,
                LineItem.name == line_item_row.name,
                LineItem.amount == line_item_row.amount,
                LineItem.priority == line_item_row.priority,
                LineItem.cadence == line_item_row.cadence,
                LineItem.start_date == line_item_row.start_date,
                LineItem.end_date == line_item_row.end_date,
                LineItem.deferrable == line_item_row.deferrable,
                LineItem.partial_payment_allowed == line_item_row.partial_payment_allowed
            )
            result = db.execute(select_stmt)
            new_id = result.scalar_one()

        new_line_item_row_ids.append(new_id)
    
    # insert decision rules
    new_decision_rule_row_ids = []
    for decision_rule_row in draft_dict.decision_rules:

        stmt = insert(DecisionRule).values(
            user_id=fief_uuid,
            memo_regex=line_item_row.memo_regex,
            priority=line_item_row.priority,
            account_from=line_item_row.account_from,
            account_to=line_item_row.account_to
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=['user_id', 'memo_regex', 'priority', 'account_from', 'account_to'])
        stmt = stmt.returning(DecisionRule.id)
        logger.info(stmt)
        result = db.execute(stmt)
        new_id = result.scalar() 
        if new_id is None: #the row already existed, we have to select for it
            select_stmt = select(DecisionRule.id).where(
                DecisionRule.user_id == fief_uuid,
                DecisionRule.memo_regex == line_item_row.memo_regex,
                DecisionRule.priority == line_item_row.priority,
                DecisionRule.account_from == line_item_row.account_from,
                DecisionRule.account_to == line_item_row.account_to,
            )
            result = db.execute(select_stmt)
            new_id = result.scalar_one()

        new_decision_rule_row_ids.append(new_id)
    
    # insert account milestones
    new_account_milestone_row_ids = []
    for account_milestone_row in draft_dict.account_milestones:

        stmt = insert(AccountMilestone).values(
            user_id=fief_uuid,
            # memo_regex=line_item_row.memo_regex,
            # priority=line_item_row.priority,
            # account_from=line_item_row.account_from,
            # account_to=line_item_row.account_to
        )
        # stmt = stmt.on_conflict_do_nothing(index_elements=['user_id', 'memo_regex', 'priority', 'account_from', 'account_to'])
        stmt = stmt.returning(AccountMilestone.id)
        logger.info(stmt)
        result = db.execute(stmt)
        new_id = result.scalar() 
        if new_id is None: #the row already existed, we have to select for it
            select_stmt = select(AccountMilestone.id).where(
                AccountMilestone.user_id == fief_uuid,
                # DecisionRule.memo_regex == line_item_row.memo_regex,
                # DecisionRule.priority == line_item_row.priority,
                # DecisionRule.account_from == line_item_row.account_from,
                # DecisionRule.account_to == line_item_row.account_to,
            )
            result = db.execute(select_stmt)
            new_id = result.scalar_one()

        new_account_milestone_row_ids.append(new_id)

    # insert memo milestones
    new_memo_milestone_row_ids = []
    for memo_milestone_row in draft_dict.memo_milestones:

        stmt = insert(MemoMilestone).values(
            user_id=fief_uuid,
            # memo_regex=line_item_row.memo_regex,
            # priority=line_item_row.priority,
            # account_from=line_item_row.account_from,
            # account_to=line_item_row.account_to
        )
        # stmt = stmt.on_conflict_do_nothing(index_elements=['user_id', 'memo_regex', 'priority', 'account_from', 'account_to'])
        stmt = stmt.returning(MemoMilestone.id)
        logger.info(stmt)
        result = db.execute(stmt)
        new_id = result.scalar() 
        if new_id is None: #the row already existed, we have to select for it
            select_stmt = select(MemoMilestone.id).where(
                MemoMilestone.user_id == fief_uuid,
                # DecisionRule.memo_regex == line_item_row.memo_regex,
                # DecisionRule.priority == line_item_row.priority,
                # DecisionRule.account_from == line_item_row.account_from,
                # DecisionRule.account_to == line_item_row.account_to,
            )
            result = db.execute(select_stmt)
            new_id = result.scalar_one()

        new_account_milestone_row_ids.append(new_id)

    # insert composite milestones
    new_composite_milestone_row_ids = []
    for memo_composite_row in draft_dict.composite_milestones:

        stmt = insert(CompositeMilestone).values(
            user_id=fief_uuid,
            # memo_regex=line_item_row.memo_regex,
            # priority=line_item_row.priority,
            # account_from=line_item_row.account_from,
            # account_to=line_item_row.account_to
        )
        # stmt = stmt.on_conflict_do_nothing(index_elements=['user_id', 'memo_regex', 'priority', 'account_from', 'account_to'])
        stmt = stmt.returning(CompositeMilestone.id)
        logger.info(stmt)
        result = db.execute(stmt)
        new_id = result.scalar() 
        if new_id is None: #the row already existed, we have to select for it
            select_stmt = select(CompositeMilestone.id).where(
                CompositeMilestone.user_id == fief_uuid,
                # DecisionRule.memo_regex == line_item_row.memo_regex,
                # DecisionRule.priority == line_item_row.priority,
                # DecisionRule.account_from == line_item_row.account_from,
                # DecisionRule.account_to == line_item_row.account_to,
            )
            result = db.execute(select_stmt)
            new_id = result.scalar_one()

        new_composite_milestone_row_ids.append(new_id)
    
    # insert account set rows
    new_account_set_row_ids = []
    for new_account_row_id in new_account_row_ids:
        stmt = insert(AccountSet).values(
            user_id=fief_uuid,
            account_id=new_account_row_id,
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=['user_id', 'account_id'])
        stmt = stmt.returning(AccountSet.id)
        logger.info(stmt)
        result = db.execute(stmt)
        new_id = result.scalar() 
        if new_id is None: #the row already existed, we have to select for it
            select_stmt = select(AccountSet.id).where(
                AccountSet.user_id == fief_uuid,
                AccountSet.account_id == new_account_row_id
            )
            result = db.execute(select_stmt)
            new_id = result.scalar_one()

        new_account_set_row_ids.append(new_id)
    
    # (TODO cross-product for each etc etc etc)
    new_line_item_set_row_ids = []
    for new_line_item_row_id in new_line_item_row_ids:

        stmt = insert(LineItem).values(
            user_id=fief_uuid,
            # memo_regex=line_item_row.memo_regex,
            # priority=line_item_row.priority,
            # account_from=line_item_row.account_from,
            # account_to=line_item_row.account_to
        )
        # stmt = stmt.on_conflict_do_nothing(index_elements=['user_id', 'memo_regex', 'priority', 'account_from', 'account_to'])
        stmt = stmt.returning(LineItem.id)
        logger.info(stmt)
        result = db.execute(stmt)
        new_id = result.scalar() 
        if new_id is None: #the row already existed, we have to select for it
            select_stmt = select(LineItem.id).where(
                LineItem.user_id == fief_uuid,
                # DecisionRule.memo_regex == line_item_row.memo_regex,
                # DecisionRule.priority == line_item_row.priority,
                # DecisionRule.account_from == line_item_row.account_from,
                # DecisionRule.account_to == line_item_row.account_to,
            )
            result = db.execute(select_stmt)
            new_id = result.scalar_one()

        new_line_item_set_row_ids.append(new_id)

    # insert decision rule set records #new_decision_rule_row_ids
    new_decision_rule_set_row_ids = []
    for new_decision_rule_row_id in new_decision_rule_row_ids:

        stmt = insert(DecisionRule).values(
            user_id=fief_uuid,
            decision_rule_id=new_decision_rule_row_id,
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=['user_id', 'decision_rule_id'])
        stmt = stmt.returning(LineItem.id)
        logger.info(stmt)
        result = db.execute(stmt)
        new_id = result.scalar() 
        if new_id is None: #the row already existed, we have to select for it
            select_stmt = select(LineItem.id).where(
                LineItem.user_id == fief_uuid,
                # DecisionRule.memo_regex == line_item_row.memo_regex,
                # DecisionRule.priority == line_item_row.priority,
                # DecisionRule.account_from == line_item_row.account_from,
                # DecisionRule.account_to == line_item_row.account_to,
            )
            result = db.execute(select_stmt)
            new_id = result.scalar_one()

        new_decision_rule_set_row_ids.append(new_id)

    # insert milestone set records

    # insert expense forecast records
    # insert expense forecast set records


    ### insert to forecast_stage
    # start_date = Column(Date, nullable=False)
    # end_date = Column(Date, nullable=False)
    # forecast_name = Column(String, nullable=False)
    # approximate = Column(Boolean, default=False)
    # status = Column(String, nullable=False)
    # progress = Column(String, nullable=False)
    # start_ts = Column(DateTime, nullable=False)
    # elapsed = Column(Float, nullable=False)

    

    # Step 2: Create ForecastStage row
    new_stage = ForecastStage(
        user_id=fief_uuid,  # fief id for hume.dickie@live.com
        start_date=datetime(2025, 4, 25).date(),   # just the date part
        end_date=datetime(2025, 5, 1).date(),      # another date
        forecast_name="April 2025 Forecast",
        approximate=False,
        status="in_progress",
        progress="0%",  # or whatever you want to track here
        start_ts=datetime.now(),  # full timestamp, now
        elapsed=0.0,  # just starting, so 0 seconds elapsed
    )

    # Step 3: Add and commit
    db.add(new_stage)

    #only commit at the end so ALL queries get rolled back if something fails
    db.commit()
    # db.refresh(new_stage) #this is not needed at this specific moment
    print(f"Inserted ForecastStage with ID: {new_stage.id}")
    db.close()

    logger.info('EXIT submit_draft')
    return "Placeholder (success)"

@celery_app.task
def validate_and_submit_draft_task(draft_dict: dict):
    draft = DraftSubmission(**draft_dict)

    try:
        validate_draft_submission(draft)
        submit_draft(draft)
        return "Draft submitted successfully!"
    except Exception as e:
        raise e