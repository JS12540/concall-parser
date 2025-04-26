import logging

logger = logging.getLogger("concall_parser")

def configure_logger(
    save_to_file: bool = False,
    logging_level: str = "INFO",
    log_file: str = "app.log"
) -> None:
    """Configure the global logger.
    
    Args:
        save_to_file: Whether to save logs to file
        logging_level: Logging level (DEBUG/INFO/WARNING/ERROR)
        log_file: Log file path when save_to_file is True
    """
    logger.handlers.clear()
    level = getattr(logging, logging_level.upper())
    logger.setLevel(level)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if save_to_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)