import time
import logging
import asyncio
from typing import Dict, Any, Optional
from functools import wraps
from collections import defaultdict, deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collect and store application metrics"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.request_times = deque(maxlen=max_history)
        self.request_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        self.endpoint_metrics = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'errors': 0,
            'last_called': None
        })
        self.start_time = time.time()
    
    def record_request(self, endpoint: str, method: str, duration: float, status_code: int):
        """Record a request metric"""
        key = f"{method}:{endpoint}"
        self.request_times.append(duration)
        self.request_counts[key] += 1
        
        metrics = self.endpoint_metrics[key]
        metrics['count'] += 1
        metrics['total_time'] += duration
        metrics['last_called'] = datetime.utcnow()
        
        if status_code >= 400:
            metrics['errors'] += 1
            self.error_counts[key] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics summary"""
        uptime = time.time() - self.start_time
        
        # Calculate average response time
        avg_response_time = (
            sum(self.request_times) / len(self.request_times)
            if self.request_times else 0
        )
        
        # Calculate requests per minute
        total_requests = sum(self.request_counts.values())
        requests_per_minute = (total_requests / (uptime / 60)) if uptime > 0 else 0
        
        # Get endpoint statistics
        endpoint_stats = {}
        for endpoint, metrics in self.endpoint_metrics.items():
            avg_time = metrics['total_time'] / metrics['count'] if metrics['count'] > 0 else 0
            error_rate = metrics['errors'] / metrics['count'] if metrics['count'] > 0 else 0
            
            endpoint_stats[endpoint] = {
                'requests': metrics['count'],
                'avg_response_time': avg_time,
                'error_rate': error_rate,
                'last_called': metrics['last_called'].isoformat() if metrics['last_called'] else None
            }
        
        return {
            'uptime_seconds': uptime,
            'total_requests': total_requests,
            'requests_per_minute': requests_per_minute,
            'average_response_time': avg_response_time,
            'error_rate': sum(self.error_counts.values()) / total_requests if total_requests > 0 else 0,
            'endpoints': endpoint_stats
        }


# Global metrics collector
metrics = MetricsCollector()


def monitor_performance(func):
    """Decorator to monitor function performance"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            raise
        finally:
            duration = time.time() - start_time
            logger.info(f"{func.__name__} took {duration:.3f}s")
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            raise
        finally:
            duration = time.time() - start_time
            logger.info(f"{func.__name__} took {duration:.3f}s")
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


class HealthChecker:
    """Check health of various system components"""
    
    def __init__(self):
        self.checks = {}
    
    def register_check(self, name: str, check_func):
        """Register a health check function"""
        self.checks[name] = check_func
    
    async def run_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {}
        overall_healthy = True
        
        for name, check_func in self.checks.items():
            try:
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                
                results[name] = {
                    'status': 'healthy',
                    'details': result if isinstance(result, dict) else {'message': str(result)}
                }
            except Exception as e:
                results[name] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                overall_healthy = False
        
        return {
            'overall_status': 'healthy' if overall_healthy else 'unhealthy',
            'checks': results,
            'timestamp': datetime.utcnow().isoformat()
        }


# Global health checker
health_checker = HealthChecker()


# Database health check
async def check_database_health():
    """Check MongoDB connection"""
    try:
        from utils.db import async_db
        await async_db.command("ping")
        return {'connection': 'ok'}
    except Exception as e:
        raise Exception(f"Database connection failed: {str(e)}")


# Redis health check
async def check_redis_health():
    """Check Redis connection"""
    try:
        from utils.db import redis_client
        if redis_client:
            await asyncio.to_thread(redis_client.ping)
            return {'connection': 'ok'}
        else:
            return {'connection': 'not configured'}
    except Exception as e:
        raise Exception(f"Redis connection failed: {str(e)}")


# API health check
def check_api_health():
    """Check API health"""
    return {
        'status': 'running',
        'metrics': metrics.get_metrics()
    }


# Register health checks
health_checker.register_check('database', check_database_health)
health_checker.register_check('redis', check_redis_health)
health_checker.register_check('api', check_api_health)


class AlertManager:
    """Manage alerts based on metrics"""
    
    def __init__(self):
        self.alert_thresholds = {
            'error_rate': 0.1,  # 10% error rate
            'avg_response_time': 5.0,  # 5 seconds
            'requests_per_minute': 100  # 100 requests per minute
        }
        self.active_alerts = set()
    
    def check_alerts(self, metrics_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check if any alerts should be triggered"""
        alerts = []
        
        # Check error rate
        if metrics_data['error_rate'] > self.alert_thresholds['error_rate']:
            alert = {
                'type': 'high_error_rate',
                'message': f"Error rate is {metrics_data['error_rate']:.2%}",
                'severity': 'warning'
            }
            alerts.append(alert)
        
        # Check response time
        if metrics_data['average_response_time'] > self.alert_thresholds['avg_response_time']:
            alert = {
                'type': 'slow_response',
                'message': f"Average response time is {metrics_data['average_response_time']:.2f}s",
                'severity': 'warning'
            }
            alerts.append(alert)
        
        # Check request rate
        if metrics_data['requests_per_minute'] > self.alert_thresholds['requests_per_minute']:
            alert = {
                'type': 'high_traffic',
                'message': f"Request rate is {metrics_data['requests_per_minute']:.1f} req/min",
                'severity': 'info'
            }
            alerts.append(alert)
        
        return alerts


# Global alert manager
alert_manager = AlertManager()


# Middleware for request monitoring
async def monitoring_middleware(request, call_next):
    """Middleware to monitor requests"""
    start_time = time.time()
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Record metrics
        metrics.record_request(
            endpoint=request.url.path,
            method=request.method,
            duration=duration,
            status_code=response.status_code
        )
        
        return response
    except Exception as e:
        duration = time.time() - start_time
        metrics.record_request(
            endpoint=request.url.path,
            method=request.method,
            duration=duration,
            status_code=500
        )
        raise
