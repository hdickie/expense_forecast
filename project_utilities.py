import datetime, pandas as pd, subprocess, os, pyodbc, re, prefect


def generate_date_sequence(start_date_YYYYMMDD,num_days,cadence):
    """ A wrapper for pd.date_range intended to make code easier to read.

    #todo write project_utilities.generate_date_sequence() doctests
    """

    start_date = datetime.datetime.strptime(start_date_YYYYMMDD,'%Y%m%d')
    end_date = start_date + datetime.timedelta(days=num_days)

    if cadence.lower() == "once":
        return pd.Series(start_date)
    elif cadence.lower() == "daily":
        return_series = pd.date_range(start_date,end_date,freq='D')
    elif cadence.lower() == "weekly":
        return_series = pd.date_range(start_date,end_date,freq='W')
    elif cadence.lower() == "biweekly":
        return_series = pd.date_range(start_date,end_date,freq='2W')
    elif cadence.lower() == "monthly":

        day_delta = int(start_date.strftime('%d'))-1
        first_of_each_relevant_month = pd.date_range(start_date,end_date,freq='MS')

        return_series = first_of_each_relevant_month + datetime.timedelta(days=day_delta)
    elif cadence.lower() == "quarterly":
        #todo check if this needs an adjustment like the monthly case did
        return_series = pd.date_range(start_date,end_date,freq='Q')
    elif cadence.lower() == "yearly":
        # todo check if this needs an adjustment like the monthly case did
        return_series = pd.date_range(start_date,end_date,freq='Y')

    return return_series

def run_tests(test_suite_name=''):

    #using the verbose version would give more detailed output, but i would rather spend time on other stuff
    #results = subprocess.run(['python','-m','unittest','discover','-v'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    start_ts = datetime.datetime.now()
    results = subprocess.run(['python', '-m', 'unittest', 'discover'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    end_ts = datetime.datetime.now()

    time_elapsed = end_ts - start_ts

    literal_test_result_string = results.stdout
    test_result_lines = str(literal_test_result_string).split('\\r\\n')

    test_result_summary = test_result_lines[0]
    passing_test_count = 0
    failing_test_count = 0
    error_test_count = 0
    for i in range(2,len(test_result_summary)):
        character = test_result_summary[i]

        if character == ".":
            passing_test_count += 1
        elif character == "F":
            failing_test_count += 1
        elif character == "E":
            error_test_count += 1
        else:
            print('edge case')
            print('value was:'+str(character))


    error_lines = []
    for i in range(0,len(test_result_lines)):
        line = test_result_lines[i]
        if 'ERROR' in line:
            error_lines.append(line)

    return_string = ""
    return_string += ''.ljust(15,'#')+"\n"
    return_string += '#  PASS: '+str(passing_test_count)+"\n"
    return_string += '#  FAIL: '+str(failing_test_count)+"\n"
    return_string += '# ERROR: '+str(error_test_count)+"\n"
    return_string += '# TOTAL: '+str(passing_test_count + failing_test_count + error_test_count)+"\n"
    return_string += ''.ljust(15, '#')+"\n"
    return_string += 'Time Elapsed: '+str(time_elapsed)+"\n"
    return_string += ''.ljust(15,'#')+"\n"
    for error_line in error_lines:
        return_string += error_line+"\n"
    return_string += ''.ljust(15, '#')+"\n"

    #for line in test_result_lines:
    #    print(line)

    return return_string


def plot_all():
    plot_name_to_path__dict = {}

    return plot_name_to_path__dict

def generate_HTML_debug_report(test_result__string,plot_paths__dict={}):

    test_result_text = test_result__string.replace('\n','<br>')

    plot_1_name = "Account Type Totals"
    plot_1_path = "account_type_totals.png"
    plot_2_name = ""
    plot_2_path = ""
    plot_3_name = ""
    plot_3_path = ""
    plot_4_name = ""
    plot_4_path = ""
    plot_5_name = ""
    plot_5_path = ""

    template = """
    <!doctype html>
    <html>
    <head>
    <title>expense_forecast debug summary</title>
    <meta name="description" content="Our first page">
    <meta name="keywords" content="html tutorial template">
    </head>
    <body>
    
    Test Plots
    <br>
    Plot 1: %s <br> <img src="%s"> <br> <br>
    Plot 2: %s <br> <img src="%s"> <br> <br>
    Plot 3: %s <br> <img src="%s"> <br> <br>
    Plot 4: %s <br> <img src="%s"> <br> <br>
    Plot 5: %s <br> <img src="%s"> <br> <br>
    
    <br>
    </body>
    </html>
    """

    page_html = template % (plot_1_name,
                            plot_1_path,
                            plot_2_name,
                            plot_2_path,
                            plot_3_name,
                            plot_3_path,
                            plot_4_name,
                            plot_4_path,
                            plot_5_name,
                            plot_5_path,
                            test_result_text)
    with open('expense_forecast_debug_summary.html','w') as f:
        f.writelines(page_html)

def generate_HTML_expense_forecast_report():
    plot_1_path = "account_type_totals.png"

    template = """
        <!doctype html>
        <html>
        <head>
        <title>expense_forecast debug summary</title>
        <meta name="description" content="Our first page">
        <meta name="keywords" content="html tutorial template">
        </head>
        <body>
        <img src="%s">
        </body>
        </html>
        """

    page_html = template % (plot_1_path)

    with open('expense_forecast_summary.html','w') as f:
        f.writelines(page_html)

def update_sphinx_docs():
    subprocess.run(['make','html'])

def copy_sphinx_docs_to_path_without_underscore():
   #first, we read through the files we want to move to find all the paths we are going to refactor
   paths_to_replace = {}
   print('Paths to refactor:')
   for root, dirs, files in os.walk("./_build/html/", topdown=False):
       for name in files:

           # skip hidden folders
           if '.\.' in root:
               continue

           print(os.path.join(root, name))

           #this records absolute paths to refactor
           paths_to_replace[os.path.join(root, name)] = os.path.join(root, name).replace('_','')

   for root, dirs, files in os.walk("./_build/html/_static/", topdown=False):
       for name in files:
           # skip hidden folders
           if '.\.' in root:
               continue

           print(os.path.join(root, name))

           # this records absolute paths to refactor
           paths_to_replace[os.path.join(root, name)] = os.path.join(root, name).replace('_', '')



           #shutil.copyfile(os.path.join(root, name),os.path.join(root, name).replace('_',''))

   # now that the files are at the new location, refactor with the new paths
   print('Attempting refactor')
   for root, dirs, files in os.walk("./_build/html/", topdown=True):
       for name in files:

           #only refactor certain file types
           if ('.txt' in name or '.css' in name or '.html' in name or '.js' in name) and 'venv' not in root:
               pass
           else:
               continue



           #print(name)
           #print('Reading: ' + str(os.path.join(root, name)))
           with open(os.path.join(root, name),'r', encoding="utf8") as f:
               file_lines = f.readlines()

           #print(file_lines)
           for path_tuple in paths_to_replace.items():
               file_lines = [file_line.replace(path_tuple[1],path_tuple[0]) for file_line in file_lines]

           #print('Writing: ' + str(os.path.join(root, name).replace('_', '')))
           with open(os.path.join(root, name).replace('_',''), 'w', encoding="utf8") as f:

               f.writelines(file_lines)

   for root, dirs, files in os.walk("./_build/html/_static/", topdown=True):
       for name in files:

           # only refactor certain file types\
           if ('.txt' in name or '.css' in name or '.html' in name or '.js' in name) and 'venv' not in root:
               pass
           else:
               continue

           # print(name)
           #print('Reading: ' + str(os.path.join(root, name)))
           with open(os.path.join(root, name), 'r', encoding="utf8") as f:
               file_lines = f.readlines()

           # print(file_lines)
           for path_tuple in paths_to_replace.items():
               file_lines = [file_line.replace(path_tuple[1], path_tuple[0]) for file_line in file_lines]

           #print('Writing: ' + str(os.path.join(root, name).replace('_', '')))
           with open(os.path.join(root, name).replace('_', ''), 'w', encoding="utf8") as f:
               f.writelines(file_lines)




if __name__ == "__main__":
    copy_sphinx_docs_to_path_without_underscore()
    # cnxn_str = ("Driver={SQL Server Native Client 11.0};"
    #         "Server=localhost\SQLEXPRESS;"
    #         "Database=master;"
    #         "Trusted_Connection=yes;")
    # cnxn = pyodbc.connect(cnxn_str)
    # cursor = cnxn.cursor()
    # data = pd.read_sql("select * from sys.tables", cnxn)
    # print(data)

    # test_result__string = run_tests()
    # plot_paths__dict = plot_all()
    # generate_HTML_debug_report(test_result__string)
    # generate_HTML_expense_forecast_report()