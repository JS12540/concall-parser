import logging

logger = logging.Logger()

stream_handler = logging.StreamHandler()
file_handler = logging.FileHandler(filename="logs/app.log")

formatter = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(message)s")

stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)
