import sys
from datetime import datetime


class Logger:
    def _log(self, level: str, message: str, *args) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        prefixes = {
            "debug": "DEBUG",
            "info": " INFO",
            "success": "  OK ",
            "warn": " WARN",
            "error": " ERR ",
            "command": "  CMD",
        }
        prefix = prefixes.get(level, "LOG ")
        formatted = " ".join(str(a) for a in args) if args else ""
        full = f"{ts} [{prefix}] {message} {formatted}".strip()
        stream = sys.stderr if level == "error" else sys.stdout
        try:
            stream.write(full + "\n")
        except UnicodeEncodeError:
            stream.write(full.encode("ascii", errors="replace").decode("ascii") + "\n")
        stream.flush()

    def debug(self, message: str, *args) -> None:
        self._log("debug", message, *args)

    def info(self, message: str, *args) -> None:
        self._log("info", message, *args)

    def success(self, message: str, *args) -> None:
        self._log("success", message, *args)

    def warn(self, message: str, *args) -> None:
        self._log("warn", message, *args)

    def error(self, message: str, *args) -> None:
        self._log("error", message, *args)

    def command(self, message: str, *args) -> None:
        self._log("command", message, *args)


logger = Logger()
