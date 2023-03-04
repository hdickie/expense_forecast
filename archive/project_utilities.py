import datetime, pandas as pd, subprocess, os, pyodbc, re, prefect, requests as req
import mysql
import mysql.connector

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

    if test_suite_name != '':
        results = subprocess.run(['python', '-m', 'unittest', 'discover'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    else:
        results = subprocess.run(['python', '-m', 'unittest', 'discover',test_suite_name], stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT)
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
    
    <link rel="stylesheet" type="text/css" href="build/html/static/classic.css" />
    </head>
    <body>
    
    Test Plots
    <br>
    Plot 1: %s <br> <img src="%s"> <br> <br>
    Plot 2: %s <br> <img src="%s"> <br> <br>
    Plot 3: %s <br> <img src="%s"> <br> <br>
    Plot 4: %s <br> <img src="%s"> <br> <br>
    Plot 5: %s <br> <img src="%s"> <br> <br>
    
    %s
    
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
        <title>Expense Forecast</title>
        <link rel="stylesheet" type="text/css" href="build/html/static/classic.css" />
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

           #print('Path:'+str(os.path.join(root, name)))
           # this records paths to refactor that start with "./", which is used for file operations
           paths_to_replace[os.path.join(root, name)] = os.path.join(root, name).replace('_','')

           #this records paths to refactor without the "./", which is used in html js and css elements
           paths_to_replace[os.path.join(root, name).replace('./', '').replace('_build/html/', '')] = os.path.join(root, name).replace('_', '').replace('./', '')
           # print('Path:' + str(os.path.join(root, name)).replace('_', '').replace('./', ''))

   for root, dirs, files in os.walk("./_build/html/_static/", topdown=False):
       for name in files:
           # skip hidden folders
           if '.\.' in root:
               continue

           #print('Path:' + str(os.path.join(root, name)))
           # this records paths to refactor that start with "./"
           paths_to_replace[os.path.join(root, name)] = os.path.join(root, name).replace('_', '')
           # print(str(os.path.join(root, name)) + ' -> ' + str(os.path.join(root, name)).replace('_', ''))

           #this records paths to refactor without the "./", which is used in html js and css elements
           #Since those elements refer to other files relative to ./build/html/, we delete the aforementioned path prefix
           paths_to_replace[os.path.join(root, name).replace('./', '').replace('_build/html/', '')] = os.path.join(root, name).replace('_', '').replace('build/html/', '').replace('./', '')
           # print( str(os.path.join(root, name).replace('./', '').replace('_build/html/', '')) + ' -> ' + str(os.path.join(root, name)).replace('_', '').replace('build/html/', '').replace('./', ''))

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
               # for file_line in file_lines:
               #     if name == 'index.html':
               #         if str(path_tuple[1]) in file_line:
               #             print(str(path_tuple[0]) + ' -> ' + str(path_tuple[1]))
               #     file_line.replace(path_tuple[0],path_tuple[1])
               file_lines = [file_line.replace(path_tuple[0],path_tuple[1]) for file_line in file_lines]

           #print('Writing: ' + str(os.path.join(root, name).replace('_', '')))
           with open(os.path.join(root, name).replace('_',''), 'w', encoding="utf8") as f:

               f.writelines(file_lines)

   for root, dirs, files in os.walk("./_build/html/_static/", topdown=True):
       for name in files:

           # only refactor certain file types
           if ('.txt' in name or '.css' in name or '.html' in name or '.js' in name) and 'venv' not in root:
               pass
           else:
               continue

           # print(name)
           #print('Reading: ' + str(os.path.join(root, name)))
           with open(os.path.join(root, name), 'r', encoding="utf8") as f:
               file_lines = f.readlines()

           # print(file_lines)
           # print(name)
           for path_tuple in paths_to_replace.items():
               file_lines = [file_line.replace(path_tuple[1], path_tuple[0]) for file_line in file_lines]

           #print('Writing: ' + str(os.path.join(root, name).replace('_', '')))
           with open(os.path.join(root, name).replace('_', ''), 'w', encoding="utf8") as f:
               f.writelines(file_lines)


def trello_api_test():
    api_personal_key="34ac57600bcd22547628e5099c6bde15"
    api_token = "31af6b3f449284940b226e34a8754301eecc0bcf64ef87d13e672c63c542493c"
    r = req.get("https://api.trello.com/1/members/me/boards?key=%s&token=%s" % (api_personal_key, api_token))
    print(r.text)

def mssql_database_connection_test():
    cnxn_str = ("Driver={SQL Server Native Client 11.0};"
            "Server=localhost\SQLEXPRESS;"
            "Database=master;"
            "Trusted_Connection=yes;")
    cnxn = pyodbc.connect(cnxn_str)
    cursor = cnxn.cursor()
    cursor.execute("create table test_table AS (select * from sys.tables );")
    data = pd.read_sql("select * from sys.tables", cnxn)
    print(data)

def remote_mysql_database_connection_test():
    # cnxn_str = ("Driver={SQL Server Native Client 11.0};",
    #             "Server=cpanel-box5161.bluehost.com:3306;",
    #             user="admin",
    #             password="triplethickroofofnaturalcedarshingles",
    #             "Database=humedick_sandbox;"
    #             "Trusted_Connection=yes;")
    # cnxn = pyodbc.connect(cnxn_str)
    # cursor = cnxn.cursor()
    # cursor.execute("create table test_table AS (select * from sys.tables );")
    # data = pd.read_sql("select * from sys.tables", cnxn)
    # print(data)

    mydb = mysql.connector.connect(
        host="cpanel-box5161.bluehost.com",
        user="admin",
        password="triplethickroofofnaturalcedarshingles"
    )

    mycursor = mydb.cursor()

    mycursor.execute("select * from sandbox.accounts")
    for x in mycursor:
        print(x)

    #not working, but i think i can work around this

def plot_expected_vs_actual_for_each_account(expected_df,actual_df,label='',output_folder=','):

    #no formal input validation just this check
    assert expected_df.shape[1] == actual_df.shape[1] #if error, then diff number of columns

    raise NotImplementedError

import paramiko
def ssh_test():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) #this is not secure and should be changed

    # k = paramiko.RSAKey.from_private_key_file(keyfilename)
    # # OR k = paramiko.DSSKey.from_private_key_file(keyfilename)
    #
    # ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # ssh.connect(hostname=host, username=user, pkey=k)



    ssh.connect("humedickie.com", username="humedick", password="Eatsh1tandD1E!")
    pass

def send_text_to_my_phone(msg):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("humedickie.com", username="humedick", password="Eatsh1tandD1E!")
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("echo \""+msg+"\" > msg.txt")
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("mail 5303836572@mypixmessages.com < msg.txt")

    # it works!

if __name__ == "__main__":
    pass
    #remote_mysql_database_connection_test()
    # copy_sphinx_docs_to_path_without_underscore()

    #trello_api_test()
    #database_connection_test()

    #test_result__string = run_tests()
    # plot_paths__dict = plot_all()
    #generate_HTML_debug_report(test_result__string)
    # generate_HTML_expense_forecast_report()
