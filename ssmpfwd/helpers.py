import logging
import functools
import click
import os
import packaging.version
import subprocess
import sys
import boto3
from time import time
from typing import Callable
from ssmpfwd import __version__

logger = logging.getLogger(__name__)


def time_decorator(original_func: Callable) -> Callable:
    """
    Logs elapsed time that took for a function to return.

    Args:
        original_func: Callable

    Returns:
        Callable
    """

    def wrapper(*args, **kwargs):
        logger.info("[*] starting {}".format(original_func.__name__))
        start = time()
        result = original_func(*args, **kwargs)
        end = time()
        logger.info("{} took {:.2f} seconds to execute.".format(original_func.__name__, end - start))
        return result

    functools.wraps(original_func)
    return wrapper


def chunks(l, n):
    """
    Split list into chunks of a given size
    """
    return [l[i : i + n] for i in range(0, len(l), n)]


def configure_logging(logger_name: str, level: int):
    """
    Configure logging format and level.
    """
    streamHandler = logging.StreamHandler()
    formatter = logging.Formatter("[%(name)s] %(levelname)s: %(message)s")
    streamHandler.setFormatter(formatter)
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.addHandler(streamHandler)

    return logger


def verbose_debug_quiet(function):
    """Common Logging decorator to deal with parameter order limitations.
    Propagates given log level to the root logger.
    """

    def _set_level(ctx, param, value):
        if value:
            if ctx.obj:
                if ctx.obj.get("log_level") == value:
                    return value
                ctx.obj["log_level"] = value
                if __name__ == (os.path.splitext(__file__)[0].split(os.path.sep)[-1]):
                    root_logger = "root"
                else:
                    root_logger = __name__.split(".")[0]
                logging.getLogger(root_logger).setLevel(value)
                if value <= 20:
                    logger.info(f"Logger set to {logging.getLevelName(logger.getEffectiveLevel())}")
        return value

    verbose_debug_quiet_options = [
        click.option("--loglevel", "log_level", hidden=True, flag_value=logging.WARN, callback=_set_level, expose_value=False, is_eager=True, default=True),
        click.option(
            "--verbose",
            "-v",
            "log_level",
            flag_value=logging.INFO,
            callback=_set_level,
            expose_value=False,
            is_eager=True,
            help="Increase log_level level (INFO)",
        ),
        click.option(
            "--debug",
            "log_level",
            flag_value=logging.DEBUG,
            callback=_set_level,
            expose_value=False,
            is_eager=True,
            help="Increase log_level level (DEBUG)",
        ),
        click.option("--quiet", is_flag=True, help="Be quiet. Exit code is just enough for me."),
    ]

    functools.wraps(function)
    for option in reversed(verbose_debug_quiet_options):
        function = option(function)

    return function


def verify_plugin_version(version_required: str) -> bool:
    """
    Verify that a session-manager-plugin is installed
    and is of a required version or newer.
    """
    session_manager_plugin = "session-manager-plugin"

    try:
        result = subprocess.run([session_manager_plugin, "--version"], stdout=subprocess.PIPE)
        plugin_version = result.stdout.decode("ascii").strip()
        logger.debug(f"{session_manager_plugin} version {plugin_version}")

        if packaging.version.parse(plugin_version) >= packaging.version.parse(version_required):
            return True

        logger.error(f"session-manager-plugin version {plugin_version} is installed, {version_required} is required")
    except FileNotFoundError as e:
        logger.error(f"{session_manager_plugin} not installed")

    logger.error("Check out https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html for instructions")

    return False


def print_version(ctx: click.Context, param: str, value: str) -> None:
    if not value or ctx.resilient_parsing:
        return
    version_string = f"ssmpfwd/{__version__}"

    version_string += f" python/{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    version_string += f" boto3/{boto3.__version__}"
    click.echo(version_string)
    ctx.exit()
