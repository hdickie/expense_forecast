import AccountSet
import BudgetSet
import MemoRuleSet
import MilestoneSet
import ExpenseForecast
import ForecastHandler
import os
import pebble
import datetime
import MilestoneSet
from time import sleep


class ForecastRunner:

    def __init__(self, lock_directory):

        #establish connection to lock directory
        assert os.path.isdir(lock_directory)

        #calling Executor w no args uses system architecture default
        self.executor = pebble.ProcessPool()
        self.id_to_futures_dict = {}
        self.futures_to_id_dict = {}
        self.forecasts = {}

    def start_forecast(self, E):

        #we also check the lock directory in case there are multiple instance of ForecastRunner at the same time
        #future = self.executor.submit(E.fake_runForecast)
        future = self.executor.schedule(E.fake_runForecast, args=[])
        self.id_to_futures_dict[E.unique_id] = future
        self.futures_to_id_dict[future] = E.unique_id
        self.forecasts[E.unique_id] = E

    def ps(self):
        print('------------------------------------')
        print('Id     Running    Cancelled    Done')
        for id, f in self.id_to_futures_dict.items():
            print(id+' '+str(f.running()).ljust(10)+' '+str(f.cancelled()).ljust(12)+' '+str(f.done()))
        print('------------------------------------')

    def cancel(self,unique_id):
        print('Attempting to cancel '+str(unique_id))
        try:
            self.id_to_futures_dict[unique_id].cancel()
        except Exception as e:
            raise e

    def __str__(self):
        pass

