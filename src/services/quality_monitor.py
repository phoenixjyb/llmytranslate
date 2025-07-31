"""
Quality Monitoring and Fallback Service for Phone Call Mode
Monitors service quality and provides intelligent fallbacks
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)

class ServiceHealth(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"

class QualityLevel(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    UNACCEPTABLE = "unacceptable"

class QualityMonitor:
    """Monitor and manage service quality with intelligent fallbacks"""
    
    def __init__(self):
        # Service health tracking
        self.service_health = {
            "stt": ServiceHealth.HEALTHY,
            "llm": ServiceHealth.HEALTHY,
            "tts": ServiceHealth.HEALTHY,
            "background_music": ServiceHealth.HEALTHY
        }
        
        # Quality thresholds
        self.quality_thresholds = {
            "stt": {
                "excellent": 1.0,
                "good": 2.0,
                "acceptable": 3.0,
                "poor": 5.0
            },
            "llm": {
                "excellent": 1.0,
                "good": 2.0,
                "acceptable": 4.0,
                "poor": 8.0
            },
            "tts": {
                "excellent": 1.5,
                "good": 2.5,
                "acceptable": 4.0,
                "poor": 6.0
            }
        }
        
        # Fallback configurations
        self.fallback_configs = {
            "stt": {
                "primary": "whisper_local",
                "fallbacks": ["whisper_api", "google_speech", "azure_speech"],
                "emergency": "simple_speech_detection"
            },
            "llm": {
                "primary": "phi3-mini",
                "fallbacks": ["gemma2:2b", "llama3.2:1b", "gemma3:2b"],
                "emergency": "simple_responses"
            },
            "tts": {
                "primary": "coqui_tts",
                "fallbacks": ["system_tts", "openai_tts"],
                "emergency": "text_only_response"
            }
        }
        
        # Health check history
        self.health_history = {}
        self.quality_history = {}
        
        # Circuit breaker settings
        self.circuit_breakers = {}
        
        # Callback functions for service switching
        self.fallback_callbacks: Dict[str, List[Callable]] = {}
        
        logger.info("Quality monitor initialized")
    
    def register_fallback_callback(self, service: str, callback: Callable):
        """Register a callback to be called when service falls back"""
        if service not in self.fallback_callbacks:
            self.fallback_callbacks[service] = []
        self.fallback_callbacks[service].append(callback)
    
    def record_service_performance(self, service: str, duration: float, 
                                 success: bool, error: str = None) -> QualityLevel:
        """Record performance and determine quality level"""
        timestamp = datetime.now()
        
        # Determine quality level
        quality = self._determine_quality_level(service, duration, success)
        
        # Record in history
        if service not in self.quality_history:
            self.quality_history[service] = []
        
        self.quality_history[service].append({
            "timestamp": timestamp.isoformat(),
            "duration": duration,
            "success": success,
            "error": error,
            "quality": quality.value
        })
        
        # Keep only recent history (last 100 entries)
        self.quality_history[service] = self.quality_history[service][-100:]
        
        # Update service health
        self._update_service_health(service)
        
        # Check if fallback is needed
        if self._should_trigger_fallback(service):
            asyncio.create_task(self._trigger_fallback(service))
        
        return quality
    
    def _determine_quality_level(self, service: str, duration: float, success: bool) -> QualityLevel:
        """Determine quality level based on performance metrics"""
        if not success:
            return QualityLevel.UNACCEPTABLE
        
        thresholds = self.quality_thresholds.get(service, self.quality_thresholds["llm"])
        
        if duration <= thresholds["excellent"]:
            return QualityLevel.EXCELLENT
        elif duration <= thresholds["good"]:
            return QualityLevel.GOOD
        elif duration <= thresholds["acceptable"]:
            return QualityLevel.ACCEPTABLE
        elif duration <= thresholds["poor"]:
            return QualityLevel.POOR
        else:
            return QualityLevel.UNACCEPTABLE
    
    def _update_service_health(self, service: str):
        """Update overall service health based on recent performance"""
        if service not in self.quality_history:
            return
        
        recent_cutoff = datetime.now() - timedelta(minutes=5)
        recent_records = [
            r for r in self.quality_history[service]
            if datetime.fromisoformat(r["timestamp"]) > recent_cutoff
        ]
        
        if not recent_records:
            return
        
        # Calculate success rate and average quality
        successful_records = [r for r in recent_records if r["success"]]
        success_rate = len(successful_records) / len(recent_records)
        
        if success_rate < 0.5:
            self.service_health[service] = ServiceHealth.OFFLINE
        elif success_rate < 0.7:
            self.service_health[service] = ServiceHealth.UNHEALTHY
        else:
            # Check quality distribution
            quality_scores = {"excellent": 4, "good": 3, "acceptable": 2, "poor": 1, "unacceptable": 0}
            avg_quality = sum(quality_scores.get(r["quality"], 0) for r in successful_records) / len(successful_records)
            
            if avg_quality >= 3.0:
                self.service_health[service] = ServiceHealth.HEALTHY
            elif avg_quality >= 2.0:
                self.service_health[service] = ServiceHealth.DEGRADED
            else:
                self.service_health[service] = ServiceHealth.UNHEALTHY
    
    def _should_trigger_fallback(self, service: str) -> bool:
        """Determine if a fallback should be triggered"""
        health = self.service_health.get(service, ServiceHealth.HEALTHY)
        
        # Trigger fallback if service is unhealthy or offline
        if health in [ServiceHealth.UNHEALTHY, ServiceHealth.OFFLINE]:
            return True
        
        # Check circuit breaker
        if service in self.circuit_breakers:
            breaker = self.circuit_breakers[service]
            if breaker.get("state") == "open":
                return True
        
        return False
    
    async def _trigger_fallback(self, service: str):
        """Trigger fallback for a service"""
        fallback_config = self.fallback_configs.get(service)
        if not fallback_config:
            logger.warning(f"No fallback configuration for service: {service}")
            return
        
        # Try fallback services in order
        for fallback_service in fallback_config["fallbacks"]:
            if await self._test_service_availability(service, fallback_service):
                logger.info(f"Falling back from {fallback_config['primary']} to {fallback_service} for {service}")
                
                # Notify callbacks
                if service in self.fallback_callbacks:
                    for callback in self.fallback_callbacks[service]:
                        try:
                            await callback(service, fallback_service)
                        except Exception as e:
                            logger.error(f"Error in fallback callback: {e}")
                
                return fallback_service
        
        # If all fallbacks fail, use emergency service
        emergency_service = fallback_config["emergency"]
        logger.warning(f"All fallbacks failed for {service}, using emergency service: {emergency_service}")
        
        return emergency_service
    
    async def _test_service_availability(self, service_type: str, service_name: str) -> bool:
        """Test if a fallback service is available"""
        try:
            if service_type == "llm":
                # Test LLM availability with a simple request
                from ..services.optimized_llm_service import optimized_llm_service
                result = await optimized_llm_service.fast_completion(
                    message="test",
                    model=service_name,
                    timeout=3.0
                )
                return result.get("success", False)
            
            elif service_type == "stt":
                # Test STT availability
                # For now, assume available if configured
                return True
            
            elif service_type == "tts":
                # Test TTS availability
                # For now, assume available if configured
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to test {service_name} availability: {e}")
            return False
    
    def get_service_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for optimal service configuration"""
        recommendations = []
        
        # Analyze recent performance
        for service, health in self.service_health.items():
            if health == ServiceHealth.DEGRADED:
                recommendations.append({
                    "service": service,
                    "type": "performance",
                    "message": f"{service} performance is degraded - consider fallback options",
                    "severity": "warning"
                })
            elif health == ServiceHealth.UNHEALTHY:
                recommendations.append({
                    "service": service,
                    "type": "availability",
                    "message": f"{service} is unhealthy - immediate fallback recommended",
                    "severity": "critical"
                })
        
        # Model-specific recommendations
        if "llm" in self.quality_history:
            recent_llm = self.quality_history["llm"][-20:]  # Last 20 requests
            if recent_llm:
                avg_duration = sum(r["duration"] for r in recent_llm if r["success"]) / len(recent_llm)
                if avg_duration > 3.0:
                    recommendations.append({
                        "service": "llm",
                        "type": "optimization",
                        "message": f"LLM responses are slow (avg: {avg_duration:.2f}s) - consider phi3-mini",
                        "severity": "info"
                    })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "service_health": {k: v.value for k, v in self.service_health.items()},
            "recommendations": recommendations,
            "optimal_configuration": self._get_optimal_configuration()
        }
    
    def _get_optimal_configuration(self) -> Dict[str, str]:
        """Get optimal service configuration based on current performance"""
        config = {}
        
        for service in ["stt", "llm", "tts"]:
            health = self.service_health.get(service, ServiceHealth.HEALTHY)
            fallback_config = self.fallback_configs.get(service, {})
            
            if health in [ServiceHealth.HEALTHY, ServiceHealth.DEGRADED]:
                config[service] = fallback_config.get("primary", "default")
            else:
                # Use first available fallback
                config[service] = fallback_config.get("fallbacks", ["default"])[0]
        
        return config
    
    def force_fallback(self, service: str, target_service: str = None) -> bool:
        """Manually force a fallback for a service"""
        fallback_config = self.fallback_configs.get(service)
        if not fallback_config:
            return False
        
        if target_service is None:
            target_service = fallback_config["fallbacks"][0]
        
        logger.info(f"Manually forcing fallback for {service} to {target_service}")
        
        # Update service health to trigger fallback behavior
        self.service_health[service] = ServiceHealth.UNHEALTHY
        
        # Trigger fallback
        asyncio.create_task(self._trigger_fallback(service))
        
        return True
    
    def reset_service_health(self, service: str):
        """Reset service health to healthy state"""
        self.service_health[service] = ServiceHealth.HEALTHY
        
        # Clear circuit breaker if it exists
        if service in self.circuit_breakers:
            self.circuit_breakers[service]["state"] = "closed"
        
        logger.info(f"Reset {service} health to healthy")
    
    def get_quality_report(self) -> Dict[str, Any]:
        """Get comprehensive quality report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "service_health": {k: v.value for k, v in self.service_health.items()},
            "recent_performance": {},
            "quality_trends": {},
            "recommendations": self.get_service_recommendations()
        }
        
        # Calculate recent performance metrics
        recent_cutoff = datetime.now() - timedelta(minutes=15)
        
        for service, history in self.quality_history.items():
            recent_records = [
                r for r in history
                if datetime.fromisoformat(r["timestamp"]) > recent_cutoff
            ]
            
            if recent_records:
                successful_records = [r for r in recent_records if r["success"]]
                
                report["recent_performance"][service] = {
                    "total_requests": len(recent_records),
                    "successful_requests": len(successful_records),
                    "success_rate": len(successful_records) / len(recent_records) * 100,
                    "average_duration": sum(r["duration"] for r in successful_records) / max(len(successful_records), 1),
                    "quality_distribution": self._calculate_quality_distribution(successful_records)
                }
        
        return report
    
    def _calculate_quality_distribution(self, records: List[Dict]) -> Dict[str, int]:
        """Calculate distribution of quality levels"""
        distribution = {"excellent": 0, "good": 0, "acceptable": 0, "poor": 0, "unacceptable": 0}
        
        for record in records:
            quality = record.get("quality", "unacceptable")
            if quality in distribution:
                distribution[quality] += 1
        
        return distribution
    
    def get_quality_summary(self) -> Dict[str, Any]:
        """Get comprehensive quality summary for status monitoring"""
        try:
            summary = {
                "timestamp": datetime.now().isoformat(),
                "overall_quality": self.overall_quality_level.value,
                "service_health": {service: health.value for service, health in self.service_health.items()},
                "quality_metrics": {
                    "total_assessments": sum(len(history) for history in self.quality_history.values()),
                    "recent_quality_trend": self.get_quality_trend(),
                    "quality_distribution": self.get_quality_distribution()
                },
                "performance_summary": self.get_performance_summary(),
                "service_status": {
                    "healthy_services": sum(1 for h in self.service_health.values() if h == ServiceHealth.HEALTHY),
                    "total_services": len(self.service_health),
                    "degraded_services": [service for service, health in self.service_health.items() 
                                        if health == ServiceHealth.DEGRADED]
                }
            }
            return summary
        except Exception as e:
            logger.error(f"Error getting quality summary: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def get_current_quality_level(self) -> QualityLevel:
        """Get current overall quality level"""
        return self.overall_quality_level
    
    def get_quality_trend(self) -> str:
        """Get quality trend direction"""
        try:
            # Analyze recent quality history to determine trend
            recent_cutoff = datetime.now() - timedelta(hours=1)
            all_recent = []
            
            for history in self.quality_history.values():
                recent = [r for r in history if datetime.fromisoformat(r["timestamp"]) > recent_cutoff]
                all_recent.extend(recent)
            
            if len(all_recent) < 5:
                return "insufficient_data"
            
            # Sort by timestamp and analyze trend
            all_recent.sort(key=lambda x: x["timestamp"])
            
            # Compare first half vs second half quality scores
            mid_point = len(all_recent) // 2
            first_half = all_recent[:mid_point]
            second_half = all_recent[mid_point:]
            
            first_avg = sum(self._quality_to_score(r.get("quality", "poor")) for r in first_half) / len(first_half)
            second_avg = sum(self._quality_to_score(r.get("quality", "poor")) for r in second_half) / len(second_half)
            
            if second_avg > first_avg + 0.5:
                return "improving"
            elif second_avg < first_avg - 0.5:
                return "declining"
            else:
                return "stable"
                
        except Exception as e:
            logger.error(f"Error calculating quality trend: {e}")
            return "unknown"
    
    def get_total_assessments(self) -> int:
        """Get total number of quality assessments performed"""
        return sum(len(history) for history in self.quality_history.values())
    
    def get_quality_distribution(self) -> Dict[str, int]:
        """Get distribution of quality levels across all services"""
        try:
            distribution = {"excellent": 0, "good": 0, "acceptable": 0, "poor": 0, "unacceptable": 0}
            
            for history in self.quality_history.values():
                for record in history:
                    quality = record.get("quality", "unacceptable")
                    if quality in distribution:
                        distribution[quality] += 1
            
            return distribution
        except Exception as e:
            logger.error(f"Error calculating quality distribution: {e}")
            return {"excellent": 0, "good": 0, "acceptable": 0, "poor": 0, "unacceptable": 0}
    
    def _quality_to_score(self, quality: str) -> float:
        """Convert quality level to numeric score for trend analysis"""
        scores = {
            "excellent": 5.0,
            "good": 4.0,
            "acceptable": 3.0,
            "poor": 2.0,
            "unacceptable": 1.0
        }
        return scores.get(quality, 1.0)

# Global instance
quality_monitor = QualityMonitor()
