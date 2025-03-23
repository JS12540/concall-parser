import logging

logger = logging.Logger("concall_logger")
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
debug_file_handler = logging.FileHandler(filename="logs/debug.log", mode="w")
info_file_handler = logging.FileHandler(filename="logs/info.log", mode="w")
error_file_handler = logging.FileHandler(filename="logs/error.log", mode="w")

formatter = logging.Formatter(
    fmt="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
)

stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.INFO)
debug_file_handler.setFormatter(formatter)
debug_file_handler.setLevel(logging.DEBUG)
info_file_handler.setFormatter(formatter)
info_file_handler.setLevel(logging.INFO)
error_file_handler.setFormatter(formatter)
error_file_handler.setLevel(logging.ERROR)

logger.addHandler(stream_handler)
logger.addHandler(debug_file_handler)
logger.addHandler(info_file_handler)
logger.addHandler(error_file_handler)
