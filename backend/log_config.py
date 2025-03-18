import logging

logger = logging.Logger("concall_logger")
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
file_handler = logging.FileHandler(filename="logs/app.log")

formatter = logging.Formatter(
    fmt="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
)

stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

logger.addHandler(stream_handler)
logger.addHandler(file_handler)
