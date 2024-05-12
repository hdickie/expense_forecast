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
import traceback
import sys
import multiprocessing

def task(n_seconds):
    sleep(n_seconds)
    return 'Done!'

def runAndReturn(E, log_level='WARNING'):
    lock_file_name = 'Forecast_' + str(E.unique_id) + '.lock'
    try:
        print('Writing lock file '+str(lock_file_name))
        with open(lock_file_name, 'w') as f:
            f.writelines(datetime.datetime.now().strftime('%Y%m%d %H:%M:%S'))
        E.runForecast(log_level)
    except:
        pass
    os.remove(lock_file_name) #want to always remove lock if possible
    return E

def runAndReturnApproximate(E):
    #print('START runAndReturn '+str(E.unique_id))
    E.runForecastApproximate()
    #print('END runAndReturn ' + str(E.unique_id))
    return E

class ForecastRunner:

    def __init__(self, lock_directory):

        #establish connection to lock directory
        assert os.path.isdir(lock_directory)
        self.lock_directory = lock_directory

        #calling Executor w no args uses system architecture default
        self.executor = pebble.ProcessPool()
        #self.executor = pebble.ThreadPool()
        self.id_to_futures_dict = {}
        self.futures_to_id_dict = {}
        self.forecasts = {}





    def start_forecast(self, E, log_level='WARNING'):

        #we also check the lock directory in case there are multiple instance of ForecastRunner at the same time
        #future = self.executor.submit(E.fake_runForecast)
        #print('BEFORE schedule ' + str(E.unique_id))
        lock_file_name = 'Forecast_'+str(E.unique_id)+'.lock'
        if lock_file_name in os.listdir(self.lock_directory):
            print('Found '+lock_file_name+': SKIPPING')
        else:
            print('Scheduling '+E.unique_id)
            future = self.executor.schedule(runAndReturn, args=[E,log_level])
            #print('AFTER schedule ' + str(E.unique_id))
            self.id_to_futures_dict[E.unique_id] = future
            self.futures_to_id_dict[future] = E.unique_id
            #self.forecasts[E.unique_id] = E

    def start_forecast_approximate(self, E):

        #we also check the lock directory in case there are multiple instance of ForecastRunner at the same time
        #future = self.executor.submit(E.fake_runForecast)
        #print('BEFORE schedule ' + str(E.unique_id))
        future = self.executor.schedule(runAndReturnApproximate, args=[E])
        #print('AFTER schedule ' + str(E.unique_id))
        self.id_to_futures_dict[E.unique_id] = future
        self.futures_to_id_dict[future] = E.unique_id
        #self.forecasts[E.unique_id] = E

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

    def waitAll(self):
        self.executor.close()
        self.executor.join()

        for unique_id, future in self.id_to_futures_dict.items():
            if future.exception() is not None:
                print(f'ERROR: {future}: {future.exception()}')
                continue
            self.forecasts[unique_id] = future.result()

        for E in self.forecasts.values():
            E.appendSummaryLines()
            E.writeToJSONFile('./out/')

    def __str__(self):
        pass

