import logging

logger = logging.Logger("concall_logger")
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
formatter = logging.Formatter(
    fmt="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
)

stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.INFO)
