from sqlalchemy import Column, Integer, String, Float, Boolean, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy import UniqueConstraint

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)

    # Relationships
    parameters = relationship("Parameter", back_populates="user", cascade="all, delete")
    accounts = relationship("AccountSet", back_populates="user", cascade="all, delete")
    line_item_sets = relationship("LineItemSet", back_populates="user", cascade="all, delete")
    decision_rule_sets = relationship("DecisionRuleSet", back_populates="user", cascade="all, delete")
    milestone_sets = relationship("MilestoneSet", back_populates="user", cascade="all, delete")
    forecasts = relationship("ExpenseForecast", back_populates="user", cascade="all, delete")
    forecast_sets = relationship("ExpenseForecastSet", back_populates="user", cascade="all, delete")
    checking_accounts = relationship("CheckingAccount", back_populates="user", cascade="all, delete")
    credit_accounts = relationship("CreditAccount", back_populates="user", cascade="all, delete")
    loan_accounts = relationship("LoanAccount", back_populates="user", cascade="all, delete")
    investment_accounts = relationship("InvestmentAccount", back_populates="user", cascade="all, delete")
    

class Parameter(Base):
    __tablename__ = "parameter"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="parameters")

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    forecast_name = Column(String, nullable=False)
    approximate = Column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'start_date', 'end_date', 'forecast_name', 'approximate', name='uq_parameter_natural_key'),
    )

class AccountSet(Base):
    __tablename__ = "account_set"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="accounts")

    account_id = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'account_id', name='uq_account_set_natural_key'),
    )

# --- Account Types ---

class InvestmentAccount(Base):
    __tablename__ = "investment_account"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="investment_accounts")

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
        UniqueConstraint('user_id', 'account_name', 'balance','min_balance',
                        'max_balance', 'interest_type', 'interest_cadence','billing_start_date',
                        'apr', 'minimum_payment', 'prev_cycle_balance', name='uq_investment_account_natural_key'),
    )

class LoanAccount(Base):
    __tablename__ = "loan_account"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="loan_accounts")

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
        UniqueConstraint('user_id', 'account_name', 'balance','min_balance',
                        'max_balance', 'interest_type', 'interest_cadence','billing_start_date',
                        'apr', 'minimum_payment', 'prev_cycle_balance', name='uq_loan_account_natural_key'),
    )

class CreditAccount(Base):
    __tablename__ = "credit_account"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="credit_accounts")

    account_name = Column(String, nullable=False)
    balance = Column(Float, nullable=False)
    min_balance = Column(Float, nullable=False)
    max_balance = Column(Float, nullable=False)
    billing_start_date = Column(Date, nullable=False) 
    apr = Column(Float, nullable=False)
    minimum_payment = Column(Float, nullable=False)
    prev_cycle_balance = Column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'account_name', 'balance','min_balance',
                        'max_balance', 'billing_start_date', 'apr','minimum_payment',
                        'prev_cycle_balance', name='uq_credit_account_natural_key'),
    )

class CheckingAccount(Base):
    __tablename__ = "checking_account"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="checking_accounts")

    account_name = Column(String, nullable=False)
    balance = Column(Float, nullable=False)
    min_balance = Column(Float, nullable=False)
    max_balance = Column(Float, nullable=False)
    primary_checking = Column(Boolean, nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'account_name', 'balance','min_balance',
                        'max_balance','primary_checking', name='uq_checking_account_natural_key'),
    )

# --- Line Items ---

class LineItemSet(Base):
    __tablename__ = "line_item_set"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="line_item_sets")

    line_item_id = Column(Integer)  # Might eventually want a relationship here!

class LineItem(Base):
    __tablename__ = "line_item"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User")

    name = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    priority = Column(Integer, nullable=False)
    cadence = Column(String, nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)
    deferrable = Column(Boolean, nullable=False)
    partial_payment_allowed = Column(Boolean, nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'name', 'amount', 'priority', 'cadence',
                        'start_date','end_date','deferrable','partial_payment_allowed', name='uq_line_item_natural_key'),
    )

# --- Decision Rules ---

class DecisionRuleSet(Base):
    __tablename__ = "decision_rule_set"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="decision_rule_sets")

    decision_rule_id = Column(Integer)

class DecisionRule(Base):
    __tablename__ = "decision_rule"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User")

    memo_regex = Column(String, nullable=False)
    priority = Column(Integer, nullable=False)
    account_from = Column(String, nullable=False)
    account_to = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'memo_regex', 'priority', 'account_from', 'account_to', name='uq_decision_rule_natural_key'),
    )

# --- Milestones ---

class AccountMilestone(Base):
    __tablename__ = "account_milestone"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User")

    milestone_name = Column(String, nullable=False)
    account_name = Column(String)
    min_balance = Column(Float)
    max_balance = Column(Float)

class MemoMilestone(Base):
    __tablename__ = "memo_milestone"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User")

    milestone_name = Column(String, nullable=False)
    memo_regex = Column(String)
    account_milestone_names = Column(String)

class CompositeMilestone(Base):
    __tablename__ = "composite_milestone"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User")

    milestone_name = Column(String, nullable=False)
    account_milestone = Column(Integer, ForeignKey("account_milestone.id", ondelete="SET NULL"))
    memo_milestone = Column(Integer, ForeignKey("memo_milestone.id", ondelete="SET NULL"))

class MilestoneSet(Base):
    __tablename__ = "milestone_set"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="milestone_sets")

    milestone_name = Column(String, nullable=False)
    account_milestone = Column(Integer, ForeignKey("account_milestone.id", ondelete="SET NULL"))
    memo_milestone = Column(Integer, ForeignKey("memo_milestone.id", ondelete="SET NULL"))
    composite_milestone = Column(Integer, ForeignKey("composite_milestone.id", ondelete="SET NULL"))

# --- Forecasts ---

class ExpenseForecast(Base):
    __tablename__ = "expense_forecast"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="forecasts")

    stable_id = Column(String, nullable=False)

    parameter_id = Column(Integer, ForeignKey("parameter.id", ondelete="CASCADE"), nullable=False)
    account_set_id = Column(Integer, ForeignKey("account_set.id", ondelete="CASCADE"), nullable=False)
    line_item_set_id = Column(Integer, ForeignKey("line_item_set.id", ondelete="CASCADE"), nullable=False)
    decision_rule_set_id = Column(Integer, ForeignKey("decision_rule_set.id", ondelete="CASCADE"), nullable=False)
    milestone_set_id = Column(Integer, ForeignKey("milestone_set.id", ondelete="CASCADE"), nullable=False)

class ExpenseForecastSet(Base):
    __tablename__ = "expense_forecast_set"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="forecast_sets")

    

class ForecastStage(Base):
    __tablename__ = "forecast_stage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    # user = relationship("User", back_populates="parameters")

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    forecast_name = Column(String, nullable=False)
    approximate = Column(Boolean, default=False)

    status = Column(String, nullable=False)
    progress = Column(String, nullable=False)
    start_ts = Column(DateTime, nullable=False)
    elapsed = Column(Float, nullable=False)