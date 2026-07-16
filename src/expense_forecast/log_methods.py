

import logging
import sys
import threading
import time
from pathlib import Path
from colorama import init as colorama_init
from colorama import Fore
from colorama import Style
from tqdm.auto import tqdm

colorama_init()

BEGIN_RED = f"{Fore.RED}"
BEGIN_GREEN = f"{Fore.GREEN}"
BEGIN_YELLOW = f"{Fore.YELLOW}"
BEGIN_BLUE = f"{Fore.BLUE}"
BEGIN_MAGENTA = f"{Fore.MAGENTA}"
BEGIN_WHITE = f"{Fore.WHITE}"
BEGIN_CYAN = f"{Fore.CYAN}"
RESET_COLOR = f"{Style.RESET_ALL}"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_ROOT / "log"


class TqdmConsoleHandler(logging.StreamHandler):
    """Write log records without corrupting an active tqdm progress line."""

    def emit(self, record):
        if getattr(record, "file_only", False):
            return
        try:
            tqdm.write(self.format(record), file=self.stream)
        except Exception:
            self.handleError(record)


def project_log_file(logger_name: str) -> Path:
    """Return a project log path, creating the log directory if needed."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    return LOG_DIR / f"{logger_name}.log"


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

def setup_logger(
    logger_name,
    log_file=None,
    level=logging.DEBUG,
    *,
    console_level=logging.INFO,
    file_level=None,
):
    """
    @interface-report: ignore
    """
    logger_object = logging.getLogger(logger_name)
    file_level = level if file_level is None else file_level
    log_file = Path(log_file or project_log_file(logger_name))
    log_file.parent.mkdir(parents=True, exist_ok=True)

    managed_handlers = [
        handler for handler in logger_object.handlers
        if getattr(handler, "_expense_forecast_managed", False)
    ]
    if managed_handlers:
        for handler in managed_handlers:
            handler.setLevel(
                file_level if isinstance(handler, logging.FileHandler)
                else console_level
            )
        logger_object.setLevel(min(file_level, console_level))
        return logger_object

    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    console_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )
    file_handler = logging.FileHandler(log_file, mode="w")
    file_handler.setLevel(file_level)
    file_handler.setFormatter(file_formatter)
    file_handler._expense_forecast_managed = True
    stream_handler = TqdmConsoleHandler()
    stream_handler.setLevel(console_level)
    stream_handler.setFormatter(console_formatter)
    stream_handler._expense_forecast_managed = True

    logger_object.setLevel(min(file_level, console_level))
    logger_object.addHandler(file_handler)
    logger_object.addHandler(stream_handler)
    logger_object.propagate = False
    return logger_object


#
# setup_logger('root','main.log')
# col_logger = logging.getLogger('root')


def log_in_color_with_breadcrumbs(
    logger, color, level, msg, stack_depth=0, color_stack=[]
):
    """
    @interface-report: ignore
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


def log_in_color(
    logger,
    color,
    level,
    msg,
    stack_depth=0,
    *,
    user_facing=False,
    file_only=False,
):
    """
    @interface-report: ignore
    """
    return _log_in_color(
        logger,
        color,
        level,
        msg,
        stack_depth=stack_depth,
        user_facing=user_facing,
        file_only=file_only,
    )


def _log_in_color(
    logger,
    color,
    level,
    msg,
    *,
    stack_depth=0,
    user_facing=False,
    file_only=False,
):
    """Core colored logger with optional user-facing and file-only output."""
    color_codes = {
        "red": BEGIN_RED,
        "green": BEGIN_GREEN,
        "yellow": BEGIN_YELLOW,
        "blue": BEGIN_BLUE,
        "magenta": BEGIN_MAGENTA,
        "white": BEGIN_WHITE,
        "cyan": BEGIN_CYAN,
    }
    prefix = "" if user_facing else str(stack_depth).ljust(stack_depth * 4) + " "
    log_level = getattr(logging, str(level).upper(), None)
    if not isinstance(log_level, int):
        raise ValueError(f"Unsupported log level: {level}")
    color_code = color_codes.get(str(color).lower(), "")
    for line in str(msg).split("\n"):
        logger.log(
            log_level,
            color_code + prefix + line + RESET_COLOR,
            extra={"file_only": file_only},
        )


def log_user_message(logger, color, level, msg, *, file_only=False):
    """Log a colored phase message without an execution-depth prefix."""
    return _log_in_color(
        logger,
        color,
        level,
        msg,
        user_facing=True,
        file_only=file_only,
    )


class ForecastProgress:
    """Phase-local tqdm bar with periodic terminal refresh and log heartbeat."""

    def __init__(
        self,
        logger,
        phase,
        total,
        *,
        heartbeat_interval=10.0,
        stream=None,
        enabled=True,
    ):
        self.logger = logger
        self.phase = str(phase)
        self.total = max(1, int(total))
        self.heartbeat_interval = float(heartbeat_interval)
        self.stream = stream or sys.stderr
        self.enabled = bool(enabled)
        self.current_context = None
        self.started_at = None
        self._stop_event = threading.Event()
        self._thread = None
        self.bar = None

    @property
    def interactive(self):
        return bool(getattr(self.stream, "isatty", lambda: False)())

    def __enter__(self):
        self.started_at = time.monotonic()
        self.bar = tqdm(
            total=self.total,
            desc=self.phase,
            ascii=True,
            dynamic_ncols=True,
            file=self.stream,
            disable=not (self.enabled and self.interactive),
            bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} "
            "[{elapsed}] {postfix}",
            leave=True,
        )
        if self.enabled and self.heartbeat_interval > 0:
            self._thread = threading.Thread(
                target=self._heartbeat_loop,
                name=f"forecast-heartbeat-{self.phase}",
                daemon=True,
            )
            self._thread.start()
        return self

    def update(self, amount=1, *, context=None):
        if context is not None:
            self.current_context = str(context)
        if self.bar is not None:
            self.bar.update(amount)

    def refresh(self):
        if self.bar is not None and self.interactive:
            self.bar.refresh()

    def _heartbeat_message(self):
        elapsed = time.monotonic() - self.started_at
        completed = min(self.bar.n if self.bar is not None else 0, self.total)
        percentage = 100 * completed / self.total
        context = f" current={self.current_context}" if self.current_context else ""
        return (
            f"Heartbeat: phase={self.phase} elapsed={elapsed:.0f}s "
            f"progress={completed}/{self.total} ({percentage:.0f}%){context}"
        )

    def _heartbeat_loop(self):
        while not self._stop_event.wait(self.heartbeat_interval):
            message = self._heartbeat_message()
            if self.interactive and self.bar is not None:
                elapsed = time.monotonic() - self.started_at
                self.bar.set_postfix_str(f"working {elapsed:.0f}s", refresh=True)
                log_user_message(
                    self.logger, "cyan", "info", message, file_only=True
                )
            else:
                log_user_message(self.logger, "cyan", "info", message)

    def __exit__(self, exc_type, exc_value, traceback):
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=max(1.0, self.heartbeat_interval + 0.5))
        if self.bar is not None:
            if exc_type is None and self.bar.n < self.total:
                self.bar.update(self.total - self.bar.n)
            self.bar.close()
        return False


def display_test_result(logger, test_name, df1):
    """
    @interface-report: ignore
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
