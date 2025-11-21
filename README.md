# FastMCP Sasai Wallet Operations Server

A production-grade FastMCP server providing comprehensive wallet operation tools for the Sasai Payment Gateway. This server enables secure interaction with the Sasai Payment Gateway through the Model Context Protocol (MCP) for wallet management, transaction history, payment cards, and mobile services.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Virtual environment activated
- Sasai Payment Gateway API credentials

### Installation & Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your Sasai credentials

# Run the server directly
python src/main.py

# Or use Claude Desktop integration
python claude_desktop_server.py
```

## 🏗️ Architecture

This server features a modular, production-ready architecture:

```
src/
├── config/          # Configuration management
│   ├── __init__.py
│   └── settings.py  # Environment-based configuration
├── core/            # Server initialization and exceptions  
│   ├── __init__.py
│   ├── server.py    # FastMCP server setup
│   └── exceptions.py # Custom exception hierarchy
├── api/             # HTTP client for Sasai API
│   ├── __init__.py
│   └── client.py    # Robust API client with error handling
├── auth/            # Authentication and token management
│   ├── __init__.py
│   ├── manager.py   # Token lifecycle management
│   └── tools.py     # Authentication tools
├── wallet/          # Wallet operation modules
│   ├── __init__.py
│   ├── balance.py   # Balance operations
│   ├── transactions.py # Transaction history  
│   ├── cards.py     # Linked cards management
│   ├── airtime.py   # Airtime and mobile services
│   └── profile.py   # Customer profile
├── monitoring/      # Health monitoring
│   ├── __init__.py
│   └── health.py    # API health checks
└── utils/          # Utility functions
    ├── __init__.py
    └── helpers.py   # Common utilities
```

## ✨ Features

### 🔐 Authentication
- **Complete OAuth Flow**: Automated login, PIN verification, and token refresh
- **Token Management**: Automatic token storage and lifecycle management  
- **Error Recovery**: Graceful handling of expired tokens and authentication failures

### 💰 Wallet Operations
- **Balance Inquiry**: Multi-currency wallet balance retrieval
- **Transaction History**: Paginated transaction history with filtering
- **Payment Cards**: Linked card and payment method management
- **Mobile Services**: Airtime plans and mobile service management
- **Customer Profile**: Comprehensive profile information access

### 📊 Monitoring & Reliability
- **Health Checks**: Real-time API connectivity and health monitoring
- **Error Handling**: Comprehensive error handling with detailed diagnostics
- **Rate Limiting**: Intelligent rate limit detection and handling
- **Logging**: Structured logging with configurable levels

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- FastMCP framework
- Valid Sasai Payment Gateway credentials

### Installation

#### Option 1: Automated Setup (Recommended)
```bash
# Clone and set up the project
git clone <repository-url>
cd fastmcp2.0

# Run setup script
chmod +x scripts/setup.sh
./scripts/setup.sh --dev  # Include --dev for development setup
```

#### Option 2: Manual Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Copy environment configuration
cp .env.example .env
```

### Configuration

Update your `.env` file with Sasai credentials:

```bash
# Sasai API Configuration
SASAI_ENVIRONMENT=sandbox
SASAI_USERNAME=your_username
SASAI_PASSWORD=your_password  
SASAI_PIN=your_encrypted_pin
SASAI_USER_REFERENCE_ID=your_user_reference_id

# RAG Service Configuration (optional)
RAG_SERVICE_URL=http://localhost:8000/api/retriever
RAG_TENANT_ID=sasai
RAG_TENANT_SUB_ID=sasai-sub
RAG_KNOWLEDGE_BASE_ID=sasai-compliance-kb
RAG_PROVIDER_CONFIG_ID=azure-openai-llm-gpt-4o-mini
RAG_REQUEST_TIMEOUT=30.0

# Server Configuration (optional)
LOG_LEVEL=INFO
REQUEST_TIMEOUT=30.0
```

### Running the Server

#### Development
```bash
# Activate virtual environment
source venv/bin/activate

# Run the server
python src/main.py
```

#### Production
```bash
# Using production runner with additional features
python scripts/run_server.py

# With specific configuration
python scripts/run_server.py --log-file /var/log/sasai-server.log --pid-file /var/run/sasai-server.pid

# Validate environment only
python scripts/run_server.py --validate-only
```

## 🔧 Available Tools

### Authentication Tools
- **`generate_token`** - Generate authentication token using complete OAuth flow
- **`get_token_status`** - Check current token availability and metadata
- **`clear_token`** - Clear current authentication token

### Wallet Operation Tools
- **`get_wallet_balance`** - Retrieve wallet balance for specified currency/provider
- **`get_transaction_history`** - Get paginated transaction history with filtering
- **`get_linked_cards`** - Fetch linked payment cards and methods
- **`get_airtime_plans`** - Browse available airtime and data plans
- **`get_customer_profile`** - Access customer profile information

### Monitoring Tools  
- **`health_check`** - Comprehensive API health and connectivity check

### Compliance & Knowledge Tools (RAG Integration)
- **`wallet_query_compliance_knowledge`** - Query Sasai compliance knowledge base for policy and regulatory information
- **`wallet_search_compliance_policies`** - Search for wallet-specific compliance policies (AML, KYC, fraud prevention)
- **`wallet_get_regulatory_guidance`** - Get regulatory guidance for wallet operations across different jurisdictions

### RAG (Compliance Knowledge) Tools
- **`wallet_query_compliance_knowledge`** - Retrieve relevant compliance document chunks for Claude to synthesize answers
- **`wallet_search_compliance_policies`** - Search and retrieve wallet-specific compliance policy documents
- **`wallet_get_regulatory_guidance`** - Retrieve regulatory guidance document chunks for wallet operations

**Note**: RAG tools now return raw document chunks from the retrieval API, allowing Claude to be the single point of intelligence for synthesizing comprehensive responses. This eliminates double LLM processing and reduces latency.

## 📖 Usage Examples

### Basic Workflow
```python
# 1. Generate authentication (automatic with other tools)
await generate_token()

# 2. Check wallet balance
balance = await get_wallet_balance(
    currency="USD", 
    provider_code="ecocash"
)

# 3. Get recent transactions
transactions = await get_transaction_history(
    page=0, 
    pageSize=10, 
    currency="USD"
)

# 4. Monitor system health
health = await health_check()

# 5. Query compliance knowledge
compliance_info = await wallet_query_compliance_knowledge(
    question="What are the KYC requirements for wallet accounts?",
    knowledge_area="regulatory"
)

# 6. Search compliance policies  
policy_info = await wallet_search_compliance_policies(
    topic="transaction limits",
    policy_type="aml"
)
```

### Auto-Authentication
All wallet tools support automatic authentication:
```python
# This will automatically authenticate if no token exists
balance = await get_wallet_balance(
    currency="USD", 
    auto_generate_token=True
)
```

## 🛠️ Development

### Running Tests
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run specific test module
python -m pytest tests/test_auth.py -v
```

### Code Quality
```bash
# Format code
black src/ tests/

# Lint code  
flake8 src/ tests/

# Type checking
mypy src/

# Import sorting
isort src/ tests/
```

### Adding New Tools
1. Create tool module in appropriate package (e.g., `src/wallet/`)
2. Implement tool function with proper type hints and documentation
3. Create registration function for the MCP server
4. Add registration call in `src/core/server.py`
5. Write tests in `tests/` directory

## 🚀 Deployment

### Docker Deployment
```bash
# Build image
docker build -t sasai-wallet-server:2.0.0 .

# Run with environment file
docker run -d --name sasai-wallet-server --env-file .env sasai-wallet-server:2.0.0
```

### Systemd Service
```bash
# Install service
sudo cp scripts/sasai-wallet-server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable sasai-wallet-server
sudo systemctl start sasai-wallet-server
```

### Process Manager (PM2)
```bash
# Install PM2
npm install -g pm2

# Start application
pm2 start scripts/ecosystem.config.js

# Monitor
pm2 monitor
```

## 📊 Monitoring

### Health Monitoring
The server provides built-in health monitoring:
```bash
# Check health via tool
python -c "
import asyncio
from src.core import initialize_server
server = initialize_server()
# Use health_check tool
"
```

### Logging
- **Structured logging** with JSON format support
- **Log rotation** with configurable retention
- **Multiple log levels** for different environments
- **Sensitive data masking** for security

### Metrics (Optional)
With monitoring extras:
```bash
pip install -e .[monitoring]
```

## 🔒 Security

### Credentials Management
- Environment-based configuration
- Sensitive data masking in logs  
- No credential storage in code
- Support for external secret managers

### Network Security
- HTTPS-only communication
- Request timeout protection
- Rate limiting awareness
- Network error resilience

### Token Security
- In-memory token storage only
- Automatic token expiry handling
- Secure token refresh flows
- Token metadata tracking

## 📚 Documentation

- **[API Documentation](docs/API.md)** - Detailed API reference and examples
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment strategies
- **[Configuration Reference](#configuration)** - Environment configuration options

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the coding standards
4. Add tests for new functionality
5. Ensure all tests pass (`python -m pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Write comprehensive docstrings
- Add type hints to all functions
- Maintain test coverage above 80%
- Update documentation for new features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the [API Documentation](docs/API.md)
- **Issues**: Report bugs and request features via GitHub Issues
- **Community**: Join discussions in GitHub Discussions

## 🚦 Status

- **Environment**: Sandbox testing environment
- **API Version**: Sasai Payment Gateway v1-v4 APIs
- **MCP Version**: Compatible with FastMCP 2.0+
- **Python**: Supports Python 3.8+

---

*FastMCP Sasai Wallet Operations Server - Production-grade financial integration for the Model Context Protocol ecosystem.*
