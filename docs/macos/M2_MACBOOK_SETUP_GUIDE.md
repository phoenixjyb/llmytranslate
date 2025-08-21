# 🍎 MacBook Air M2 Server Setup Guide
## Pipeline 1b Implementation - Quick Start

### Document Version: 1.0
### Date: August 19, 2025
### Target: 3-Week Implementation

---

## 🎯 Quick Setup Overview

Your MacBook Air M2 with 16GB RAM is perfect for running **larger models** efficiently. Unlike the mobile pipelines limited to 270M models, you can run:
- **gemma2:2b** (1.6GB) - Recommended default
- **phi3:mini** (3.8GB) - High reasoning capability  
- **llama3.1:8b** (4.7GB) - Maximum quality

---

## ⚡ Quick Start (30 minutes)

### **Step 1: Install Ollama for Apple Silicon**
```bash
# Install Ollama with native M2 support
curl -fsSL https://ollama.ai/install.sh | sh

# Verify installation
ollama --version
```

### **Step 2: Pull Recommended Models**
```bash
# Start with the balanced default (1.6GB)
ollama pull gemma2:2b

# Optional: High-quality reasoning model (3.8GB)
ollama pull phi3:mini

# Optional: Maximum quality model (4.7GB) - uses 70% of memory
ollama pull llama3.1:8b

# Keep the fast mobile model for comparison
ollama pull gemma2:270m
```

### **Step 3: Test Model Performance**
```bash
# Test response speed with different models
echo "Test performance of each model:"

echo "Testing gemma2:270m (270MB)..."
time ollama run gemma2:270m "Translate 'Hello world' to Chinese"

echo "Testing gemma2:2b (1.6GB)..."
time ollama run gemma2:2b "Translate 'Hello world' to Chinese"

echo "Testing phi3:mini (3.8GB)..."
time ollama run phi3:mini "Translate 'Hello world' to Chinese"

echo "Testing llama3.1:8b (4.7GB)..."
time ollama run llama3.1:8b "Translate 'Hello world' to Chinese"
```

### **Step 4: Setup Existing Service**
```bash
# Navigate to your project
cd /Users/yanbo/Projects/llmYTranslate

# Update default model in environment
echo "export OLLAMA_MODEL_DEFAULT=gemma2:2b" >> ~/.zshrc
source ~/.zshrc

# Start the service with larger model
python run.py
```

---

## 📊 Expected Performance on M2

### **Model Performance Comparison:**
```yaml
gemma2:270m:
  Memory Usage: ~500MB total
  Response Time: 0.3-0.8 seconds
  Quality: Good for basic tasks
  Use Case: Mobile-speed testing

gemma2:2b:
  Memory Usage: ~2.5GB total  
  Response Time: 0.8-2.0 seconds
  Quality: Very good for most tasks
  Use Case: RECOMMENDED DEFAULT

phi3:mini:
  Memory Usage: ~4.5GB total
  Response Time: 1.0-2.5 seconds  
  Quality: Excellent reasoning
  Use Case: Complex problem solving

llama3.1:8b:
  Memory Usage: ~6.0GB total
  Response Time: 2.0-4.0 seconds
  Quality: Premium quality
  Use Case: Maximum quality needed
```

### **Memory Usage Guidelines:**
- **Safe zone**: Models using <8GB total (gemma2:2b, phi3:mini)
- **Caution zone**: Models using 8-12GB total (llama3.1:8b)
- **Avoid**: Models requiring >12GB (leaves too little for system)

---

## 🔧 Advanced Configuration

### **Adaptive Model Selection (Week 2)**

Create a smart model router based on query complexity:

```python
# File: src/services/m2_model_router.py
import psutil
import ollama

class M2ModelRouter:
    def __init__(self):
        self.models = {
            'fast': 'gemma2:270m',
            'balanced': 'gemma2:2b', 
            'reasoning': 'phi3:mini',
            'quality': 'llama3.1:8b'
        }
    
    def get_available_memory_gb(self):
        """Get available system memory in GB"""
        memory = psutil.virtual_memory()
        return memory.available / (1024**3)
    
    def analyze_query_complexity(self, query: str) -> str:
        """Analyze query to determine required model capability"""
        query_lower = query.lower()
        
        # Simple translation tasks
        if any(word in query_lower for word in ['translate', 'what is', 'how to say']):
            return 'fast' if len(query) < 50 else 'balanced'
        
        # Reasoning tasks
        if any(word in query_lower for word in ['why', 'explain', 'analyze', 'compare']):
            return 'reasoning'
        
        # Complex tasks
        if any(word in query_lower for word in ['write', 'create', 'generate', 'compose']):
            return 'quality'
        
        return 'balanced'  # Default
    
    def select_model(self, query: str) -> str:
        """Select optimal model based on query and system state"""
        complexity = self.analyze_query_complexity(query)
        available_memory = self.get_available_memory_gb()
        
        # Memory-based fallback
        if available_memory < 4:
            return self.models['fast']
        elif available_memory < 8:
            return self.models['balanced']
        
        # Use requested complexity if memory allows
        model_memory_requirements = {
            'fast': 1,      # 1GB needed
            'balanced': 4,  # 4GB needed  
            'reasoning': 6, # 6GB needed
            'quality': 8    # 8GB needed
        }
        
        if available_memory >= model_memory_requirements[complexity]:
            return self.models[complexity]
        
        # Fallback to largest model that fits
        for level in ['quality', 'reasoning', 'balanced', 'fast']:
            if available_memory >= model_memory_requirements[level]:
                return self.models[level]
        
        return self.models['fast']  # Ultimate fallback

# Integration with existing service
def get_optimal_model(query: str) -> str:
    router = M2ModelRouter()
    return router.select_model(query)
```

### **Memory Monitoring (Week 3)**

```python
# Add to existing optimized_llm_service.py
import psutil
import logging

def monitor_memory_usage():
    """Monitor and log memory usage"""
    memory = psutil.virtual_memory()
    
    logging.info(f"Memory usage: {memory.percent}% used")
    logging.info(f"Available: {memory.available / (1024**3):.1f}GB")
    
    if memory.percent > 85:
        logging.warning("High memory usage detected - consider model downgrade")
    
    return memory.available / (1024**3)

# Usage in LLM service
class OptimizedLLMService:
    def __init__(self):
        self.model_router = M2ModelRouter()
    
    async def get_translation(self, query: str) -> str:
        # Check memory before processing
        available_memory = monitor_memory_usage()
        
        # Select optimal model
        model = self.model_router.select_model(query)
        
        logging.info(f"Using model: {model} (Available memory: {available_memory:.1f}GB)")
        
        # Process with selected model
        return await self.process_with_model(model, query)
```

---

## 🚀 3-Week Implementation Plan

### **Week 1: Basic Setup**
- ✅ Install Ollama for Apple Silicon
- ✅ Pull and test recommended models  
- ✅ Verify existing service works with larger models
- ✅ Performance benchmarking and comparison

### **Week 2: Smart Model Selection**
- 🔧 Implement adaptive model router
- 🔧 Add memory monitoring and alerts
- 🔧 Create model selection UI in web interface
- 🔧 Test automatic model switching

### **Week 3: Production Optimization**
- 🚀 Performance tuning and optimization
- 🚀 Error handling and fallback logic
- 🚀 Documentation and deployment guide
- 🚀 Integration with cross-pipeline routing

---

## 💡 Key Benefits of M2 Pipeline

### **Advantages Over Mobile Pipelines:**
- **Larger Models**: Can run 2B-8B parameter models vs 270M mobile limit
- **Better Quality**: Significantly improved response quality
- **Flexible Memory**: 16GB allows model experimentation
- **Development**: Perfect for testing before mobile deployment

### **Advantages Over RTX 3090:**
- **Portability**: Battery-powered server capability
- **Efficiency**: 15-25W vs 300W+ power consumption
- **Quiet**: Fanless operation vs loud GPU cooling
- **Backup**: Secondary server for high availability

### **Use Cases:**
- **Portable Development**: Coding and testing on the go
- **Quality Testing**: Experiment with larger models
- **Remote Work**: Full server capability anywhere
- **Backup Server**: High availability setup
- **Power Efficiency**: Lower cost operation

---

## 📊 Success Metrics

### **Week 1 Targets:**
- ✅ All models (270M to 8B) running successfully
- ✅ Performance benchmarks completed
- ✅ Memory usage analysis done

### **Week 2 Targets:**
- 🎯 Smart model selection working
- 🎯 Memory monitoring alerts functional
- 🎯 UI for model selection added

### **Week 3 Targets:**
- 🚀 Production-ready deployment
- 🚀 Integration with existing pipeline routing
- 🚀 Documentation and handoff complete

### **Performance Goals:**
- **gemma2:2b**: <2.0s response time (realistic on M2)
- **Memory efficiency**: <70% usage under normal load
- **Reliability**: 99%+ uptime for development workflows
- **Quality**: 8.5/10 rating vs 6/10 for mobile-only pipelines

---

*This M2 MacBook Air pipeline bridges the gap between mobile limitations and desktop performance, providing an excellent balance of portability, efficiency, and model capability.*
