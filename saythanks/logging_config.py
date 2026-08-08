import logging


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
    )

    # Suppress the noisy Werkzeug access log without disabling app DEBUG logs.
    logging.getLogger("werkzeug").setLevel(logging.INFO)
