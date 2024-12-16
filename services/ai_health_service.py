
import os
import json
import logging
import httpx
from datetime import datetime, timedelta
from services.monitoring_service import bot_monitor, BotMetrics
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class AIHealthAnalyzer:
    def __init__(self):
        self.api_key = os.getenv('ABACUS_API_KEY')
        self.api_base_url = "https://api.abacus.ai/v0/gpt"
        self.metrics_history: List[BotMetrics] = []
        self.analysis_interval = 300  # 5 minutes
        self.last_analysis_time = None

    def add_metrics_snapshot(self, metrics: BotMetrics):
        """Add new metrics to history"""
        self.metrics_history.append(metrics)
        # Keep last hour of metrics
        cutoff = datetime.now() - timedelta(hours=1)
        self.metrics_history = [m for m in self.metrics_history 
                              if m.last_message_time and m.last_message_time > cutoff]

    async def analyze_health(self) -> Dict:
        """Generate health predictions and recommendations using AI"""
        if not self.metrics_history:
            return {
                "status": "insufficient_data",
                "predictions": [],
                "recommendations": []
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

            # Generate AI analysis using AbacusAI
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
                                "content": "You are an AI expert in analyzing bot infrastructure health metrics."
                            },
                            {
                                "role": "user",
                                "content": (
                                    "Analyze these Telegram bot metrics and provide health predictions "
                                    "and specific recommendations. Focus on performance, stability, and "
                                    "resource utilization. Respond in JSON format with 'predictions' and "
                                    "'recommendations' arrays.\n\n"
                                    f"Metrics: {json.dumps(metrics_summary)}"
                                )
                            }
                        ],
                        "response_format": {"type": "json_object"}
                    }
                )
                
                response.raise_for_status()
                analysis = response.json()
                analysis["status"] = "healthy" if metrics_summary["error_rate"] < 0.1 else "warning"
                
                logger.info(f"Generated health analysis: {analysis}")
                return analysis

        except Exception as e:
            logger.error(f"Error generating health analysis: {e}")
            return {
                "status": "error",
                "error": str(e),
                "predictions": [],
                "recommendations": []
            }

# Global instance
health_analyzer = AIHealthAnalyzer()
