# 🚀 LLM 翻译服务 - 优化版

一个高性能的本地托管翻译服务，利用 Ollama 管理的大型语言模型进行中英文双向翻译，兼容百度翻译 API。

**🆕 现已配备先进的性能优化：连接池、智能缓存和缓存翻译 244,891 倍速度提升！**

## ⚡ 性能优化

- **🔗 连接池**：持久 HTTP 连接与保活机制（100% 复用率）
- **💾 增强缓存**：带压缩和持久存储的 LRU 缓存
- **🧠 智能模型选择**：Gemma3（快速）和 Llama3.1（准确）模型
- **📊 实时指标**：全面的性能跟踪和时间分解
- **⚡ 异步处理**：非阻塞操作与连接复用
- **🎯 GPU 加速**：针对 NVIDIA Quadro P2000 及类似硬件优化

### 📈 性能结果
- **首次翻译速度提升 30.8%**（冷缓存）：19.8秒 → 13.7秒
- **缓存翻译速度提升 244,891 倍**：19.8秒 → 0.1毫秒
- **每个缓存翻译请求节省约 20 秒**
- **零延迟**缓存命中，瞬时响应

## 🚀 功能特性

- 🚀 **本地 LLM 翻译**：使用 Ollama 进行本地 LLM 管理和翻译
- ⚡ **极致性能**：冷缓存提升 30.8%，热缓存提升 244,891 倍，配备优化端点
- 🔄 **双向翻译**：中文 ↔ 英文翻译支持，自动检测语言
- 🎛️ **双翻译模式**：简洁模式（默认）输出干净结果，详细模式提供详细解释
- 🔗 **API 兼容性**：百度翻译 API 的直接替代品，支持签名验证
- 🏎️ **连接池**：持久 HTTP 连接，100% 复用率，最大化效率
- 🗄️ **智能缓存**：增强 LRU 缓存，支持 gzip 压缩和模式感知缓存键
- 📊 **实时监控**：实时性能指标、时间分解和缓存统计
- 🎯 **模型优化**：基于性能基准的智能模型选择（Gemma3/Llama3.1）
- 🔐 **身份验证**：基于 API 密钥的身份验证，可配置速率限制
- 🐳 **Docker 就绪**：完整的容器化支持与 docker-compose
- 🛡️ **健壮错误处理**：优雅降级和全面错误响应
- 📝 **自动文档**：基于 FastAPI/OpenAPI 的交互式 API 文档
- 🌐 **跨平台**：Windows、Linux 和 macOS 的完整 shell 脚本支持
- 🔍 **服务发现**：翻译服务的自动检测和连接
- 🛑 **服务管理**：所有平台的全面启动/停止脚本
- 🚇 **远程访问**：内置 ngrok 集成，支持全球访问（已在远程网络测试）

## 📋 部署模式

### 🏠 本地模式
当 systemDesign 和 llmYTranslate 在同一台计算机上时使用：
- 针对单机开发优化
- 最小网络配置
- 直接 localhost 通信
- 简化身份验证（可选）

### 🌐 远程模式
当 systemDesign 和 llmYTranslate 在不同计算机上时使用：
- 跨网络部署
- 增强安全性和身份验证
- 服务发现和自动连接
- 生产就绪配置

## 🚀 快速开始

### 选项 1：自动化部署（推荐）

#### Windows (PowerShell)
```powershell
# 完整生产环境设置（包括 Docker、Ollama、Python）
.\scripts\production-setup.ps1

# 或者快速开发设置
.\scripts\setup.ps1

# 启动所有服务
.\start-service.ps1
```

#### Linux/macOS (Shell)
```bash
# 完整生产环境设置
./scripts/production-setup.sh

# 或者快速开发设置
./scripts/setup.sh

# 启动所有服务
./start-service.sh
```

### 选项 2：手动设置

#### 先决条件
- Python 3.11+
- Docker & Docker Compose
- Ollama（用于 LLM 管理）
- 8GB+ RAM（推荐用于模型）

#### 安装

##### 1. 克隆仓库
```bash
git clone https://github.com/phoenixjyb/llmytranslate.git
cd llmytranslate
```

##### 2. 设置 Python 环境
```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

##### 3. 安装并设置 Ollama
```bash
# 从 https://ollama.ai 下载并安装 Ollama

# 拉取推荐的模型
ollama pull gemma2:2b    # 快速模型
ollama pull llama3.1:8b  # 准确模型
```

##### 4. 配置环境
```bash
# 复制并编辑配置文件
cp config/.env.local .env    # 本地开发
# 或
cp config/.env.remote .env   # 远程部署

# 根据需要编辑 .env 文件
```

##### 5. 启动服务
```bash
# 选项 A：使用脚本（推荐）
python run.py

# 选项 B：使用 Docker
docker-compose up -d

# 选项 C：开发模式
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🔧 服务管理

### 快速服务命令

#### 启动服务

##### Windows (PowerShell)
```powershell
# 启动完整翻译服务
.\start-service.ps1

# 仅启动 Python 服务（假设 Ollama 已运行）
.\start-service.ps1 -python-only

# 启动并设置 ngrok 隧道进行远程访问
.\start-service.ps1 -with-ngrok
```

##### Linux/macOS/Windows (Shell/WSL)
```bash
# 启动完整翻译服务
./start-service.sh

# 仅启动 Python 服务
./start-service.sh --python-only

# 启动并设置 ngrok 隧道
./start-service.sh --with-ngrok
```

#### 停止服务

##### Windows (PowerShell)
```powershell
# 停止所有服务
.\stop-service.ps1

# 仅停止 Python 服务
.\stop-service.ps1 -python-only

# 仅停止 ngrok
.\stop-service.ps1 -ngrok-only
```

##### Linux/macOS/Windows (Shell/WSL)
```bash
# 停止所有服务
./stop-service.sh

# 仅停止 Python 服务
./stop-service.sh --python-only

# 仅停止 ngrok
./stop-service.sh --ngrok-only
```

### 远程访问设置

#### Ngrok 隧道（测试最简单）
```powershell
# 1. 设置 ngrok 身份验证（仅首次）
.\scripts\setup_ngrok.ps1 YOUR_AUTH_TOKEN

# 2. 启动翻译服务
.\start-service.ps1

# 3. 在另一个终端启动 ngrok 隧道
ngrok http 8000

# 您的服务现在可通过 ngrok URL 在全球访问！
```

#### 完整工作流程
```powershell
# 启动所有服务
.\start-service.ps1
ngrok http 8000

# 测试远程访问（替换为您的 ngrok URL）
curl -H "ngrok-skip-browser-warning: true" https://abc123.ngrok-free.app/api/health

# 完成后停止所有服务
.\stop-service.ps1
```

### 服务状态和健康检查
```bash
# 检查服务健康状态
curl http://localhost:8000/api/health

# 验证安装
python validate.py

# 测试 Ollama 连接
python test_ollama_connectivity.py

# 服务发现
python discover_service.py
```

## 📁 项目结构

### 根目录
```
llmytranslate/
├── src/                    # 核心应用程序源代码
├── scripts/                # 自动化和实用脚本
├── tests/                  # 测试套件和验证
├── performance/            # 性能测试和结果
├── config/                 # 配置模板
├── docker/                 # Docker 部署文件
├── docs/                   # 全面文档
├── logs/                   # 应用程序和服务日志
├── docker-compose.yml      # 本地 Docker 设置
├── requirements.txt        # Python 依赖
├── run.py                  # 直接 Python 入口点
├── translation_server.py   # 旧版服务器（请使用 run.py）
└── validate.py            # 安装验证器
```

### 关键目录

#### 📂 src/ - 应用程序核心
```
src/
├── api/
│   └── routes/            # API 端点定义
├── core/
│   ├── config.py         # 配置管理
│   ├── network.py        # 网络和发现服务
│   └── production_config.py  # 生产设置
├── models/
│   └── schemas.py        # 数据模型和验证
└── services/
    ├── translation_service.py  # 核心翻译逻辑
    ├── ollama_client.py         # LLM 集成
    ├── auth_service.py          # 身份验证处理
    ├── cache_service.py         # 响应缓存
    └── stats_service.py         # 使用分析
```

#### 🔧 scripts/ - 跨平台自动化
```
scripts/
├── *.ps1                 # PowerShell 脚本（Windows 主要）
├── *.sh                  # Shell 脚本（Linux/macOS + Windows/WSL）
├── *.bat                 # 批处理脚本（Windows 备用）
├── deploy-online.ps1/.sh # 云部署自动化
├── production-setup.ps1/.sh  # 生产环境设置
├── service-manager.ps1/.sh   # 服务生命周期管理
├── setup_remote_access.ps1/.sh  # 远程访问配置
└── README.md             # 脚本使用文档
```

#### 🧪 tests/ - 质量保证
```
tests/
├── unit/                 # 单元测试用例
├── integration/          # API 和服务集成测试
├── examples/             # 使用示例和快速测试
├── test_baidu_compatibility.py  # 百度 API 兼容性
└── test_*.py             # 各种测试场景
```

#### ⚡ performance/ - 优化和监控
```
performance/
├── test_*.py             # 性能测试脚本
├── *.json                # 性能测试结果
├── benchmarks/           # 基准数据和分析
└── README.md             # 性能测试指南
```

#### ⚙️ config/ - 配置管理
```
config/
├── .env.remote           # 远程部署模板
├── nginx.conf            # Nginx 配置
├── requirements-minimal.txt  # 最小依赖
└── README.md             # 配置指南
```

#### 🐳 docker/ - 容器部署
```
docker/
├── Dockerfile            # 容器构建说明
├── docker-compose.yml    # 服务编排
├── docker-compose.remote.yml  # 远程部署变体
├── nginx.remote.conf     # 远程 nginx 配置
└── README.md             # Docker 部署指南
```

#### 📚 docs/ - 文档中心
```
docs/
├── api/                  # API 文档和示例
├── architecture/         # 系统设计和架构
├── guides/               # 设置和使用指南
├── setup/                # 特定平台设置说明
└── *.md                  # 各种文档文件
```

### 文件组织原则

- **跨平台支持**：所有脚本都提供 PowerShell（.ps1）、Shell（.sh）和批处理（.bat）格式
- **环境分离**：本地、远程和生产配置之间的清晰区分
- **模块化架构**：核心功能分离为逻辑服务模块
- **全面测试**：单元、集成和性能测试按类别组织
- **文档优先**：每个目录都包含解释其目的的 README.md
- **自动化就绪**：脚本处理复杂部署场景，用户干预最少

## 🐳 Docker 部署

### 本地 Docker 部署
```bash
# 启动本地开发服务
docker-compose -f docker-compose.local.yml up -d

# 拉取所需的 LLM 模型
docker exec llm-ollama-local ollama pull llava:latest
```

### 远程 Docker 部署
```bash
# 设置环境变量
export EXTERNAL_HOST=your-external-ip-or-domain
export SECRET_KEY=your-production-secret-key
export DISABLE_AUTH=false

# 启动远程访问服务
docker-compose -f docker-compose.remote.yml up -d

# 拉取所需的 LLM 模型
docker exec llm-ollama-remote ollama pull llava:latest
```

## 🔍 服务发现

### 发现可用服务
```bash
# 查找所有可用的翻译服务
python discover_service.py --discover

# 查找最佳可用服务
python discover_service.py --best

# 测试特定服务
python discover_service.py --test http://192.168.1.100:8000
```

### 与 systemDesign 集成
该服务提供 systemDesign 可以使用的自动发现端点：

```bash
# 获取服务信息
curl --noproxy "*" http://your-service:8000/api/discovery/info

# 测试连接
curl --noproxy "*" http://your-service:8000/api/discovery/network

# 发现网络上的其他服务
curl --noproxy "*" http://your-service:8000/api/discovery/discover
```

## ⚙️ 配置

### 本地模式配置（.env.local）
```bash
DEPLOYMENT__MODE=local
DEPLOYMENT__SERVICE_NAME=llm-translation-local
API__HOST=127.0.0.1
API__PORT=8000
AUTH__DISABLE_SIGNATURE_VALIDATION=true
ENVIRONMENT=development
DEBUG=true
```

### 远程模式配置（.env.remote）
```bash
DEPLOYMENT__MODE=remote
DEPLOYMENT__SERVICE_NAME=llm-translation-remote
DEPLOYMENT__EXTERNAL_HOST=your-external-ip-or-domain
DEPLOYMENT__EXTERNAL_PORT=8000
DEPLOYMENT__ENABLE_DISCOVERY=true
API__HOST=0.0.0.0
API__PORT=8000
AUTH__DISABLE_SIGNATURE_VALIDATION=false
ENVIRONMENT=production
```

## 🔑 API 使用

### 百度 API 兼容端点

#### 基本翻译（与百度 API 兼容）
```bash
curl -X POST "http://localhost:8000/api/trans/vip/translate" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "q=Hello World&from=en&to=zh&appid=your_app_id&salt=12345&sign=your_signature"
```

#### 增强翻译端点（推荐用于新集成）
```bash
# 简洁模式（默认）
curl -X POST "http://localhost:8000/api/translate" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello World", "source_lang": "auto", "target_lang": "zh", "mode": "succinct"}'

# 详细模式
curl -X POST "http://localhost:8000/api/translate" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello World", "source_lang": "auto", "target_lang": "zh", "mode": "verbose"}'
```

### 性能端点

#### 优化的缓存端点（最快）
```bash
curl -X POST "http://localhost:8000/api/translate/optimized" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello World", "source_lang": "auto", "target_lang": "zh"}'
```

#### 实时性能指标
```bash
# 获取性能统计
curl "http://localhost:8000/api/stats/performance"

# 获取缓存统计
curl "http://localhost:8000/api/stats/cache"

# 获取连接池统计
curl "http://localhost:8000/api/stats/connection"
```

## 🎯 性能优化

### 缓存策略
- **LRU 缓存**：最近最少使用缓存，自动清理
- **Gzip 压缩**：减少内存使用
- **模式感知**：简洁和详细模式的独立缓存
- **持久化**：缓存在重启间保持

### 连接优化
- **连接池**：持久 HTTP 连接
- **Keep-Alive**：连接复用最大化
- **超时管理**：智能超时处理
- **重试逻辑**：自动重试失败的连接

### 模型优化
- **智能选择**：基于任务复杂度的模型选择
- **GPU 利用**：针对可用硬件优化
- **批处理**：多请求批处理（计划中）

## 🛠️ 开发

### 运行测试
```bash
# 运行所有测试
python -m pytest

# 运行特定测试
python -m pytest tests/integration/test_baidu_compatibility.py

# 运行性能测试
python performance/test_performance.py
```

### 代码质量
```bash
# 代码格式化
black src/ tests/

# 类型检查
mypy src/

# 代码检查
flake8 src/ tests/
```

## 📝 API 文档

服务运行时，API 文档可在以下位置获得：
- **交互式文档（Swagger UI）**：http://localhost:8000/docs
- **ReDoc 文档**：http://localhost:8000/redoc
- **OpenAPI 规范**：http://localhost:8000/openapi.json

## 🔧 故障排除

### 常见问题

#### Ollama 连接问题
```bash
# 检查 Ollama 是否运行
ollama list

# 测试 Ollama 连接
python test_ollama_connectivity.py

# 重启 Ollama 服务
# Windows: 重启 Ollama 应用程序
# Linux/macOS: systemctl restart ollama
```

#### 端口冲突
```bash
# 检查端口 8000 使用情况
# Windows:
netstat -ano | findstr :8000
# Linux/macOS:
lsof -i :8000

# 在不同端口启动
python run.py --port 8001
```

#### 内存问题
```bash
# 监控内存使用
# Windows: 任务管理器
# Linux: htop 或 free -h
# macOS: Activity Monitor

# 使用更小的模型
ollama pull gemma2:2b  # 更小，更快
```

## 🤝 贡献

1. Fork 项目
2. 创建功能分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'Add amazing feature'`
4. 推送到分支：`git push origin feature/amazing-feature`
5. 打开 Pull Request

## 📄 许可证

此项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Ollama](https://ollama.ai) - 本地 LLM 管理
- [FastAPI](https://fastapi.tiangolo.com) - 现代 Web 框架
- [Docker](https://docker.com) - 容器化平台
- [Ngrok](https://ngrok.com) - 安全隧道服务

## 📞 支持

- 📧 **Email**: [您的邮箱]
- 🐛 **Issues**: [GitHub Issues](https://github.com/phoenixjyb/llmytranslate/issues)
- 📖 **文档**: [项目文档](docs/)
- 💬 **讨论**: [GitHub Discussions](https://github.com/phoenixjyb/llmytranslate/discussions)

---

**⭐ 如果这个项目对您有帮助，请给它一个星标！**
