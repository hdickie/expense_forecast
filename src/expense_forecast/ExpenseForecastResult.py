"""
Summary
-------

Description
-----------

Contract
--------

@interface-report: show
"""



import json
from io import StringIO
from pathlib import Path
from expense_forecast.ExpenseForecastInitialConditions import ExpenseForecastInitialConditions
import pandas as pd
import jsonpickle
import datetime
from datetime import date
from expense_forecast.AccountSet import AccountSet
from expense_forecast.LineItemSet import LineItemSet
from expense_forecast.MemoRuleSet import MemoRuleSet


#TODO DOC manual review of ExpenseForecastResult docstring
class ExpenseForecastResult:

    """
    Summary
    -------

    Description
    -----------

    Contract
    --------

    @interface-report: show
    """
    #TODO DOC manual review of ExpenseForecastResult._dataframe_to_json_data docstring
    @staticmethod
    def _dataframe_to_json_data(dataframe):
        """
        #TODO DOC one-line description of ExpenseForecastResult._dataframe_to_json_data.

        #TODO DOC multi-line description of ExpenseForecastResult._dataframe_to_json_data.
        #TODO DOC explain how ExpenseForecastResult._dataframe_to_json_data participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        dataframe : object
            #TODO DOC one-line description of ExpenseForecastResult._dataframe_to_json_data.dataframe.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastResult._dataframe_to_json_data.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult._dataframe_to_json_data.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult._dataframe_to_json_data.

        @interface-report: show
        """
        if dataframe is None:
            return None
        return json.loads(dataframe.to_json(orient="split", date_format="iso"))

    #TODO DOC manual review of ExpenseForecastResult._dataframe_from_json_data docstring
    @staticmethod
    def _dataframe_from_json_data(data):
        """
        #TODO DOC one-line description of ExpenseForecastResult._dataframe_from_json_data.

        #TODO DOC multi-line description of ExpenseForecastResult._dataframe_from_json_data.
        #TODO DOC explain how ExpenseForecastResult._dataframe_from_json_data participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        data : dict
            #TODO DOC one-line description of ExpenseForecastResult._dataframe_from_json_data.data.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastResult._dataframe_from_json_data.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult._dataframe_from_json_data.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult._dataframe_from_json_data.

        @interface-report: show
        """
        if data is None:
            return None
        dataframe = pd.read_json(StringIO(json.dumps(data)), orient="split")
        if "Date" in dataframe.columns:
            dataframe["Date"] = dataframe["Date"].apply(
                lambda value: value.date() if hasattr(value, "date") else value
            )
        return dataframe

    ### I don't understand why these helper methods were created
    #TODO DOC manual review of ExpenseForecastResult._object_to_json_data docstring
    @staticmethod
    def _object_to_json_data(obj):
        """
        #TODO DOC one-line description of ExpenseForecastResult._object_to_json_data.

        #TODO DOC multi-line description of ExpenseForecastResult._object_to_json_data.
        #TODO DOC explain how ExpenseForecastResult._object_to_json_data participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        obj : object
            #TODO DOC one-line description of ExpenseForecastResult._object_to_json_data.obj.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastResult._object_to_json_data.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult._object_to_json_data.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult._object_to_json_data.

        @interface-report: show
        """
        if obj is None:
            return None
        return json.loads(jsonpickle.encode(obj))

    #TODO DOC manual review of ExpenseForecastResult._object_from_json_data docstring
    @staticmethod
    def _object_from_json_data(data):
        """
        #TODO DOC one-line description of ExpenseForecastResult._object_from_json_data.

        #TODO DOC multi-line description of ExpenseForecastResult._object_from_json_data.
        #TODO DOC explain how ExpenseForecastResult._object_from_json_data participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        data : dict
            #TODO DOC one-line description of ExpenseForecastResult._object_from_json_data.data.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastResult._object_from_json_data.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult._object_from_json_data.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult._object_from_json_data.

        @interface-report: show
        """
        if data is None:
            return None
        return jsonpickle.decode(json.dumps(data))

    #TODO DOC manual review of ExpenseForecastResult.__eq__ docstring
    def __eq__(self, other):
        """
        #TODO DOC one-line description of ExpenseForecastResult.__eq__.

        #TODO DOC multi-line description of ExpenseForecastResult.__eq__.
        #TODO DOC explain how ExpenseForecastResult.__eq__ participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        other : object
            #TODO DOC one-line description of ExpenseForecastResult.__eq__.other.

        Returns
        -------
        bool
            #TODO DOC one-line description of return value of ExpenseForecastResult.__eq__.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult.__eq__.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult.__eq__.

        @interface-report: show
        """
        raise NotImplementedError #TOOD DEFER implement ExpenseForecastResult __eq__

    #TODO DOC manual review of ExpenseForecastResult.__ne__ docstring
    def __ne__(self, other):
        """
        #TODO DOC one-line description of ExpenseForecastResult.__ne__.

        #TODO DOC multi-line description of ExpenseForecastResult.__ne__.
        #TODO DOC explain how ExpenseForecastResult.__ne__ participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        other : object
            #TODO DOC one-line description of ExpenseForecastResult.__ne__.other.

        Returns
        -------
        bool
            #TODO DOC one-line description of return value of ExpenseForecastResult.__ne__.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult.__ne__.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult.__ne__.

        @interface-report: show
        """
        raise NotImplementedError #TODO DEFER implement ExpenseForecastResult __ne__

    #TODO DOC manual review of ExpenseForecastResult.__hash__ docstring
    def __hash__(self):
        """
        #TODO DOC one-line description of ExpenseForecastResult.__hash__.

        #TODO DOC multi-line description of ExpenseForecastResult.__hash__.
        #TODO DOC explain how ExpenseForecastResult.__hash__ participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastResult.__hash__ takes no parameters beyond self/cls.

        Returns
        -------
        int
            #TODO DOC one-line description of return value of ExpenseForecastResult.__hash__.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult.__hash__.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult.__hash__.

        @interface-report: show
        """
        raise NotImplementedError #TODO DEFER implement ExpenseForecastResult __hash__ ; unclear on the purpose of this- LLM-generated

    #TODO DOC manual review of ExpenseForecastResult.__init__ docstring
    def __init__(self, initial_conditions: ExpenseForecastInitialConditions, forecast_df, start_ts, end_ts, **kwargs):

        """
        #TODO DOC one-line description of ExpenseForecastResult.__init__.

        #TODO DOC multi-line description of ExpenseForecastResult.__init__.
        #TODO DOC explain how ExpenseForecastResult.__init__ participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        initial_conditions : object
            #TODO DOC one-line description of ExpenseForecastResult.__init__.initial_conditions.

        forecast_df : object
            #TODO DOC one-line description of ExpenseForecastResult.__init__.forecast_df.

        **kwargs : dict
            #TODO DOC one-line description of ExpenseForecastResult.__init__.kwargs.

        Returns
        -------
        None
            #TODO DOC one-line description of return value of ExpenseForecastResult.__init__.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult.__init__.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult.__init__.

        @interface-report: show
        """
        allowed_kwargs = ['confirmed_df', 'deferred_df', 'skipped_df', 'milestone_set', 'milestone_results', 'approximate_flag', 'policy_results', 'safety_decisions', 'graph_diagnostics', 'transition_results', 'resolved_line_item_set']
        for key in kwargs:
            if key not in allowed_kwargs:
                raise TypeError(f"Unexpected keyword argument '{key}'")

        if 'milestone_set' in kwargs:
            assert 'milestone_results' in kwargs

        if 'milestone_results' in kwargs:
            assert 'milestone_set' in kwargs

        # interval can be inferred, and validation logic for that belongs in SimulationStepper
        # this is an internal method, so we don't validate here. Validate only at entry points

        self.initial_conditions = initial_conditions
        self.forecast_df = forecast_df

        self.confirmed_df = kwargs.get('confirmed_df', None)

        self.deferred_df = kwargs.get('deferred_df', None)

        self.skipped_df = kwargs.get('skipped_df', None)
        if (
            self.skipped_df is not None
            and "Memo" in self.skipped_df.columns
        ):
            # Policy transactions are internal allocation attempts. A policy
            # that has no remaining executable amount is described by its
            # policy result; exposing each synthetic attempt as an ordinary
            # skipped user transaction is redundant and misleading.
            policy_rows = self.skipped_df["Memo"].astype(str).str.startswith(
                "POLICY "
            )
            self.skipped_df = self.skipped_df.loc[~policy_rows].copy()

        self.milestone_set = kwargs.get('milestone_set', None)

        self.milestone_results = kwargs.get('milestone_results', None)

        self.policy_results = kwargs.get('policy_results', {})
        self.safety_decisions = kwargs.get('safety_decisions', [])
        self.graph_diagnostics = kwargs.get('graph_diagnostics', None)
        self.transition_results = kwargs.get('transition_results', {})
        self.resolved_line_item_set = kwargs.get(
            'resolved_line_item_set',
            initial_conditions.initial_line_item_set,
        )

        self.approximate_flag = kwargs.get('approximate_flag', False)
        if self.approximate_flag:
            self.unique_id = initial_conditions.unique_id + "_A"
        else:
            self.unique_id = initial_conditions.unique_id

        # TODO validation and type checking to R start_ts and end_ts
        self.start_ts = start_ts
        self.end_ts = end_ts

    #TODO DOC manual review of ExpenseForecastResult.__str__ docstring
    def __str__(self):
        """
        #TODO DOC one-line description of ExpenseForecastResult.__str__.

        #TODO DOC multi-line description of ExpenseForecastResult.__str__.
        #TODO DOC explain how ExpenseForecastResult.__str__ participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastResult.__str__ takes no parameters beyond self/cls.

        Returns
        -------
        str
            #TODO DOC one-line description of return value of ExpenseForecastResult.__str__.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult.__str__.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult.__str__.

        @interface-report: show
        """
        raise NotImplementedError #TODO DEFER implement R::__str__

    #TODO DOC manual review of ExpenseForecastResult.__repr__ docstring
    def __repr__(self):
        """
        #TODO DOC one-line description of ExpenseForecastResult.__repr__.

        #TODO DOC multi-line description of ExpenseForecastResult.__repr__.
        #TODO DOC explain how ExpenseForecastResult.__repr__ participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastResult.__repr__ takes no parameters beyond self/cls.

        Returns
        -------
        str
            #TODO DOC one-line description of return value of ExpenseForecastResult.__repr__.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult.__repr__.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult.__repr__.

        @interface-report: show
        """
        raise NotImplementedError #TODO DEFER implement R::__repr__

    # Class methods for loading data
    #TODO DOC manual review of ExpenseForecastResult.load_csv_file docstring
    @classmethod
    def load_csv_file(cls):
        """
        #TODO DOC one-line description of ExpenseForecastResult.load_csv_file.

        #TODO DOC multi-line description of ExpenseForecastResult.load_csv_file.
        #TODO DOC explain how ExpenseForecastResult.load_csv_file participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastResult.load_csv_file takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastResult.load_csv_file.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult.load_csv_file.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult.load_csv_file.

        @interface-report: show
        """
        raise NotImplementedError

    #TODO DOC manual review of ExpenseForecastResult.load_xml_file docstring
    @classmethod
    def load_xml_file(cls):
        """
        #TODO DOC one-line description of ExpenseForecastResult.load_xml_file.

        #TODO DOC multi-line description of ExpenseForecastResult.load_xml_file.
        #TODO DOC explain how ExpenseForecastResult.load_xml_file participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastResult.load_xml_file takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastResult.load_xml_file.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult.load_xml_file.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult.load_xml_file.

        @interface-report: show
        """
        raise NotImplementedError

    #TODO DOC manual review of ExpenseForecastResult.loadJSON docstring
    @classmethod
    def loadJSON(cls, json_or_path):
        """
        #TODO DOC one-line description of ExpenseForecastResult.loadJSON.

        #TODO DOC multi-line description of ExpenseForecastResult.loadJSON.
        #TODO DOC explain how ExpenseForecastResult.loadJSON participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        json_or_path : str | Path
            #TODO DOC one-line description of ExpenseForecastResult.loadJSON.json_or_path.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastResult.loadJSON.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult.loadJSON.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult.loadJSON.

        @interface-report: show
        """
        json_string_candidate = str(json_or_path).strip()
        if isinstance(json_or_path, (str, Path)) and not json_string_candidate.startswith(("{", "[")):
            candidate_path = Path(json_or_path)
            json_string = candidate_path.read_text()
        else:
            json_string = str(json_or_path)

        data = json.loads(json_string)
        return cls.initialize_from_dict(data)

    #TODO DOC manual review of ExpenseForecastResult.load_json_file docstring
    @classmethod
    def load_json_file(cls, path_to_json):
        """
        #TODO DOC one-line description of ExpenseForecastResult.load_json_file.

        #TODO DOC multi-line description of ExpenseForecastResult.load_json_file.
        #TODO DOC explain how ExpenseForecastResult.load_json_file participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        path_to_json : str | Path
            #TODO DOC one-line description of ExpenseForecastResult.load_json_file.path_to_json.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastResult.load_json_file.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult.load_json_file.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult.load_json_file.

        @interface-report: show
        """
        return cls.loadJSON(path_to_json)

    #TODO DOC manual review of ExpenseForecastResult.initialize_from_json_file docstring
    @classmethod
    def initialize_from_json_file(cls, path_to_json):
        """
        #TODO DOC one-line description of ExpenseForecastResult.initialize_from_json_file.

        #TODO DOC multi-line description of ExpenseForecastResult.initialize_from_json_file.
        #TODO DOC explain how ExpenseForecastResult.initialize_from_json_file participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        path_to_json : str | Path
            #TODO DOC one-line description of ExpenseForecastResult.initialize_from_json_file.path_to_json.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastResult.initialize_from_json_file.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult.initialize_from_json_file.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult.initialize_from_json_file.

        @interface-report: show
        """
        return cls.loadJSON(path_to_json)

    #TODO DOC manual review of ExpenseForecastResult.initialize_from_json_string docstring
    @classmethod
    def initialize_from_json_string(cls, json_string):
        """
        #TODO DOC one-line description of ExpenseForecastResult.initialize_from_json_string.

        #TODO DOC multi-line description of ExpenseForecastResult.initialize_from_json_string.
        #TODO DOC explain how ExpenseForecastResult.initialize_from_json_string participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        json_string : str
            #TODO DOC one-line description of ExpenseForecastResult.initialize_from_json_string.json_string.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastResult.initialize_from_json_string.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult.initialize_from_json_string.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult.initialize_from_json_string.

        @interface-report: show
        """
        return cls.loadJSON(json_string)

    #TODO DOC manual review of ExpenseForecastResult.initialize_from_dict docstring
    @classmethod
    def initialize_from_dict(cls, data):
        """
        #TODO DOC one-line description of ExpenseForecastResult.initialize_from_dict.

        #TODO DOC multi-line description of ExpenseForecastResult.initialize_from_dict.
        #TODO DOC explain how ExpenseForecastResult.initialize_from_dict participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        data : dict
            #TODO DOC one-line description of ExpenseForecastResult.initialize_from_dict.data.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastResult.initialize_from_dict.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult.initialize_from_dict.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult.initialize_from_dict.

        @interface-report: show
        """
        if "initial_conditions" in data:
            initial_conditions = ExpenseForecastInitialConditions.initialize_from_dict(data["initial_conditions"])
        else:
            raise ValueError("Initial Conditions not found.")

        milestone_set = cls._object_from_json_data(data.get("milestone_set"))
        milestone_results = cls._object_from_json_data(data.get("milestone_results"))
        optional_kwargs = {
            "confirmed_df": cls._dataframe_from_json_data(data.get("confirmed_df")),
            "deferred_df": cls._dataframe_from_json_data(data.get("deferred_df")),
            "skipped_df": cls._dataframe_from_json_data(data.get("skipped_df")),
            "policy_results": cls._object_from_json_data(
                data.get("policy_results")
            ) or {},
            "safety_decisions": cls._object_from_json_data(
                data.get("safety_decisions")
            ) or [],
            "graph_diagnostics": cls._object_from_json_data(
                data.get("graph_diagnostics")
            ),
            "transition_results": cls._object_from_json_data(
                data.get("transition_results")
            ) or {},
            "resolved_line_item_set": LineItemSet.from_dict(
                data["resolved_line_item_set"]
            ) if data.get("resolved_line_item_set") else initial_conditions.initial_line_item_set,
            "approximate_flag": data.get("approximate_flag", False),
        }
        if milestone_set is not None or milestone_results is not None:
            optional_kwargs["milestone_set"] = milestone_set
            optional_kwargs["milestone_results"] = milestone_results

        return cls(
            initial_conditions=initial_conditions,
            forecast_df=cls._dataframe_from_json_data(data["forecast_df"]),
            start_ts=datetime.datetime.fromisoformat(data["start_ts"])
            if data.get("start_ts")
            else datetime.datetime.now(),
            end_ts=datetime.datetime.fromisoformat(data["end_ts"])
            if data.get("end_ts")
            else datetime.datetime.now(),
            **optional_kwargs,
        )

    #TODO DOC manual review of ExpenseForecastResult.load_database_tables docstring
    @classmethod
    def load_database_tables(cls):
        """
        #TODO DOC one-line description of ExpenseForecastResult.load_database_tables.

        #TODO DOC multi-line description of ExpenseForecastResult.load_database_tables.
        #TODO DOC explain how ExpenseForecastResult.load_database_tables participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastResult.load_database_tables takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastResult.load_database_tables.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult.load_database_tables.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult.load_database_tables.

        @interface-report: show
        """
        raise NotImplementedError

    #TODO DOC manual review of ExpenseForecastResult.load_excel_file docstring
    @classmethod
    def load_excel_file(cls):
        """
        #TODO DOC one-line description of ExpenseForecastResult.load_excel_file.

        #TODO DOC multi-line description of ExpenseForecastResult.load_excel_file.
        #TODO DOC explain how ExpenseForecastResult.load_excel_file participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastResult.load_excel_file takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastResult.load_excel_file.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult.load_excel_file.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult.load_excel_file.

        @interface-report: show
        """
        raise NotImplementedError

    #TODO DOC manual review of ExpenseForecastResult.load_pickle_file docstring
    @classmethod
    def load_pickle_file(cls):
        """
        #TODO DOC one-line description of ExpenseForecastResult.load_pickle_file.

        #TODO DOC multi-line description of ExpenseForecastResult.load_pickle_file.
        #TODO DOC explain how ExpenseForecastResult.load_pickle_file participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastResult.load_pickle_file takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastResult.load_pickle_file.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult.load_pickle_file.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult.load_pickle_file.

        @interface-report: show
        """
        raise NotImplementedError

    # Instance methods for exporting data to strings
    #TODO DOC manual review of ExpenseForecastResult.to_csv_string docstring
    def to_csv_string(self):
        """
        #TODO DOC one-line description of ExpenseForecastResult.to_csv_string.

        #TODO DOC multi-line description of ExpenseForecastResult.to_csv_string.
        #TODO DOC explain how ExpenseForecastResult.to_csv_string participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastResult.to_csv_string takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastResult.to_csv_string.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult.to_csv_string.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult.to_csv_string.

        @interface-report: show
        """
        raise NotImplementedError

    #TODO DOC manual review of ExpenseForecastResult.to_xml_string docstring
    def to_xml_string(self):
        """
        #TODO DOC one-line description of ExpenseForecastResult.to_xml_string.

        #TODO DOC multi-line description of ExpenseForecastResult.to_xml_string.
        #TODO DOC explain how ExpenseForecastResult.to_xml_string participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastResult.to_xml_string takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastResult.to_xml_string.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult.to_xml_string.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult.to_xml_string.

        @interface-report: show
        """
        raise NotImplementedError

    #TODO DOC manual review of ExpenseForecastResult.to_json_string docstring
    def to_json_string(self):
        """
        #TODO DOC one-line description of ExpenseForecastResult.to_json_string.

        #TODO DOC multi-line description of ExpenseForecastResult.to_json_string.
        #TODO DOC explain how ExpenseForecastResult.to_json_string participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastResult.to_json_string takes no parameters beyond self/cls.

        Returns
        -------
        str
            #TODO DOC one-line description of return value of ExpenseForecastResult.to_json_string.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult.to_json_string.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult.to_json_string.

        @interface-report: show
        """
        return json.dumps(self.to_dict(), indent=4)

    #TODO DOC manual review of ExpenseForecastResult.to_dict docstring
    def to_dict(self):
        """
        #TODO DOC one-line description of ExpenseForecastResult.to_dict.

        #TODO DOC multi-line description of ExpenseForecastResult.to_dict.
        #TODO DOC explain how ExpenseForecastResult.to_dict participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastResult.to_dict takes no parameters beyond self/cls.

        Returns
        -------
        dict
            #TODO DOC one-line description of return value of ExpenseForecastResult.to_dict.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult.to_dict.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult.to_dict.

        @interface-report: show
        """
        data = {
            "unique_id": self.unique_id,
            "initial_conditions": self.initial_conditions.to_dict(),
            "forecast_df": self._dataframe_to_json_data(self.forecast_df),
            "confirmed_df": self._dataframe_to_json_data(self.confirmed_df),
            "deferred_df": self._dataframe_to_json_data(self.deferred_df),
            "skipped_df": self._dataframe_to_json_data(self.skipped_df),
            "milestone_set": self._object_to_json_data(self.milestone_set),
            "milestone_results": self._object_to_json_data(self.milestone_results),
            "policy_results": self._object_to_json_data(self.policy_results),
            "safety_decisions": self._object_to_json_data(self.safety_decisions),
            "graph_diagnostics": self._object_to_json_data(self.graph_diagnostics),
            "transition_results": self._object_to_json_data(
                self.transition_results
            ),
            "resolved_line_item_set": self.resolved_line_item_set.to_dict(),
            "start_ts": self.start_ts.isoformat(),
            "end_ts": self.end_ts.isoformat(),
            "approximate_flag": self.approximate_flag,
        }
        return data

    #TODO DOC manual review of ExpenseForecastResult.to_json docstring
    def to_json(self):
        """
        #TODO DOC one-line description of ExpenseForecastResult.to_json.

        #TODO DOC multi-line description of ExpenseForecastResult.to_json.
        #TODO DOC explain how ExpenseForecastResult.to_json participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastResult.to_json takes no parameters beyond self/cls.

        Returns
        -------
        str
            #TODO DOC one-line description of return value of ExpenseForecastResult.to_json.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult.to_json.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult.to_json.

        @interface-report: show
        """
        return self.to_json_string()

    # Instance methods for writing data to external sources
    #TODO DOC manual review of ExpenseForecastResult.write_csv_file docstring
    def write_csv_file(self):
        """
        #TODO DOC one-line description of ExpenseForecastResult.write_csv_file.

        #TODO DOC multi-line description of ExpenseForecastResult.write_csv_file.
        #TODO DOC explain how ExpenseForecastResult.write_csv_file participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastResult.write_csv_file takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastResult.write_csv_file.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult.write_csv_file.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult.write_csv_file.

        @interface-report: show
        """
        raise NotImplementedError

    #TODO DOC manual review of ExpenseForecastResult.write_xml_file docstring
    def write_xml_file(self):
        """
        #TODO DOC one-line description of ExpenseForecastResult.write_xml_file.

        #TODO DOC multi-line description of ExpenseForecastResult.write_xml_file.
        #TODO DOC explain how ExpenseForecastResult.write_xml_file participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastResult.write_xml_file takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastResult.write_xml_file.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult.write_xml_file.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult.write_xml_file.

        @interface-report: show
        """
        raise NotImplementedError

    #TODO DOC manual review of ExpenseForecastResult.write_json_file docstring
    def write_json_file(self, path_to_json):
        """
        #TODO DOC one-line description of ExpenseForecastResult.write_json_file.

        #TODO DOC multi-line description of ExpenseForecastResult.write_json_file.
        #TODO DOC explain how ExpenseForecastResult.write_json_file participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        path_to_json : str | Path
            #TODO DOC one-line description of ExpenseForecastResult.write_json_file.path_to_json.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastResult.write_json_file.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult.write_json_file.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult.write_json_file.

        @interface-report: show
        """
        return self.dumpJSON(path_to_json)

    #TODO DOC manual review of ExpenseForecastResult.dumpJSON docstring
    def dumpJSON(self, path_to_json):
        """
        #TODO DOC one-line description of ExpenseForecastResult.dumpJSON.

        #TODO DOC multi-line description of ExpenseForecastResult.dumpJSON.
        #TODO DOC explain how ExpenseForecastResult.dumpJSON participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        path_to_json : str | Path
            #TODO DOC one-line description of ExpenseForecastResult.dumpJSON.path_to_json.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastResult.dumpJSON.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult.dumpJSON.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult.dumpJSON.

        @interface-report: show
        """
        target_path = Path(path_to_json)
        if target_path.is_dir():
            # Older releases treated the supplied path as a directory and put
            # Forecast_<id>.json inside it. Preserve that legacy output while
            # freeing the exact path for the file the caller requested.
            legacy_path = target_path.with_name(target_path.name + ".legacy")
            suffix = 1
            while legacy_path.exists():
                legacy_path = target_path.with_name(
                    f"{target_path.name}.legacy.{suffix}"
                )
                suffix += 1
            target_path.rename(legacy_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(self.to_json_string())
        return True

    #TODO DOC manual review of ExpenseForecastResult.writeToJSONFile docstring
    def writeToJSONFile(self, output_path=None):
        """
        #TODO DOC one-line description of ExpenseForecastResult.writeToJSONFile.

        #TODO DOC multi-line description of ExpenseForecastResult.writeToJSONFile.
        #TODO DOC explain how ExpenseForecastResult.writeToJSONFile participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        output_path : str | Path, optional
            Exact path of the JSON file. If omitted, writes
            ``Forecast_<unique_id>.json`` in the current directory.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastResult.writeToJSONFile.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult.writeToJSONFile.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult.writeToJSONFile.

        @interface-report: show
        """
        if output_path is None:
            output_path = Path(f"Forecast_{self.unique_id}.json")
        return self.dumpJSON(output_path)

    #TODO DOC manual review of ExpenseForecastResult.write_database_tables docstring
    def write_database_tables(self):
        """
        #TODO DOC one-line description of ExpenseForecastResult.write_database_tables.

        #TODO DOC multi-line description of ExpenseForecastResult.write_database_tables.
        #TODO DOC explain how ExpenseForecastResult.write_database_tables participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastResult.write_database_tables takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastResult.write_database_tables.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult.write_database_tables.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult.write_database_tables.

        @interface-report: show
        """
        raise NotImplementedError

    #TODO DOC manual review of ExpenseForecastResult.write_excel_file docstring
    def write_excel_file(self):
        """
        #TODO DOC one-line description of ExpenseForecastResult.write_excel_file.

        #TODO DOC multi-line description of ExpenseForecastResult.write_excel_file.
        #TODO DOC explain how ExpenseForecastResult.write_excel_file participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastResult.write_excel_file takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastResult.write_excel_file.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult.write_excel_file.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult.write_excel_file.

        @interface-report: show
        """
        raise NotImplementedError

    #TODO DOC manual review of ExpenseForecastResult.write_pickle_file docstring
    def write_pickle_file(self):
        """
        #TODO DOC one-line description of ExpenseForecastResult.write_pickle_file.

        #TODO DOC multi-line description of ExpenseForecastResult.write_pickle_file.
        #TODO DOC explain how ExpenseForecastResult.write_pickle_file participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastResult.write_pickle_file takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastResult.write_pickle_file.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastResult.write_pickle_file.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastResult.write_pickle_file.

        @interface-report: show
        """
        raise NotImplementedError
