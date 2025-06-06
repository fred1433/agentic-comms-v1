import sys
import logging
from typing import Any, Dict
import structlog
import json
from datetime import datetime

from config import settings

def setup_logging():
    """Setup structured logging with structlog"""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            # Add timestamp
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            add_timestamp,
            add_service_context,
            # JSON formatting for production, pretty for development
            structlog.dev.ConsoleRenderer() if settings.DEBUG else structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def add_timestamp(logger, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add timestamp to log entries"""
    event_dict["timestamp"] = datetime.utcnow().isoformat()
    return event_dict

def add_service_context(logger, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add service context to log entries"""
    event_dict.update({
        "service": "agentic-comms-api",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    })
    return event_dict

class RequestLoggingMiddleware:
    """Middleware to log HTTP requests"""
    
    def __init__(self, app):
        self.app = app
        
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            logger = structlog.get_logger()
            
            # Log request start
            start_time = datetime.utcnow()
            
            # Get request info
            method = scope["method"]
            path = scope["path"]
            client_ip = scope.get("client", ["unknown", None])[0]
            
            logger.info(
                "Request started",
                method=method,
                path=path,
                client_ip=client_ip
            )
            
            # Process request
            async def log_response(message):
                if message["type"] == "http.response.start":
                    status_code = message["status"]
                    duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                    
                    logger.info(
                        "Request completed",
                        method=method,
                        path=path,
                        status_code=status_code,
                        duration_ms=round(duration_ms, 2),
                        client_ip=client_ip
                    )
                
                await send(message)
            
            await self.app(scope, receive, log_response)
        else:
            await self.app(scope, receive, send)

def log_performance(func_name: str, duration_ms: float, **kwargs):
    """Log performance metrics"""
    logger = structlog.get_logger()
    logger.info(
        "Performance metric",
        function=func_name,
        duration_ms=round(duration_ms, 2),
        **kwargs
    )

def log_error(error: Exception, context: Dict[str, Any] = None):
    """Log errors with context"""
    logger = structlog.get_logger()
    logger.error(
        "Error occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        **(context or {})
    ) 