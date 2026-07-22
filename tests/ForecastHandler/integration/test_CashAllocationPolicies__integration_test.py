from datetime import date
import json

import pytest

from expense_forecast.AccountSet import AccountSet
from expense_forecast.ExpenseForecastInitialConditions import ExpenseForecastInitialConditions
from expense_forecast.ExpenseForecastResult import ExpenseForecastResult
from expense_forecast.FixedMonthlyInvestmentPolicy import FixedMonthlyInvestmentPolicy
from expense_forecast.ForecastHandler import ForecastHandler
from expense_forecast.ForecastPolicySet import ForecastPolicySet
from expense_forecast.IncomePercentageInvestmentPolicy import IncomePercentageInvestmentPolicy
from expense_forecast.LineItemSet import LineItemSet
from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.MinimumCheckingBalancePolicy import MinimumCheckingBalancePolicy
from expense_forecast.PeriodicInvestmentContributionCapPolicy import PeriodicInvestmentContributionCapPolicy
from expense_forecast.SurplusDebtPaymentPolicy import SurplusDebtPaymentPolicy
from expense_forecast.SurplusSavingPolicy import SurplusSavingPolicy
from expense_forecast.SurplusInvestmentPolicy import SurplusInvestmentPolicy
from expense_forecast.CurrentStatementBalancePaymentPolicy import (
    CurrentStatementBalancePaymentPolicy,
)


def _base(accounts, budget, rules, *policies):
    return ExpenseForecastInitialConditions(
        date(2026, 2, 1), date(2026, 2, 4), accounts, budget, rules,
        policy_set=ForecastPolicySet(*policies),
    )


def _checking_and_investment():
    accounts = AccountSet()
    accounts.createCheckingAccount("Checking", 1000, 0, float("inf"), True)
    accounts.createInvestmentAccount("Brokerage", 0, date(2026, 2, 1), 0)
    return accounts


def test_exact_deterministic_checking_spend_avoids_recursive_suffix(monkeypatch):
    accounts = AccountSet()
    accounts.createCheckingAccount("Checking", 1000, 100, float("inf"), True)
    budget = LineItemSet()
    budget.addLineItem(
        date(2026, 2, 2), date(2026, 2, 2), 2, "once", 100, "optional food",
        partial_payment_allowed=True,
    )
    rules = MemoRuleSet()
    rules.addMemoRule("optional food", "Checking", None, 2)
    conditions = _base(accounts, budget, rules)
    recursive_calls = 0
    original = ForecastHandler._attemptTransaction.__func__

    def counted(cls, *args, **kwargs):
        nonlocal recursive_calls
        recursive_calls += 1
        return original(cls, *args, **kwargs)

    monkeypatch.setattr(ForecastHandler, "_attemptTransaction", classmethod(counted))
    result = ForecastHandler.runForecast(conditions)

    assert recursive_calls == 0
    assert result.confirmed_df["Memo"].tolist() == ["optional food"]
    assert result.forecast_df.iloc[-1]["Checking"] == 900


def test_exact_surplus_investment_omits_exhausted_zero_dollar_proposals():
    accounts = AccountSet()
    accounts.createCheckingAccount("Checking", 2_000, 500, float("inf"), True)
    accounts.createInvestmentAccount("Brokerage", 0, date(2026, 2, 1), 0)

    result = ForecastHandler.runForecast(
        _base(
            accounts,
            LineItemSet(),
            MemoRuleSet(),
            SurplusInvestmentPolicy(
                "Brokerage", checking_threshold=1_000, priority=2
            ),
        ),
        engine="legacy",
    )

    policy_confirmed = result.confirmed_df[
        result.confirmed_df["Memo"].str.startswith(
            "POLICY surplus_investment:Brokerage", na=False
        )
    ]
    rendered_memos = "; ".join(
        result.forecast_df["Memo"].astype(str).tolist()
        + result.forecast_df["Memo Directives"].astype(str).tolist()
    )

    assert policy_confirmed["Amount"].astype(float).tolist() == [1_000.0]
    assert "$0.00" not in rendered_memos
    assert result.forecast_df.iloc[-1]["Checking"] == 1_000
    assert result.forecast_df.iloc[-1]["Brokerage"] == 1_000


def test_policy_report_renders_summary_and_type_specific_details():
    accounts = AccountSet()
    accounts.createCheckingAccount("Checking", 5_000, 0, float("inf"), True)
    accounts.createInvestmentAccount("Brokerage", 0, date(2026, 2, 1), 0)
    accounts.createInvestmentAccount("IRA", 0, date(2026, 2, 1), 0)
    accounts.createCreditCardAccount(
        name="Chase", current_statement_balance=0,
        previous_statement_balance=0, billing_start_date=date(2026, 1, 1),
        minimum_payment=0, end_of_previous_cycle_balance=0,
        min_balance=0, max_balance=10_000, apr=0,
    )
    result = ForecastHandler.runForecast(
        _base(accounts, LineItemSet(), MemoRuleSet())
    )
    result.initial_conditions.policy_set = ForecastPolicySet(
        CurrentStatementBalancePaymentPolicy("Chase", priority=2, on_unmet="fail"),
        MinimumCheckingBalancePolicy(2_000, priority=1),
        SurplusDebtPaymentPolicy("credit", "avalanche", priority=3),
        FixedMonthlyInvestmentPolicy("Brokerage", 500, priority=4, day=1),
        FixedMonthlyInvestmentPolicy("IRA", 250, priority=4, day=15),
        IncomePercentageInvestmentPolicy("Brokerage", 0.10, priority=5),
        SurplusInvestmentPolicy("Brokerage", 3_000, priority=6),
        PeriodicInvestmentContributionCapPolicy(
            "IRA", 7_000, "year", priority=7
        ),
    )
    result.policy_results = {
        "minimum_checking_balance": {
            "status": "activated", "activation_date": date(2026, 2, 2),
        },
        "current_statement_balance_payment:Chase": {
            "status": "completed", "requested": 300, "executed": 300,
        },
        "surplus_debt_payment:credit": {
            "status": "completed", "debt_paid": 1_200,
        },
        "fixed_monthly_investment:Brokerage": {
            "status": "capped", "requested": 500, "executed": 400,
            "capped": 100, "missed": 0,
        },
        "fixed_monthly_investment:IRA": {
            "status": "completed", "requested": 250, "executed": 250,
            "capped": 0, "missed": 0,
        },
        "income_percentage_investment:Brokerage": {
            "status": "unmet", "requested": 100, "executed": 80,
            "capped": 0, "missed": 1,
        },
        "surplus_investment:Brokerage": {
            "status": "completed", "executed": 600,
        },
        "periodic_investment_contribution_cap:IRA:year": {
            "status": "completed",
        },
    }

    html = ForecastHandler.generateHTMLReport(result, write_file=False)
    summary = html.split(">Policies</h2>", 1)[1].split(">Forecast Metadata</h2>", 1)[0]

    assert summary.index("Minimum Checking Balance") < summary.index(
        "Current Statement Balance Payment"
    )
    assert summary.index("Current Statement Balance Payment") < summary.index(
        "Surplus Debt Payment"
    )
    assert summary.index("Brokerage") < summary.index("IRA")
    assert "Keep $2,000.00 available" in summary
    assert "$500.00 on day 1" in summary
    assert "$7,000.00 / year" in summary
    assert "Fail" in summary
    assert 'id="detail-tab-policies"' in html
    assert 'id="detail-page-policies"' in html

    policy_page = html.split('id="detail-page-policies"', 1)[1].split(
        'id="detail-page-output_data"', 1
    )[0]
    for heading in (
        "Minimum Checking Balance",
        "Current Statement Balance Payment",
        "Surplus Debt Payment",
        "Fixed Monthly Investment",
        "Income Percentage Investment",
        "Surplus Investment",
        "Surplus Saving",
        "Investment Contribution Cap",
    ):
        assert f">{heading}</h2>" in policy_page
    assert "2026-02-02" in policy_page
    assert "$1,200.00" in policy_page
    assert "$100.00" in policy_page
    assert "Unmet" in policy_page


def test_policy_report_shows_empty_messages_for_all_policy_types():
    result = ForecastHandler.runForecast(
        _base(_checking_and_investment(), LineItemSet(), MemoRuleSet())
    )

    html = ForecastHandler.generateHTMLReport(result, write_file=False)
    policy_page = html.split('id="detail-page-policies"', 1)[1].split(
        'id="detail-page-output_data"', 1
    )[0]

    summary = html.split(">Policies</h2>", 1)[1].split(
        ">Forecast Metadata</h2>", 1
    )[0]
    assert "No policies configured." in summary
    assert policy_page.count("No policies configured.") == 8
    parameters_page = html.split('id="detail-page-parameters"', 1)[1].split(
        'id="detail-page-policies"', 1
    )[0]
    milestones_page = html.split('id="detail-page-milestones"', 1)[1].split(
        'id="detail-page-sankey"', 1
    )[0]
    assert "Milestone Definitions" not in parameters_page
    assert "Achievement Dates" in milestones_page
    assert "Account Milestone Definitions" in milestones_page
    assert 'id="all-chart"' in html
    assert 'id="sankey-chart"' in html
    assert 'data-sankey-mode="transaction"' in html
    assert 'data-sankey-mode="account"' in html
    assert ">Account Type Summary</h2>" in html
    assert ">Accounts</h2>" in html
    assert "AccountSet.from_dict(" in html
    assert "float(&#x27;inf&#x27;)" in html
    assert "report-table-last-day-account-type-summary" in html
    for table_id in (
        "report-table-last-day-account-type-summary",
        "report-table-last-day-accounts",
    ):
        table_html = html.split(table_id, 1)[1].split("</table>", 1)[0]
        assert table_html.split("<tbody>", 1)[1].count("<tr>") == 1
    assert ".last-day-summary-card .report-table" in html
    assert "#detail-page-last_day .table-card-title" not in html
    assert "#detail-page-last_day .report-table thead th" not in html
    assert "font-size: 1.6rem" not in html
    assert "font-size: 1.72rem" in html
    assert "[...data.right].sort((a, b) => b.value - a.value)" in html
    assert "Interest &amp; Investment Returns" in html
    detail_chart_data = json.loads(
        html.split('id="detail-chart-data"', 1)[1]
        .split(">", 1)[1]
        .split("</script>", 1)[0]
    )
    interest_chart = detail_chart_data["interest"]
    assert interest_chart["options"]["line_styles"] == {
        "Investment Returns": {"color": "#268a51"},
        "Interest Accrued": {"color": "#c94747"},
    }
    assert interest_chart["options"]["absolute_tooltip_series"] == [
        "Interest Accrued"
    ]


def test_report_ignores_string_none_for_unachieved_milestone():
    result = ForecastHandler.runForecast(
        _base(_checking_and_investment(), LineItemSet(), MemoRuleSet())
    )
    result.milestone_results = [
        {"Achieved": date(2026, 2, 2), "Not Achieved": "None"}, {}, {}
    ]

    html = ForecastHandler.generateHTMLReport(result, write_file=False)

    milestone_page = html.split('id="detail-page-milestones"', 1)[1].split(
        'id="detail-page-sankey"', 1
    )[0]
    assert "Not Achieved" not in milestone_page
    assert "Achieved" in milestone_page
    assert "2026-02-02" in milestone_page
    assert milestone_page.index(">Milestone</th>") < milestone_page.index(">Date</th>")
    assert milestone_page.index(">Date</th>") < milestone_page.index(">Time</th>")


def test_fixed_monthly_investment_executes_at_policy_priority():
    result = ForecastHandler.runForecast(
        _base(
            _checking_and_investment(), LineItemSet(), MemoRuleSet(),
            FixedMonthlyInvestmentPolicy("Brokerage", 250, priority=2, day=2),
        )
    )

    assert result.forecast_df.iloc[-1]["Checking"] == 750
    assert result.forecast_df.iloc[-1]["Brokerage"] == 250
    assert result.policy_results["fixed_monthly_investment:Brokerage"]["executed"] == 250


def test_income_percentage_investment_uses_lower_priority_income():
    accounts = _checking_and_investment()
    budget, rules = LineItemSet(), MemoRuleSet()
    budget.addLineItem(
        date(2026, 2, 2), date(2026, 2, 2), 1, "once", 500, "income",
        income_flag=True,
    )
    rules.addMemoRule("income", None, "Checking", 1)

    result = ForecastHandler.runForecast(
        _base(
            accounts, budget, rules,
            IncomePercentageInvestmentPolicy("Brokerage", 0.10, priority=2),
        )
    )

    assert result.forecast_df.iloc[-1]["Checking"] == 1450
    assert result.forecast_df.iloc[-1]["Brokerage"] == 50
    html = ForecastHandler.generateHTMLReport(result, write_file=False)
    income_section = html.split(">Income</h2>", 1)[1].split(">Non-Essential Transactions</h2>", 1)[0]
    assert "income" in income_section
    margin_metrics = html.split(">Margin Metrics</h2>", 1)[1].split(
        "</table>", 1
    )[0]
    assert "Initial Investments" in margin_metrics
    assert "Final Investments" in margin_metrics
    assert "$50.00" in margin_metrics
    sankey_data = json.loads(
        html.split('id="sankey-data" type="application/json">', 1)[1]
        .split("</script>", 1)[0]
    )
    assert sankey_data["account"]["left"] == [
        {"name": "Checking", "value": 1500.0},
        {"name": "Income", "value": 500.0},
    ]
    assert sankey_data["account"]["right"] == [
        {"name": "Not Spent", "value": 1450.0},
        {"name": "Checking", "value": 500.0},
        {"name": "Brokerage", "value": 50.0}
    ]
    assert sankey_data["account"]["links"] == [
        {"source": "Income", "target": "Checking", "value": 500.0},
        {"source": "Checking", "target": "Brokerage", "value": 50.0},
        {"source": "Checking", "target": "Not Spent", "value": 1450.0},
    ]
    assert any(
        link["target"] == "Policy: Income Percentage Investment"
        for link in sankey_data["transaction"]["links"]
    )


@pytest.mark.parametrize("approximate", [False, True])
def test_surplus_saving_funds_named_savings_to_threshold(approximate):
    accounts = AccountSet()
    accounts.createCheckingAccount("Checking", 5000, 1000, float("inf"), True)
    accounts.createCheckingAccount("Savings", 0, 0, float("inf"), False)
    conditions = _base(
        accounts,
        LineItemSet(),
        MemoRuleSet(),
        SurplusSavingPolicy(
            account_name="Savings",
            saved_minimum_threshold=2000,
            priority=2,
        ),
    )
    rebuilt_conditions = ExpenseForecastInitialConditions.initialize_from_dict(
        conditions.to_dict()
    )
    rebuilt_policy = rebuilt_conditions.policy_set.get(SurplusSavingPolicy)
    assert rebuilt_policy.account_name == "Savings"
    assert rebuilt_policy.saved_minimum_threshold == 2000

    runner = (
        ForecastHandler.runForecastApproximate
        if approximate else ForecastHandler.runForecast
    )
    result = runner(conditions)

    assert result.forecast_df.iloc[-1]["Checking"] == 3000
    assert result.forecast_df.iloc[-1]["Savings"] == 2000
    assert result.forecast_df["Net Gain"].sum() == pytest.approx(2000)
    assert result.safety_decisions
    saving_decisions = [
        decision for decision in result.safety_decisions
        if "surplus_saving:Savings" in decision["memo"]
    ]
    assert saving_decisions[0]["resolution_method"] == "constraint"

    rebuilt_result = ExpenseForecastResult.initialize_from_json_string(
        result.to_json_string()
    )
    assert rebuilt_result.safety_decisions == result.safety_decisions
    assert result.forecast_df["Net Loss"].sum() == pytest.approx(0)
    policy_result = result.policy_results["surplus_saving:Savings"]
    assert policy_result["status"] == "completed"
    assert policy_result["requested"] == 2000
    assert policy_result["executed"] == 2000
    assert policy_result["shortfall"] == 0

    html = ForecastHandler.generateHTMLReport(result, write_file=False)
    assert ">Surplus Saving</h2>" in html
    assert "Save until $2,000.00" in html
    last_day_summary = html.split(">Account Type Summary</h2>", 1)[1].split(
        "</table>", 1
    )[0]
    assert "Investment Total" in last_day_summary
    sankey_data = json.loads(
        html.split('id="sankey-data" type="application/json">', 1)[1]
        .split("</script>", 1)[0]
    )["account"]
    assert {
        "source": "Checking", "target": "Savings", "value": 2000.0
    } in sankey_data["links"]


def test_surplus_saving_warns_when_threshold_is_unmet():
    accounts = AccountSet()
    accounts.createCheckingAccount("Checking", 1500, 1000, float("inf"), True)
    accounts.createCheckingAccount("Savings", 0, 0, float("inf"), False)
    result = ForecastHandler.runForecastApproximate(_base(
        accounts,
        LineItemSet(),
        MemoRuleSet(),
        SurplusSavingPolicy("Savings", 2000, priority=2, on_unmet="warn"),
    ))

    assert result.forecast_df.iloc[-1]["Checking"] == 1000
    assert result.forecast_df.iloc[-1]["Savings"] == 500
    assert result.forecast_df["Net Gain"].sum() == pytest.approx(500)
    assert result.policy_results["surplus_saving:Savings"]["status"] == "unmet"
    assert result.policy_results["surplus_saving:Savings"]["shortfall"] == 1500
    assert not result.skipped_df["Memo"].astype(str).str.startswith(
        "POLICY "
    ).any()


def test_approximate_income_is_reported_as_net_gain():
    accounts = AccountSet()
    accounts.createCheckingAccount("Checking", 1_000, 0, float("inf"), True)
    budget, rules = LineItemSet(), MemoRuleSet()
    budget.addLineItem(
        date(2026, 2, 2), date(2026, 2, 2), 1, "once", 500, "income",
        income_flag=True,
    )
    rules.addMemoRule("income", None, "Checking", 1)
    conditions = ExpenseForecastInitialConditions(
        date(2026, 2, 1), date(2026, 2, 3), accounts, budget, rules,
    )

    result = ForecastHandler.runForecastApproximate(conditions)

    assert result.forecast_df["Net Gain"].sum() == pytest.approx(500)
    assert result.forecast_df["Net Loss"].sum() == pytest.approx(0)


def test_surplus_loan_policy_uses_snowball():
    accounts = AccountSet()
    accounts.createCheckingAccount("Checking", 1000, 500, float("inf"), True)
    accounts.createLoanAccount(
        name="Large", principal_balance=900, interest_balance=0,
        min_balance=0, max_balance=2000,
        billing_start_date=date(2026, 1, 1), minimum_payment=40,
        billing_cycle_payment_balance=0, apr=0.10,
    )
    accounts.createLoanAccount(
        name="Small", principal_balance=300, interest_balance=0,
        min_balance=0, max_balance=2000,
        billing_start_date=date(2026, 1, 1), minimum_payment=40,
        billing_cycle_payment_balance=0, apr=0.05,
    )

    result = ForecastHandler.runForecast(
        _base(
            accounts, LineItemSet(), MemoRuleSet(),
            SurplusDebtPaymentPolicy("loan", "snowball", priority=2),
        )
    )

    assert result.forecast_df.iloc[-1]["Checking"] == 500
    assert result.forecast_df.iloc[-1]["Small"] == 0
    assert result.forecast_df.iloc[-1]["Large"] == pytest.approx(700.86)
    html = ForecastHandler.generateHTMLReport(result, write_file=False)
    loan_section = html.split(">Loan Payments</h2>", 1)[1].split(">All Transactions</h2>", 1)[0]
    assert "ALL_LOANS" in loan_section
    assert "Policy" in loan_section
    sankey_data = json.loads(
        html.split('id="sankey-data" type="application/json">', 1)[1]
        .split("</script>", 1)[0]
    )["account"]
    assert sankey_data["left"] == sorted(
        sankey_data["left"], key=lambda node: node["value"], reverse=True
    )
    assert any(
        link["source"] == "Checking"
        and link["target"] == "Small"
        and link["value"] > 0
        for link in sankey_data["links"]
    )
    assert any(
        link["source"] == "Checking"
        and link["target"] == "Large"
        and link["value"] > 0
        for link in sankey_data["links"]
    )
    account_set_code = html.split(">AccountSet Code</h2>", 1)[1].split(
        "</code>", 1
    )[0]
    assert "&#x27;Small&#x27;" not in account_set_code


def test_periodic_cap_limits_later_policy_contribution():
    result = ForecastHandler.runForecast(
        _base(
            _checking_and_investment(), LineItemSet(), MemoRuleSet(),
            PeriodicInvestmentContributionCapPolicy(
                "Brokerage", 100, "month", priority=2
            ),
            FixedMonthlyInvestmentPolicy("Brokerage", 250, priority=3, day=2),
        )
    )

    assert result.forecast_df.iloc[-1]["Brokerage"] == 100
    fixed = result.policy_results["fixed_monthly_investment:Brokerage"]
    assert fixed["requested"] == 250
    assert fixed["executed"] == 100
    assert fixed["capped"] == 150
    assert fixed["status"] == "capped"


def test_credit_card_surplus_allocation_supports_avalanche_and_snowball():
    accounts = AccountSet()
    accounts.createCheckingAccount("Checking", 2_000, 500, float("inf"), True)
    accounts.createCreditCardAccount(
        name="High APR", current_statement_balance=0,
        previous_statement_balance=1_000,
        billing_start_date=date(2026, 1, 1), minimum_payment=40,
        end_of_previous_cycle_balance=1_000,
        min_balance=0, max_balance=5_000, apr=0.25,
    )
    accounts.createCreditCardAccount(
        name="Small Balance", current_statement_balance=0,
        previous_statement_balance=200,
        billing_start_date=date(2026, 1, 1), minimum_payment=40,
        end_of_previous_cycle_balance=200,
        min_balance=0, max_balance=5_000, apr=0.10,
    )

    avalanche = accounts.allocate_additional_credit_card_payments(
        300, strategy="avalanche"
    )
    snowball = accounts.allocate_additional_credit_card_payments(
        300, strategy="snowball"
    )

    assert avalanche[0][1] == "High APR"
    assert snowball[0][1] == "Small Balance"
    assert snowball[0][2] == 200


def test_approximate_surplus_policy_occurs_only_on_output_boundaries():
    accounts = AccountSet()
    accounts.createCheckingAccount("Checking", 1_000, 500, float("inf"), True)
    accounts.createLoanAccount(
        name="Loan", principal_balance=1_000, interest_balance=0,
        min_balance=0, max_balance=2_000,
        billing_start_date=date(2026, 1, 1), minimum_payment=0,
        billing_cycle_payment_balance=0, apr=0,
    )
    conditions = ExpenseForecastInitialConditions(
        date(2026, 2, 1), date(2026, 4, 4), accounts,
        LineItemSet(), MemoRuleSet(),
        policy_set=ForecastPolicySet(
            SurplusDebtPaymentPolicy("loan", "avalanche", priority=2)
        ),
    )

    result = ForecastHandler.runForecastApproximate(conditions)
    policy_rows = result.confirmed_df.loc[
        result.confirmed_df["Memo"].str.startswith("POLICY surplus_debt_payment")
    ]

    assert set(policy_rows["Date"]) <= {date(2026, 3, 1), date(2026, 4, 1), date(2026, 4, 4)}
    assert result.forecast_df["Net Gain"].sum() == pytest.approx(0)
    assert result.forecast_df["Net Loss"].sum() == pytest.approx(0)


def test_approximate_current_statement_policy_pays_current_cycle_charges():
    accounts = AccountSet()
    accounts.createCheckingAccount("Checking", 5_000, 0, float("inf"), True)
    accounts.createCreditCardAccount(
        name="Card", current_statement_balance=100,
        previous_statement_balance=1_000,
        billing_start_date=date(2026, 3, 1), minimum_payment=0,
        end_of_previous_cycle_balance=1_000,
        min_balance=0, max_balance=10_000, apr=0,
    )
    budget, rules = LineItemSet(), MemoRuleSet()
    budget.addLineItem(
        date(2026, 2, 10), date(2026, 2, 10), 1, "once", 200,
        "cycle purchase", income_flag=False,
    )
    rules.addMemoRule("cycle purchase", "Card", None, 1)
    conditions = ExpenseForecastInitialConditions(
        date(2026, 2, 1), date(2026, 3, 2), accounts, budget, rules,
        policy_set=ForecastPolicySet(
            CurrentStatementBalancePaymentPolicy("Card", priority=1)
        ),
    )

    result = ForecastHandler.runForecastApproximate(conditions)
    policy_rows = result.confirmed_df.loc[
        result.confirmed_df["Memo"].str.startswith(
            "POLICY current_statement_balance_payment:Card"
        )
    ]

    assert policy_rows["Date"].tolist() == [date(2026, 2, 28)]
    assert policy_rows["Amount"].sum() == pytest.approx(300)


@pytest.mark.parametrize("approximate", [False, True])
def test_surplus_debt_policy_preserves_future_mandatory_payment(approximate):
    """A surplus payment must be sized by recursively forecasting its suffix."""
    accounts = AccountSet()
    accounts.createCheckingAccount("Checking", 2_000, 500, float("inf"), True)
    accounts.createLoanAccount(
        name="Debt", principal_balance=1_000, interest_balance=0,
        min_balance=0, max_balance=5_000,
        billing_start_date=date(2026, 6, 15), minimum_payment=0,
        billing_cycle_payment_balance=0, apr=0,
    )
    budget, rules = LineItemSet(), MemoRuleSet()
    if approximate:
        start_date, payment_date, end_date = (
            date(2026, 1, 1), date(2026, 3, 1), date(2026, 3, 1)
        )
    else:
        start_date, payment_date, end_date = (
            date(2026, 2, 1), date(2026, 2, 3), date(2026, 2, 3)
        )
    budget.addLineItem(
        payment_date, payment_date, 1, "once", 600,
        "scheduled debt payment", partial_payment_allowed=False,
    )
    rules.addMemoRule("scheduled debt payment", "Checking", "Debt", 1)
    conditions = ExpenseForecastInitialConditions(
        start_date, end_date, accounts, budget, rules,
        policy_set=ForecastPolicySet(
            SurplusDebtPaymentPolicy("loan", "avalanche", priority=2)
        ),
    )

    runner = (
        ForecastHandler.runForecastApproximate
        if approximate else ForecastHandler.runForecast
    )
    result = runner(conditions)
    scheduled = result.confirmed_df.loc[
        result.confirmed_df["Memo"] == "scheduled debt payment"
    ]
    policy_rows = result.confirmed_df.loc[
        result.confirmed_df["Memo"].str.startswith("POLICY surplus_debt_payment")
    ]

    assert scheduled["Amount"].sum() == pytest.approx(600)
    if approximate:
        assert policy_rows["Amount"].sum() == pytest.approx(400, abs=0.01)
    else:
        assert policy_rows["Amount"].sum() <= 400.01
    expected_final_debt = 0 if approximate else 400
    assert result.forecast_df.iloc[-1]["Debt"] == pytest.approx(
        expected_final_debt, abs=0.01
    )
