
class ExpenseForecast:

    def __init__(self,accountset,budgetset):

        #TODO assert consistency between accountset and budgetset

        pass

    def computeForecast(self,start_date,num_days):
        raise NotImplementedError
        pass

    def plotOutput(self,output_path):
        raise NotImplementedError
        pass
