"""Logging configuration for PT Manager"""

import logging
import sys
from typing import Optional
from datetime import datetime
from queue import Queue, Empty
from threading import Thread
import atexit

# Configure root logger for console output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)


# Map logger names to module names for database storage
MODULE_MAP = {
    'pt_manager.rss': 'rss',
    'pt_manager.delete': 'delete',
    'pt_manager.speed_limit': 'speed_limit',
    'pt_manager.u2_magic': 'u2_magic',
    'pt_manager.downloader': 'downloader',
    'pt_manager.scheduler': 'scheduler',
    'pt_manager.main': 'system',
    'pt_manager.auth': 'auth',
}


class DatabaseLogHandler(logging.Handler):
    """Custom handler that writes logs to the database asynchronously"""

    def __init__(self):
        super().__init__()
        self.log_queue = Queue()
        self._stop = False
        self._worker = Thread(target=self._process_logs, daemon=True)
        self._worker.start()
        atexit.register(self.close)

    def emit(self, record: logging.LogRecord):
        """Add log record to queue for async processing"""
        try:
            # Extract module name from logger name
            module = MODULE_MAP.get(record.name, 'system')
            if module == 'system' and record.name.startswith('pt_manager.'):
                module = record.name.replace('pt_manager.', '')

            log_entry = {
                'timestamp': datetime.utcnow(),
                'level': record.levelname,
                'module': module,
                'message': record.getMessage(),
                'details': str(record.exc_info) if record.exc_info else ''
            }
            self.log_queue.put(log_entry)
        except Exception:
            self.handleError(record)

    def _process_logs(self):
        """Worker thread to process log queue and write to database"""
        import time

        batch = []
        batch_size = 5  # Smaller batch for faster updates
        flush_interval = 2  # seconds - faster flush for real-time updates
        last_flush = time.time()

        while not self._stop:
            try:
                # Get log from queue with timeout
                try:
                    log_entry = self.log_queue.get(timeout=1)
                    batch.append(log_entry)
                except Empty:
                    pass

                # Flush batch if full or timeout reached
                current_time = time.time()
                if len(batch) >= batch_size or (batch and current_time - last_flush >= flush_interval):
                    self._flush_batch(batch)
                    batch = []
                    last_flush = current_time

            except Exception as e:
                print(f"Error processing log batch: {e}")

        # Flush remaining logs on shutdown
        if batch:
            self._flush_batch(batch)

    def _flush_batch(self, batch):
        """Write a batch of logs to the database with retry logic."""
        if not batch:
            return

        max_retries = 3
        retry_delay = 0.5

        for attempt in range(max_retries):
            try:
                from app.database import SessionLocal
                from app.models.models import LogRecord, LogLevel

                db = SessionLocal()
                try:
                    for entry in batch:
                        try:
                            level = LogLevel(entry['level']) if entry['level'] in LogLevel.__members__ else LogLevel.INFO
                        except (ValueError, KeyError):
                            level = LogLevel.INFO
                        record = LogRecord(
                            timestamp=entry['timestamp'],
                            level=level,
                            module=entry['module'],
                            message=entry['message'][:2000] if entry['message'] else '',
                            details=entry['details'][:2000] if entry['details'] else ''
                        )
                        db.add(record)
                    db.commit()
                    return  # Success
                except Exception as e:
                    db.rollback()
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(retry_delay * (attempt + 1))
                    else:
                        print(f"Error committing logs to database after {max_retries} attempts: {e}")
                finally:
                    db.close()
            except Exception as e:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay * (attempt + 1))
                else:
                    print(f"Error writing logs to database after {max_retries} attempts: {e}")

    def close(self):
        """Stop the worker thread"""
        self._stop = True
        if self._worker.is_alive():
            self._worker.join(timeout=5)
        super().close()


# Global database handler instance
_db_handler: Optional[DatabaseLogHandler] = None


def init_db_logging():
    """Initialize database logging handler"""
    global _db_handler
    if _db_handler is None:
        _db_handler = DatabaseLogHandler()
        _db_handler.setLevel(logging.INFO)
        # Add to pt_manager logger (parent of all app loggers)
        pt_logger = logging.getLogger('pt_manager')
        pt_logger.setLevel(logging.DEBUG)
        pt_logger.addHandler(_db_handler)

        # Add console handler so logs appear in docker logs
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        pt_logger.addHandler(console_handler)

        # Ensure logs propagate properly
        pt_logger.propagate = False  # Prevent duplicate logs to root
        print("Database logging handler initialized successfully")
        # Write a test log to verify it's working
        pt_logger.info("Database logging initialized and ready")


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (usually __name__)
        level: Optional logging level override

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    if level is not None:
        logger.setLevel(level)

    return logger


# Pre-configured loggers for common modules
def get_rss_logger() -> logging.Logger:
    return get_logger('pt_manager.rss')


def get_delete_logger() -> logging.Logger:
    return get_logger('pt_manager.delete')


def get_speed_limit_logger() -> logging.Logger:
    return get_logger('pt_manager.speed_limit')


def get_u2_magic_logger() -> logging.Logger:
    return get_logger('pt_manager.u2_magic')


def get_downloader_logger() -> logging.Logger:
    return get_logger('pt_manager.downloader')


def get_scheduler_logger() -> logging.Logger:
    return get_logger('pt_manager.scheduler')


def get_auth_logger() -> logging.Logger:
    return get_logger('pt_manager.auth')
