"""
Summary
-------

Description
-----------

Contract
--------

@interface-report: show
"""


import logging
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


# https://stackoverflow.com/questions/6796492/temporarily-redirect-stdout-stderr
# class RedirectStdStreams(object):
#     def __init__(self, stdout=None, stderr=None):
#         self._stdout = stdout or sys.stdout
#         self._stderr = stderr or sys.stderr
#
#     def __enter__(self):
#         self.old_stdout, self.old_stderr = sys.stdout, sys.stderr
#         self.old_stdout.flush(); self.old_stderr.flush()
#         sys.stdout, sys.stderr = self._stdout, self._stderr
#
#     def __exit__(self, exc_type, exc_value, traceback):
#         self._stdout.flush(); self._stderr.flush()
#         sys.stdout = self.old_stdout
#         sys.stderr = self.old_stderr

#TODO manual review of log_methods.setup_logger docstring
def setup_logger(logger_name, log_file, level=logging.DEBUG):
    """
    TODO one-line description of log_methods.setup_logger.

    TODO multi-line description of log_methods.setup_logger.
    TODO explain how log_methods.setup_logger participates in this module.
    TODO document important state, validation, or serialization behavior.

    Parameters
    ----------
    logger_name : object
        TODO one-line description of log_methods.setup_logger.logger_name.

    log_file : object
        TODO one-line description of log_methods.setup_logger.log_file.

    level : object
        TODO one-line description of log_methods.setup_logger.level.

    Returns
    -------
    object
        TODO one-line description of return value of log_methods.setup_logger.

    Contract
    --------
    - #TODO contract lines for log_methods.setup_logger.
    - #TODO document exceptions, mutations, and precision assumptions for log_methods.setup_logger.

    @interface-report: show
    """
    logger_object = logging.getLogger(logger_name)
    formatter = logging.Formatter("%(asctime)s - %(levelname)-8s - %(message)s")
    fileHandler = logging.FileHandler(log_file, mode="w")
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)

    logger_object.setLevel(level)
    logger_object.handlers.clear()
    logger_object.addHandler(fileHandler)
    logger_object.addHandler(streamHandler)
    logger_object.propagate = False
    return logger_object


#
# setup_logger('root','main.log')
# col_logger = logging.getLogger('root')


#TODO manual review of log_methods.log_in_color_with_breadcrumbs docstring
def log_in_color_with_breadcrumbs(
    logger, color, level, msg, stack_depth=0, color_stack=[]
):
    """
    TODO one-line description of log_methods.log_in_color_with_breadcrumbs.

    TODO multi-line description of log_methods.log_in_color_with_breadcrumbs.
    TODO explain how log_methods.log_in_color_with_breadcrumbs participates in this module.
    TODO document important state, validation, or serialization behavior.

    Parameters
    ----------
    logger : object
        TODO one-line description of log_methods.log_in_color_with_breadcrumbs.logger.

    color : object
        TODO one-line description of log_methods.log_in_color_with_breadcrumbs.color.

    level : object
        TODO one-line description of log_methods.log_in_color_with_breadcrumbs.level.

    msg : object
        TODO one-line description of log_methods.log_in_color_with_breadcrumbs.msg.

    stack_depth : object
        TODO one-line description of log_methods.log_in_color_with_breadcrumbs.stack_depth.

    color_stack : object
        TODO one-line description of log_methods.log_in_color_with_breadcrumbs.color_stack.

    Returns
    -------
    object
        TODO one-line description of return value of log_methods.log_in_color_with_breadcrumbs.

    Contract
    --------
    - #TODO contract lines for log_methods.log_in_color_with_breadcrumbs.
    - #TODO document exceptions, mutations, and precision assumptions for log_methods.log_in_color_with_breadcrumbs.

    @interface-report: show
    """
    left_prefix = " "

    if len(color_stack) > 0:
        for c in color_stack:
            if c.lower() == "red":
                left_prefix += BEGIN_RED + ".".ljust(4) + RESET_COLOR
            elif c.lower() == "green":
                left_prefix += BEGIN_GREEN + ".".ljust(4) + RESET_COLOR
            elif c.lower() == "yellow":
                left_prefix += BEGIN_YELLOW + ".".ljust(4) + RESET_COLOR
            elif c.lower() == "blue":
                left_prefix += BEGIN_BLUE + ".".ljust(4) + RESET_COLOR
            elif c.lower() == "magenta":
                left_prefix += BEGIN_MAGENTA + ".".ljust(4) + RESET_COLOR
            elif c.lower() == "white":
                left_prefix += BEGIN_WHITE + ".".ljust(4) + RESET_COLOR
            elif c.lower() == "cyan":
                left_prefix += BEGIN_CYAN + ".".ljust(4) + RESET_COLOR
    else:
        left_prefix = left_prefix.ljust(stack_depth * 4, " ") + " "

    level = level.lower()
    for line in str(msg).split("\n"):
        if color.lower() == "red":
            line = (
                BEGIN_RED
                + str(stack_depth)
                + RESET_COLOR
                + left_prefix
                + BEGIN_RED
                + line
            )
        elif color.lower() == "green":
            line = (
                BEGIN_GREEN
                + str(stack_depth)
                + RESET_COLOR
                + left_prefix
                + BEGIN_GREEN
                + line
                + RESET_COLOR
            )
        elif color.lower() == "yellow":
            line = (
                BEGIN_YELLOW
                + str(stack_depth)
                + RESET_COLOR
                + left_prefix
                + BEGIN_YELLOW
                + line
                + RESET_COLOR
            )
        elif color.lower() == "blue":
            line = (
                BEGIN_BLUE
                + str(stack_depth)
                + RESET_COLOR
                + left_prefix
                + BEGIN_BLUE
                + line
                + RESET_COLOR
            )
        elif color.lower() == "magenta":
            line = (
                BEGIN_MAGENTA
                + str(stack_depth)
                + RESET_COLOR
                + left_prefix
                + BEGIN_MAGENTA
                + line
                + RESET_COLOR
            )
        elif color.lower() == "white":
            line = (
                BEGIN_WHITE
                + str(stack_depth)
                + RESET_COLOR
                + left_prefix
                + BEGIN_WHITE
                + line
                + RESET_COLOR
            )
        elif color.lower() == "cyan":
            line = (
                BEGIN_CYAN
                + str(stack_depth)
                + RESET_COLOR
                + left_prefix
                + BEGIN_CYAN
                + line
                + RESET_COLOR
            )

        if level == "debug":
            logger.debug(line)
        elif level == "warning":
            logger.warning(line)
        elif level == "error":
            logger.error(line)
        elif level == "info":
            logger.info(line)
        elif level == "critical":
            logger.critical(line)
        else:
            print(line)


#TODO manual review of log_methods.log_in_color docstring
def log_in_color(logger, color, level, msg, stack_depth=0):
    """
    TODO one-line description of log_methods.log_in_color.

    TODO multi-line description of log_methods.log_in_color.
    TODO explain how log_methods.log_in_color participates in this module.
    TODO document important state, validation, or serialization behavior.

    Parameters
    ----------
    logger : object
        TODO one-line description of log_methods.log_in_color.logger.

    color : object
        TODO one-line description of log_methods.log_in_color.color.

    level : object
        TODO one-line description of log_methods.log_in_color.level.

    msg : object
        TODO one-line description of log_methods.log_in_color.msg.

    stack_depth : object
        TODO one-line description of log_methods.log_in_color.stack_depth.

    Returns
    -------
    object
        TODO one-line description of return value of log_methods.log_in_color.

    Contract
    --------
    - #TODO contract lines for log_methods.log_in_color.
    - #TODO document exceptions, mutations, and precision assumptions for log_methods.log_in_color.

    @interface-report: show
    """
    left_prefix = str(stack_depth)
    left_prefix = left_prefix.ljust(stack_depth * 4, " ") + " "
    level = level.lower()

    for line in str(msg).split("\n"):

        if color.lower() == "red":
            line = BEGIN_RED + left_prefix + line + RESET_COLOR
        elif color.lower() == "green":
            line = BEGIN_GREEN + left_prefix + line + RESET_COLOR
        elif color.lower() == "yellow":
            line = BEGIN_YELLOW + left_prefix + line + RESET_COLOR
        elif color.lower() == "blue":
            line = BEGIN_BLUE + left_prefix + line + RESET_COLOR
        elif color.lower() == "magenta":
            line = BEGIN_MAGENTA + left_prefix + line + RESET_COLOR
        elif color.lower() == "white":
            line = BEGIN_WHITE + left_prefix + line + RESET_COLOR
        elif color.lower() == "cyan":
            line = BEGIN_CYAN + left_prefix + line + RESET_COLOR

        if level == "debug":
            logger.debug(line)
        elif level == "warning":
            logger.warning(line)
        elif level == "error":
            logger.error(line)
        elif level == "info":
            logger.info(line)
        elif level == "critical":
            logger.critical(line)
        else:
            print(line)


#TODO manual review of log_methods.display_test_result docstring
def display_test_result(logger, test_name, df1):
    """
    TODO one-line description of log_methods.display_test_result.

    TODO multi-line description of log_methods.display_test_result.
    TODO explain how log_methods.display_test_result participates in this module.
    TODO document important state, validation, or serialization behavior.

    Parameters
    ----------
    logger : object
        TODO one-line description of log_methods.display_test_result.logger.

    test_name : object
        TODO one-line description of log_methods.display_test_result.test_name.

    df1 : object
        TODO one-line description of log_methods.display_test_result.df1.

    Returns
    -------
    object
        TODO one-line description of return value of log_methods.display_test_result.

    Contract
    --------
    - #TODO contract lines for log_methods.display_test_result.
    - #TODO document exceptions, mutations, and precision assumptions for log_methods.display_test_result.

    @interface-report: show
    """
    display_width = max([len(x) for x in df1.T.to_string().split("\n")])
    # display_width = 120
    left_prefix = "# "

    lines_to_print = []
    test_passed = False

    lines_to_print.append(
        f"{Fore.BLUE}" + "".ljust(display_width, "#") + f"{Style.RESET_ALL}"
    )
    lines_to_print.append((left_prefix + test_name).ljust(display_width - 1, " ") + "#")

    df1 = df1.reindex(sorted(df1.columns), axis=1)
    # print('DF PRE-ANALYSIS')
    # print(df1.T.to_string())
    index = 0
    columns_to_include = []
    # lines_to_highlight_red = []
    mismatch_column_count = 0
    for cname in df1.columns:
        if cname in ["Memo Directives", "Memo", "Date"]:
            columns_to_include.append(index)
        elif "Diff" in cname:
            if sum(df1[cname]) != 0:
                # if we got diffs only, then only append the line itself
                columns_to_include.append(index)

                # we check to confirm that the lines before and after are the expected and actual
                if (
                    df1.columns[index - 1] == cname.split("(")[0]
                    and cname.split("(")[0] == df1.columns[index + 1].split("(")[0]
                ):  # if the account name had parenthesis in it then this wil get fucked up
                    columns_to_include.append(index - 1)
                    columns_to_include.append(index + 1)

                mismatch_column_count = mismatch_column_count + 1

                # lines_to_highlight_red.append(index + 2)

        index = index + 1

    # print('COLUMNS TO INCLUDE')
    # print(str(columns_to_include))

    df1.Date = [x.strftime("%Y-%m-%d") for x in df1.Date]

    output_lines = df1.iloc[:, columns_to_include].T.to_string().split("\n")
    index = 0
    if mismatch_column_count > 0:
        for line in output_lines:
            # if index in lines_to_highlight_red:
            #    print(f"{Fore.RED}" + line + f"{Style.RESET_ALL}")
            # else:
            #    print(line)

            if "(Diff)" in line:
                lines_to_print.append(f"{Fore.RED}" + line + f"{Style.RESET_ALL}")
            else:
                lines_to_print.append(line)

            index = index + 1
        lines_to_print.append(left_prefix + "RESULT: FAIL")
    else:
        lines_to_print.append(left_prefix + "No mismatched columns to show")
        lines_to_print.append(
            (left_prefix + "RESULT: PASS").ljust(display_width - 1, " ") + "#"
        )
        test_passed = True

    lines_to_print.append(
        f"{Fore.BLUE}" + "".ljust(display_width, "#") + f"{Style.RESET_ALL}"
    )
    if not test_passed:
        for line in lines_to_print:
            log_in_color(logger, "white", "debug", line)
