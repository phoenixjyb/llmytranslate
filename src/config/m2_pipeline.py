"""
M2 MacBook Pipeline Configuration Manager
Optimized settings for Apple M2 chip with Metal GPU acceleration
"""

import yaml
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ModelTier:
    """Configuration for a model performance tier"""
    name: str
    size: str
    speed: str
    use_case: str
    memory_usage: str


@dataclass 
class M2PipelineConfig:
    """M2 MacBook Pipeline Configuration"""
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            # Look for config in the project root config directory
            project_root = Path(__file__).parent.parent.parent
            config_path = str(project_root / "config" / "m2_pipeline_config.yaml")
        
        self.config_path = Path(config_path)
        self._config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"M2 config file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in M2 config: {e}")
    
    @property
    def pipeline_info(self) -> Dict[str, Any]:
        """Get pipeline information"""
        return self._config.get("pipeline_info", {})
    
    @property
    def model_tiers(self) -> Dict[str, List[ModelTier]]:
        """Get model tiers configuration"""
        tiers = {}
        for tier_name, tier_config in self._config.get("model_tiers", {}).items():
            models = []
            for model_config in tier_config.get("models", []):
                models.append(ModelTier(
                    name=model_config["name"],
                    size=model_config["size"], 
                    speed=model_config["speed"],
                    use_case=model_config["use_case"],
                    memory_usage=model_config["memory_usage"]
                ))
            tiers[tier_name] = models
        return tiers
    
    @property
    def performance_settings(self) -> Dict[str, Any]:
        """Get performance settings"""
        return self._config.get("performance_settings", {})
    
    @property 
    def routing_strategy(self) -> Dict[str, Any]:
        """Get routing strategy configuration"""
        return self._config.get("routing_strategy", {})
    
    @property
    def quality_settings(self) -> Dict[str, Any]:
        """Get quality settings"""
        return self._config.get("quality_settings", {})
    
    @property
    def monitoring(self) -> Dict[str, Any]:
        """Get monitoring configuration"""
        return self._config.get("monitoring", {})
    
    @property
    def integration(self) -> Dict[str, Any]:
        """Get integration settings"""
        return self._config.get("integration", {})
    
    @property
    def deployment(self) -> Dict[str, Any]:
        """Get deployment configuration"""
        return self._config.get("deployment", {})
    
    def get_model_for_speed_requirement(self, max_seconds: float) -> Optional[str]:
        """Get the best model for a speed requirement"""
        thresholds = self.routing_strategy
        
        if max_seconds <= thresholds.get("realtime_threshold", 0.5):
            # Ultra fast tier
            ultra_fast = self.model_tiers.get("ultra_fast", [])
            return ultra_fast[0].name if ultra_fast else None
            
        elif max_seconds <= thresholds.get("interactive_threshold", 1.0):
            # Fast tier
            fast = self.model_tiers.get("fast", [])
            return fast[0].name if fast else None
            
        elif max_seconds <= thresholds.get("batch_threshold", 3.0):
            # Capable tier
            capable = self.model_tiers.get("capable", [])
            return capable[0].name if capable else None
            
        else:
            # Advanced tier
            advanced = self.model_tiers.get("advanced", [])
            return advanced[0].name if advanced else None
    
    def get_fallback_models(self) -> List[str]:
        """Get fallback model order"""
        return self.routing_strategy.get("fallback_order", [])
    
    def get_startup_models(self) -> List[str]:
        """Get models to load at startup"""
        return self.deployment.get("startup_models", [])
    
    def get_lazy_load_models(self) -> List[str]:
        """Get models to load on demand"""
        return self.deployment.get("lazy_load_models", [])
    
    def get_max_tokens_for_tier(self, tier: str) -> int:
        """Get max tokens for a model tier"""
        quality = self.quality_settings
        max_tokens = quality.get("max_tokens", {})
        return max_tokens.get(tier, 200)
    
    def should_bypass_proxy(self) -> bool:
        """Check if should bypass proxy for local connections"""
        return self.performance_settings.get("bypass_proxy_for_local", True)
    
    def get_local_endpoints(self) -> List[str]:
        """Get list of local endpoints to bypass proxy"""
        return self.performance_settings.get("local_endpoints", ["localhost", "127.0.0.1"])
    
    def get_concurrent_request_limit(self) -> int:
        """Get maximum concurrent requests"""
        return self.performance_settings.get("max_concurrent_requests", 8)
    
    def get_memory_threshold(self) -> float:
        """Get memory threshold for model unloading"""
        return self.performance_settings.get("memory_threshold", 0.75)
    
    def get_response_time_alert_threshold(self, tier: str) -> float:
        """Get response time alert threshold for a tier"""
        alerts = self.monitoring.get("response_time_alerts", {})
        return alerts.get(tier, 10.0)  # Default 10 seconds
    
    def summary(self) -> str:
        """Get a summary of the M2 pipeline configuration"""
        info = self.pipeline_info
        tiers = list(self.model_tiers.keys())
        startup_models = self.get_startup_models()
        
        return f"""
🍎 M2 MacBook Pipeline Configuration Summary
============================================
Platform: {info.get('platform', 'macOS_apple_silicon')}
Chip: {info.get('chip', 'Apple M2')}  
Memory: {info.get('memory', '16GB LPDDR5')}
GPU: {info.get('gpu', '10-core GPU')}

Model Tiers: {', '.join(tiers)}
Startup Models: {', '.join(startup_models)}
Max Concurrent: {self.get_concurrent_request_limit()}
Memory Threshold: {self.get_memory_threshold()*100}%
Proxy Bypass: {self.should_bypass_proxy()}
"""


# Global M2 configuration instance
try:
    m2_config = M2PipelineConfig()
except (FileNotFoundError, ValueError) as e:
    print(f"Warning: Could not load M2 config: {e}")
    m2_config = None
