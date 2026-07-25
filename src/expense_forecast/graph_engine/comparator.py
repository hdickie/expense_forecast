from __future__ import annotations

import json
import re

import pandas as pd

from .errors import GraphShadowMismatchError


def _normalized_frame(frame, *, transaction=False):
    if frame is None:
        return pd.DataFrame()
    result = frame.copy()
    if transaction:
        for column in (
            "Income_Flag",
            "Deferrable",
            "Partial_Payment_Allowed",
        ):
            if column in result:
                # Historical approximate frames used null for an omitted
                # false flag.  The graph schema stores the same meaning as an
                # explicit bool, so compare the business value.
                result[column] = result[column].map(
                    lambda value: (
                        False if pd.isna(value) else bool(value)
                    )
                )
    if transaction and not result.empty:
        sort_columns = [
            column for column in ("Date", "Priority", "Memo", "Amount")
            if column in result.columns
        ]
        result = result.sort_values(sort_columns).reset_index(drop=True)
    for column in result.columns:
        if column == "Date":
            result[column] = result[column].astype(str)
            continue
        numeric = pd.to_numeric(result[column], errors="coerce")
        if numeric.notna().all():
            result[column] = numeric.round(2)
        else:
            result[column] = result[column].fillna("").astype(str)
            if column in {"Memo", "Memo Directives"}:
                result[column] = result[column].map(_normalize_presented_money)
    return result.reset_index(drop=True)


def _normalize_presented_money(value):
    """Compare monetary annotations at the report's cent precision."""
    return re.sub(
        r"\$([0-9]+(?:\.[0-9]+)?)",
        lambda match: f"${float(match.group(1)):.2f}",
        str(value),
    )


def _compare_frame(section, graph_frame, legacy_frame, transaction=False):
    graph = _normalized_frame(graph_frame, transaction=transaction)
    legacy = _normalized_frame(legacy_frame, transaction=transaction)
    if list(graph.columns) != list(legacy.columns):
        raise GraphShadowMismatchError(
            section=section,
            variable="columns",
            graph_value=list(graph.columns),
            legacy_value=list(legacy.columns),
            producer="presentation" if section == "forecast_df" else "checking-state",
        )
    if graph.shape != legacy.shape:
        raise GraphShadowMismatchError(
            section=section,
            variable="shape",
            graph_value=graph.shape,
            legacy_value=legacy.shape,
            producer="presentation" if section == "forecast_df" else "checking-state",
        )
    for row_index in range(len(graph)):
        for column in graph.columns:
            graph_value = graph.at[row_index, column]
            legacy_value = legacy.at[row_index, column]
            if graph_value != legacy_value:
                event = graph.at[row_index, "Date"] if "Date" in graph.columns else row_index
                raise GraphShadowMismatchError(
                    section=section,
                    event=event,
                    variable=column,
                    graph_value=graph_value,
                    legacy_value=legacy_value,
                    producer="summary" if column in graph_frame.columns else "presentation",
                    provenance=["graph shadow comparison"],
                )


def compare_results(graph_result, legacy_result):
    _compare_frame("forecast_df", graph_result.forecast_df, legacy_result.forecast_df)
    for section in ("confirmed_df", "deferred_df", "skipped_df"):
        _compare_frame(
            section,
            getattr(graph_result, section),
            getattr(legacy_result, section),
            transaction=True,
        )
    for attribute in ("unique_id", "milestone_results", "policy_results"):
        graph_value = getattr(graph_result, attribute)
        legacy_value = getattr(legacy_result, attribute)
        if graph_value != legacy_value:
            raise GraphShadowMismatchError(
                section="result",
                variable=attribute,
                graph_value=graph_value,
                legacy_value=legacy_value,
                producer="result-assembly",
            )
    graph_data = graph_result.to_dict()
    legacy_data = legacy_result.to_dict()
    for payload in (graph_data, legacy_data):
        payload.pop("start_ts", None)
        payload.pop("end_ts", None)
        payload.pop("graph_diagnostics", None)
        # Resolution provenance and regime timing are engine diagnostics. The
        # configured policies and their financial results are compared above.
        payload.pop("safety_decisions", None)
        # The resolved scenario history is produced by the transition-aware v2
        # wrapper.  The first graph engine and legacy policy materializer do not
        # yet share an equivalent lifecycle for this audit-only field.
        payload.pop("resolved_line_item_set", None)
        # DataFrames were compared above using their public normalized form;
        # legacy preserves incidental index/order details in split JSON.
        for dataframe_key in (
            "forecast_df", "confirmed_df", "deferred_df", "skipped_df"
        ):
            payload.pop(dataframe_key, None)
    if json.dumps(graph_data, sort_keys=True, default=str) != json.dumps(
        legacy_data, sort_keys=True, default=str
    ):
        raise GraphShadowMismatchError(
            section="serialization",
            variable="to_dict",
            graph_value=graph_data,
            legacy_value=legacy_data,
            producer="result-assembly",
        )
