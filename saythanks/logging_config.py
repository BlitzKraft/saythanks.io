import logging


class IgnoreReloaderPollFilter(logging.Filter):
    """
    A custom logging filter to suppress Flask/Werkzeug development
    server polling.
    This prevents the log file from being flooded with routine heartbeat
    or health-check requests when running the app in development mode.
    """

    def filter(self, record):
        """
        Determine if the specified log record should be processed.
        Args:
            record (logging.LogRecord): The log record being evaluated.
        Returns:
            bool: False if the log message contains a standard
                  root GET request (indicating a reloader poll),
                  True to allow all other traffic.
        """
        msg = record.getMessage()
        # Ignore only the Flask/Werkzeug reloader heartbeat,
        # not normal app traffic.
        if 'GET / HTTP/1.1' in msg:
            return False
        return True


def configure_logging():
    """
    Initialize and configure the application's root logger.

    Sets up file-based logging (appending to `Logfile.log`) with a specific
    message and date format. It checks for existing handlers to ensure the
    logger is only configured once, avoiding duplicate log entries. Finally,
    it attaches `IgnoreReloaderPollFilter` to the Werkzeug logger to keep
    development logs clean.
    """
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    logging.basicConfig(
        filename='Logfile.log',
        filemode='a',
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%d-%b-%y %H:%M:%S',
        level=logging.INFO,
    )

    # Keep Werkzeug request logging on, but suppress only the dev-server poll.
    logging.getLogger("werkzeug").addFilter(IgnoreReloaderPollFilter())
