import os
import json
import logging
import httpx
import asyncio
from datetime import datetime, timedelta
from services.monitoring_service import bot_monitor, BotMetrics
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class AIHealthAnalyzer:
    def __init__(self):
        self.api_key = os.getenv('ABACUS_API_KEY')
        if not self.api_key:
            logger.error("ABACUS_API_KEY is not set in environment variables")
            raise ValueError("ABACUS_API_KEY is required")
            
        # Abacus AI GPT4 endpoint
        self.api_base_url = "https://api.abacus.ai/v0/gpt4"
        self.metrics_history: List[BotMetrics] = []
        self.analysis_interval = 300  # 5 minutes
        self.last_analysis_time: Optional[datetime] = None
        self._lock = asyncio.Lock()

    def add_metrics_snapshot(self, metrics: BotMetrics):
        """Add new metrics to history"""
        self.metrics_history.append(metrics)
        # Keep last hour of metrics
        cutoff = datetime.now() - timedelta(hours=1)
        self.metrics_history = [m for m in self.metrics_history 
                              if m.last_message_time and m.last_message_time > cutoff]

    async def analyze_health(self) -> Dict:
        """Generate health predictions and recommendations using Abacus AI"""
        async with self._lock:
            if not self.metrics_history:
                return {
                    "status": "insufficient_data",
                    "predictions": [],
                    "recommendations": [],
                    "alerts": []
                }

            try:
                # Prepare metrics summary for AI analysis
                recent_metrics = self.metrics_history[-10:]  # Last 10 snapshots
                metrics_summary = {
                    "average_cpu": sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics),
                    "average_memory": sum(m.memory_usage for m in recent_metrics) / len(recent_metrics),
                    "error_rate": sum(1 for m in recent_metrics if m.error_count > 0) / len(recent_metrics),
                    "response_times": [sum(m.response_times) / len(m.response_times) if m.response_times else 0 
                                     for m in recent_metrics],
                    "message_volume": sum(m.message_count for m in recent_metrics),
                    "recent_errors": [err for m in recent_metrics for err in m.recent_errors]
                }

                # Detect trends and anomalies
                response_time_trend = self._calculate_trend(metrics_summary["response_times"])
                cpu_threshold_exceeded = metrics_summary["average_cpu"] > 80
                memory_threshold_exceeded = metrics_summary["average_memory"] > 1024  # 1GB

                # Generate AI analysis using Abacus AI
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.api_base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "messages": [
                                {
                                    "role": "system",
                                    "content": (
                                        "You are an AI expert in analyzing bot infrastructure health metrics. "
                                        "Provide detailed analysis with actionable recommendations."
                                    )
                                },
                                {
                                    "role": "user",
                                    "content": (
                                        f"Analyze these Telegram bot metrics and provide health predictions "
                                        f"and specific recommendations:\n{json.dumps(metrics_summary)}\n"
                                        f"Additional context:\n"
                                        f"- Response time trend: {response_time_trend}\n"
                                        f"- CPU threshold exceeded: {cpu_threshold_exceeded}\n"
                                        f"- Memory threshold exceeded: {memory_threshold_exceeded}\n"
                                        "Provide analysis in JSON format with the following structure:\n"
                                        "{\n"
                                        "  'status': 'healthy'|'warning'|'critical',\n"
                                        "  'predictions': [{'issue': string, 'probability': float, 'impact': string}],\n"
                                        "  'recommendations': [{'action': string, 'priority': high|medium|low, 'rationale': string}],\n"
                                        "  'alerts': [{'type': string, 'message': string, 'severity': string}]\n"
                                        "}"
                                    )
                                }
                            ],
                            "response_format": {"type": "json_object"}
                        }
                    )
                    
                    response.raise_for_status()
                    analysis = response.json()
                    
                    # Add system-generated alerts
                    if cpu_threshold_exceeded:
                        analysis["alerts"].append({
                            "type": "resource_usage",
                            "message": "High CPU usage detected",
                            "severity": "warning"
                        })
                    if memory_threshold_exceeded:
                        analysis["alerts"].append({
                            "type": "resource_usage",
                            "message": "High memory usage detected",
                            "severity": "warning"
                        })
                    
                    logger.info(f"Generated health analysis: {analysis}")
                    return analysis

            except Exception as e:
                logger.error(f"Error generating health analysis: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "predictions": [],
                    "recommendations": [],
                    "alerts": [{
                        "type": "system",
                        "message": f"Analysis failed: {str(e)}",
                        "severity": "error"
                    }]
                }

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a series of values"""
        if not values or len(values) < 2:
            return "insufficient_data"
            
        differences = [values[i] - values[i-1] for i in range(1, len(values))]
        avg_change = sum(differences) / len(differences)
        
        if abs(avg_change) < 0.1:  # Threshold for significant change
            return "stable"
        return "increasing" if avg_change > 0 else "decreasing"

# Global instance
health_analyzer = AIHealthAnalyzer()