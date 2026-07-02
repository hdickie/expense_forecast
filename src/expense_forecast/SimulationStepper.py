
import pandas as pd
from expense_forecast.ExpenseForecastInitialConditions import ExpenseForecastInitialConditions
from expense_forecast.ExpenseForecastResult import ExpenseForecastResult
from expense_forecast.log_methods import log_in_color
import logging
import datetime
pd.set_option("display.precision", 100) #todo this may more appropriate near some code for output or logging

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s - %(levelname)-8s - %(message)s")
fileHandler = logging.FileHandler(__name__ + ".log", mode="w")
fileHandler.setFormatter(formatter)
streamHandler = logging.StreamHandler()
streamHandler.setFormatter(formatter)
logger.setLevel(logging.DEBUG) 
logger.handlers.clear()
logger.addHandler(fileHandler)
logger.addHandler(streamHandler)
logger.propagate = False

class SimulationStepper:

    ROUNDING_ERROR_TOLERANCE = 0.0000000001

    def __init__(self):
        pass

    # @staticmethod
    # def step(initial_conditions: ExpenseForecastInitialConditions) -> ExpenseForecastResult:
    #     # Validate initial conditions
    #     if not isinstance(initial_conditions, ExpenseForecastInitialConditions):
    #         raise TypeError("initial_conditions must be an instance of ExpenseForecastInitialConditions")

    #     # # Extract the forecast DataFrame from the initial conditions
    #     # forecast_df = initial_conditions.forecast_df.copy()

    #     # # Here you would implement the logic to step through the simulation.
    #     # # For demonstration purposes, let's assume we just return the forecast_df as is.

    #     # # Create an ExpenseForecastResult object with the forecast DataFrame
    #     # result = ExpenseForecastResult(
    #     #     unique_id=initial_conditions.unique_id,
    #     #     forecast_df=forecast_df,
    #     #     confirmed_df=initial_conditions.confirmed_df,
    #     #     deferred_df=initial_conditions.deferred_df,
    #     #     skipped_df=initial_conditions.skipped_df,
    #     #     milestone_set=initial_conditions.milestone_set,
    #     #     milestone_results=initial_conditions.milestone_results
    #     # )

    #     # return result
    #     raise NotImplementedError

    
    