
import json
from io import StringIO
from pathlib import Path

import pandas as pd
import jsonpickle


class ExpenseForecast:

    @staticmethod
    def _dataframe_to_json_data(dataframe):
        if dataframe is None:
            return None
        return json.loads(dataframe.to_json(orient="split", date_format="iso"))

    @staticmethod
    def _dataframe_from_json_data(data):
        if data is None:
            return None
        return pd.read_json(StringIO(json.dumps(data)), orient="split")

    @staticmethod
    def _object_to_json_data(obj):
        if obj is None:
            return None
        return json.loads(jsonpickle.encode(obj))

    @staticmethod
    def _object_from_json_data(data):
        if data is None:
            return None
        return jsonpickle.decode(json.dumps(data))

    def __eq__(self, other):
        raise NotImplementedError #todo

    def __ne__(self, other):
        raise NotImplementedError #todo

    def __hash__(self):
        raise NotImplementedError #todo

    # todo confirm that I don't need __getstate__, __setstate__. I think pickle can compress data frames and I might not want that

    def __init__(self, unique_id, forecast_df, **kwargs):

        allowed_kwargs = ['confirmed_df', 'deferred_df', 'skipped_df', 'milestone_set', 'milestone_results']
        for key in kwargs:
            if key not in allowed_kwargs:
                raise TypeError(f"Unexpected keyword argument '{key}'")

        if 'milestone_set' in kwargs:
            assert 'milestone_results' in kwargs

        if 'milestone_results' in kwargs:
            assert 'milestone_set' in kwargs

        # interval can be inferred, and validation logic for that belongs in SimulationStepper
        # this is an internal method, so we don't validate here. Validate only at entry points

        self.unique_id = unique_id
        self.forecast_df = forecast_df

        self.confirmed_df = kwargs.get('confirmed_df', None)

        self.deferred_df = kwargs.get('deferred_df', None)

        self.skipped_df = kwargs.get('skipped_df', None)

        self.milestone_set = kwargs.get('milestone_set', None)

        self.milestone_results = kwargs.get('milestone_results', None)

    def __str__(self):
        raise NotImplementedError #todo

    def __repr__(self):
        raise NotImplementedError #todo

    # Class methods for loading data
    @classmethod
    def load_csv_file(cls):
        raise NotImplementedError

    @classmethod
    def load_xml_file(cls):
        raise NotImplementedError

    @classmethod
    def loadJSON(cls, json_or_path):
        json_string_candidate = str(json_or_path).strip()
        if isinstance(json_or_path, (str, Path)) and not json_string_candidate.startswith(("{", "[")):
            candidate_path = Path(json_or_path)
            json_string = candidate_path.read_text()
        else:
            json_string = str(json_or_path)

        data = json.loads(json_string)
        return cls.initialize_from_dict(data)

    @classmethod
    def load_json_file(cls, path_to_json):
        return cls.loadJSON(path_to_json)

    @classmethod
    def initialize_from_json_file(cls, path_to_json):
        return cls.loadJSON(path_to_json)

    @classmethod
    def initialize_from_json_string(cls, json_string):
        return cls.loadJSON(json_string)

    @classmethod
    def initialize_from_dict(cls, data):
        return cls(
            unique_id=data["unique_id"],
            forecast_df=cls._dataframe_from_json_data(data["forecast_df"]),
            confirmed_df=cls._dataframe_from_json_data(data.get("confirmed_df")),
            deferred_df=cls._dataframe_from_json_data(data.get("deferred_df")),
            skipped_df=cls._dataframe_from_json_data(data.get("skipped_df")),
            milestone_set=cls._object_from_json_data(data.get("milestone_set")),
            milestone_results=cls._object_from_json_data(data.get("milestone_results")),
        )

    @classmethod
    def load_database_tables(cls):
        raise NotImplementedError

    @classmethod
    def load_excel_file(cls):
        raise NotImplementedError

    @classmethod
    def load_pickle_file(cls):
        raise NotImplementedError

    # Instance methods for exporting data to strings
    def to_csv_string(self):
        raise NotImplementedError

    def to_xml_string(self):
        raise NotImplementedError

    def to_json_string(self):
        data = {
            "unique_id": self.unique_id,
            "forecast_df": self._dataframe_to_json_data(self.forecast_df),
            "confirmed_df": self._dataframe_to_json_data(self.confirmed_df),
            "deferred_df": self._dataframe_to_json_data(self.deferred_df),
            "skipped_df": self._dataframe_to_json_data(self.skipped_df),
            "milestone_set": self._object_to_json_data(self.milestone_set),
            "milestone_results": self._object_to_json_data(self.milestone_results),
        }
        return json.dumps(data, indent=4)

    def to_json(self):
        return self.to_json_string()

    # Instance methods for writing data to external sources
    def write_csv_file(self):
        raise NotImplementedError

    def write_xml_file(self):
        raise NotImplementedError

    def write_json_file(self, path_to_json):
        return self.dumpJSON(path_to_json)

    def dumpJSON(self, path_to_json):
        target_path = Path(path_to_json)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(self.to_json_string())
        return True

    def writeToJSONFile(self, output_dir="./"):
        output_path = Path(output_dir) / f"Forecast_{self.unique_id}.json"
        return self.dumpJSON(output_path)

    def write_database_tables(self):
        raise NotImplementedError

    def write_excel_file(self):
        raise NotImplementedError

    def write_pickle_file(self):
        raise NotImplementedError
