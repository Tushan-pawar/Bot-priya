"""Self-optimization logging and analysis system."""
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from ..utils.logging import logger

@dataclass
class FailedResponse:
    """Failed response entry."""
    timestamp: str
    user_id: str
    server_id: Optional[str]
    user_message: str
    bot_response: str
    failure_reason: str
    context: Dict[str, Any]
    severity: str  # low, medium, high, critical

@dataclass
class UnclearQuery:
    """Unclear query entry."""
    timestamp: str
    user_id: str
    server_id: Optional[str]
    query: str
    attempted_response: str
    confidence_score: float
    context: Dict[str, Any]

@dataclass
class OptimizationInsight:
    """Optimization insight."""
    timestamp: str
    category: str  # response_quality, user_satisfaction, performance
    issue: str
    suggested_fix: str
    priority: str  # low, medium, high
    affected_users: List[str]
    frequency: int

class SelfOptimizationLogger:
    """Logs and analyzes bot performance for self-improvement."""
    
    def __init__(self, data_dir: str = "data/optimization"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.failed_responses_file = self.data_dir / "failed_responses.jsonl"
        self.unclear_queries_file = self.data_dir / "unclear_queries.jsonl"
        self.insights_file = self.data_dir / "insights.json"
        
        self.failed_responses: List[FailedResponse] = []
        self.unclear_queries: List[UnclearQuery] = []
        self.insights: List[OptimizationInsight] = []
        
        # Load existing data
        self._load_data()
        
        # Start background analysis
        asyncio.create_task(self._background_analysis())
    
    def _load_data(self):
        """Load existing optimization data."""
        try:
            # Load failed responses
            if self.failed_responses_file.exists():
                with open(self.failed_responses_file, 'r') as f:
                    for line in f:
                        data = json.loads(line.strip())
                        self.failed_responses.append(FailedResponse(**data))
            
            # Load unclear queries
            if self.unclear_queries_file.exists():
                with open(self.unclear_queries_file, 'r') as f:
                    for line in f:
                        data = json.loads(line.strip())
                        self.unclear_queries.append(UnclearQuery(**data))
            
            # Load insights
            if self.insights_file.exists():
                with open(self.insights_file, 'r') as f:
                    data = json.load(f)
                    self.insights = [OptimizationInsight(**item) for item in data]
            
            logger.info(f"Loaded {len(self.failed_responses)} failed responses, "
                       f"{len(self.unclear_queries)} unclear queries, "
                       f"{len(self.insights)} insights")
                       
        except Exception as e:
            logger.error(f"Failed to load optimization data: {e}")
    
    async def log_failed_response(
        self,
        user_id: str,
        user_message: str,
        bot_response: str,
        failure_reason: str,
        server_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        severity: str = "medium"
    ):
        """Log a failed response."""
        failed_response = FailedResponse(
            timestamp=datetime.now().isoformat(),
            user_id=user_id,
            server_id=server_id,
            user_message=user_message,
            bot_response=bot_response,
            failure_reason=failure_reason,
            context=context or {},
            severity=severity
        )
        
        self.failed_responses.append(failed_response)
        
        # Append to file
        with open(self.failed_responses_file, 'a') as f:
            f.write(json.dumps(asdict(failed_response)) + '\n')
        
        logger.warning(f"Failed response logged: {failure_reason}")
    
    async def log_unclear_query(
        self,
        user_id: str,
        query: str,
        attempted_response: str,
        confidence_score: float,
        server_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Log an unclear query."""
        unclear_query = UnclearQuery(
            timestamp=datetime.now().isoformat(),
            user_id=user_id,
            server_id=server_id,
            query=query,
            attempted_response=attempted_response,
            confidence_score=confidence_score,
            context=context or {}
        )
        
        self.unclear_queries.append(unclear_query)
        
        # Append to file
        with open(self.unclear_queries_file, 'a') as f:
            f.write(json.dumps(asdict(unclear_query)) + '\n')
        
        logger.info(f"Unclear query logged: {query[:50]}... (confidence: {confidence_score})")
    
    async def _background_analysis(self):
        """Background analysis for generating insights."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                await self._analyze_patterns()
                await self._cleanup_old_data()
                
            except Exception as e:
                logger.error(f"Background analysis error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _analyze_patterns(self):
        """Analyze patterns in failed responses and unclear queries."""
        # Analyze failed responses
        await self._analyze_failed_responses()
        
        # Analyze unclear queries
        await self._analyze_unclear_queries()
        
        # Save insights
        await self._save_insights()
    
    async def _analyze_failed_responses(self):
        """Analyze patterns in failed responses."""
        if len(self.failed_responses) < 10:
            return
        
        # Get recent failures (last 24 hours)
        cutoff = datetime.now() - timedelta(hours=24)
        recent_failures = [
            f for f in self.failed_responses
            if datetime.fromisoformat(f.timestamp) > cutoff
        ]
        
        if not recent_failures:
            return
        
        # Analyze failure reasons
        failure_counts = {}
        for failure in recent_failures:
            reason = failure.failure_reason
            failure_counts[reason] = failure_counts.get(reason, 0) + 1
        
        # Generate insights for common failures
        for reason, count in failure_counts.items():
            if count >= 3:  # At least 3 occurrences
                insight = OptimizationInsight(
                    timestamp=datetime.now().isoformat(),
                    category="response_quality",
                    issue=f"Frequent failure: {reason}",
                    suggested_fix=self._suggest_fix_for_failure(reason),
                    priority="high" if count >= 10 else "medium",
                    affected_users=list(set(f.user_id for f in recent_failures if f.failure_reason == reason)),
                    frequency=count
                )
                
                # Check if we already have this insight
                if not any(i.issue == insight.issue for i in self.insights):
                    self.insights.append(insight)
    
    async def _analyze_unclear_queries(self):
        """Analyze patterns in unclear queries."""
        if len(self.unclear_queries) < 5:
            return
        
        # Get recent unclear queries (last 24 hours)
        cutoff = datetime.now() - timedelta(hours=24)
        recent_unclear = [
            q for q in self.unclear_queries
            if datetime.fromisoformat(q.timestamp) > cutoff
        ]
        
        if not recent_unclear:
            return
        
        # Find queries with very low confidence
        low_confidence = [q for q in recent_unclear if q.confidence_score < 0.3]
        
        if len(low_confidence) >= 3:
            insight = OptimizationInsight(
                timestamp=datetime.now().isoformat(),
                category="user_satisfaction",
                issue="High number of low-confidence responses",
                suggested_fix="Improve training data or add clarification prompts",
                priority="medium",
                affected_users=list(set(q.user_id for q in low_confidence)),
                frequency=len(low_confidence)
            )
            
            if not any(i.issue == insight.issue for i in self.insights):
                self.insights.append(insight)
    
    def _suggest_fix_for_failure(self, failure_reason: str) -> str:
        """Suggest fixes for common failure reasons."""
        suggestions = {
            "timeout": "Increase timeout values or optimize model selection",
            "api_limit": "Add more API providers or implement better rate limiting",
            "model_unavailable": "Improve fallback system or add more local models",
            "parsing_error": "Improve input validation and error handling",
            "memory_error": "Optimize memory usage or increase limits",
            "network_error": "Add retry logic and better error handling"
        }
        
        for key, suggestion in suggestions.items():
            if key in failure_reason.lower():
                return suggestion
        
        return "Review logs and implement specific fix for this failure type"
    
    async def _save_insights(self):
        """Save insights to file."""
        try:
            with open(self.insights_file, 'w') as f:
                json.dump([asdict(insight) for insight in self.insights], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save insights: {e}")
    
    async def _cleanup_old_data(self):
        """Clean up old data to prevent file growth."""
        cutoff = datetime.now() - timedelta(days=30)
        
        # Clean failed responses
        self.failed_responses = [
            f for f in self.failed_responses
            if datetime.fromisoformat(f.timestamp) > cutoff
        ]
        
        # Clean unclear queries
        self.unclear_queries = [
            q for q in self.unclear_queries
            if datetime.fromisoformat(q.timestamp) > cutoff
        ]
        
        # Clean old insights
        self.insights = [
            i for i in self.insights
            if datetime.fromisoformat(i.timestamp) > cutoff
        ]
        
        # Rewrite files
        await self._rewrite_data_files()
    
    async def _rewrite_data_files(self):
        """Rewrite data files after cleanup."""
        try:
            # Rewrite failed responses
            with open(self.failed_responses_file, 'w') as f:
                for failure in self.failed_responses:
                    f.write(json.dumps(asdict(failure)) + '\n')
            
            # Rewrite unclear queries
            with open(self.unclear_queries_file, 'w') as f:
                for query in self.unclear_queries:
                    f.write(json.dumps(asdict(query)) + '\n')
            
            # Save insights
            await self._save_insights()
            
        except Exception as e:
            logger.error(f"Failed to rewrite data files: {e}")
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Get optimization report for admin review."""
        # Get recent data (last 7 days)
        cutoff = datetime.now() - timedelta(days=7)
        
        recent_failures = [
            f for f in self.failed_responses
            if datetime.fromisoformat(f.timestamp) > cutoff
        ]
        
        recent_unclear = [
            q for q in self.unclear_queries
            if datetime.fromisoformat(q.timestamp) > cutoff
        ]
        
        recent_insights = [
            i for i in self.insights
            if datetime.fromisoformat(i.timestamp) > cutoff
        ]
        
        # Calculate metrics
        total_failures = len(recent_failures)
        total_unclear = len(recent_unclear)
        avg_confidence = sum(q.confidence_score for q in recent_unclear) / len(recent_unclear) if recent_unclear else 1.0
        
        # Group failures by reason
        failure_reasons = {}
        for failure in recent_failures:
            reason = failure.failure_reason
            failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
        
        return {
            "period": "Last 7 days",
            "total_failures": total_failures,
            "total_unclear_queries": total_unclear,
            "average_confidence": round(avg_confidence, 3),
            "failure_reasons": failure_reasons,
            "insights": [asdict(i) for i in recent_insights],
            "recommendations": self._generate_recommendations(recent_failures, recent_unclear, recent_insights)
        }
    
    def _generate_recommendations(
        self, 
        failures: List[FailedResponse], 
        unclear: List[UnclearQuery], 
        insights: List[OptimizationInsight]
    ) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        if len(failures) > 50:
            recommendations.append("High failure rate detected. Consider reviewing API limits and fallback systems.")
        
        if len(unclear) > 20:
            recommendations.append("Many unclear queries. Consider improving prompt engineering or adding clarification flows.")
        
        high_priority_insights = [i for i in insights if i.priority == "high"]
        if high_priority_insights:
            recommendations.append(f"Address {len(high_priority_insights)} high-priority issues immediately.")
        
        if not recommendations:
            recommendations.append("System performance is stable. Continue monitoring.")
        
        return recommendations

# Global optimization logger
optimization_logger = SelfOptimizationLogger()