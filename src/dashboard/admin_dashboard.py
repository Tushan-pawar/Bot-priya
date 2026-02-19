"""Web admin dashboard for monitoring and control."""
import asyncio
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta
from pathlib import Path
import uvicorn
from ..utils.logging import logger
from ..memory.persistent_memory import memory_system
from ..skills.skill_manager import skill_manager

# Security
security = HTTPBearer()
ADMIN_TOKEN = "your-secure-admin-token-here"  # In production, use proper auth

class AdminDashboard:
    """Web admin dashboard."""
    
    def __init__(self, port: int = 8080):
        self.app = FastAPI(title="Priya AI Assistant Dashboard", version="2.0.0")
        self.port = port
        self.templates = Jinja2Templates(directory="src/dashboard/templates")
        
        # Create templates directory if it doesn't exist
        Path("src/dashboard/templates").mkdir(parents=True, exist_ok=True)
        Path("src/dashboard/static").mkdir(parents=True, exist_ok=True)
        
        self.setup_routes()
        self.active_users = {}
        self.system_logs = []
    
    def verify_token(self, credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Verify admin token."""
        if credentials.credentials != ADMIN_TOKEN:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        return credentials.credentials
    
    def _get_memory_stats(self):
        """Get memory statistics from database."""
        try:
            import sqlite3
            with sqlite3.connect(memory_system.db_path) as conn:
                total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
                users = conn.execute("SELECT COUNT(DISTINCT user_id) FROM memories").fetchone()[0]
                return total, users
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return 0, 0
    
    def _fetch_memories(self, user_id: Optional[str], limit: int):
        """Fetch memories from database."""
        import sqlite3
        with sqlite3.connect(memory_system.db_path) as conn:
            if user_id:
                cursor = conn.execute(
                    "SELECT user_id, content, timestamp, importance FROM memories WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
                    (user_id, limit)
                )
            else:
                cursor = conn.execute(
                    "SELECT user_id, content, timestamp, importance FROM memories ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                )
            return [{
                "user_id": row[0],
                "content": row[1][:200] + ("..." if len(row[1]) > 200 else ""),
                "timestamp": row[2],
                "importance": row[3]
            } for row in cursor.fetchall()]
    
    def _fetch_users(self):
        """Fetch user statistics from database."""
        import sqlite3
        with sqlite3.connect(memory_system.db_path) as conn:
            cursor = conn.execute("""
                SELECT user_id, COUNT(*) as memory_count, MAX(timestamp) as last_interaction, AVG(importance) as avg_importance
                FROM memories GROUP BY user_id ORDER BY memory_count DESC
            """)
            return [{
                "user_id": row[0],
                "memory_count": row[1],
                "last_interaction": row[2],
                "avg_importance": round(row[3], 2) if row[3] else 0,
                "status": "active" if row[0] in self.active_users else "inactive"
            } for row in cursor.fetchall()]
    
    def setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home(request: Request, token: str = Depends(self.verify_token)):
            """Main dashboard page."""
            return self.templates.TemplateResponse("dashboard.html", {
                "request": request,
                "title": "Priya AI Dashboard"
            })
        
        @self.app.get("/api/stats")
        async def get_stats(token: str = Depends(self.verify_token)):
            """Get system statistics."""
            total_memories, user_count = self._get_memory_stats()
            return {
                "total_memories": total_memories,
                "unique_users": user_count,
                "active_skills": len(skill_manager.get_skill_info()),
                "active_users": len(self.active_users),
                "uptime": str(datetime.now() - datetime.now().replace(hour=0, minute=0, second=0)),
                "system_status": "healthy"
            }
        
        @self.app.get("/api/logs")
        async def get_logs(limit: int = 100, token: str = Depends(self.verify_token)):
            """Get recent system logs."""
            return {"logs": self.system_logs[-limit:], "total": len(self.system_logs)}
        
        @self.app.get("/api/memories")
        async def get_memories(user_id: Optional[str] = None, limit: int = 50, token: str = Depends(self.verify_token)):
            """Get memory entries."""
            try:
                return {"memories": self._fetch_memories(user_id, limit)}
            except Exception as e:
                logger.error(f"Failed to get memories: {e}")
                return {"memories": [], "error": str(e)}
        
        @self.app.get("/api/users")
        async def get_users(token: str = Depends(self.verify_token)):
            """Get user statistics."""
            try:
                return {"users": self._fetch_users()}
            except Exception as e:
                logger.error(f"Failed to get users: {e}")
                return {"users": [], "error": str(e)}
        
        @self.app.post("/api/personality")
        async def set_personality_mode(request: Request, token: str = Depends(self.verify_token)):
            """Set personality mode for a server."""
            data = await request.json()
            server_id, mode = data.get("server_id"), data.get("mode")
            if not server_id or not mode:
                raise HTTPException(400, "server_id and mode required")
            from ..discord_integration.native_features import discord_integration
            if not discord_integration:
                raise HTTPException(500, "Discord integration not available")
            discord_integration.personality_modes[server_id] = mode
            self.log_action(f"Personality mode changed to {mode} for server {server_id}")
            return {"success": True, "message": f"Personality mode set to {mode}"}
        
        @self.app.get("/api/skills")
        async def get_skills(token: str = Depends(self.verify_token)):
            """Get loaded skills information."""
            return {"skills": skill_manager.get_skill_info()}
        
        @self.app.post("/api/skills/reload")
        async def reload_skill(request: Request, token: str = Depends(self.verify_token)):
            """Reload a specific skill."""
            data = await request.json()
            skill_name = data.get("skill_name")
            if not skill_name:
                raise HTTPException(400, "skill_name required")
            success = await skill_manager.reload_skill(skill_name)
            if success:
                self.log_action(f"Skill {skill_name} reloaded successfully")
                return {"success": True, "message": f"Skill {skill_name} reloaded"}
            raise HTTPException(500, f"Failed to reload skill {skill_name}")
    
    def log_action(self, message: str):
        """Log admin action."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": "INFO",
            "source": "admin_dashboard",
            "message": message
        }
        self.system_logs.append(log_entry)
        logger.info(f"Admin: {message}")
    
    def update_active_users(self, users: Dict[str, Any]):
        """Update active users list."""
        self.active_users = users
    
    async def start(self):
        """Start the dashboard server."""
        # Create basic HTML template if it doesn't exist
        self.create_dashboard_template()
        
        config = uvicorn.Config(
            app=self.app,
            host="127.0.0.1",
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        logger.info(f"Starting admin dashboard on http://127.0.0.1:{self.port}")
        await server.serve()
    
    def create_dashboard_template(self):
        """Create basic dashboard HTML template."""
        template_path = Path("src/dashboard/templates/dashboard.html")
        
        if template_path.exists():
            return
        
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Priya AI Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #7289da; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-number { font-size: 2em; font-weight: bold; color: #7289da; }
        .section { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .log-entry { padding: 10px; border-bottom: 1px solid #eee; font-family: monospace; font-size: 12px; }
        .memory-entry { padding: 10px; border-bottom: 1px solid #eee; }
        .user-entry { padding: 10px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; }
        .status-active { color: #43b581; }
        .status-inactive { color: #f04747; }
        button { background: #7289da; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
        button:hover { background: #5b6eae; }
        select { padding: 8px; border-radius: 4px; border: 1px solid #ddd; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Priya AI Assistant Dashboard</h1>
            <p>Monitor and control your AI assistant</p>
        </div>
        
        <div class="stats" id="stats">
            <div class="stat-card">
                <div class="stat-number" id="total-memories">-</div>
                <div>Total Memories</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="unique-users">-</div>
                <div>Unique Users</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="active-skills">-</div>
                <div>Active Skills</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="active-users">-</div>
                <div>Active Users</div>
            </div>
        </div>
        
        <div class="section">
            <h2>Personality Control</h2>
            <div>
                <label>Server ID: <input type="text" id="server-id" placeholder="Enter server ID"></label>
                <label>Mode: 
                    <select id="personality-mode">
                        <option value="calm">Calm</option>
                        <option value="savage">Savage</option>
                        <option value="motivational">Motivational</option>
                        <option value="study">Study</option>
                        <option value="corporate">Corporate</option>
                    </select>
                </label>
                <button onclick="setPersonality()">Update Personality</button>
            </div>
        </div>
        
        <div class="section">
            <h2>Recent Logs</h2>
            <div id="logs" style="max-height: 300px; overflow-y: auto;"></div>
        </div>
        
        <div class="section">
            <h2>Recent Memories</h2>
            <div id="memories" style="max-height: 300px; overflow-y: auto;"></div>
        </div>
        
        <div class="section">
            <h2>Active Users</h2>
            <div id="users" style="max-height: 300px; overflow-y: auto;"></div>
        </div>
    </div>
    
    <script>
        const API_TOKEN = 'your-secure-admin-token-here';
        
        async function fetchWithAuth(url) {
            const response = await fetch(url, {
                headers: { 'Authorization': `Bearer ${API_TOKEN}` }
            });
            return response.json();
        }
        
        async function loadStats() {
            try {
                const stats = await fetchWithAuth('/api/stats');
                document.getElementById('total-memories').textContent = stats.total_memories;
                document.getElementById('unique-users').textContent = stats.unique_users;
                document.getElementById('active-skills').textContent = stats.active_skills;
                document.getElementById('active-users').textContent = stats.active_users;
            } catch (error) {
                console.error('Failed to load stats:', error);
            }
        }
        
        async function loadLogs() {
            try {
                const data = await fetchWithAuth('/api/logs?limit=20');
                const logsDiv = document.getElementById('logs');
                logsDiv.innerHTML = data.logs.map(log => 
                    `<div class="log-entry">[${log.timestamp}] ${log.level}: ${log.message}</div>`
                ).join('');
            } catch (error) {
                console.error('Failed to load logs:', error);
            }
        }
        
        async function loadMemories() {
            try {
                const data = await fetchWithAuth('/api/memories?limit=10');
                const memoriesDiv = document.getElementById('memories');
                memoriesDiv.innerHTML = data.memories.map(memory => 
                    `<div class="memory-entry">
                        <strong>User ${memory.user_id}</strong> (${memory.importance}): ${memory.content}
                        <small>${memory.timestamp}</small>
                    </div>`
                ).join('');
            } catch (error) {
                console.error('Failed to load memories:', error);
            }
        }
        
        async function loadUsers() {
            try {
                const data = await fetchWithAuth('/api/users');
                const usersDiv = document.getElementById('users');
                usersDiv.innerHTML = data.users.map(user => 
                    `<div class="user-entry">
                        <span>User ${user.user_id} (${user.memory_count} memories)</span>
                        <span class="status-${user.status}">${user.status}</span>
                    </div>`
                ).join('');
            } catch (error) {
                console.error('Failed to load users:', error);
            }
        }
        
        async function setPersonality() {
            const serverId = document.getElementById('server-id').value;
            const mode = document.getElementById('personality-mode').value;
            
            if (!serverId) {
                alert('Please enter a server ID');
                return;
            }
            
            try {
                const response = await fetch('/api/personality', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${API_TOKEN}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ server_id: serverId, mode: mode })
                });
                
                const result = await response.json();
                alert(result.message || 'Personality updated');
            } catch (error) {
                alert('Failed to update personality: ' + error.message);
            }
        }
        
        // Load data on page load
        loadStats();
        loadLogs();
        loadMemories();
        loadUsers();
        
        // Refresh data every 30 seconds
        setInterval(() => {
            loadStats();
            loadLogs();
            loadMemories();
            loadUsers();
        }, 30000);
    </script>
</body>
</html>
        """
        
        template_path.write_text(html_content)

# Global dashboard instance
admin_dashboard = AdminDashboard()