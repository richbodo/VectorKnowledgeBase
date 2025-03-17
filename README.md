# PDF Knowledge Base

Vector DB and API for use with OpenAI custom GPTs to hook into with GPT Actions written in python using flask.  This is a simple intro to RAG LLM coding for me that allowed me to enable my custom GPT to access a library of hundreds of research papers that I have access to but the GPT couldn't find as easily.  

<<<<<<< HEAD
I implmented on Replit, using a bunch of other tools.  It should be possible to re-use this there.  My notes on this setup are [here](http://richbodo.pbworks.com/w/page/160057005/LLM%20RAG%20Intro), and my upload and API test tool is [here](https://github.com/richbodo/snh_bridge_test).
=======
I implemented on Replit.  It should be possible to re-use this there.  My notes on this setup are [here](http://richbodo.pbworks.com/w/page/160057005/LLM%20RAG%20Intro), and my upload and API test tool is [here](https://github.com/richbodo/snh_bridge_test).
>>>>>>> 446e53914c5d9f82f391a8f0f259dd39892a7531

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
- [License](#license)

<<<<<<< HEAD
## Documentation Index

### Core Documentation
- [API Specification](docs/api_specification.md) - Detailed API endpoint documentation
- [Authentication Guide](docs/authentication.md) - Authentication setup and configuration
- [Backup System Guide](docs/BackupSystem.md) - ChromaDB backup and persistence details
- [Replit Secrets Guide](docs/replit_secrets_guide.md) - Managing secrets in Replit environments
- [Project Roadmap](docs/Roadmap.md) - Future development plans and research areas

### Privacy and Security
- [Privacy Controls](docs/privacy_controls.md) - Implementation of privacy features
- [PII Protection Overview](docs/pii_protection.md) - Personal Identifiable Information protection
- [PII Implementation Guide](docs/pii_implementation_guide.md) - Technical guide for PII protection
- [User PII Guide](docs/user_pii_guide.md) - End-user focused PII information

### Documentation Index
- [Documentation Overview](docs/README.md) - Master documentation index

=======
>>>>>>> 446e53914c5d9f82f391a8f0f259dd39892a7531
## Features

- **PDF Processing**: Extract text from PDF documents with memory-efficient processing
- **Semantic Search**: Search across all your documents using natural language queries
- **Vector Database Storage**: Store and retrieve document embeddings efficiently
- **API Access**: Programmatically upload documents and query the knowledge base
- **Web Interface**: User-friendly interface for uploading and querying documents
- **Persistence**: Robust backup and restore functionality with automatic rotation
- **Monitoring**: Built-in diagnostic tools for system health and database stats
<<<<<<< HEAD
=======
- **PII Filtering**: Logs, headers, stuff like that
- **Backup and restore SQLite**: Needed for persistence on Replit
>>>>>>> 446e53914c5d9f82f391a8f0f259dd39892a7531

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
<<<<<<< HEAD
   # Required for functionality
   export OPENAI_API_KEY="your_openai_api_key"
   export VKB_API_KEY="your_custom_api_key"
   
   # Required for authentication and session management
   export SESSION_SECRET="your_random_secret_key"
   export BASIC_AUTH_USERNAME="your_secure_username"
   export BASIC_AUTH_PASSWORD="your_secure_password"
=======
   export OPENAI_API_KEY="your_openai_api_key"
   export VKB_API_KEY="your_custom_api_key"
>>>>>>> 446e53914c5d9f82f391a8f0f259dd39892a7531
   ```
4. Run the application: `python main.py`
5. Access the web interface at `http://localhost:5000`

## API Usage

<<<<<<< HEAD
For detailed API documentation including authentication methods, endpoints, and example usage, see [API Specification](docs/api_specification.md).
=======
For detailed API documentation including authentication methods, endpoints, and example usage, see [api_specification.md](api_specification.md).
>>>>>>> 446e53914c5d9f82f391a8f0f259dd39892a7531

## Architecture

- **Flask Backend**: Web framework for interface and API
- **PyMuPDF**: PDF text extraction with optimized memory usage
- **OpenAI**: Text embeddings and query processing
- **ChromaDB**: Vector database for semantic search
- **Object Storage**: Persistent storage for ChromaDB data with automatic backup rotation
<<<<<<< HEAD
- **Backup System**: For details, see [Backup System Guide](docs/BackupSystem.md)
=======
- **Backup System**: For details, see [BackupSystem.md](BackupSystem.md)
>>>>>>> 446e53914c5d9f82f391a8f0f259dd39892a7531

## Deployment

### Deploying on Replit

1. **Fork the Repository**
   - Create a new Replit project importing from GitHub repository

<<<<<<< HEAD
2. **Set Required Environment Variables in Replit Secrets**
   - `OPENAI_API_KEY`: Your OpenAI API key for embeddings and queries
   - `VKB_API_KEY`: Custom API key for API endpoint authentication
   - `SESSION_SECRET`: Random string for secure session management
   - `BASIC_AUTH_USERNAME`: Secure username for HTTP Basic Authentication
   - `BASIC_AUTH_PASSWORD`: Strong password for HTTP Basic Authentication
   
   > **IMPORTANT**: For production deployments, always use Replit Secrets rather than environment variables in .env files or code. See [Authentication Guide](docs/authentication.md) for detailed setup instructions.
=======
2. **Set Required Environment Variables**
   - `OPENAI_API_KEY`: Your OpenAI API key for embeddings and queries
   - `VKB_API_KEY`: Custom API key for API endpoint authentication
>>>>>>> 446e53914c5d9f82f391a8f0f259dd39892a7531

3. **Install Dependencies**
   - Replit will automatically install dependencies from pyproject.toml

4. **Configure Storage**
   - Ensure persistent storage is enabled
   - For production, enable Replit's Object Storage
<<<<<<< HEAD
   - The backup system automatically manages data persistence (see [Backup System Guide](docs/BackupSystem.md))
=======
   - The backup system automatically manages data persistence (see BackupSystem.md)
>>>>>>> 446e53914c5d9f82f391a8f0f259dd39892a7531
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
   git clone https://github.com/yourusername/pdf-knowledge-base.git
   cd pdf-knowledge-base
   ```

2. **Set Up Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   ```bash
<<<<<<< HEAD
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
=======
   export OPENAI_API_KEY="your_openai_api_key"
   export VKB_API_KEY="your_custom_api_key"
   # Optional: Configure ChromaDB location
   export CHROMADB_DIR="/path/to/persistent/storage"
   ```
>>>>>>> 446e53914c5d9f82f391a8f0f259dd39892a7531

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

<<<<<<< HEAD
For more information on development and future research areas, please refer to [Project Roadmap](docs/Roadmap.md).
=======
For more information on development and future research areas, please refer to [Roadmap.md](Roadmap.md).
>>>>>>> 446e53914c5d9f82f391a8f0f259dd39892a7531

## License

This project is MIT licensed. See LICENSE file for details.

---

Built with ❤️ on Replit.
