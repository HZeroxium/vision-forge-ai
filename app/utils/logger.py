# app/utils/logger.py
# Logger configuration to set up logging for the application

import logging

def setup_logger():
    # Configure the root logger with desired settings
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
    logging.info("Logger is set up successfully")
