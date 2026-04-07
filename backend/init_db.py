from database import Base, engine
from logger import configure_logging
from loguru import logger

configure_logging()

Base.metadata.create_all(bind=engine)
logger.info("Database initialized successfully.")
