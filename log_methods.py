

from colorama import init as colorama_init
from colorama import Fore
from colorama import Style
colorama_init()

BEGIN_RED = f"{Fore.RED}"
BEGIN_GREEN = f"{Fore.GREEN}"
BEGIN_YELLOW = f"{Fore.YELLOW}"
BEGIN_BLUE = f"{Fore.BLUE}"
BEGIN_MAGENTA = f"{Fore.MAGENTA}"
BEGIN_WHITE = f"{Fore.WHITE}"
BEGIN_CYAN = f"{Fore.CYAN}"
RESET_COLOR = f"{Style.RESET_ALL}"

import logging

color_log_format = '%(asctime)s - %(levelname)-8s - %(message)s'
color_formatter = logging.Formatter(color_log_format)
col_ch = logging.StreamHandler()
col_ch.setFormatter(color_formatter)
col_ch.setLevel(logging.DEBUG)

col_logger = logging.getLogger(__name__)
col_logger.propagate = False
col_logger.handlers.clear()
col_logger.addHandler(col_ch)



def log_in_color(color,level,msg,stack_depth=0):

    if stack_depth == 0:
        left_prefix = ''
    else:
        left_prefix = ' '
    left_prefix = left_prefix.ljust(stack_depth*4,' ') + ' '

    for line in str(msg).split('\n'):

        if color.lower() == 'red':
            line = BEGIN_RED + left_prefix + line + RESET_COLOR
        elif color.lower() == 'green':
            line = BEGIN_GREEN + left_prefix + line + RESET_COLOR
        elif color.lower() == 'yellow':
            line = BEGIN_YELLOW + left_prefix + line + RESET_COLOR
        elif color.lower() == 'blue':
            line = BEGIN_BLUE + left_prefix + line + RESET_COLOR
        elif color.lower() == 'magenta':
            line = BEGIN_MAGENTA + left_prefix + line + RESET_COLOR
        elif color.lower() == 'white':
            line = BEGIN_WHITE + left_prefix + line + RESET_COLOR
        elif color.lower() == 'cyan':
            line = BEGIN_CYAN + left_prefix + line + RESET_COLOR

        if level == 'debug':
            col_logger.debug(line)
        elif level == 'warning':
            col_logger.warning(line)
        elif level == 'error':
            col_logger.error(line)
        elif level == 'info':
            col_logger.info(line)
        elif level == 'critical':
            col_logger.critical(line)
        else:
            print(line)


def display_test_result(test_name, df1):
    display_width = max([len(x) for x in df1.T.to_string().split('\n')])
    left_prefix = '# '

    lines_to_print = []
    test_passed = False

    lines_to_print.append(f"{Fore.BLUE}" + ''.ljust(display_width, '#') + f"{Style.RESET_ALL}")
    lines_to_print.append((left_prefix + test_name).ljust(display_width - 1, ' ') + '#')

    df1 = df1.reindex(sorted(df1.columns), axis=1)
    # print('DF PRE-ANALYSIS')
    # print(df1.T.to_string())
    index = 0
    columns_to_include = []
    #lines_to_highlight_red = []
    mismatch_column_count = 0
    for cname in df1.columns:
        if cname in ['Memo', 'Date']:
            columns_to_include.append(index)
        elif 'Diff' in cname:
            if sum(df1[cname]) != 0:
                #if we got diffs only, then only append the line itself
                columns_to_include.append(index)

                # we check to confirm that the lines before and after are the expected and actual
                if df1.columns[index - 1] == cname.split('(')[0] and cname.split('(')[0] == df1.columns[index + 1].split('(')[0]: #if the account name had parenthesis in it then this wil get fucked up
                    columns_to_include.append(index - 1)
                    columns_to_include.append(index + 1)

                mismatch_column_count = mismatch_column_count + 1

                #lines_to_highlight_red.append(index + 2)

        index = index + 1

    # print('COLUMNS TO INCLUDE')
    # print(str(columns_to_include))

    df1.Date = [ x.strftime('%Y-%m-%d') for x in df1.Date ]

    output_lines = df1.iloc[:, columns_to_include].T.to_string().split('\n')
    index = 0
    if mismatch_column_count > 0:
        for line in output_lines:
            #if index in lines_to_highlight_red:
            #    print(f"{Fore.RED}" + line + f"{Style.RESET_ALL}")
            #else:
            #    print(line)

            if '(Diff)' in line:
                lines_to_print.append(f"{Fore.RED}" + line + f"{Style.RESET_ALL}")
            else:
                lines_to_print.append(line)

            index = index + 1
        lines_to_print.append(left_prefix + 'RESULT: FAIL')
    else:
        lines_to_print.append(left_prefix + 'No mismatched columns to show')
        lines_to_print.append((left_prefix + 'RESULT: PASS').ljust(display_width - 1, ' ') + '#')
        test_passed = True

    lines_to_print.append(f"{Fore.BLUE}" + ''.ljust(display_width, '#') + f"{Style.RESET_ALL}")
    if not test_passed:
        for line in lines_to_print:
            print(line)
