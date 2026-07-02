

class ExpenseForecast:

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

        if 'confirmed_df' not in kwargs:
            self.confirmed_df = None #todo

        if 'deferred_df' not in kwargs:
            self.deferred_df = None #todo

        if 'skipped_df' not in kwargs:
            self.skipped_df = None #todo

        if 'milestone_set' not in kwargs:
            self.milestone_set = None #todo

        if 'milestone_results' not in kwargs:
            self.milestone_results = None #todo

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
    def load_json_file(cls):
        raise NotImplementedError

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
        raise NotImplementedError

    # Instance methods for writing data to external sources
    def write_csv_file(self):
        raise NotImplementedError

    def write_xml_file(self):
        raise NotImplementedError

    def write_json_file(self):
        raise NotImplementedError

    def write_database_tables(self):
        raise NotImplementedError

    def write_excel_file(self):
        raise NotImplementedError

    def write_pickle_file(self):
        raise NotImplementedError