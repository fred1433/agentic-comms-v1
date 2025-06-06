import time
from typing import Dict, Optional
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
import structlog

logger = structlog.get_logger()

class MetricsRegistry:
    """Registry for Prometheus metrics"""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        
        # Request metrics
        self.request_count = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # Agent metrics
        self.agent_count = Gauge(
            'agents_active_total',
            'Number of active agents',
            registry=self.registry
        )
        
        self.message_processing_time = Histogram(
            'message_processing_duration_seconds',
            'Message processing duration',
            ['channel', 'agent_type'],
            registry=self.registry
        )
        
        self.messages_processed = Counter(
            'messages_processed_total',
            'Total messages processed',
            ['channel', 'escalated'],
            registry=self.registry
        )
        
        # LLM metrics
        self.llm_requests = Counter(
            'llm_requests_total',
            'Total LLM requests',
            ['model', 'context'],
            registry=self.registry
        )
        
        self.llm_tokens = Counter(
            'llm_tokens_total',
            'Total LLM tokens used',
            ['model', 'type'],  # type: prompt, completion
            registry=self.registry
        )
        
        self.llm_confidence = Histogram(
            'llm_confidence_score',
            'LLM response confidence scores',
            registry=self.registry
        )
        
        # Voice metrics
        self.voice_processing_time = Histogram(
            'voice_processing_duration_seconds',
            'Voice processing duration',
            ['operation'],  # stt, tts
            registry=self.registry
        )
        
        self.voice_requests = Counter(
            'voice_requests_total',
            'Total voice requests',
            ['operation'],
            registry=self.registry
        )
        
        # Vector database metrics
        self.vector_operations = Counter(
            'vector_operations_total',
            'Total vector database operations',
            ['operation'],  # store, retrieve, search
            registry=self.registry
        )
        
        self.vector_search_results = Histogram(
            'vector_search_results_count',
            'Number of results from vector searches',
            registry=self.registry
        )
        
        # Business metrics
        self.escalation_rate = Gauge(
            'escalation_rate',
            'Current escalation rate',
            registry=self.registry
        )
        
        self.resolution_rate = Gauge(
            'resolution_rate',
            'Current resolution rate',
            registry=self.registry
        )
        
        self.customer_satisfaction = Gauge(
            'customer_satisfaction_score',
            'Customer satisfaction score',
            registry=self.registry
        )
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        self.request_count.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        self.request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_message_processing(self, channel: str, duration_ms: float, escalated: bool, agent_type: str = "general"):
        """Record message processing metrics"""
        self.message_processing_time.labels(
            channel=channel,
            agent_type=agent_type
        ).observe(duration_ms / 1000)  # Convert to seconds
        
        self.messages_processed.labels(
            channel=channel,
            escalated=str(escalated)
        ).inc()
    
    def record_llm_request(self, model: str, context: str, tokens_used: int, confidence: float):
        """Record LLM request metrics"""
        self.llm_requests.labels(
            model=model,
            context=context
        ).inc()
        
        self.llm_tokens.labels(
            model=model,
            type="total"
        ).inc(tokens_used)
        
        self.llm_confidence.observe(confidence)
    
    def record_voice_operation(self, operation: str, duration_ms: float):
        """Record voice operation metrics"""
        self.voice_requests.labels(operation=operation).inc()
        self.voice_processing_time.labels(operation=operation).observe(duration_ms / 1000)
    
    def record_vector_operation(self, operation: str, result_count: Optional[int] = None):
        """Record vector database operation metrics"""
        self.vector_operations.labels(operation=operation).inc()
        
        if result_count is not None:
            self.vector_search_results.observe(result_count)
    
    def update_agent_count(self, count: int):
        """Update active agent count"""
        self.agent_count.set(count)
    
    def update_business_metrics(self, escalation_rate: float, resolution_rate: float, satisfaction: Optional[float] = None):
        """Update business metrics"""
        self.escalation_rate.set(escalation_rate)
        self.resolution_rate.set(resolution_rate)
        
        if satisfaction is not None:
            self.customer_satisfaction.set(satisfaction)
    
    def get_metrics(self) -> str:
        """Get Prometheus formatted metrics"""
        return generate_latest(self.registry).decode('utf-8')
    
    def record_response_time(self, response_time_ms: float, channel: str):
        """Record response time for dashboard stats"""
        # This is handled by record_message_processing
        pass

# Global metrics registry
metrics_registry = MetricsRegistry()

def track_performance(operation: str):
    """Decorator to track performance of functions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                logger.info(
                    f"{operation} completed",
                    duration_ms=duration,
                    function=func.__name__
                )
                return result
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                logger.error(
                    f"{operation} failed",
                    duration_ms=duration,
                    function=func.__name__,
                    error=str(e)
                )
                raise
        return wrapper
    return decorator

async def track_async_performance(operation: str):
    """Async decorator to track performance"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                logger.info(
                    f"{operation} completed",
                    duration_ms=duration,
                    function=func.__name__
                )
                return result
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                logger.error(
                    f"{operation} failed",
                    duration_ms=duration,
                    function=func.__name__,
                    error=str(e)
                )
                raise
        return wrapper
    return decorator 