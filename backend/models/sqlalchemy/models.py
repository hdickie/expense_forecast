from sqlalchemy import Column, Integer, String, Float, Boolean, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy import UniqueConstraint
from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.orm import relationship, foreign
from sqlalchemy import and_



Base = declarative_base()

class UserModel(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)

    expense_forecasts = relationship("ExpenseForecastModel", back_populates="user")

class ParameterModel(Base):
    __tablename__ = "parameter"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("UserModel")

    stable_parameter_id = Column(String, nullable=False)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    forecast_name = Column(String, nullable=False)
    approximate = Column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'stable_parameter_id', name='uq_parameter_natural_key'),
    )

class AccountSetModel(Base):
    __tablename__ = "account_set"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("UserModel")

    stable_account_set_id = Column(String, nullable=False)

    account_type = Column(String, nullable=False)
    stable_account_id = Column(String, nullable=False)

    __table_args__ = (
        # UniqueConstraint('user_id', 'stable_account_set_id', name='uq_account_set_user_stable'),
        UniqueConstraint('user_id', 'stable_account_set_id', 'account_type', 'stable_account_id', name='uq_account_set_natural_key'),
    )

# --- Account Types ---

class InvestmentAccountModel(Base):
    __tablename__ = "investment_account"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("UserModel")

    stable_account_id = Column(String, nullable=False)

    account_name = Column(String, nullable=False)
    account_type = Column(String, nullable=False)
    interest_type = Column(String, nullable=False)
    interest_cadence = Column(String, nullable=False)
    balance = Column(Float, nullable=False)
    min_balance = Column(Float, nullable=False)
    max_balance = Column(Float, nullable=False)
    billing_start_date = Column(Date, nullable=False) 
    apr = Column(Float, nullable=False)
    minimum_payment = Column(Float, nullable=False)
    prev_cycle_balance = Column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'stable_account_id', name='uq_investment_account_natural_key'),
    )

class LoanAccountModel(Base):
    __tablename__ = "loan_account"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("UserModel")

    stable_account_id = Column(String, nullable=False)

    account_name = Column(String, nullable=False)
    account_type = Column(String, nullable=False)
    interest_type = Column(String, nullable=False)
    interest_cadence = Column(String, nullable=False)
    balance = Column(Float, nullable=False)
    min_balance = Column(Float, nullable=False)
    max_balance = Column(Float, nullable=False)
    billing_start_date = Column(Date, nullable=False) 
    apr = Column(Float, nullable=False)
    minimum_payment = Column(Float, nullable=False)
    prev_cycle_balance = Column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'stable_account_id', name='uq_loan_account_natural_key'),
    )

class CreditAccountModel(Base):
    __tablename__ = "credit_account"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("UserModel")

    stable_account_id = Column(String, nullable=False)

    account_name = Column(String, nullable=False)
    balance = Column(Float, nullable=False)
    min_balance = Column(Float, nullable=False)
    max_balance = Column(Float, nullable=False)
    billing_start_date = Column(Date, nullable=False) 
    apr = Column(Float, nullable=False)
    minimum_payment = Column(Float, nullable=False)
    prev_cycle_balance = Column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'stable_account_id', name='uq_credit_account_natural_key'),
    )

class CheckingAccountModel(Base):
    __tablename__ = "checking_account"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("UserModel")

    stable_account_id = Column(String, nullable=False)

    account_name = Column(String, nullable=False)
    balance = Column(Float, nullable=False)
    min_balance = Column(Float, nullable=False)
    max_balance = Column(Float, nullable=False)
    primary_checking = Column(Boolean, nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'stable_account_id', name='uq_checking_account_natural_key'),
    )

# --- Line Items ---

class LineItemSetModel(Base):
    __tablename__ = "line_item_set"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("UserModel")

    stable_line_item_set_id = Column(String, nullable=False)
    stable_line_item_id = Column(Integer, nullable=False) 

    __table_args__ = (
        UniqueConstraint('user_id', 'stable_line_item_set_id', 'stable_line_item_id', name='uq_line_item_set_natural_key'),
    )

class LineItemModel(Base):
    __tablename__ = "line_item"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("UserModel")

    stable_line_item_id = Column(String, nullable=False)

    name = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    priority = Column(Integer, nullable=False)
    cadence = Column(String, nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)
    deferrable = Column(Boolean, nullable=False)
    partial_payment_allowed = Column(Boolean, nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'stable_line_item_id', name='uq_line_item_natural_key'),
    )

# --- Decision Rules ---

class DecisionRuleSetModel(Base):
    __tablename__ = "decision_rule_set"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("UserModel")

    stable_decision_rule_set_id = Column(String, nullable=False)
    stable_decision_rule_id = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'stable_decision_rule_set_id', 'stable_decision_rule_id', name='uq_decision_rule_set_natural_key'),
    )

class DecisionRuleModel(Base):
    __tablename__ = "decision_rule"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("UserModel")

    stable_decision_rule_id = Column(String, nullable=False)

    memo_regex = Column(String, nullable=False)
    priority = Column(Integer, nullable=False)
    account_from = Column(String, nullable=False)
    account_to = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'stable_decision_rule_id', name='uq_decision_rule_natural_key'),
    )

# --- Milestones ---

class AccountMilestoneModel(Base):
    __tablename__ = "account_milestone"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("UserModel")

    stable_account_milestone_id = Column(String, nullable=False)

    milestone_name = Column(String, nullable=False)
    account_name = Column(String)
    min_balance = Column(Float)
    max_balance = Column(Float)

    __table_args__ = (
        UniqueConstraint('user_id', 'stable_account_milestone_id', name='uq_account_milestone_natural_key'),
    )

class MemoMilestoneModel(Base):
    __tablename__ = "memo_milestone"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("UserModel")

    stable_memo_milestone_id = Column(String, nullable=False)

    milestone_name = Column(String, nullable=False)
    memo_regex = Column(String)

    __table_args__ = (
        UniqueConstraint('user_id', 'stable_memo_milestone_id', name='uq_memo_milestone_natural_key'),
    )

class CompositeMilestoneModel(Base):
    __tablename__ = "composite_milestone"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("UserModel")

    stable_composite_milestone_id = Column(String, nullable=False)

    milestone_name = Column(String, nullable=False)
    milestone_id = Column(Integer)

    __table_args__ = (
        UniqueConstraint('user_id', 'stable_composite_milestone_id', name='uq_composite_milestone_natural_key'),
    )

class MilestoneSetModel(Base):
    __tablename__ = "milestone_set"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("UserModel")

    stable_milestone_set_id = Column(String, nullable=False)

    # milestone_set_name = Column(String, nullable=False)
    # stable_id = Column(String, nullable=False)
    milestone_type = Column(String, nullable=False)
    milestone_id = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'stable_milestone_set_id', name='uq_milestone_set_natural_key'),
    )
    

# --- Forecasts ---

class ExpenseForecastModel(Base):
    __tablename__ = "expense_forecast"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("UserModel")

    stable_forecast_id = Column(String, nullable=False)
    
    parameter_id = Column(String, nullable=False)
    account_set_id = Column(String, nullable=False)
    line_item_set_id = Column(String, nullable=True)
    decision_rule_set_id = Column(String, nullable=True)
    milestone_set_id = Column(String, nullable=True)

    # Relationships
    parameter = relationship(
        "ParameterModel",
        primaryjoin=and_(
            foreign(user_id) == ParameterModel.user_id,
            foreign(parameter_id) == ParameterModel.stable_parameter_id
        )
    )

    account_set = relationship(
        "AccountSetModel",
        primaryjoin=and_(
            foreign(user_id) == AccountSetModel.user_id,
            foreign(account_set_id) == AccountSetModel.stable_account_set_id
        )
    )

    line_item_set = relationship(
        "LineItemSetModel",
        primaryjoin=and_(
            foreign(user_id) == LineItemSetModel.user_id,
            foreign(line_item_set_id) == LineItemSetModel.stable_line_item_set_id
        )
    )

    decision_rule_set = relationship(
        "DecisionRuleSetModel",
        primaryjoin=and_(
            foreign(user_id) == DecisionRuleSetModel.user_id,
            foreign(decision_rule_set_id) == DecisionRuleSetModel.stable_decision_rule_set_id
        )
    )

    milestone_set = relationship(
        "MilestoneSetModel",
        primaryjoin=and_(
            foreign(user_id) == MilestoneSetModel.user_id,
            foreign(milestone_set_id) == MilestoneSetModel.stable_milestone_set_id
        )
    )



    __table_args__ = (
        UniqueConstraint('user_id', 'stable_forecast_id', 'parameter_id', 'account_set_id', name='uq_expense_forecast_natural_key'),
    )

    # Foreign key constraints
    # __table_args__ = (
    #     ForeignKeyConstraint(
    #         ['user_id', 'parameter_id'],
    #         ['parameter.user_id', 'parameter.stable_parameter_id'],
    #         ondelete='CASCADE'
    #     ),
    #     ForeignKeyConstraint(
    #         ['user_id', 'account_set_id'],
    #         ['account_set.user_id', 'account_set.stable_account_set_id'],
    #         ondelete='CASCADE'
    #     ),
    #     ForeignKeyConstraint(
    #         ['user_id', 'line_item_set_id'],
    #         ['line_item_set.user_id', 'line_item_set.stable_line_item_set_id'],
    #         ondelete='CASCADE'
    #     ),
    #     ForeignKeyConstraint(
    #         ['user_id', 'decision_rule_set_id'],
    #         ['decision_rule_set.user_id', 'decision_rule_set.stable_decision_rule_set_id'],
    #         ondelete='CASCADE'
    #     ),
    #     ForeignKeyConstraint(
    #         ['user_id', 'milestone_set_id'],
    #         ['milestone_set.user_id', 'milestone_set.stable_milestone_set_id'],
    #         ondelete='CASCADE'
    #     ),
    # )





class ExpenseForecastSetModel(Base):
    __tablename__ = "expense_forecast_set"

    id = Column(Integer, primary_key=True, index=True)
    stable_forecast_set_id = Column(String, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("UserModel")

    stable_forecast_id = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'stable_forecast_set_id', 'stable_forecast_id', name='uq_expense_forecast_set_natural_key'),
    )

class ForecastStatusHistoryModel(Base):
    __tablename__ = "forecast_status_history"

    id = Column(Integer, primary_key=True, index=True)
    stable_id = Column(String, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("UserModel")

    status = Column(String, nullable=False)
    insert_ts = Column(DateTime, nullable=False)

class ForecastStatusModel(Base):
    __tablename__ = "forecast_status"
    __table_args__ = {"info": {"is_view": True}}

    stable_id = Column(String, primary_key=True)  # must declare a fake PK
    forecast_name = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    status = Column(String)
    start_ts = Column(DateTime)


# class ForecastStageModel(Base):
#     __tablename__ = "forecast_stage"

#     id = Column(Integer, primary_key=True, index=True)
#     stable_id = Column(String, nullable=False)
#     user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
#     user = relationship("UserModel", back_populates="parameters")

#     # start_date = Column(Date, nullable=False)
#     # end_date = Column(Date, nullable=False)
#     # forecast_name = Column(String, nullable=False)
#     # approximate = Column(Boolean, default=False)

#     status = Column(String, nullable=False)
#     progress = Column(String, nullable=False)
#     start_ts = Column(DateTime, nullable=False)
#     elapsed = Column(Float, nullable=False)

#     insert_ts = Column(DateTime, nullable=False)
#     last_updated_ts = Column(DateTime, nullable=False)