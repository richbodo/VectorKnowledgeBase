# Vector Knowledge Base

Vector DB and API for use with OpenAI custom GPTs to hook into with GPT Actions written in python using flask. This is a simple intro to RAG LLM coding for me that allowed me to enable my custom GPT to access a library of hundreds of research papers that I have access to but the GPT couldn't find as easily.  

I implemented on Replit, using various tools for enhanced functionality. My notes on this setup are [here](http://richbodo.pbworks.com/w/page/160057005/LLM%20RAG%20Intro), and my upload and API test tool is [here](https://github.com/richbodo/snh_bridge_test).

Status is that it works for me but this code is totally alpha so I doubt it will work for you, but I'm super interested in improving it.

The Custom GPT that this is enhancing needs a lot of love and config/prompt engineering that I'll be doing over the next weeks.  I'll replace this with a link to a google doc on how to prompt engineer that GPT when I'm done.

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
  - [Requirements](#requirements)
  - [Installation](#installation)
- [API Usage](#api-usage)
- [Architecture](#architecture)
- [Deployment](#deployment)
  - [Deploying on Replit](#deploying-on-replit)
  - [Deploying on Linux Server](#deploying-on-linux-server)
- [Development](#development)
- [Testing Tools](#testing-tools)
- [Documentation](#documentation)
- [License](#license)

## Documentation Index

### Core Documentation
- [API Specification](docs/api_specification.md) - Detailed API endpoint documentation
- [Authentication Guide](docs/authentication.md) - Authentication setup and configuration
- [Backup System Guide](docs/BackupSystem.md) - ChromaDB backup and persistence details
- [Replit Secrets Guide](docs/replit_secrets_guide.md) - Managing secrets in Replit environments
- [Project Roadmap](docs/Roadmap.md) - Future development plans and research areas

### Privacy and Security
- [Privacy and PII Protection Guide](docs/privacy_and_pii_protection.md) - Comprehensive guide to privacy features and PII protection
- [Privacy Demo Script](docs/privacy_demo.py) - Interactive demonstration of privacy features

## Features

- **PDF Processing**: Extract text from PDF documents with memory-efficient processing
- **Semantic Search**: Search across all your documents using natural language queries
- **Vector Database Storage**: Store and retrieve document embeddings efficiently
- **API Access**: Programmatically upload documents and query the knowledge base
- **Web Interface**: User-friendly interface for uploading and querying documents
- **Persistence**: Robust backup and restore functionality with automatic rotation
- **Monitoring**: Built-in diagnostic tools for system health and database stats
- **PII Filtering**: Enhanced privacy controls for logs, headers, and sensitive data
- **Backup and restore**: Robust SQLite and ChromaDB persistence on Replit

## Quick Start

### Requirements

- Python 3.9+
- OpenAI API key
- At least 1GB RAM (more recommended for processing large PDFs)

### Installation

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variables:
   ```
   # Required for functionality
   export OPENAI_API_KEY="your_openai_api_key"
   export VKB_API_KEY="your_custom_api_key"
   
   # Required for authentication and session management
   export SESSION_SECRET="your_random_secret_key"
   export BASIC_AUTH_USERNAME="your_secure_username"
   export BASIC_AUTH_PASSWORD="your_secure_password"
   ```
4. Run the application: `python main.py`
5. Access the web interface at `http://localhost:5000`

## API Usage

For detailed API documentation including authentication methods, endpoints, and example usage, see [API Specification](docs/api_specification.md).

## Architecture

- **Flask Backend**: Web framework for interface and API
- **PyMuPDF**: PDF text extraction with optimized memory usage
- **OpenAI**: Text embeddings and query processing
- **ChromaDB**: Vector database for semantic search
- **Object Storage**: Persistent storage for ChromaDB data with automatic backup rotation
- **Backup System**: For details, see [Backup System Guide](docs/BackupSystem.md)

## Deployment

### Deploying on Replit

1. **Fork the Repository**
   - Create a new Replit project importing from GitHub repository

2. **Set Required Environment Variables in Replit Secrets**
   - `OPENAI_API_KEY`: Your OpenAI API key for embeddings and queries
   - `VKB_API_KEY`: Custom API key for API endpoint authentication
   - `SESSION_SECRET`: Random string for secure session management
   - `BASIC_AUTH_USERNAME`: Secure username for HTTP Basic Authentication
   - `BASIC_AUTH_PASSWORD`: Strong password for HTTP Basic Authentication
   
   > **IMPORTANT**: For production deployments, always use Replit Secrets rather than environment variables in .env files or code. See [Authentication Guide](docs/authentication.md) for detailed setup instructions.

3. **Install Dependencies**
   - Replit will automatically install dependencies from pyproject.toml

4. **Configure Storage**
   - Ensure persistent storage is enabled
   - For production, enable Replit's Object Storage
   - The backup system automatically manages data persistence (see [Backup System Guide](docs/BackupSystem.md))
   - In disk-constrained environments, use the `--skip-backup` flag with restore operations

5. **Disk Space Management**
   - The system is designed to handle disk quota limitations
   - For cleanup: `python utils/delete_backup_history.py --force`
   - For restore without local backup: `python utils/object_storage.py restore --skip-backup`
   - All restorations during application startup automatically adapt to disk constraints

6. **Run the Application**
   - Use the "Run" button in Replit
   - Application will start on the default Replit port
   - First run will initialize the ChromaDB database

7. **Verify Functionality**
   - Navigate to the web interface
   - Upload a test PDF
   - Test search functionality
   - Check the /monitoring/database-diagnostic endpoint

### Deploying on Linux Server

This is just some auto-generated stuff that Claude wrote - I haven't deployed this on bare metal.

1. **Clone the Repository**
   ```bash
   git clone https://github.com/richbodo/VectorKnowledgeBase.git
   cd VectorKnowledgeBase
   ```

2. **Set Up Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   ```bash
   # Required API keys
   export OPENAI_API_KEY="your_openai_api_key"
   export VKB_API_KEY="your_custom_api_key"
   
   # Authentication and security
   export SESSION_SECRET="your_random_secret_key"
   export BASIC_AUTH_USERNAME="your_secure_username"
   export BASIC_AUTH_PASSWORD="your_secure_password"
   
   # Optional: Configure ChromaDB location
   export CHROMADB_DIR="/path/to/persistent/storage"
   ```
   
   > **Security Note**: In production, use a secrets management solution instead of setting environment variables directly in shell scripts.

4. **Run for Development**
   ```bash
   python main.py
   ```

5. **Run for Production**
   ```bash
   gunicorn --bind 0.0.0.0:8080 --workers 4 --timeout 120 'main:create_app()'
   ```

6. **Configure Nginx (Optional)**
   - Set up Nginx as a reverse proxy
   - Configure SSL with Let's Encrypt
   - Set appropriate cache headers

7. **Set Up Systemd Service (Optional)**
   - Create a systemd service file for automatic startup
   - Enable log rotation
   - Configure automatic restarts

## Development

For more information on development and future research areas, please refer to [Project Roadmap](docs/Roadmap.md).

## Testing Tools

The following scripts are available for testing privacy and PII protection features:

- `utils/test_privacy.py` - Test script for privacy controls in API requests
- `utils/test_privacy_filter.py` - Test script for privacy log filter functionality
- `utils/run_privacy_tests.sh` - Shell script to run comprehensive privacy tests
- `docs/privacy_demo.py` - Demonstration of privacy features

## Documentation

### Using the Documentation

- Developers should start with the implementation guides
- End users should refer to the user guides
- System administrators should review both for complete understanding

### Best Practices

When working with the Vector Knowledge Base application:

1. Always prioritize privacy and security
2. Regularly test privacy controls after making changes
3. Keep documentation updated with implementation changes
4. Report any privacy or security concerns immediately

### Contributing to Documentation

When adding to this documentation set:

1. Maintain consistent formatting
2. Include concrete examples
3. Separate technical and user-focused content
4. Cross-reference related documentation

## License

This project is GPLv3 licensed. See LICENSE file for details.

---

*Documentation last updated: March 17, 2025*
