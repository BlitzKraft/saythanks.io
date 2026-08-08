import logging


class IgnoreReloaderPollFilter(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        # Ignore only the Flask/Werkzeug reloader heartbeat, not normal app traffic.
        if 'GET / HTTP/1.1' in msg:
            return False
        return True


def configure_logging():
    """Configure the application logger once for all modules."""
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
