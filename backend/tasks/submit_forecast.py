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
import traceback
from models.expenseforecast.params import ExpenseForecastParams

from datetime import datetime

from models.sqlalchemy.database import SessionLocal
from models.sqlalchemy.models import UserModel
from models.sqlalchemy.models import ParameterModel
from models.sqlalchemy.models import AccountSetModel
from models.sqlalchemy.models import InvestmentAccountModel
from models.sqlalchemy.models import LoanAccountModel
from models.sqlalchemy.models import CreditAccountModel
from models.sqlalchemy.models import CheckingAccountModel
from models.sqlalchemy.models import LineItemSetModel
from models.sqlalchemy.models import LineItemModel
from models.sqlalchemy.models import DecisionRuleSetModel
from models.sqlalchemy.models import DecisionRuleModel
from models.sqlalchemy.models import AccountMilestoneModel
from models.sqlalchemy.models import MemoMilestoneModel
from models.sqlalchemy.models import CompositeMilestoneModel
from models.sqlalchemy.models import MilestoneSetModel
from models.sqlalchemy.models import ExpenseForecastModel
from models.sqlalchemy.models import ForecastStatusHistoryModel

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

import pandas as pd
from sqlalchemy import Table, Column, Float, String, Date, MetaData

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.dialects.postgresql import dialect

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

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
    stable_ids = {}
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
        # logger.info('dir(AccountSet)')
        # logger.info(dir(AccountSet))
        A = AccountSet.from_params(list_of_AccountParams)

        logger.info('BEGIN LineItem business logic validation')
        for lineitem_params in draft.line_items:
            list_of_LineItemParams.append(LineItemParams(lineitem_params))
        if len(list_of_LineItemParams) > 0:
            L = LineItemSet.from_params(list_of_LineItemParams)
        else:
            L = LineItemSet([])

        logger.info('BEGIN DecisionRule business logic validation')
        logger.info('draft.decision_rules:')
        logger.info(draft.decision_rules)
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
        stable_ids['forecast_stable_id'] = E.unique_id
        logger.info(f'(TRUTH) SET forecast_stable_id = {E.unique_id}')
        stable_ids['account_set'] = A.get_stable_id()
        logger.info(f'(TRUTH) SET account_set stable_id = {A.get_stable_id()}')
        stable_ids['line_item_set'] = L.get_stable_id()
        logger.info(f'(TRUTH) SET lineitem_set stable_id = {L.get_stable_id()}')
        stable_ids['decision_rule_set'] = D.get_stable_id()
        logger.info(f'(TRUTH) SET decisionrule_set stable_id = {D.get_stable_id()}')
        stable_ids['milestone_set'] = M.get_stable_id()
        logger.info(f'(TRUTH) SET milestone_set stable_id = {M.get_stable_id()}')

        stable_ids['accounts'] = {}
        stable_ids['line_items'] = {}
        stable_ids['decision_rules'] = {}
        stable_ids['milestones'] = {}

        for index, row in A.getAccounts().iterrows():
            stable_ids['accounts'][row.Name] = row.Stable_Id
            logger.info(f'(TRUTH) SET account stable_id {row.Name} = {row.Stable_Id}')

        ### todo this should be a f(x) of the objects
        # #map stable ids to row ids
        # for index, row in A.getAccounts().iterrows():
        #     pass

        # for index, row in L.getLineItems().iterrows():
        #     pass

        # for index, row in A.getDecisionRules().iterrows():
        #     pass

        # for index, row in A.getAccountMilestonesDF().iterrows():
        #     pass

        # for index, row in A.getMemoMilestonesDF().iterrows():
        #     pass

        # for index, row in A.getCompositeMilestonesDF().iterrows():
        #     pass

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

    return {
        "status": "accepted",
        "stable_ids": stable_ids
    }

@celery_app.task
def submit_draft(draft_dict: dict, stable_ids: dict):
    logger.info('ENTER submit_draft')
    logger.info('draft_dict:')
    logger.info(draft_dict)
    logger.info('stable_ids:')
    logger.info(stable_ids)

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

    select_stmt = select(UserModel.id).where(
                UserModel.email == test_user_email,
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

        parameter_stable_id = parameter_row.start_date+parameter_row.end_date+str(parameter_row.approximate)

        stmt = insert(ParameterModel).values(
            user_id=fief_uuid,
            stable_parameter_id=parameter_stable_id,
            start_date=parameter_row.start_date,
            end_date=parameter_row.end_date,
            forecast_name=parameter_row.forecast_name,
            approximate=parameter_row.approximate,
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=['user_id', 'stable_parameter_id'])
        stmt = stmt.returning(ParameterModel.id)
        logger.info(stmt)
        result = db.execute(stmt)
        new_id = result.scalar() 
        if new_id is None: #the row already existed, we have to select for it
            select_stmt = select(ParameterModel.id).where(
                ParameterModel.user_id == fief_uuid,
                ParameterModel.stable_parameter_id == parameter_stable_id,
                ParameterModel.start_date == parameter_row.start_date,
                ParameterModel.end_date == parameter_row.end_date,
                ParameterModel.forecast_name == parameter_row.forecast_name,
                ParameterModel.approximate == parameter_row.approximate,
            )
            result = db.execute(select_stmt)
            new_id = result.scalar_one()
        new_parameter_row_ids.append(new_id)

    new_account_row_ids = []
    account_row_id_to_stable_id_map = {}
    account_row_id_to_account_type_map = {}
    for account_row in draft_dict.accounts:
        if account_row.account_type == 'checking':
            account_row_id_to_account_type_map[new_id] = 'checking'
            stmt = insert(CheckingAccountModel).values(
                user_id=fief_uuid,
                stable_account_id=stable_ids['accounts'][account_row.account_name],
                account_name=account_row.account_name,
                balance=account_row.balance,
                min_balance=account_row.min_balance,
                max_balance=account_row.max_balance,
                primary_checking=account_row.primary_checking,
            )
            stmt = stmt.on_conflict_do_nothing(index_elements=['user_id', 'stable_account_id'])
            stmt = stmt.returning(CheckingAccountModel.id)
            logger.info(stmt)
            result = db.execute(stmt)
            new_id = result.scalar() 
            if new_id is None: 
                select_stmt = select(CheckingAccountModel.id).where(
                    CheckingAccountModel.user_id == fief_uuid,
                    CheckingAccountModel.stable_account_id == stable_ids['accounts'][account_row.account_name],
                    CheckingAccountModel.account_name == account_row.account_name,
                    CheckingAccountModel.balance == account_row.balance,
                    CheckingAccountModel.min_balance == account_row.min_balance,
                    CheckingAccountModel.max_balance == account_row.max_balance,
                    CheckingAccountModel.primary_checking == account_row.primary_checking
                )
                result = db.execute(select_stmt)
                new_id = result.scalar_one()
        elif account_row.account_type == 'credit':
            account_row_id_to_account_type_map[new_id] = 'credit'

            stmt = insert(CreditAccountModel).values(
                account_name=account_row.account_name,
                balance=account_row.balance,
                min_balance=account_row.min_balance,
                max_balance=account_row.max_balance,
                billing_start_date=account_row.billing_start_date,
                apr=account_row.apr,
                minimum_payment=account_row.minimum_payment,
                prev_cycle_balance=account_row.prev_cycle_balance
            )
            stmt = stmt.on_conflict_do_nothing(index_elements=['user_id', 'stable_account_set_id'])
            stmt = stmt.returning(CreditAccountModel.id)
            result = db.execute(stmt)
            logger.info(stmt)
            new_id = result.scalar() 
            if new_id is None: 
                select_stmt = select(CreditAccountModel.id).where(
                    CreditAccountModel.user_id == fief_uuid,
                    CreditAccountModel.account_name == account_row.account_name,
                    CreditAccountModel.balance == account_row.balance,
                    CreditAccountModel.min_balance == account_row.min_balance,
                    CreditAccountModel.max_balance == account_row.max_balance,
                    CreditAccountModel.billing_start_date == account_row.billing_start_date,
                    CreditAccountModel.apr == account_row.apr,
                    CreditAccountModel.minimum_payment == account_row.minimum_payment,
                    CreditAccountModel.prev_cycle_balance == account_row.prev_cycle_balance
                )
                result = db.execute(select_stmt)
                new_id = result.scalar_one()
        elif account_row.account_type == 'loan':
            account_row_id_to_account_type_map[new_id] = 'loan'

            stmt = insert(LoanAccountModel).values(
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
            stmt = stmt.on_conflict_do_nothing(index_elements=['user_id', 'stable_account_set_id'])
            stmt = stmt.returning(LoanAccountModel.id)
            result = db.execute(stmt)
            logger.info(stmt)
            new_id = result.scalar() 
            if new_id is None: 
                select_stmt = select(LoanAccountModel.id).where(
                    LoanAccountModel.user_id == fief_uuid,
                    LoanAccountModel.account_name == account_row.account_name,
                    LoanAccountModel.balance == account_row.balance,
                    LoanAccountModel.min_balance == account_row.min_balance,
                    LoanAccountModel.max_balance == account_row.max_balance,
                    LoanAccountModel.interest_type == account_row.interest_type,
                    LoanAccountModel.interest_cadence == account_row.interest_cadence,
                    LoanAccountModel.billing_start_date == account_row.billing_start_date,
                    LoanAccountModel.apr == account_row.apr,
                    LoanAccountModel.minimum_payment == account_row.minimum_payment,
                    LoanAccountModel.prev_cycle_balance == account_row.prev_cycle_balance
                )
                result = db.execute(select_stmt)
                new_id = result.scalar_one()   
        elif account_row.account_type == 'investment':
            account_row_id_to_account_type_map[new_id] = 'investment'

            stmt = insert(InvestmentAccountModel).values(
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
            stmt = stmt.on_conflict_do_nothing(index_elements=['user_id', 'stable_account_set_id'])
            stmt = stmt.returning(InvestmentAccountModel.id)
            logger.info(stmt)
            result = db.execute(stmt)
            new_id = result.scalar() 
            if new_id is None: 
                select_stmt = select(InvestmentAccountModel.id).where(
                    InvestmentAccountModel.user_id == fief_uuid,
                    InvestmentAccountModel.account_name == account_row.account_name,
                    InvestmentAccountModel.balance == account_row.balance,
                    InvestmentAccountModel.min_balance == account_row.min_balance,
                    InvestmentAccountModel.max_balance == account_row.max_balance,
                    InvestmentAccountModel.interest_type == account_row.interest_type,
                    InvestmentAccountModel.interest_cadence == account_row.interest_cadence,
                    InvestmentAccountModel.billing_start_date == account_row.billing_start_date,
                    InvestmentAccountModel.apr == account_row.apr,
                    InvestmentAccountModel.minimum_payment == account_row.minimum_payment,
                    InvestmentAccountModel.prev_cycle_balance == account_row.prev_cycle_balance
                )
                result = db.execute(select_stmt)
                new_id = result.scalar_one()

        account_row_id_to_stable_id_map[new_id] = stable_ids['accounts'][account_row.account_name]
        new_account_row_ids.append(new_id)
        
    # insert line items
    new_line_item_row_ids = []
    line_item_row_id_to_stable_id_map = {}
    for line_item_row in draft_dict.line_items:

        stmt = insert(LineItemModel).values(
            user_id=fief_uuid,
            stable_line_item_id=None,
            name=line_item_row.name,
            amount=line_item_row.amount,
            priority=line_item_row.priority,
            cadence=line_item_row.cadence,
            start_date=line_item_row.start_date,
            end_date=line_item_row.end_date,
            deferrable=line_item_row.deferrable,
            partial_payment_allowed=line_item_row.partial_payment_allowed
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=['user_id', 'stable_line_item_id'])
        stmt = stmt.returning(LineItemModel.id)
        logger.info(stmt)
        result = db.execute(stmt)
        new_id = result.scalar() 
        if new_id is None: #the row already existed, we have to select for it
            select_stmt = select(LineItemModel.id).where(
                LineItemModel.user_id == fief_uuid,
                LineItemModel.name == line_item_row.name,
                LineItemModel.amount == line_item_row.amount,
                LineItemModel.priority == line_item_row.priority,
                LineItemModel.cadence == line_item_row.cadence,
                LineItemModel.start_date == line_item_row.start_date,
                LineItemModel.end_date == line_item_row.end_date,
                LineItemModel.deferrable == line_item_row.deferrable,
                LineItemModel.partial_payment_allowed == line_item_row.partial_payment_allowed
            )
            result = db.execute(select_stmt)
            new_id = result.scalar_one()

        line_item_row_id_to_stable_id_map[new_id] = stable_ids['line_items'][line_item_row.name]
        new_line_item_row_ids.append(new_id)
    
    # insert decision rules
    new_decision_rule_row_ids = []
    decision_rule_row_id_to_stable_id_map = {}
    for decision_rule_row in draft_dict.decision_rules:

        stmt = insert(DecisionRuleModel).values(
            user_id=fief_uuid,
            memo_regex=line_item_row.memo_regex,
            priority=line_item_row.priority,
            account_from=line_item_row.account_from,
            account_to=line_item_row.account_to
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=['user_id', 'stable_decision_rule_id'])
        stmt = stmt.returning(DecisionRuleModel.id)
        logger.info(stmt)
        result = db.execute(stmt)
        new_id = result.scalar() 
        if new_id is None: #the row already existed, we have to select for it
            select_stmt = select(DecisionRuleModel.id).where(
                DecisionRuleModel.user_id == fief_uuid,
                DecisionRuleModel.memo_regex == line_item_row.memo_regex,
                DecisionRuleModel.priority == line_item_row.priority,
                DecisionRuleModel.account_from == line_item_row.account_from,
                DecisionRuleModel.account_to == line_item_row.account_to,
            )
            result = db.execute(select_stmt)
            new_id = result.scalar_one()

        decision_rule_row_id_to_stable_id_map[new_id] = stable_ids['decision_rules'][line_item_row.name]
        new_decision_rule_row_ids.append(new_id)

    for milestone_row in draft_dict.milestones:
        pass
    
    # # insert account milestones
    # new_account_milestone_row_ids = []
    # for account_milestone_row in draft_dict.milestone_set.account_milestones:
    #     stmt = insert(AccountMilestone).values(
    #         user_id=fief_uuid,
    #         milestone_name=account_milestone_row.milestone_name,
    #         account_name=account_milestone_row.account_name,
    #         min_balance=account_milestone_row.min_balance,
    #         max_balance=account_milestone_row.max_balance
    #     )
    #     stmt = stmt.on_conflict_do_nothing(index_elements=['user_id', 'milestone_name', 'account_name', 'min_balance', 'max_balance'])
    #     stmt = stmt.returning(AccountMilestone.id)
    #     logger.info(stmt)
    #     result = db.execute(stmt)
    #     new_id = result.scalar() 
    #     if new_id is None: #the row already existed, we have to select for it
    #         select_stmt = select(AccountMilestone.id).where(
    #             AccountMilestone.user_id == fief_uuid,
    #             AccountMilestone.milestone_name == account_milestone_row.milestone_name,
    #             AccountMilestone.account_name == account_milestone_row.account_name,
    #             AccountMilestone.min_balance == account_milestone_row.min_balance,
    #             AccountMilestone.max_balance == account_milestone_row.max_balance,
    #         )
    #         result = db.execute(select_stmt)
    #         new_id = result.scalar_one()
    #     new_account_milestone_row_ids.append(new_id)

    # # insert memo milestones
    # new_memo_milestone_row_ids = []
    # for memo_milestone_row in draft_dict.milestone_set.memo_milestones:
    #     stmt = insert(MemoMilestone).values(
    #         user_id=fief_uuid,
    #         milestone_name=memo_milestone_row.milestone_name,
    #         memo_regex=memo_milestone_row.memo_regex,
    #     )
    #     stmt = stmt.on_conflict_do_nothing(index_elements=['user_id', 'milestone_name', 'memo_regex'])
    #     stmt = stmt.returning(MemoMilestone.id)
    #     logger.info(stmt)
    #     result = db.execute(stmt)
    #     new_id = result.scalar() 
    #     if new_id is None: #the row already existed, we have to select for it
    #         select_stmt = select(MemoMilestone.id).where(
    #             MemoMilestone.user_id == fief_uuid,
    #             MemoMilestone.milestone_name == memo_milestone_row.milestone_name,
    #             MemoMilestone.memo_regex == memo_milestone_row.memo_regex,
    #         )
    #         result = db.execute(select_stmt)
    #         new_id = result.scalar_one()
    #     new_memo_milestone_row_ids.append(new_id)

    # # # insert composite milestones
    # # new_composite_milestone_row_ids = []
    # # for composite_composite_row in draft_dict.milestone_set.composite_milestones:
    #     stmt = insert(CompositeMilestone).values(
    #         user_id=fief_uuid,
    #         milestone_name=composite_composite_row.milestone_name,
    #         milestone_id=composite_composite_row.milestone_id,
    #     )
    #     stmt = stmt.on_conflict_do_nothing(index_elements=['user_id', 'milestone_name', 'milestone_id'])
    #     stmt = stmt.returning(CompositeMilestone.id)
    #     logger.info(stmt)
    #     result = db.execute(stmt)
    #     new_id = result.scalar() 
    #     if new_id is None: #the row already existed, we have to select for it
    #         select_stmt = select(CompositeMilestone.id).where(
    #             CompositeMilestone.user_id == fief_uuid,
    #             CompositeMilestone.milestone_name == composite_composite_row.milestone_name,
    #             CompositeMilestone.milestone_id == composite_composite_row.milestone_id,
    #         )
    #         result = db.execute(select_stmt)
    #         new_id = result.scalar_one()
    #     new_composite_milestone_row_ids.append(new_id)
    
    # insert account set rows
    new_account_set_row_ids = []
    for new_account_row_id in new_account_row_ids:
        # logger.info(f'GET account_set stable_id {stable_ids['account_set']}')
        stmt = insert(AccountSetModel).values(
            user_id=fief_uuid,
            stable_account_set_id=stable_ids['account_set'],
            account_type=account_row_id_to_account_type_map[new_account_row_id],
            stable_account_id=account_row_id_to_stable_id_map[new_account_row_id],
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=['user_id', 'stable_account_set_id', 'account_type', 'stable_account_id'])
        stmt = stmt.returning(AccountSetModel.id)
        logger.info(stmt)
        result = db.execute(stmt)
        new_id = result.scalar() 
        if new_id is None: #the row already existed, we have to select for it
            select_stmt = select(AccountSetModel.id).where(
                AccountSetModel.user_id == fief_uuid,
                AccountSetModel.id == new_account_row_id
            )
            result = db.execute(select_stmt)
            new_id = result.scalar_one()

        new_account_set_row_ids.append(new_id)
    
    # (TODO cross-product for each etc etc etc)
    # stopped somewhere in the middle
    new_line_item_set_row_ids = []
    for new_line_item_row_id in new_line_item_row_ids:

        stmt = insert(LineItemSetModel).values(
            user_id=fief_uuid,
            stable_line_item_set_id=stable_ids['line_item_set'],
            stable_line_item_id=new_line_item_row_id,
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=['user_id', 'stable_line_item_set_id', 'stable_line_item_id'])
        stmt = stmt.returning(LineItemSetModel.id)
        logger.info(stmt)
        result = db.execute(stmt)
        new_id = result.scalar() 
        if new_id is None: #the row already existed, we have to select for it
            select_stmt = select(LineItemSetModel.id).where(
                LineItemSetModel.user_id == fief_uuid,
                LineItemSetModel.stable_line_item_set_id == stable_ids['line_item_set'],
            )
            result = db.execute(select_stmt)
            new_id = result.scalar_one()

        new_line_item_set_row_ids.append(new_id)

    if len(new_line_item_set_row_ids) == 0:
        new_line_item_set_row_ids.append(None)

    # insert decision rule set records #new_decision_rule_row_ids
    new_decision_rule_set_row_ids = []
    for new_decision_rule_row_id in new_decision_rule_row_ids:

        stmt = insert(DecisionRuleModel).values(
            user_id=fief_uuid,
            stable_decision_rule_set_id=stable_ids['decision_rule_set'],
            decision_rule_id=new_decision_rule_row_id,
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=['user_id', 'stable_decision_rule_set_id', 'stable_decision_rule_id'])
        stmt = stmt.returning(DecisionRuleModel.id)
        logger.info(stmt)
        result = db.execute(stmt)
        new_id = result.scalar() 
        if new_id is None: #the row already existed, we have to select for it
            select_stmt = select(DecisionRuleModel.id).where(
                DecisionRuleModel.user_id == fief_uuid,
                DecisionRuleModel.stable_decision_rule_set_id == stable_ids['decision_rule_set']
            )
            result = db.execute(select_stmt)
            new_id = result.scalar_one()

        new_decision_rule_set_row_ids.append(new_id)
    if len(new_decision_rule_set_row_ids) == 0:
        new_decision_rule_set_row_ids.append(None)

    
    new_milestone_set_row_ids = []
    # insert milestone set records
    new_milestone_set_row_ids.append(None)

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

    
    ### todo for each
    # if exists do nothing on conflict
    new_forecast = ExpenseForecastModel(
        user_id=fief_uuid, 
        stable_forecast_id=stable_ids['forecast_stable_id'],
        parameter_id=parameter_stable_id,
        account_set_id=stable_ids['account_set'],
        line_item_set_id=stable_ids['line_item_set'],
        decision_rule_set_id=stable_ids['decision_rule_set'],
        milestone_set_id=stable_ids['milestone_set'],
    )
    db.add(new_forecast)

    status_update = ForecastStatusHistoryModel(
        user_id=fief_uuid, 
        stable_id=stable_ids['forecast_stable_id'],
        status='Submitted',
        insert_ts=datetime.now()
    )

    db.add(status_update)

    # # Step 2: Create ForecastStage row
    # new_stage = ForecastStageModel(
    #     user_id=fief_uuid,  # fief id for hume.dickie@live.com
    #     stable_id=stable_ids['forecast_stable_id'],
    #     start_date=parameter_row.start_date,   # just the date part
    #     end_date=parameter_row.end_date,      # another date
    #     forecast_name=parameter_row.forecast_name,
    #     approximate=parameter_row.approximate,
    #     status="Submitted",
    #     progress="0%",  # or whatever you want to track here
    #     start_ts=datetime.now(),  # full timestamp, now
    #     elapsed=0.0,  # just starting, so 0 seconds elapsed
    # )

    # # Step 3: Add and commit
    # db.add(new_stage)

    #only commit at the end so ALL queries get rolled back if something fails
    db.commit()
    db.refresh(status_update)  # force-load from DB to confirm presence
    logger.info(f"Inserted status update: {status_update.id}")

    # db.refresh(new_stage) #this is not needed at this specific moment
    print(f"Inserted SUBMITTED status expense_forecast with ID: {new_forecast.id}")
    db.close()

    logger.info('EXIT submit_draft')
    return "Placeholder (success)"

@celery_app.task
def validate_and_submit_draft_task(draft_model_dump: dict):
    draft = DraftSubmission.model_validate(draft_model_dump)

    try:
        validation_response = validate_draft_submission(draft)
        if validation_response['status'] == 'accepted':
            submit_draft(draft, validation_response['stable_ids'])
            return "Draft submitted successfully!"
        else:
            return validation_response
    except Exception as e:
        raise e
    
def resolve_account(session, account_set_row):
    match account_set_row.account_type:
        case "checking":
            return session.get(CheckingAccountModel, account_set_row.account_id)
        case "credit":
            return session.get(CreditAccountModel, account_set_row.account_id)
        case "loan":
            return session.get(LoanAccountModel, account_set_row.account_id)
        case "investment":
            return session.get(InvestmentAccountModel, account_set_row.account_id)



def dataframe_to_forecast_table(df: pd.DataFrame, table_name: str, metadata: MetaData) -> Table:
    columns = []

    # First column must be 'Date' and is a datetime.date
    columns.append(Column('Date', Date, nullable=False))

    # sanitize column names
    df.columns = [c.replace(" ", "_") for c in df.columns]
    for col in df.columns[1:-3]:
        columns.append(Column(col, Float))

    columns.append(Column('Next_Income_Date', String))
    columns.append(Column('Memo_Directives', String))
    columns.append(Column('Memo', String))

    return Table(table_name, metadata, *columns)

from sqlalchemy import create_engine
def record_forecast_result(user_id: str, completed_expense_forecast: ExpenseForecast):
    logger.info('ENTER record_forecast_result')

    E = completed_expense_forecast
    metadata = MetaData()
    table_name = "forecast_result_" + str(E.unique_id)

    logger.info(E.forecast_df.to_string())

    ### TODO Line Items
    ### TODO Sankey Data
    ### TODO Milestone Results

    forecast_table = dataframe_to_forecast_table(E.forecast_df, table_name, metadata)

    # Create the table in the DB
    engine = create_engine('postgresql://fief:fief@postgres:5432/fief')  # replace with your actual DB URL
    metadata.create_all(engine, tables=[forecast_table])

    # Optional: insert data into the new table
    with engine.begin() as connection:
        E.forecast_df.to_sql(table_name, con=connection, if_exists='append', index=False)

    logger.info('EXIT record_forecast_result')

@celery_app.task
def run_forecast(user_id: str, forecast_id: str):
    logger.info(f'ENTER task.run_forecast(user_id={user_id}, forecast_id={forecast_id})')
    db = SessionLocal()

    status_update = ForecastStatusHistoryModel(
        user_id=user_id, 
        stable_id=forecast_id,
        status='Started',
        insert_ts=datetime.now()
    )

    db.add(status_update)
    db.commit()

    try:
        logger.info(f'Looking up forecast {forecast_id}')
        ef_stmt = (
            select(ExpenseForecastModel)
            .where(ExpenseForecastModel.stable_forecast_id == forecast_id
                #    ,ExpenseForecastModel.user_id == user_id
                )
            .options(
                selectinload(ExpenseForecastModel.user),
                selectinload(ExpenseForecastModel.parameter),
                # selectinload(ExpenseForecastModel.account_set), #account type cannot be resovled automatically
                selectinload(ExpenseForecastModel.line_item_set),
                selectinload(ExpenseForecastModel.decision_rule_set),
                # selectinload(ExpenseForecastModel.milestone_set), #milestone type cannot be resovled automatically
            )
        )
        
        logger.info(ef_stmt)
        result = db.execute(ef_stmt)
        forecast = result.scalar_one_or_none()

        logger.info('forecast:')
        logger.info(forecast)
        # logger.info(dir(forecast))

        logger.info('Parameter')
        logger.info(forecast.parameter)
        logger.info('Parameter Id')
        logger.info(forecast.parameter_id)
        logger.info('Account Set')
        logger.info(forecast.account_set)
        logger.info('Account Set Id')
        logger.info(forecast.account_set_id)
        logger.info('Decision Rule Set')
        logger.info(forecast.decision_rule_set)
        logger.info('Line Item Set')
        logger.info(forecast.line_item_set)
        logger.info('Milestone Set')
        logger.info(forecast.milestone_set)

        # 'account_set', 'account_set_id', 'decision_rule_set', 'decision_rule_set_id', 'id', 'line_item_set', 
        # 'line_item_set_id', 'metadata', 'milestone_set', 'milestone_set_id', 'parameter', 'parameter_id', 'registry', 
        # 'stable_forecast_id', 'user', 'user_id']

        account_set_stmt = (
            select(AccountSetModel)
            .where(AccountSetModel.stable_account_set_id == forecast.account_set_id
                #    ,AccountSetModel.user_id == user_id
                )
        )

        logger.info(account_set_stmt.compile(dialect=dialect(), compile_kwargs={"literal_binds": True}))
        # account_set_result = db.execute(account_set_stmt)
        # account_set_rows = account_set_result.fetchall()
        account_set_rows = db.scalars(account_set_stmt).all()

        list_of_account_params = []
        try:
            for account_set_row in account_set_rows:
                # logger.info(account_set_row)

                if account_set_row.account_type == 'checking':

                    single_account_sel_sql = (
                        select(CheckingAccountModel)
                        .where(CheckingAccountModel.stable_account_id == account_set_row.stable_account_id
                            #    ,AccountSetModel.user_id == user_id
                            )
                    )

                    logger.info(single_account_sel_sql.compile(dialect=dialect(), compile_kwargs={"literal_binds": True}))
                    account_row = db.scalars(single_account_sel_sql).one()
                        
                    new_account_param = CheckingAccountParams(
                        name=account_row.account_name,
                        balance=account_row.balance,
                        min_balance=account_row.min_balance,
                        max_balance=account_row.max_balance,
                        primary_checking_ind=account_row.primary_checking
                    )
                elif account_set_row.account_type == 'credit':
                    new_account_param = CreditCardAccountParams(
                        name=None,
                        balance=None,
                        min_balance=None,
                        max_balance=None,
                        # billing_start_date: datetime.datetime
                        # interest_type: InterestType = field(default=InterestType.COMPOUND, init=False)
                        # apr: float
                        # interest_cadence: InterestCadence = field(default=InterestCadence.MONTHLY, init=False)
                        # minimum_payment: float
                        # current_statement_balance: float
                        # previous_statement_balance: float
                        # end_of_previous_cycle_balance: Optional[float] = None
                    )
                elif account_set_row.account_type == 'loan':
                    new_account_param = LoanAccountParams(
                        name=None,
                        balance=None,
                        min_balance=None,
                        max_balance=None,
                        # principal_balance: float
                        # interest_balance: float
                        # billing_start_date: datetime.datetime
                        # interest_type: InterestType
                        # apr: float
                        # interest_cadence: InterestCadence
                        # minimum_payment: float
                        # end_of_previous_cycle_balance: Optional[float] = None
                    )
                elif account_set_row.account_type == 'investment':
                    new_account_param = InvestmentAccountParams(
                        name=None,
                        balance=None,
                        min_balance=None,
                        max_balance=None,
                        # account_type: AccountType = field(default=AccountType.INVESTMENT, init=False)
                        # billing_start_date: Optional[datetime.datetime] = None
                        # interest_type: Optional[InterestType] = None
                        # apr: Optional[float] = None
                        # interest_cadence: Optional[InterestCadence] = None
                        # end_of_previous_cycle_balance: Optional[float] = None
                    )

                list_of_account_params.append(new_account_param)
        except Exception as e:
            logger.info('Exception while hydrating account set')
            logger.info(traceback.format_exc())
            raise
        # logger.info('account_set_rows')
        # logger.info(account_set_rows)

        milestone_set_stmt = (
            select(MilestoneSetModel)
            .where(MilestoneSetModel.stable_milestone_set_id == forecast.milestone_set_id
                   ,MilestoneSetModel.user_id == user_id
                )
        )

        logger.info(milestone_set_stmt)
        milestone_set_result = db.execute(milestone_set_stmt)
        milestone_set_rows = milestone_set_result.scalar_one_or_none()
        logger.info('milestone_set_rows')
        logger.info(milestone_set_rows)



        
        list_of_line_item_params = None
        list_of_decision_rule_params = None


        A = AccountSet.from_params(list_of_account_params)
        L = LineItemSet([])
        D = DecisionRuleSet([])
        # L = LineItemSet.from_params(list_of_line_item_params)
        # D = DecisionRuleSet.from_params(list_of_decision_rule_params)
        M = MilestoneSet([])

        E_params = ExpenseForecastParams(
            account_set=A,                 
            lineitem_set=L,            
            decisionrule_set=D,         
            start_date=forecast.parameter.start_date,  
            end_date=forecast.parameter.end_date,           
            milestone_set=M,               
            approximate_flag=forecast.parameter.approximate,       
            forecast_name=forecast.parameter.forecast_name,
            validate=True    # TODO can be false once i trust the code base
        )

        

        status_update = ForecastStatusHistoryModel(
            user_id=user_id, 
            stable_id=forecast_id,
            status='In Progress',
            insert_ts=datetime.now()
        )

        db.add(status_update)
        db.commit()

        E = ExpenseForecast.from_params(E_params)
        logger.info('ABOUT TO RUN FORECAST :)')
        # import trace
        # tracer = trace.Trace(trace=True, count=False)
        # tracer.run('E.runForecast()') 
        try:
            E.runForecast()
            record_forecast_result(user_id, E)
        except Exception as e:
            logger.info('Exception in runForecast')
            logger.info(traceback.format_exc())
            raise

        logger.info('RUN FORECAST TASK COMPLETE :)')

        status_update = ForecastStatusHistoryModel(
            user_id=user_id, 
            stable_id=forecast_id,
            status='Complete',
            insert_ts=datetime.now()
        )

        db.add(status_update)
        db.commit()
        # db.refresh(new_stage) #this is not needed at this specific moment
        # print(f"Inserted expense_forecast with ID: {new_forecast.id}")
        
    except Exception as e:
        logger.info(e)
        status_update = ForecastStatusHistoryModel(
            user_id=user_id, 
            stable_id=forecast_id,
            status='Failed',
            insert_ts=datetime.now()
        )

        db.add(status_update)
        db.commit()


    db.close()



