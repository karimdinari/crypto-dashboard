import logging
from pythonjsonlogger import jsonlogger

def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger with the given name, configured with a console handler.

    Log format includes:
        - timestamp
        - log level
        - module
        - message
    Optional: JSON formatted logs if python-json-logger is used.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # You can adjust this to INFO in production

    if not logger.handlers:
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        # Choose format: JSON or simple text
        log_format = jsonlogger.JsonFormatter(
            '%(asctime)s %(levelname)s %(name)s %(module)s %(message)s'
        )
        console_handler.setFormatter(log_format)

        logger.addHandler(console_handler)

    return logger