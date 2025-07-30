"""
Performance Monitoring Service for Phone Call Mode
Tracks latency, quality metrics, and system performance
"""

import asyncio
import logging
import time
import psutil
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import deque
import json

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitor and track performance metrics for phone call mode"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        
        # Performance metrics
        self.call_metrics = deque(maxlen=max_history)
        self.stt_metrics = deque(maxlen=max_history)
        self.llm_metrics = deque(maxlen=max_history)
        self.tts_metrics = deque(maxlen=max_history)
        self.audio_metrics = deque(maxlen=max_history)
        
        # System metrics
        self.system_metrics = deque(maxlen=100)  # Last 100 system snapshots
        
        # Quality metrics
        self.quality_metrics = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "interrupted_calls": 0,
            "average_call_duration": 0.0,
            "audio_quality_issues": 0,
            "timeout_issues": 0
        }
        
        # Performance thresholds
        self.thresholds = {
            "stt_warning": 3.0,    # STT > 3s is slow
            "stt_critical": 5.0,   # STT > 5s is critical
            "llm_warning": 2.0,    # LLM > 2s is slow for phone calls
            "llm_critical": 5.0,   # LLM > 5s is critical
            "tts_warning": 2.0,    # TTS > 2s is slow
            "tts_critical": 4.0,   # TTS > 4s is critical
            "total_warning": 7.0,  # Total > 7s is slow
            "total_critical": 10.0, # Total > 10s is critical
            "memory_warning": 80.0, # Memory > 80% is concerning
            "cpu_warning": 85.0     # CPU > 85% is concerning
        }
        
        # Background system monitoring
        self.monitoring_active = False
        self.monitor_thread = None
        
        logger.info("Performance monitor initialized")
    
    def start_monitoring(self):
        """Start background system monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(target=self._system_monitor_loop, daemon=True)
            self.monitor_thread.start()
            logger.info("Background system monitoring started")
    
    def stop_monitoring(self):
        """Stop background system monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        logger.info("Background system monitoring stopped")
    
    def _system_monitor_loop(self):
        """Background loop to collect system metrics"""
        while self.monitoring_active:
            try:
                system_data = {
                    "timestamp": datetime.now().isoformat(),
                    "cpu_percent": psutil.cpu_percent(interval=1),
                    "memory_percent": psutil.virtual_memory().percent,
                    "memory_available_gb": psutil.virtual_memory().available / (1024**3),
                    "disk_usage_percent": psutil.disk_usage('/').percent if hasattr(psutil, 'disk_usage') else 0,
                    "active_connections": len(psutil.net_connections()),
                    "process_count": len(psutil.pids())
                }
                self.system_metrics.append(system_data)
                
                # Check for performance warnings
                self._check_system_health(system_data)
                
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
            
            time.sleep(5)  # Collect every 5 seconds
    
    def _check_system_health(self, system_data: Dict):
        """Check system health and log warnings"""
        if system_data["memory_percent"] > self.thresholds["memory_warning"]:
            logger.warning(f"High memory usage: {system_data['memory_percent']:.1f}%")
        
        if system_data["cpu_percent"] > self.thresholds["cpu_warning"]:
            logger.warning(f"High CPU usage: {system_data['cpu_percent']:.1f}%")
    
    def record_call_start(self, session_id: str, user_id: str = None, kid_friendly: bool = False):
        """Record the start of a phone call"""
        call_record = {
            "session_id": session_id,
            "user_id": user_id,
            "start_time": datetime.now().isoformat(),
            "kid_friendly": kid_friendly,
            "metrics": {
                "stt_calls": 0,
                "llm_calls": 0,
                "tts_calls": 0,
                "interruptions": 0,
                "audio_issues": 0
            }
        }
        self.call_metrics.append(call_record)
        self.quality_metrics["total_calls"] += 1
        
        logger.info(f"Call started tracking: {session_id}")
    
    def record_call_end(self, session_id: str, success: bool = True):
        """Record the end of a phone call"""
        # Find the call record
        call_record = None
        for record in reversed(self.call_metrics):
            if record["session_id"] == session_id and "end_time" not in record:
                call_record = record
                break
        
        if call_record:
            call_record["end_time"] = datetime.now().isoformat()
            call_record["success"] = success
            
            # Calculate duration
            start_time = datetime.fromisoformat(call_record["start_time"])
            end_time = datetime.fromisoformat(call_record["end_time"])
            duration = (end_time - start_time).total_seconds()
            call_record["duration_seconds"] = duration
            
            # Update quality metrics
            if success:
                self.quality_metrics["successful_calls"] += 1
            else:
                self.quality_metrics["failed_calls"] += 1
            
            # Update average duration
            total_calls = self.quality_metrics["successful_calls"] + self.quality_metrics["failed_calls"]
            if total_calls > 0:
                current_avg = self.quality_metrics["average_call_duration"]
                self.quality_metrics["average_call_duration"] = (
                    (current_avg * (total_calls - 1) + duration) / total_calls
                )
            
            logger.info(f"Call ended tracking: {session_id}, duration: {duration:.1f}s, success: {success}")
    
    def record_stt_performance(self, session_id: str, duration: float, audio_length: float, 
                             success: bool = True, error: str = None):
        """Record STT performance metrics"""
        stt_record = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "audio_length": audio_length,
            "success": success,
            "error": error,
            "latency_ratio": duration / max(audio_length, 0.1),  # Processing time vs audio time
            "performance_level": self._get_performance_level(duration, "stt")
        }
        self.stt_metrics.append(stt_record)
        
        # Update call record
        self._update_call_metrics(session_id, "stt_calls")
        
        if duration > self.thresholds["stt_warning"]:
            logger.warning(f"Slow STT performance: {duration:.2f}s for {audio_length:.2f}s audio")
    
    def record_llm_performance(self, session_id: str, duration: float, model: str, 
                             input_length: int, output_length: int, success: bool = True, error: str = None):
        """Record LLM performance metrics"""
        llm_record = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "model": model,
            "input_length": input_length,
            "output_length": output_length,
            "success": success,
            "error": error,
            "tokens_per_second": output_length / max(duration, 0.01),
            "performance_level": self._get_performance_level(duration, "llm")
        }
        self.llm_metrics.append(llm_record)
        
        # Update call record
        self._update_call_metrics(session_id, "llm_calls")
        
        if duration > self.thresholds["llm_warning"]:
            logger.warning(f"Slow LLM performance: {duration:.2f}s for model {model}")
    
    def record_tts_performance(self, session_id: str, duration: float, text_length: int, 
                             audio_duration: float, success: bool = True, error: str = None):
        """Record TTS performance metrics"""
        tts_record = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "text_length": text_length,
            "audio_duration": audio_duration,
            "success": success,
            "error": error,
            "chars_per_second": text_length / max(duration, 0.01),
            "realtime_factor": duration / max(audio_duration, 0.1),
            "performance_level": self._get_performance_level(duration, "tts")
        }
        self.tts_metrics.append(tts_record)
        
        # Update call record
        self._update_call_metrics(session_id, "tts_calls")
        
        if duration > self.thresholds["tts_warning"]:
            logger.warning(f"Slow TTS performance: {duration:.2f}s for {text_length} chars")
    
    def record_interrupt(self, session_id: str):
        """Record an interrupt event"""
        self._update_call_metrics(session_id, "interruptions")
        self.quality_metrics["interrupted_calls"] += 1
        logger.info(f"Interrupt recorded for session: {session_id}")
    
    def record_audio_issue(self, session_id: str, issue_type: str, details: str = None):
        """Record audio quality issues"""
        audio_record = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "issue_type": issue_type,
            "details": details
        }
        self.audio_metrics.append(audio_record)
        
        # Update call record and quality metrics
        self._update_call_metrics(session_id, "audio_issues")
        self.quality_metrics["audio_quality_issues"] += 1
        
        logger.warning(f"Audio issue recorded: {issue_type} for session {session_id}")
    
    def _update_call_metrics(self, session_id: str, metric_name: str):
        """Update metrics for a specific call"""
        for record in reversed(self.call_metrics):
            if record["session_id"] == session_id and "end_time" not in record:
                record["metrics"][metric_name] += 1
                break
    
    def _get_performance_level(self, duration: float, service_type: str) -> str:
        """Categorize performance level based on duration"""
        warning_threshold = self.thresholds.get(f"{service_type}_warning", 2.0)
        critical_threshold = self.thresholds.get(f"{service_type}_critical", 5.0)
        
        if duration <= warning_threshold * 0.5:
            return "excellent"
        elif duration <= warning_threshold:
            return "good"
        elif duration <= critical_threshold:
            return "slow"
        else:
            return "critical"
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        current_time = datetime.now()
        
        # Calculate recent performance (last hour)
        recent_cutoff = current_time - timedelta(hours=1)
        
        recent_stt = [m for m in self.stt_metrics 
                     if datetime.fromisoformat(m["timestamp"]) > recent_cutoff]
        recent_llm = [m for m in self.llm_metrics 
                     if datetime.fromisoformat(m["timestamp"]) > recent_cutoff]
        recent_tts = [m for m in self.tts_metrics 
                     if datetime.fromisoformat(m["timestamp"]) > recent_cutoff]
        
        def calc_avg(metrics, field):
            values = [m[field] for m in metrics if m["success"]]
            return sum(values) / len(values) if values else 0
        
        return {
            "timestamp": current_time.isoformat(),
            "quality_metrics": self.quality_metrics.copy(),
            "recent_performance": {
                "stt": {
                    "count": len(recent_stt),
                    "avg_duration": calc_avg(recent_stt, "duration"),
                    "success_rate": len([m for m in recent_stt if m["success"]]) / max(len(recent_stt), 1) * 100
                },
                "llm": {
                    "count": len(recent_llm),
                    "avg_duration": calc_avg(recent_llm, "duration"),
                    "success_rate": len([m for m in recent_llm if m["success"]]) / max(len(recent_llm), 1) * 100
                },
                "tts": {
                    "count": len(recent_tts),
                    "avg_duration": calc_avg(recent_tts, "duration"),
                    "success_rate": len([m for m in recent_tts if m["success"]]) / max(len(recent_tts), 1) * 100
                }
            },
            "system_health": self._get_current_system_health(),
            "performance_issues": self._identify_performance_issues(),
            "recommendations": self._generate_recommendations()
        }
    
    def _get_current_system_health(self) -> Dict[str, Any]:
        """Get current system health status"""
        if not self.system_metrics:
            return {"status": "unknown", "message": "No system data available"}
        
        latest = self.system_metrics[-1]
        health_status = "healthy"
        issues = []
        
        if latest["memory_percent"] > self.thresholds["memory_warning"]:
            health_status = "warning"
            issues.append(f"High memory usage: {latest['memory_percent']:.1f}%")
        
        if latest["cpu_percent"] > self.thresholds["cpu_warning"]:
            health_status = "warning"
            issues.append(f"High CPU usage: {latest['cpu_percent']:.1f}%")
        
        return {
            "status": health_status,
            "cpu_percent": latest["cpu_percent"],
            "memory_percent": latest["memory_percent"],
            "memory_available_gb": latest["memory_available_gb"],
            "issues": issues
        }
    
    def _identify_performance_issues(self) -> List[str]:
        """Identify current performance issues"""
        issues = []
        
        # Check recent performance
        recent_cutoff = datetime.now() - timedelta(minutes=15)
        
        recent_stt = [m for m in self.stt_metrics 
                     if datetime.fromisoformat(m["timestamp"]) > recent_cutoff]
        recent_llm = [m for m in self.llm_metrics 
                     if datetime.fromisoformat(m["timestamp"]) > recent_cutoff]
        recent_tts = [m for m in self.tts_metrics 
                     if datetime.fromisoformat(m["timestamp"]) > recent_cutoff]
        
        # STT issues
        slow_stt = [m for m in recent_stt if m["duration"] > self.thresholds["stt_warning"]]
        if slow_stt and len(slow_stt) / max(len(recent_stt), 1) > 0.3:
            issues.append(f"STT performance degraded: {len(slow_stt)}/{len(recent_stt)} calls slow")
        
        # LLM issues
        slow_llm = [m for m in recent_llm if m["duration"] > self.thresholds["llm_warning"]]
        if slow_llm and len(slow_llm) / max(len(recent_llm), 1) > 0.3:
            issues.append(f"LLM performance degraded: {len(slow_llm)}/{len(recent_llm)} calls slow")
        
        # TTS issues
        slow_tts = [m for m in recent_tts if m["duration"] > self.thresholds["tts_warning"]]
        if slow_tts and len(slow_tts) / max(len(recent_tts), 1) > 0.3:
            issues.append(f"TTS performance degraded: {len(slow_tts)}/{len(recent_tts)} calls slow")
        
        return issues
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []
        
        # Analyze recent performance patterns
        recent_cutoff = datetime.now() - timedelta(hours=1)
        recent_llm = [m for m in self.llm_metrics 
                     if datetime.fromisoformat(m["timestamp"]) > recent_cutoff]
        
        if recent_llm:
            avg_llm_duration = sum(m["duration"] for m in recent_llm if m["success"]) / max(len(recent_llm), 1)
            
            if avg_llm_duration > self.thresholds["llm_warning"]:
                recommendations.append("Consider switching to a smaller, faster LLM model (phi3-mini)")
            
            # Check model distribution
            model_usage = {}
            for m in recent_llm:
                model = m.get("model", "unknown")
                model_usage[model] = model_usage.get(model, 0) + 1
            
            if "gemma3:2b" in model_usage and model_usage["gemma3:2b"] > len(recent_llm) * 0.5:
                recommendations.append("Too many calls using larger model - optimize model selection")
        
        # System recommendations
        if self.system_metrics:
            latest_system = self.system_metrics[-1]
            if latest_system["memory_percent"] > 70:
                recommendations.append("Consider increasing system memory or optimizing memory usage")
            if latest_system["cpu_percent"] > 75:
                recommendations.append("High CPU usage detected - consider load balancing")
        
        return recommendations

# Global instance
performance_monitor = PerformanceMonitor()
