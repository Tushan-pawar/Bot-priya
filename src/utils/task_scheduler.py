"""Centralized background task scheduler."""
import asyncio
from typing import Dict, Callable, Any, Optional
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from ..utils.logging import logger

class BackgroundTaskScheduler:
    """Centralized async task scheduler."""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.running = False
    
    async def start(self):
        """Start the scheduler."""
        if self.running:
            await asyncio.sleep(0)
            return
        
        self.scheduler.start()
        self.running = True
        
        # Register default tasks
        await self._register_default_tasks()
        
        logger.info("Background task scheduler started")
    
    async def stop(self):
        """Stop the scheduler gracefully."""
        if not self.running:
            await asyncio.sleep(0)
            return
        
        logger.info("Stopping background task scheduler...")
        
        # Wait for running tasks to complete
        for task_id, task_info in self.tasks.items():
            if task_info.get("running", False):
                logger.info(f"Waiting for task {task_id} to complete...")
                await asyncio.sleep(1)  # Give tasks time to finish
        
        self.scheduler.shutdown(wait=True)
        self.running = False
        logger.info("Background task scheduler stopped")
    
    def add_interval_task(
        self, 
        task_id: str, 
        func: Callable, 
        seconds: int,
        description: str = "",
        start_immediately: bool = False
    ):
        """Add interval-based task."""
        if task_id in self.tasks:
            logger.warning(f"Task {task_id} already exists, replacing...")
            self.remove_task(task_id)
        
        job = self.scheduler.add_job(
            self._wrap_task(task_id, func),
            IntervalTrigger(seconds=seconds),
            id=task_id,
            replace_existing=True
        )
        
        self.tasks[task_id] = {
            "job": job,
            "type": "interval",
            "seconds": seconds,
            "description": description,
            "running": False,
            "last_run": None,
            "run_count": 0,
            "error_count": 0
        }
        
        if start_immediately:
            self.tasks[task_id]["immediate_task"] = asyncio.create_task(self._wrap_task(task_id, func)())
        
        logger.info(f"Added interval task: {task_id} ({seconds}s)")
    
    def add_cron_task(
        self, 
        task_id: str, 
        func: Callable, 
        cron_expression: str,
        description: str = ""
    ):
        """Add cron-based task."""
        if task_id in self.tasks:
            logger.warning(f"Task {task_id} already exists, replacing...")
            self.remove_task(task_id)
        
        # Parse cron expression
        parts = cron_expression.split()
        if len(parts) != 5:
            raise ValueError("Cron expression must have 5 parts: minute hour day month day_of_week")
        
        minute, hour, day, month, day_of_week = parts
        
        job = self.scheduler.add_job(
            self._wrap_task(task_id, func),
            CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week
            ),
            id=task_id,
            replace_existing=True
        )
        
        self.tasks[task_id] = {
            "job": job,
            "type": "cron",
            "cron": cron_expression,
            "description": description,
            "running": False,
            "last_run": None,
            "run_count": 0,
            "error_count": 0
        }
        
        logger.info(f"Added cron task: {task_id} ({cron_expression})")
    
    def remove_task(self, task_id: str):
        """Remove a task."""
        if task_id not in self.tasks:
            return
        
        self.scheduler.remove_job(task_id)
        del self.tasks[task_id]
        logger.info(f"Removed task: {task_id}")
    
    def _wrap_task(self, task_id: str, func: Callable):
        """Wrap task with error handling and stats."""
        async def wrapper():
            if task_id not in self.tasks:
                return
            
            task_info = self.tasks[task_id]
            task_info["running"] = True
            task_info["last_run"] = datetime.now()
            
            try:
                if asyncio.iscoroutinefunction(func):
                    await func()
                else:
                    func()
                
                task_info["run_count"] += 1
                logger.debug(f"Task {task_id} completed successfully")
                
            except Exception as e:
                task_info["error_count"] += 1
                logger.error(f"Task {task_id} failed: {e}")
                
                # Disable task if too many errors
                if task_info["error_count"] > 10:
                    logger.error(f"Task {task_id} disabled due to too many errors")
                    self.remove_task(task_id)
            
            finally:
                task_info["running"] = False
        
        return wrapper
    
    def get_task_status(self) -> Dict[str, Any]:
        """Get status of all tasks."""
        return {
            "scheduler_running": self.running,
            "total_tasks": len(self.tasks),
            "tasks": {
                task_id: {
                    "type": info["type"],
                    "description": info["description"],
                    "running": info["running"],
                    "last_run": info["last_run"].isoformat() if info["last_run"] else None,
                    "run_count": info["run_count"],
                    "error_count": info["error_count"]
                }
                for task_id, info in self.tasks.items()
            }
        }
    
    async def _register_default_tasks(self):
        """Register default maintenance tasks."""
        
        # Memory cleanup task
        self.add_interval_task(
            "memory_cleanup",
            self._memory_cleanup_task,
            seconds=3600,  # Every hour
            description="Clean up old memories and optimize database"
        )
        
        # Analytics aggregation
        self.add_interval_task(
            "analytics_aggregation",
            self._analytics_task,
            seconds=1800,  # Every 30 minutes
            description="Aggregate usage analytics and performance metrics"
        )
        
        # Performance logging
        self.add_interval_task(
            "performance_logging",
            self._performance_logging_task,
            seconds=300,  # Every 5 minutes
            description="Log system performance metrics"
        )
        
        # Context compression cleanup
        self.add_cron_task(
            "context_compression_cleanup",
            self._context_compression_cleanup,
            "0 2 * * *",  # Daily at 2 AM
            description="Clean up old context summaries"
        )
        
        # Rate limiter cleanup
        self.add_interval_task(
            "rate_limiter_cleanup",
            self._rate_limiter_cleanup,
            seconds=300,  # Every 5 minutes
            description="Clean up rate limiter state"
        )
        
        await asyncio.sleep(0)  # Ensure async behavior
    
    async def _memory_cleanup_task(self):
        """Memory cleanup task."""
        try:
            from ..memory.persistent_memory import memory_system
            await memory_system.cleanup_old_memories(days=90)
            logger.info("Memory cleanup completed")
        except Exception as e:
            logger.error(f"Memory cleanup failed: {e}")
    
    async def _analytics_task(self):
        """Analytics aggregation task."""
        try:
            from ..utils.optimization_logger import optimization_logger
            
            # Generate optimization report
            report = optimization_logger.get_optimization_report()
            
            # Log key metrics
            logger.info(f"Analytics: {report['total_failures']} failures, "
                       f"{report['total_unclear_queries']} unclear queries, "
                       f"avg confidence: {report['average_confidence']}")
            
            await asyncio.sleep(0)  # Ensure async behavior
        except Exception as e:
            logger.error(f"Analytics task failed: {e}")
    
    async def _performance_logging_task(self):
        """Performance logging task."""
        try:
            import psutil
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            
            # Log performance metrics
            logger.info(f"Performance: CPU {cpu_percent}%, "
                       f"Memory {memory.percent}% ({memory.used // 1024 // 1024}MB used)")
            
            await asyncio.sleep(0)  # Ensure async behavior
        except Exception as e:
            logger.error(f"Performance logging failed: {e}")
    
    async def _context_compression_cleanup(self):
        """Context compression cleanup task."""
        try:
            from ..memory.context_compression import context_compressor
            await context_compressor.cleanup_old_summaries(days=30)
            logger.info("Context compression cleanup completed")
        except Exception as e:
            logger.error(f"Context compression cleanup failed: {e}")
    
    async def _rate_limiter_cleanup(self):
        """Rate limiter cleanup task."""
        try:
            from ..utils.rate_limiter import rate_limiter
            # Cleanup is handled internally by rate_limiter
            logger.debug("Rate limiter cleanup check completed")
            await asyncio.sleep(0)  # Ensure async behavior
        except Exception as e:
            logger.error(f"Rate limiter cleanup failed: {e}")

# Global instance
task_scheduler = BackgroundTaskScheduler()