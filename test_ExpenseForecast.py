import unittest
import ExpenseForecast


class TestExpenseForecastMethods(unittest.TestCase):

    def test_ExpenseForecast_Constructor(self):

        self.assertIsNotNone(ExpenseForecast.ExpenseForecast())
