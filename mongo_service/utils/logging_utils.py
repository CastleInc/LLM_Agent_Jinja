"""Common utilities and logging setup"""
import logging
import sys
from contextvars import ContextVar

# Context variables for middleware
correlation_id_var: ContextVar[str] = ContextVar('correlation_id', default='default-correlation-id')
user_id_var: ContextVar[str] = ContextVar('user_id', default='default-user-id')
service_version_var: ContextVar[str] = ContextVar('service_version', default='unknown')


def setup_logging(level: int = logging.INFO):
    """Configure logging for the application"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Add custom filter to include correlation_id in logs
    class ContextFilter(logging.Filter):
        def filter(self, record):
            record.correlation_id = correlation_id_var.get()
            record.user_id = user_id_var.get()
            return True

    for handler in logging.root.handlers:
        handler.addFilter(ContextFilter())


def get_correlation_id() -> str:
    """Get current correlation ID"""
    return correlation_id_var.get()


def get_user_id() -> str:
    """Get current user ID"""
    return user_id_var.get()

