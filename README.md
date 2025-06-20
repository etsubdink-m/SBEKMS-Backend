# SBEKMS Backend - Semantic Knowledge Management System

A semantic web-based knowledge management system built with FastAPI, GraphDB, and Web Development Ontology (WDO).

## 🚀 Quick Start

```bash
# Show all available commands
make help

# Start development environment
make dev

# Run tests
make test-integration
```

## 📋 Available Commands

### Docker Operations
```bash
make build           # Build Docker containers
make up              # Start all services
make down            # Stop all services
make restart         # Restart all services
make rebuild         # Rebuild and restart all services
make logs            # Follow API logs
make logs-all        # Follow all container logs
```

### Testing
```bash
make test            # Run all tests
make test-quick      # Run tests with fail-fast
make test-api        # Run API tests only
make test-core       # Run core component tests only
make test-integration # Run integration tests only (recommended for verification)
make test-coverage   # Run tests with coverage report
```

### Development
```bash
make shell           # Access API container shell
make shell-graphdb   # Access GraphDB container shell
make install         # Install/update Python dependencies
```

### Health & Status
```bash
make health          # Check health of all services
make status          # Show container status
```

### Cleanup
```bash
make clean           # Clean up containers, volumes, and images
make clean-all       # Remove everything including images (destructive!)
make clean-uploads   # Clean uploaded test files
```

### Quick Actions
```bash
make dev             # Build and start development environment
make check           # Quick health check and tests
make info            # Show project information
```

## 🏗️ Project Structure

```
SBEKMS-Main/backend/
├── app/
│   ├── api/                 # FastAPI route handlers
│   ├── core/               # Core business logic
│   │   ├── triplestore_client.py    # GraphDB integration
│   │   ├── ontology_manager.py      # OWL ontology handling
│   │   ├── semantic_annotator.py    # RDF triple generation
│   │   └── artifact_parser.py       # File content analysis
│   ├── models/             # Pydantic data models
│   ├── tests/              # Test suite
│   │   ├── test_api/       # API endpoint tests
│   │   ├── test_core/      # Core component tests
│   │   └── test_integration.py  # End-to-end tests
│   └── utils/              # Utility functions
├── data/
│   ├── ontologies/         # OWL ontology files
│   └── uploads/            # File upload storage
├── docker-compose.yml      # Docker services configuration
├── Dockerfile              # API container definition
├── Makefile                # Project management commands
└── requirements.txt        # Python dependencies
```

## 🔧 Technology Stack

- **Backend API**: FastAPI with Python 3.12
- **Triplestore**: GraphDB 10.0.2 (RDF database)
- **Ontology**: Web Development Ontology (WDO) with OWL 2 DL
- **Containerization**: Docker & Docker Compose
- **Testing**: pytest with async support
- **RDF Processing**: rdflib, SPARQLWrapper, owlrl

## 🌐 Service URLs

- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **GraphDB Workbench**: http://localhost:7200

## 🧪 Testing

The system includes comprehensive tests:

- **Integration Tests**: End-to-end file upload and semantic annotation workflows
- **API Tests**: REST endpoint validation and error handling
- **Core Tests**: Component-level functionality testing

Run the integration tests to verify everything is working:
```bash
make test-integration
```

Expected output: ✅ 5/5 tests passing with semantic triple generation confirmed.

## 📊 Key Features

- **Semantic File Classification**: Automatic WDO-based file type classification
- **RDF Triple Generation**: 19-22 semantic triples per uploaded file
- **Multi-level Ontology Mapping**: Hierarchical classification (e.g., DigitalInformationCarrier → SourceCodeFile → PythonSourceCodeFile)
- **Checksum Validation**: SHA-256 file integrity verification
- **SPARQL Query Interface**: Direct triplestore querying capabilities
- **RESTful API**: Comprehensive FastAPI-based interface

## 🔍 Example Workflow

1. **Start System**: `make dev`
2. **Upload File**: POST to `/api/assets/upload` with file and metadata
3. **Semantic Processing**: System generates 19-22 RDF triples with WDO classification
4. **Storage**: Triples stored in GraphDB repository "sbekms"
5. **Verification**: `make test-integration` confirms end-to-end functionality

## 📝 Development Notes

- Tests are automatically included in Docker builds
- File uploads trigger automatic server reloads in development
- System supports Python, Markdown, JSON, and other file types
- All semantic annotations follow W3C RDF standards
- OWL reasoning is applied for ontology consistency

## 🚨 Troubleshooting

```bash
# Check system health
make health

# View logs for debugging
make logs

# Restart if issues occur
make restart

# Full reset (destructive)
make clean-all && make dev
```

## 📖 Further Reading

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [GraphDB Documentation](https://graphdb.ontotext.com/)
- [RDF/OWL Specifications](https://www.w3.org/RDF/)
- [Web Development Ontology](docs/ontology.md) (if available)
