MAINPREFIX = ""

def output(*args: any, doPrint: bool | int = True, customPrefix: str = "") -> None:
	"""dont use this func, use info() instead... :)
fr: full flemme de faire la docstring, jean neymar... ... """
	if doPrint: print(MAINPREFIX + customPrefix, *args)

INFO = True
def info(*args: any, bypass: bool | int = False) -> None:
	"""Print informations"""
	output(*args, doPrint = bypass or INFO, customPrefix = "[INFO]")

DEBUG = True
def debug(*args: any, bypass: bool | int = False) -> None:
	"""Print debug messages"""
	output(*args, doPrint = bypass or DEBUG, customPrefix = "[DEBUG]")

WARN = True
def warn(*args: any, bypass: bool | int = False) -> None:
	"""Print warn messages"""
	output(*args, doPrint = bypass or WARN, customPrefix = "[WARN]")

def warning(*args: any, **kwargs) -> None:
	"""Alias for warn()"""
	warn(*args, **kwargs)

ERROR = True
def error(*args: any, bypass: bool | int = False, fatal: bool | int = False) -> None:
	"""Print error messages"""
	output(*args, doPrint = bypass or ERROR, customPrefix = "[FATAL]" if fatal else "[ERROR]")

def fatal(*args: any, **kwargs) -> None:
	"""Alias for error()"""
	error(*args, **kwargs, fatal = True)
