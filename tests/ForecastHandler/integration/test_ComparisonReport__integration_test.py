import json
from datetime import date

import pytest

from expense_forecast.AccountSet import AccountSet
from expense_forecast.ExpenseForecastInitialConditions import (
    ExpenseForecastInitialConditions,
)
from expense_forecast.ForecastHandler import ForecastHandler
from expense_forecast.ForecastResultSet import ForecastResultSet
from expense_forecast.ForecastPolicySet import ForecastPolicySet
from expense_forecast.LineItemSet import LineItemSet
from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.MinimumCheckingBalancePolicy import (
    MinimumCheckingBalancePolicy,
)


def _comparison_result(name, choice, *, card_purchase=0, end=date(2026, 1, 3)):
    accounts = AccountSet()
    accounts.createCheckingAccount(
        "Checking", 1_000, 0, float("inf"), True
    )
    accounts.createCreditCardAccount(
        name="Card",
        current_statement_balance=0,
        previous_statement_balance=0,
        billing_start_date=date(2026, 2, 1),
        minimum_payment=40,
        end_of_previous_cycle_balance=0,
        min_balance=0,
        max_balance=10_000,
        apr=0,
    )
    line_items = LineItemSet(
        scenario_selections={"Food": choice},
        scenario_dimensions={"Food": {choice: LineItemSet()}},
        scenario_timelines={
            "Food": [{
                "choice": choice,
                "effective_date": date(2026, 1, 1),
                "end_date": end,
            }]
        },
    )
    rules = MemoRuleSet()
    if card_purchase:
        line_items.addLineItem(
            date(2026, 1, 2),
            date(2026, 1, 2),
            1,
            "once",
            card_purchase,
            "food expense",
        )
        rules.addMemoRule("food expense", "Card", None, 1)
    conditions = ExpenseForecastInitialConditions(
        date(2026, 1, 1),
        end,
        accounts,
        line_items,
        rules,
        forecast_name=name,
    )
    return ForecastHandler.runForecast(conditions)


def _embedded_comparison_data(html):
    payload = html.split(
        'id="comparison-data" type="application/json">', 1
    )[1].split("</script>", 1)[0]
    return json.loads(payload)


def _embedded_single_reports(html):
    payload = html.split(
        'id="embedded-reports-data" type="application/json">', 1
    )[1].split("</script>", 1)[0]
    return json.loads(payload)


def test_comparison_report_renders_deltas_timelines_and_milestones():
    baseline = _comparison_result("Low Food", "Low")
    comparison = _comparison_result(
        "Standard Food", "Standard", card_purchase=100
    )
    baseline.milestone_results = [
        {
            "Shared": date(2026, 1, 1),
            "Baseline only": date(2026, 1, 2),
        },
        {},
        {},
    ]
    comparison.milestone_results = [
        {
            "Shared": date(2026, 1, 3),
            "Comparison only": date(2026, 1, 2),
        },
        {},
        {},
    ]
    for result, activation_date in (
        (baseline, date(2026, 1, 2)),
        (comparison, None),
    ):
        policy = MinimumCheckingBalancePolicy(500, priority=2)
        result.initial_conditions.policy_set = ForecastPolicySet(policy)
        result.policy_results = {
            policy.policy_key: {
                "status": "activated" if activation_date else "not_achieved",
                "activation_date": activation_date,
            }
        }
        result.resolved_line_item_set.scenario_selections["Income"] = "Salary"
        result.resolved_line_item_set.scenario_timelines["Income"] = [{
            "choice": "Salary",
            "effective_date": date(2026, 1, 1),
            "end_date": date(2026, 1, 3),
        }]

    html = ForecastHandler.generateComparisonReport(
        baseline,
        comparison,
        report_name="Food <Comparison>",
        write_file=False,
    )
    data = _embedded_comparison_data(html)

    assert html.startswith("<!DOCTYPE html>")
    assert "Food &lt;Comparison&gt;" in html
    assert "Baseline Only Choices" in html
    assert "Alternate Choices" in html
    assert ">Low<" in html
    assert ">Standard<" in html
    assert ">Salary<" not in html
    assert "Debt balances retain their raw sign" not in html
    assert (
        '<p class="subtitle">Comparison minus baseline</p>'
        '<p class="subtitle">2026-01-01 to 2026-01-03</p>'
    ) in html
    landing_html = html.split(
        '<script id="embedded-reports-data"', 1
    )[0]
    assert landing_html.count("Minimum Checking Balance $500") == 2
    assert "Active from 2026-01-02</span> · Activated" in html
    assert "No activation recorded</span> · Not Achieved" in html
    card = next(row for row in data["accounts"] if row["account"] == "Card")
    assert card["baseline"] == 0
    assert card["comparison"] == 100
    assert card["delta"] == 100
    assert data["milestones"] == [
        {
            "milestone": "Baseline only",
            "baseline_date": "2026-01-02",
            "comparison_date": "Not achieved",
            "delta_days": None,
            "achievement_status": "baseline_only",
        },
        {
            "milestone": "Comparison only",
            "baseline_date": "Not achieved",
            "comparison_date": "2026-01-02",
            "delta_days": None,
            "achievement_status": "comparison_only",
        },
        {
            "milestone": "Shared",
            "baseline_date": "2026-01-01",
            "comparison_date": "2026-01-03",
            "delta_days": 2,
            "achievement_status": "both",
        },
    ]
    assert "Baseline only" in html
    assert "Comparison only" in html
    assert "Waterfall analysis will be added" in html
    assert html.count('class="waterfall-tab') == 2
    assert 'data-account="Checking"' in html
    assert 'data-account="Card"' in html
    assert 'data-report-view="baseline"' in html
    assert 'data-report-view="alternate"' in html
    assert "<iframe" in html
    assert "<iframe class=\"embedded-report-frame\"" in html
    embedded = _embedded_single_reports(html)
    assert embedded["baseline"].startswith("<!DOCTYPE html>")
    assert embedded["alternate"].startswith("<!DOCTYPE html>")
    assert "This report was generated as part of a comparison" in embedded[
        "baseline"
    ]
    assert "expense-forecast:return-comparison" in embedded["alternate"]


def test_comparison_colors_only_matching_alternate_policy_activation():
    baseline = _comparison_result("Baseline", "Low")
    alternate = _comparison_result("Alternate", "Standard")
    for result, activation in (
        (baseline, date(2026, 1, 3)),
        (alternate, date(2026, 1, 2)),
    ):
        policy = MinimumCheckingBalancePolicy(500, priority=2)
        result.initial_conditions.policy_set = ForecastPolicySet(policy)
        result.policy_results = {
            policy.policy_key: {
                "status": "activated",
                "activation_date": activation,
            }
        }

    html = ForecastHandler.generateComparisonReport(
        baseline, alternate, write_file=False
    )

    assert (
        'class="policy-activation activation-earlier">'
        "Active from 2026-01-02</span>"
    ) in html
    assert html.count("activation-earlier") == 2  # CSS and alternate value.

    key = MinimumCheckingBalancePolicy(500, priority=2).policy_key
    alternate.policy_results[key]["activation_date"] = date(2026, 1, 4)
    later_html = ForecastHandler.generateComparisonReport(
        baseline, alternate, write_file=False
    )
    assert (
        'class="policy-activation activation-later">'
        "Active from 2026-01-04</span>"
    ) in later_html

    alternate.policy_results[key]["activation_date"] = date(2026, 1, 3)
    equal_html = ForecastHandler.generateComparisonReport(
        baseline, alternate, write_file=False
    )
    assert (
        'class="policy-activation">Active from 2026-01-03</span>'
    ) in equal_html


def test_forecast_set_report_renders_filters_series_table_and_matrix():
    low = _comparison_result("Low", "Low")
    standard = _comparison_result("Standard", "Standard")
    for result, achieved in (
        (low, date(2026, 1, 2)),
        (standard, None),
    ):
        result.milestone_results = [{"Retirement": achieved}, {}, {}]

    html = ForecastHandler.generateForecastSetReport(
        ForecastResultSet(low, standard),
        write_file=False,
    )

    assert html.startswith("<!DOCTYPE html>")
    assert "<h1>Feasibility Report</h1>" in html
    assert 'data-mode="single"' in html
    assert 'data-mode="multiple"' in html
    assert 'data-mode="range"' in html
    assert '"milestones": ["Retirement"]' in html
    assert "s.milestone+' × '+s.metric" in html
    assert "Visible Ranges" in html
    assert "Final Checking" in html
    assert "Rows are baselines; columns are alternates." in html
    assert html.count(">Compare</a>") == 1
    assert html.count(">Single</a>") == 2
    assert '"Retirement": null' in html


def test_forecast_set_report_writes_child_report_bundle(tmp_path):
    low = _comparison_result("Low", "Low")
    standard = _comparison_result("Standard", "Standard")
    result_set = ForecastResultSet(low, standard)

    output = ForecastHandler.generateForecastSetReport(
        result_set,
        output_path=tmp_path / "plans.html",
    )

    report_dir = tmp_path / "plans_reports"
    assert output == str(tmp_path / "plans.html")
    assert (tmp_path / "plans.html").exists()
    assert (report_dir / f"Forecast_{low.unique_id}.html").exists()
    assert (report_dir / f"Forecast_{standard.unique_id}.html").exists()
    assert (
        report_dir
        / f"Comparison_{low.unique_id}_vs_{standard.unique_id}.html"
    ).exists()
    assert (report_dir / "hero_chart.js").exists()
    assert (report_dir / "detail_charts.js").exists()


def test_comparison_report_file_output_contract(tmp_path, monkeypatch):
    baseline = _comparison_result("Low", "Low")
    comparison = _comparison_result("Standard", "Standard")

    explicit = ForecastHandler.generateComparisonReport(
        baseline,
        comparison,
        output_path=tmp_path / "custom.html",
    )
    assert explicit == str(tmp_path / "custom.html")
    assert (tmp_path / "custom.html").read_text().startswith("<!DOCTYPE html>")

    monkeypatch.chdir(tmp_path)
    generated = ForecastHandler.generateComparisonReport(baseline, comparison)
    assert generated == (
        f"Comparison_{baseline.unique_id}_vs_{comparison.unique_id}.html"
    )
    assert (tmp_path / generated).exists()


def test_comparison_report_rejects_incompatible_results():
    baseline = _comparison_result("Low", "Low")
    different_dates = _comparison_result(
        "Standard", "Standard", end=date(2026, 1, 4)
    )
    with pytest.raises(ValueError, match="matching forecast date"):
        ForecastHandler.generateComparisonReport(
            baseline, different_dates, write_file=False
        )

    different_accounts = _comparison_result("Standard", "Standard")
    different_accounts.initial_conditions.initial_account_set.accounts[
        0
    ].name = "Other Checking"
    with pytest.raises(ValueError, match="missing account column"):
        ForecastHandler.generateComparisonReport(
            baseline, different_accounts, write_file=False
        )
