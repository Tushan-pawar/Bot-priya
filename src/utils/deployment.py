"""Deployment readiness features for production stability."""
import asyncio
import psutil
import time
import json
import os
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path
from ..utils.logging import logger

# Constants
MAINTENANCE_FLAG_FILE = 'data/maintenance.flag'

class HealthMonitor:
    """Monitor bot health and performance."""
    
    def __init__(self):
        self.start_time = time.time()
        self.health_data = {
            'status': 'starting',
            'uptime': 0,
            'memory_usage': 0,
            'cpu_usage': 0,
            'response_times': [],
            'error_count': 0,
            'last_error': None,
            'api_status': {},
            'voice_status': 'inactive'
        }
        self.max_memory_mb = 150  # Alert threshold
        self.max_response_time = 5.0  # Alert threshold
        
    def update_health(self, **kwargs):
        """Update health metrics."""
        self.health_data.update(kwargs)
        self.health_data['uptime'] = time.time() - self.start_time
        
        # System metrics
        try:
            process = psutil.Process()
            self.health_data['memory_usage'] = process.memory_info().rss / 1024 / 1024  # MB
            self.health_data['cpu_usage'] = process.cpu_percent()
        except (psutil.Error, OSError) as e:
            logger.warning(f"Failed to get system metrics: {e}")
    
    def log_response_time(self, duration: float):
        """Log response time for monitoring."""
        self.health_data['response_times'].append(duration)
        
        # Keep only last 100 response times
        if len(self.health_data['response_times']) > 100:
            self.health_data['response_times'] = self.health_data['response_times'][-100:]
    
    def log_error(self, error: str):
        """Log error for monitoring."""
        self.health_data['error_count'] += 1
        self.health_data['last_error'] = {
            'message': str(error),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        avg_response_time = 0
        if self.health_data['response_times']:
            avg_response_time = sum(self.health_data['response_times']) / len(self.health_data['response_times'])
        
        # Determine overall status
        status = 'healthy'
        alerts = []
        
        if self.health_data['memory_usage'] > self.max_memory_mb:
            status = 'warning'
            alerts.append(f"High memory usage: {self.health_data['memory_usage']:.1f}MB")
        
        if avg_response_time > self.max_response_time:
            status = 'warning'
            alerts.append(f"Slow responses: {avg_response_time:.1f}s average")
        
        if self.health_data['error_count'] > 10:
            status = 'critical'
            alerts.append(f"High error count: {self.health_data['error_count']}")
        
        return {
            **self.health_data,
            'avg_response_time': avg_response_time,
            'status': status,
            'alerts': alerts,
            'timestamp': datetime.now().isoformat()
        }

class AutoRestart:
    """Auto-restart functionality for production."""
    
    def __init__(self):
        self.restart_file = Path('data/restart_required.flag')
        self.restart_scheduled = False
        self.graceful_shutdown_timeout = 30
        
    def schedule_restart(self, reason: str = "Manual restart"):
        """Schedule a graceful restart."""
        logger.info(f"Restart scheduled: {reason}")
        self.restart_scheduled = True
        
        # Create restart flag file
        self.restart_file.parent.mkdir(exist_ok=True)
        with open(self.restart_file, 'w') as f:
            json.dump({
                'reason': reason,
                'scheduled_at': datetime.now().isoformat(),
                'pid': os.getpid()
            }, f)
    
    def check_restart_required(self) -> bool:
        """Check if restart is required."""
        return self.restart_file.exists() or self.restart_scheduled
    
    async def graceful_restart(self):
        """Perform graceful restart."""
        logger.info("Starting graceful restart...")
        
        try:
            loop = asyncio.get_event_loop()
            if await loop.run_in_executor(None, self.restart_file.exists):
                await loop.run_in_executor(None, self.restart_file.unlink)
            
            logger.info("Graceful restart completed")
            await asyncio.sleep(0)  # Ensure async behavior
            
            # Restart process
            os.execv(sys.executable, ['python'] + sys.argv)
            
        except Exception as e:
            logger.error(f"Graceful restart failed: {e}")
            os._exit(1)

class ProductionManager:
    """Manage production deployment features."""
    
    def __init__(self):
        self.health_monitor = HealthMonitor()
        self.auto_restart = AutoRestart()
        self.maintenance_mode = False
        self.update_in_progress = False
        
    async def start_monitoring(self):
        """Start production monitoring."""
        logger.info("Starting production monitoring...")
        
        # Start health monitoring loop
        self._health_task = asyncio.create_task(self._health_monitoring_loop())
        
        # Start restart checking loop
        self._restart_task = asyncio.create_task(self._restart_checking_loop())
        
        self.health_monitor.update_health(status='running')
        await asyncio.sleep(0)  # Ensure async behavior
    
    async def _health_monitoring_loop(self):
        """Continuous health monitoring."""
        while True:
            try:
                self.health_monitor.update_health()
                
                health = self.health_monitor.get_health_status()
                
                # Log warnings
                if health['status'] == 'warning':
                    logger.warning(f"Health warning: {', '.join(health['alerts'])}")
                elif health['status'] == 'critical':
                    logger.error(f"Health critical: {', '.join(health['alerts'])}")
                    
                    # Auto-restart on critical issues
                    if health['memory_usage'] > 200:  # 200MB emergency threshold
                        self.auto_restart.schedule_restart("Critical memory usage")
                
                # Save health data
                await self._save_health_data(health)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _restart_checking_loop(self):
        """Check for restart requirements."""
        while True:
            try:
                if self.auto_restart.check_restart_required():
                    logger.info("Restart required, initiating graceful restart...")
                    await self.auto_restart.graceful_restart()
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Restart checking error: {e}")
                await asyncio.sleep(30)
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, scheduling graceful restart...")
            self.auto_restart.schedule_restart(f"Signal {signum}")
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        # Windows compatibility
        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, signal_handler)
    
    async def _save_health_data(self, health_data: Dict):
        """Save health data to file."""
        try:
            import aiofiles
            health_file = Path('data/health.json')
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, health_file.parent.mkdir, True)
            
            async with aiofiles.open(health_file, 'w') as f:
                await f.write(json.dumps(health_data, indent=2))
                
        except Exception as e:
            logger.error(f"Failed to save health data: {e}")
    
    async def enable_maintenance_mode(self, reason: str = "Maintenance"):
        """Enable maintenance mode."""
        self.maintenance_mode = True
        logger.info(f"Maintenance mode enabled: {reason}")
        
        maintenance_file = Path(MAINTENANCE_FLAG_FILE)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, maintenance_file.parent.mkdir, True)
        
        def write_file():
            with open(maintenance_file, 'w') as f:
                json.dump({'reason': reason, 'enabled_at': datetime.now().isoformat()}, f)
        
        await loop.run_in_executor(None, write_file)
    
    async def disable_maintenance_mode(self):
        """Disable maintenance mode."""
        self.maintenance_mode = False
        logger.info("Maintenance mode disabled")
        
        maintenance_file = Path(MAINTENANCE_FLAG_FILE)
        loop = asyncio.get_event_loop()
        if await loop.run_in_executor(None, maintenance_file.exists):
            await loop.run_in_executor(None, maintenance_file.unlink)
    
    def is_maintenance_mode(self) -> bool:
        """Check if in maintenance mode."""
        return self.maintenance_mode or Path(MAINTENANCE_FLAG_FILE).exists()
    
    async def update_bot(self, update_command: str):
        """Perform bot update with zero downtime."""
        if self.update_in_progress:
            return False
        
        self.update_in_progress = True
        logger.info("Starting bot update...")
        
        try:
            await self.enable_maintenance_mode("Bot update in progress")
            
            # Run update command asynchronously
            process = await asyncio.create_subprocess_shell(
                update_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info("Update successful, scheduling restart...")
                self.auto_restart.schedule_restart("Bot update completed")
                return True
            else:
                logger.error(f"Update failed: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Update error: {e}")
            return False
        finally:
            self.update_in_progress = False
            await self.disable_maintenance_mode()
    
    async def get_deployment_status(self) -> Dict[str, Any]:
        """Get deployment status information."""
        await asyncio.sleep(0)  # Ensure async behavior
        return {
            'health': self.health_monitor.get_health_status(),
            'maintenance_mode': self.is_maintenance_mode(),
            'update_in_progress': self.update_in_progress,
            'restart_scheduled': self.auto_restart.restart_scheduled,
            'deployment_info': {
                'python_version': sys.version,
                'platform': sys.platform,
                'pid': os.getpid(),
                'working_directory': os.getcwd()
            }
        }

# Global instance
production_manager = ProductionManager()