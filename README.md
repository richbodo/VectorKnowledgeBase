# PDF Knowledge Base

A Flask-powered PDF document processing service that enables semantic search and content retrieval using advanced vector database technologies and OpenAI GPT integration.

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

## Features

- **PDF Processing**: Extract text from PDF documents with memory-efficient processing
- **Semantic Search**: Search across all your documents using natural language queries
- **Vector Database Storage**: Store and retrieve document embeddings efficiently
- **API Access**: Programmatically upload documents and query the knowledge base
- **Web Interface**: User-friendly interface for uploading and querying documents
- **Persistence**: Robust backup and restore functionality for vector database
- **Monitoring**: Built-in diagnostic tools for system health and database stats

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
   export OPENAI_API_KEY="your_openai_api_key"
   export VKB_API_KEY="your_custom_api_key"
   ```
4. Run the application: `python main.py`
5. Access the web interface at `http://localhost:5000`

## API Usage

For detailed API documentation including authentication methods, endpoints, and example usage, see [api_specification.md](api_specification.md).

## Architecture

- **Flask Backend**: Web framework for interface and API
- **PyMuPDF**: PDF text extraction with optimized memory usage
- **OpenAI**: Text embeddings and query processing
- **ChromaDB**: Vector database for semantic search
- **Object Storage**: Persistent storage for ChromaDB data

## Deployment

### Deploying on Replit

1. **Fork the Repository**
   - Create a new Replit project importing from GitHub repository

2. **Set Required Environment Variables**
   - `OPENAI_API_KEY`: Your OpenAI API key for embeddings and queries
   - `VKB_API_KEY`: Custom API key for API endpoint authentication

3. **Install Dependencies**
   - Replit will automatically install dependencies from pyproject.toml

4. **Configure Storage**
   - Ensure persistent storage is enabled
   - For production, consider enabling Replit's Object Storage

5. **Run the Application**
   - Use the "Run" button in Replit
   - Application will start on the default Replit port
   - First run will initialize the ChromaDB database

6. **Verify Functionality**
   - Navigate to the web interface
   - Upload a test PDF
   - Test search functionality
   - Check the /monitoring/database-diagnostic endpoint

### Deploying on Linux Server

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
   export OPENAI_API_KEY="your_openai_api_key"
   export VKB_API_KEY="your_custom_api_key"
   # Optional: Configure ChromaDB location
   export CHROMADB_DIR="/path/to/persistent/storage"
   ```

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

For more information on development and future research areas, please refer to [Roadmap.md](Roadmap.md).

## License

This project is MIT licensed. See LICENSE file for details.

---

Built with ❤️ on Replit.