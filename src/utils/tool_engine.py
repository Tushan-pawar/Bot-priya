"""Structured tool execution engine with safety validation."""
import json
import asyncio
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod
import jsonschema
from ..utils.logging import logger

@dataclass
class ToolResult:
    """Tool execution result."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0

class BaseTool(ABC):
    """Base class for all tools."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description."""
        pass
    
    @property
    @abstractmethod
    def schema(self) -> Dict[str, Any]:
        """JSON schema for tool parameters."""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool."""
        pass

class ToolRegistry:
    """Registry for managing tools."""
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.execution_stats = {}
    
    def register(self, tool: BaseTool):
        """Register a tool."""
        self.tools[tool.name] = tool
        self.execution_stats[tool.name] = {"calls": 0, "errors": 0, "avg_time": 0.0}
        logger.info(f"Registered tool: {tool.name}")
    
    def get_tool_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Get all tool schemas for LLM."""
        return {
            name: {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.schema
            }
            for name, tool in self.tools.items()
        }
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolResult:
        """Execute a tool with validation."""
        if tool_name not in self.tools:
            return ToolResult(success=False, error=f"Tool '{tool_name}' not found")
        
        tool = self.tools[tool_name]
        
        # Validate parameters
        try:
            jsonschema.validate(parameters, tool.schema)
        except jsonschema.ValidationError as e:
            return ToolResult(success=False, error=f"Invalid parameters: {e.message}")
        
        # Execute tool
        start_time = asyncio.get_event_loop().time()
        try:
            result = await tool.execute(**parameters)
            execution_time = asyncio.get_event_loop().time() - start_time
            result.execution_time = execution_time
            
            # Update stats
            stats = self.execution_stats[tool_name]
            stats["calls"] += 1
            if not result.success:
                stats["errors"] += 1
            stats["avg_time"] = (stats["avg_time"] * (stats["calls"] - 1) + execution_time) / stats["calls"]
            
            return result
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            self.execution_stats[tool_name]["errors"] += 1
            logger.error(f"Tool {tool_name} execution failed: {e}")
            return ToolResult(success=False, error=str(e), execution_time=execution_time)

class ToolExecutionEngine:
    """Main tool execution engine."""
    
    def __init__(self):
        self.registry = ToolRegistry()
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default tools."""
        self.registry.register(WebSearchTool())
        self.registry.register(CalculatorTool())
        self.registry.register(TimeInfoTool())
        self.registry.register(MemorySearchTool())
    
    async def process_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[ToolResult]:
        """Process multiple tool calls."""
        results = []
        for call in tool_calls:
            tool_name = call.get("name")
            parameters = call.get("parameters", {})
            result = await self.registry.execute_tool(tool_name, parameters)
            results.append(result)
        return results
    
    def get_tools_prompt(self) -> str:
        """Get tools description for LLM prompt."""
        schemas = self.registry.get_tool_schemas()
        if not schemas:
            return ""
        
        tools_desc = "Available tools:\n"
        for name, schema in schemas.items():
            tools_desc += f"- {name}: {schema['description']}\n"
        
        tools_desc += "\nTo use tools, respond with JSON: {\"tool_calls\": [{\"name\": \"tool_name\", \"parameters\": {...}}]}"
        return tools_desc

# Default Tools
class WebSearchTool(BaseTool):
    @property
    def name(self) -> str:
        return "web_search"
    
    @property
    def description(self) -> str:
        return "Search the web for current information"
    
    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"]
        }
    
    async def execute(self, query: str) -> ToolResult:
        # Simplified web search - integrate with existing web browsing
        try:
            from ..engines.web_browser import web_browser
            results = await web_browser.search(query, limit=3)
            return ToolResult(success=True, data=results)
        except Exception as e:
            return ToolResult(success=False, error=str(e))

class CalculatorTool(BaseTool):
    @property
    def name(self) -> str:
        return "calculator"
    
    @property
    def description(self) -> str:
        return "Perform mathematical calculations"
    
    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Mathematical expression to evaluate"}
            },
            "required": ["expression"]
        }
    
    async def execute(self, expression: str) -> ToolResult:
        try:
            # Safe evaluation - only allow basic math
            allowed_chars = set("0123456789+-*/.() ")
            if not all(c in allowed_chars for c in expression):
                return ToolResult(success=False, error="Invalid characters in expression")
            
            result = eval(expression)
            return ToolResult(success=True, data=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))

class TimeInfoTool(BaseTool):
    @property
    def name(self) -> str:
        return "time_info"
    
    @property
    def description(self) -> str:
        return "Get current time and date information"
    
    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "timezone": {"type": "string", "description": "Timezone (optional)", "default": "UTC"}
            }
        }
    
    async def execute(self, timezone: str = "UTC") -> ToolResult:
        from datetime import datetime
        import pytz
        
        try:
            tz = pytz.timezone(timezone) if timezone != "UTC" else pytz.UTC
            current_time = datetime.now(tz)
            return ToolResult(success=True, data={
                "datetime": current_time.isoformat(),
                "formatted": current_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                "timezone": timezone
            })
        except Exception as e:
            return ToolResult(success=False, error=str(e))

class MemorySearchTool(BaseTool):
    @property
    def name(self) -> str:
        return "memory_search"
    
    @property
    def description(self) -> str:
        return "Search user's conversation memories"
    
    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User ID to search memories for"},
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results", "default": 5}
            },
            "required": ["user_id", "query"]
        }
    
    async def execute(self, user_id: str, query: str, limit: int = 5) -> ToolResult:
        try:
            from ..memory.persistent_memory import memory_system
            memories = await memory_system.retrieve_memory(user_id, query, limit)
            return ToolResult(success=True, data=memories)
        except Exception as e:
            return ToolResult(success=False, error=str(e))

# Global instance
tool_engine = ToolExecutionEngine()