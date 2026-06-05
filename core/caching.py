"""
Caching and performance utilities for VETA Connect
Handles caching, memoization, and performance optimization
"""

from functools import wraps
from typing import Any, Callable, Optional, Dict, List
from datetime import datetime, timedelta
import hashlib
import pickle
from collections import OrderedDict


class CacheKey:
    """Generates cache keys"""
    
    @staticmethod
    def generate(prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_parts = [prefix]
        
        for arg in args:
            key_parts.append(str(arg))
        
        for k, v in sorted(kwargs.items()):
            key_parts.append(f'{k}={v}')
        
        key_string = ':'.join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    @staticmethod
    def for_user(prefix: str, user_id: int, *args, **kwargs) -> str:
        """Generate cache key for user"""
        return CacheKey.generate(f'{prefix}:user:{user_id}', *args, **kwargs)
    
    @staticmethod
    def for_model(model_name: str, model_id: int) -> str:
        """Generate cache key for model"""
        return f'{model_name}:{model_id}'


class SimpleCache:
    """In-memory cache"""
    
    def __init__(self, max_size: int = 1000):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.timestamps = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache"""
        if key in self.cache:
            timestamp = self.timestamps.get(key)
            if timestamp and datetime.now() > timestamp:
                del self.cache[key]
                del self.timestamps[key]
                return default
            
            self.cache.move_to_end(key)
            return self.cache[key]
        return default
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None):
        """Set value in cache"""
        if key in self.cache:
            self.cache.move_to_end(key)
        
        self.cache[key] = value
        
        if timeout:
            self.timestamps[key] = datetime.now() + timedelta(seconds=timeout)
        
        if len(self.cache) > self.max_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            if oldest_key in self.timestamps:
                del self.timestamps[oldest_key]
    
    def delete(self, key: str):
        """Delete from cache"""
        if key in self.cache:
            del self.cache[key]
            if key in self.timestamps:
                del self.timestamps[key]
    
    def clear(self):
        """Clear cache"""
        self.cache.clear()
        self.timestamps.clear()
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'usage': (len(self.cache) / self.max_size * 100) if self.max_size else 0
        }


class Memoizer:
    """Memoization decorator"""
    
    def __init__(self, cache: Optional[SimpleCache] = None, timeout: Optional[int] = None):
        self.cache = cache or SimpleCache()
        self.timeout = timeout
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = CacheKey.generate(func.__name__, *args, **kwargs)
            
            cached_value = self.cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            result = func(*args, **kwargs)
            self.cache.set(cache_key, result, self.timeout)
            return result
        
        return wrapper


# Global cache instance
_global_cache = SimpleCache(max_size=10000)


def memoize(timeout: Optional[int] = None):
    """Decorator for memoizing function results"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = CacheKey.generate(func.__name__, *args, **kwargs)
            
            cached = _global_cache.get(cache_key)
            if cached is not None:
                return cached
            
            result = func(*args, **kwargs)
            _global_cache.set(cache_key, result, timeout)
            return result
        
        wrapper.cache_clear = lambda: _global_cache.delete(
            CacheKey.generate(func.__name__)
        )
        return wrapper
    
    return decorator


def cache_method_result(timeout: Optional[int] = None):
    """Decorator for caching method results"""
    def decorator(method: Callable) -> Callable:
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            cache_key = CacheKey.generate(f'{self.__class__.__name__}.{method.__name__}', *args, **kwargs)
            
            cached = _global_cache.get(cache_key)
            if cached is not None:
                return cached
            
            result = method(self, *args, **kwargs)
            _global_cache.set(cache_key, result, timeout)
            return result
        
        return wrapper
    
    return decorator


class CachedProperty:
    """Cached property for classes"""
    
    def __init__(self, func: Callable, timeout: Optional[int] = None):
        self.func = func
        self.timeout = timeout
        self.__doc__ = func.__doc__
        self.cache_attr = f'_cached_{func.__name__}'
        self.timestamp_attr = f'_cached_timestamp_{func.__name__}'
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        
        cached_value = getattr(obj, self.cache_attr, None)
        timestamp = getattr(obj, self.timestamp_attr, None)
        
        if timestamp and self.timeout:
            if datetime.now() > timestamp:
                cached_value = None
        
        if cached_value is not None:
            return cached_value
        
        value = self.func(obj)
        setattr(obj, self.cache_attr, value)
        
        if self.timeout:
            setattr(obj, self.timestamp_attr, datetime.now() + timedelta(seconds=self.timeout))
        
        return value


class QueryCache:
    """Cache for database queries"""
    
    def __init__(self, cache: Optional[SimpleCache] = None):
        self.cache = cache or SimpleCache(max_size=5000)
    
    def cache_queryset(self, queryset, cache_key: str, timeout: Optional[int] = 3600):
        """Cache queryset results"""
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        
        results = list(queryset)
        self.cache.set(cache_key, results, timeout)
        return results
    
    def invalidate_model_cache(self, model_name: str):
        """Invalidate cache for model"""
        keys_to_delete = [k for k in self.cache.cache.keys() if model_name in k]
        for key in keys_to_delete:
            self.cache.delete(key)


class PerformanceMonitor:
    """Monitor performance metrics"""
    
    def __init__(self):
        self.metrics = {}
    
    def record_time(self, operation: str, elapsed_time: float):
        """Record operation time"""
        if operation not in self.metrics:
            self.metrics[operation] = {
                'count': 0,
                'total_time': 0,
                'min_time': float('inf'),
                'max_time': 0
            }
        
        stats = self.metrics[operation]
        stats['count'] += 1
        stats['total_time'] += elapsed_time
        stats['min_time'] = min(stats['min_time'], elapsed_time)
        stats['max_time'] = max(stats['max_time'], elapsed_time)
    
    def get_stats(self, operation: str) -> Optional[Dict]:
        """Get statistics for operation"""
        if operation in self.metrics:
            stats = self.metrics[operation]
            return {
                'operation': operation,
                'count': stats['count'],
                'total_time': stats['total_time'],
                'average_time': stats['total_time'] / stats['count'],
                'min_time': stats['min_time'],
                'max_time': stats['max_time']
            }
        return None
    
    def get_all_stats(self) -> List[Dict]:
        """Get all statistics"""
        return [self.get_stats(op) for op in self.metrics.keys()]


def measure_time(operation_name: str, monitor: Optional[PerformanceMonitor] = None):
    """Decorator to measure function execution time"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed_time = time.time() - start_time
                
                if monitor:
                    monitor.record_time(operation_name or func.__name__, elapsed_time)
                else:
                    print(f'{operation_name or func.__name__} took {elapsed_time:.4f}s')
        
        return wrapper
    
    return decorator


# Global performance monitor
_global_monitor = PerformanceMonitor()


class BatchProcessor:
    """Process items in batches for efficiency"""
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
    
    def process_batch(self, items: List[Any], processor: Callable) -> List[Any]:
        """Process items in batches"""
        results = []
        
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_results = [processor(item) for item in batch]
            results.extend(batch_results)
        
        return results
    
    def process_batch_async(self, items: List[Any], processor: Callable, max_workers: int = 4):
        """Process items in batches asynchronously"""
        from concurrent.futures import ThreadPoolExecutor
        
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for i in range(0, len(items), self.batch_size):
                batch = items[i:i + self.batch_size]
                future = executor.submit(lambda b: [processor(item) for item in b], batch)
                futures.append(future)
            
            for future in futures:
                batch_results = future.result()
                results.extend(batch_results)
        
        return results
