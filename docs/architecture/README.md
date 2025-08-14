# 🏗️ Architecture Documentation

This directory contains comprehensive architecture documentation for the LLM Translation Service.

## 📋 Documentation Index

### 🎯 System Overview
- **[SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)** - High-level system architecture and design principles
- **[SOFTWARE_DESIGN_DOCUMENT.md](SOFTWARE_DESIGN_DOCUMENT.md)** - Detailed software design documentation
- **[SOFTWARE_STACK_FLOWCHART.md](SOFTWARE_STACK_FLOWCHART.md)** - Complete software stack visualization with Mermaid diagrams
- **[SOFTWARE_STACK_FLOWCHART-zh.md](SOFTWARE_STACK_FLOWCHART-zh.md)** - 软件栈流程图（中文版）

### 📊 Technical Details
- **[DATA_FLOW_DIAGRAM.md](DATA_FLOW_DIAGRAM.md)** - Data flow and processing diagrams
- **[DIRECTORY_STRUCTURE.md](DIRECTORY_STRUCTURE.md)** - File system organization and structure
- **[PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md)** - Project organization and component relationships

## 🎨 Diagram Types

### 🔄 Software Stack Flowchart
The **SOFTWARE_STACK_FLOWCHART.md** provides:
- **System Architecture Overview** - Complete visual representation of all components
- **Component Interaction Flow** - Request processing and performance optimization flows
- **Deployment Architecture** - Docker containerization and deployment structure
- **Technology Stack Summary** - Complete technology breakdown

### 📈 Key Visualizations Include:
1. **Main Architecture Diagram** - Shows all layers from client to storage
2. **Request Processing Sequence** - Step-by-step request handling
3. **Performance Optimization Flow** - Cache and connection optimization paths
4. **Deployment Container Structure** - Docker multi-container setup

## 🌟 Quick Navigation

### For Developers
- Start with **[SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)** for system overview
- Review **[SOFTWARE_STACK_FLOWCHART.md](SOFTWARE_STACK_FLOWCHART.md)** for component relationships
- Check **[DATA_FLOW_DIAGRAM.md](DATA_FLOW_DIAGRAM.md)** for processing flows
- See **[docs/web/README.md](../web/README.md)** for Web client details

### For DevOps/Deployment
- Focus on **[SOFTWARE_STACK_FLOWCHART.md](SOFTWARE_STACK_FLOWCHART.md)** deployment section
- Reference **[SOFTWARE_DESIGN_DOCUMENT.md](SOFTWARE_DESIGN_DOCUMENT.md)** for technical requirements

### For Project Management
- Review **[../PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md)** for project organization
- Check **[DIRECTORY_STRUCTURE.md](DIRECTORY_STRUCTURE.md)** for file layouts

### 📱 Client Architectures
- **Web Client**: [docs/web/README.md](../web/README.md)
- **Android App**: [android/README.md](../../android/README.md) — see “Component Diagram (Mermaid)”

## 🔧 Architecture Highlights

### 🚀 Performance Optimizations
- **Connection Pooling**: 100% HTTP connection reuse
- **Smart Caching**: LRU cache with 244,891x speedup on cached requests
- **GPU Acceleration**: NVIDIA CUDA support for model processing
- **Async Processing**: Non-blocking operations throughout

### 🌐 Scalability Features
- **Microservices Architecture**: Containerized components
- **Load Balancing**: Nginx reverse proxy
- **Service Discovery**: Auto-detection and registration
- **Cross-Platform Support**: Windows, Linux, macOS compatibility

### 🔒 Security & Reliability
- **API Authentication**: Baidu-compatible signature validation
- **Health Monitoring**: Comprehensive health checks
- **Error Handling**: Graceful degradation and recovery
- **Logging & Metrics**: Real-time monitoring and analytics

## 📚 Related Documentation

- **[../setup/](../setup/)** - Platform-specific setup instructions
- **[../guides/](../guides/)** - User and administration guides
- **[../api/](../api/)** - API documentation and examples
- **[../../README.md](../../README.md)** - Project overview and quick start

---

💡 **Tip**: The Mermaid diagrams in the flowchart files can be rendered in GitHub, VS Code with Mermaid extensions, or any Mermaid-compatible viewer for interactive exploration.
