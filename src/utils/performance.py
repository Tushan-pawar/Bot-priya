"""System optimization for memory management and performance."""
import asyncio
import gc
import sys
import time
import psutil
from typing import Dict, Any, Optional, List
from ..utils.logging import logger

class MemoryOptimizer:
    """Optimize memory usage and prevent leaks."""
    
    def __init__(self, max_memory_mb: int = 100):
        self.max_memory_mb = max_memory_mb
        self.cleanup_callbacks = []
        self.memory_history = []
        self.last_cleanup = 0
        
    def register_cleanup_callback(self, callback):
        """Register cleanup callback function."""
        self.cleanup_callbacks.append(callback)
    
    async def monitor_memory(self):
        """Continuous memory monitoring."""
        while True:
            try:
                current_memory = self.get_memory_usage()
                self.memory_history.append({
                    'timestamp': time.time(),
                    'memory_mb': current_memory
                })
                
                # Keep only last 100 readings
                if len(self.memory_history) > 100:
                    self.memory_history = self.memory_history[-100:]
                
                # Cleanup if memory is high
                if current_memory > self.max_memory_mb:
                    logger.warning(f"High memory usage: {current_memory:.1f}MB, running cleanup...")
                    await self.cleanup_memory()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Memory monitoring error: {e}")
                await asyncio.sleep(60)
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except (psutil.Error, OSError):
            return 0.0
    
    async def cleanup_memory(self):
        """Perform memory cleanup."""
        if time.time() - self.last_cleanup < 60:  # Don't cleanup too frequently
            return
        
        initial_memory = self.get_memory_usage()
        
        try:
            # Run registered cleanup callbacks
            for callback in self.cleanup_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback()
                    else:
                        callback()
                except Exception as e:
                    logger.error(f"Cleanup callback failed: {e}")
            
            # Force garbage collection
            collected = gc.collect()
            
            final_memory = self.get_memory_usage()
            freed_mb = initial_memory - final_memory
            
            logger.info(f"Memory cleanup: {freed_mb:.1f}MB freed, {collected} objects collected")
            self.last_cleanup = time.time()
            
        except Exception as e:
            logger.error(f"Memory cleanup failed: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        current = self.get_memory_usage()
        
        if self.memory_history:
            avg_memory = sum(h['memory_mb'] for h in self.memory_history) / len(self.memory_history)
            max_memory = max(h['memory_mb'] for h in self.memory_history)
        else:
            avg_memory = current
            max_memory = current
        
        return {
            'current_mb': current,
            'average_mb': avg_memory,
            'max_mb': max_memory,
            'limit_mb': self.max_memory_mb,
            'usage_percent': (current / self.max_memory_mb) * 100,
            'gc_stats': {
                'collections': gc.get_stats(),
                'objects': len(gc.get_objects())
            }
        }

class StartupOptimizer:
    """Optimize bot startup time."""
    
    def __init__(self):
        self.startup_start = time.time()
        self.initialization_steps = []
        self.lazy_imports = {}
        
    def log_step(self, step_name: str):
        """Log initialization step timing."""
        current_time = time.time()
        duration = current_time - self.startup_start
        
        self.initialization_steps.append({
            'step': step_name,
            'duration': duration,
            'timestamp': current_time
        })
        
        logger.info(f"Startup step '{step_name}' completed in {duration:.2f}s")
    
    def lazy_import(self, module_name: str, import_func):
        """Register lazy import for heavy modules."""
        self.lazy_imports[module_name] = {
            'import_func': import_func,
            'module': None,
            'imported': False
        }
    
    def get_lazy_module(self, module_name: str):
        """Get lazily imported module."""
        if module_name not in self.lazy_imports:
            raise ImportError(f"Module {module_name} not registered for lazy import")
        
        lazy_info = self.lazy_imports[module_name]
        
        if not lazy_info['imported']:
            logger.info(f"Lazy importing {module_name}...")
            start_time = time.time()
            
            try:
                lazy_info['module'] = lazy_info['import_func']()
                lazy_info['imported'] = True
                
                duration = time.time() - start_time
                logger.info(f"Lazy import of {module_name} completed in {duration:.2f}s")
                
            except Exception as e:
                logger.error(f"Lazy import of {module_name} failed: {e}")
                raise
        
        return lazy_info['module']
    
    def get_startup_stats(self) -> Dict[str, Any]:
        """Get startup statistics."""
        total_time = time.time() - self.startup_start
        
        return {
            'total_startup_time': total_time,
            'initialization_steps': self.initialization_steps,
            'lazy_imports': {
                name: info['imported'] 
                for name, info in self.lazy_imports.items()
            }
        }

class ResourceMonitor:
    """Monitor system resources and performance."""
    
    def __init__(self):
        self.metrics = {
            'cpu_usage': [],
            'memory_usage': [],
            'disk_usage': [],
            'network_io': [],
            'response_times': []
        }
        self.monitoring_active = False
        self._monitoring_task = None
    
    async def start_monitoring(self):
        """Start resource monitoring."""
        self.monitoring_active = True
        logger.info("Resource monitoring started")
        
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        await asyncio.sleep(0)  # Yield control to event loop
    
    def stop_monitoring(self):
        """Stop resource monitoring."""
        self.monitoring_active = False
        logger.info("Resource monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                # Collect metrics
                metrics = self._collect_metrics()
                
                # Store metrics
                for key, value in metrics.items():
                    if key in self.metrics:
                        self.metrics[key].append({
                            'timestamp': time.time(),
                            'value': value
                        })
                        
                        # Keep only last 100 readings
                        if len(self.metrics[key]) > 100:
                            self.metrics[key] = self.metrics[key][-100:]
                
                await asyncio.sleep(30)  # Collect every 30 seconds
                
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                await asyncio.sleep(60)
    
    def _collect_metrics(self) -> Dict[str, float]:
        """Collect current system metrics."""
        try:
            process = psutil.Process()
            
            return {
                'cpu_usage': process.cpu_percent(),
                'memory_usage': process.memory_info().rss / 1024 / 1024,  # MB
                'disk_usage': psutil.disk_usage('.').percent,
                'network_io': sum(psutil.net_io_counters()[:2]) / 1024 / 1024  # MB
            }
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            return {}
    
    def log_response_time(self, duration: float, operation: str = "general"):
        """Log response time for performance tracking."""
        self.metrics['response_times'].append({
            'timestamp': time.time(),
            'duration': duration,
            'operation': operation
        })
        
        # Keep only last 200 response times
        if len(self.metrics['response_times']) > 200:
            self.metrics['response_times'] = self.metrics['response_times'][-200:]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = {}
        
        for metric_name, metric_data in self.metrics.items():
            if not metric_data:
                continue
            
            if metric_name == 'response_times':
                stats[metric_name] = self._calculate_response_time_stats(metric_data)
            else:
                stats[metric_name] = self._calculate_metric_stats(metric_data)
        
        return stats
    
    def _calculate_response_time_stats(self, metric_data: List[Dict]) -> Dict[str, float]:
        """Calculate response time statistics."""
        durations = [m['duration'] for m in metric_data]
        return {
            'count': len(durations),
            'average': sum(durations) / len(durations) if durations else 0,
            'min': min(durations) if durations else 0,
            'max': max(durations) if durations else 0
        }
    
    def _calculate_metric_stats(self, metric_data: List[Dict]) -> Dict[str, float]:
        """Calculate general metric statistics."""
        values = [m['value'] for m in metric_data]
        return {
            'current': values[-1] if values else 0,
            'average': sum(values) / len(values) if values else 0,
            'min': min(values) if values else 0,
            'max': max(values) if values else 0
        }

class SystemOptimizer:
    """Main system optimization coordinator."""
    
    def __init__(self, max_memory_mb: int = 100):
        self.memory_optimizer = MemoryOptimizer(max_memory_mb)
        self.startup_optimizer = StartupOptimizer()
        self.resource_monitor = ResourceMonitor()
        self._memory_task = None
        
    async def start_optimization(self):
        """Start all optimization systems."""
        logger.info("Starting system optimization...")
        
        # Start memory monitoring
        self._memory_task = asyncio.create_task(self.memory_optimizer.monitor_memory())
        
        # Start resource monitoring
        await self.resource_monitor.start_monitoring()
        
        # Register cleanup callbacks
        self.memory_optimizer.register_cleanup_callback(self._cleanup_caches)
        self.memory_optimizer.register_cleanup_callback(self._cleanup_temp_files)
        
        logger.info("System optimization started")
    
    def _cleanup_caches(self):
        """Cleanup internal caches."""
        # Clear import caches
        if hasattr(sys, '_clear_type_cache'):
            sys._clear_type_cache()
        
        # Clear regex cache
        import re
        re.purge()
    
    def _cleanup_temp_files(self):
        """Cleanup temporary files."""
        import tempfile
        import glob
        import os
        
        try:
            temp_dir = tempfile.gettempdir()
            temp_files = glob.glob(f"{temp_dir}/tmp*")
            
            cleaned = 0
            for temp_file in temp_files:
                try:
                    if time.time() - os.path.getmtime(temp_file) > 3600:  # 1 hour old
                        os.unlink(temp_file)
                        cleaned += 1
                except (OSError, IOError):
                    pass
            
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} temporary files")
                
        except (OSError, IOError) as e:
            logger.error(f"Temp file cleanup failed: {e}")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        return {
            'memory': self.memory_optimizer.get_memory_stats(),
            'startup': self.startup_optimizer.get_startup_stats(),
            'performance': self.resource_monitor.get_performance_stats(),
            'system_info': {
                'python_version': sys.version,
                'platform': sys.platform,
                'cpu_count': psutil.cpu_count(),
                'total_memory_mb': psutil.virtual_memory().total / 1024 / 1024
            }
        }

# Global instance
system_optimizer = SystemOptimizer()