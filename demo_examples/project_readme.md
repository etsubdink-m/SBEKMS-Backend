# SBEKMS Demo Project

This project demonstrates the semantic knowledge management capabilities of the SBEKMS system.

## Overview

SBEKMS (Semantic-Based Explicit Knowledge Management System) automatically transforms document uploads into a searchable knowledge graph using semantic web technologies.

## Features

- **Automatic Document Classification**: Upload any file and get instant semantic annotation
- **Intelligent Semantic Search**: Find documents by meaning, not just keywords  
- **Interactive Knowledge Graph**: Visual exploration of document relationships
- **Multi-format Support**: Python, Markdown, JSON, and many other file types
- **Standards-Based**: Built on W3C semantic web standards (RDF, SPARQL, OWL)

## Technologies Used

- **Backend**: Python, FastAPI
- **Database**: GraphDB (RDF Triplestore)
- **Frontend**: D3.js for graph visualization
- **Containerization**: Docker, Docker Compose
- **Semantic Web**: RDF, SPARQL, OWL ontologies

## Core Components

1. **Semantic Annotator**: Converts documents to RDF triples
2. **Search Engine**: Hybrid semantic and textual search
3. **Knowledge Graph API**: SPARQL-based graph operations  
4. **Interactive Visualizer**: D3.js-powered graph exploration

## Getting Started

```bash
# Start the system
make restart

# Upload a document
curl -X POST "http://localhost:8000/api/v1/assets/upload" \
  -F "file=@your_file.py" \
  -F "title=Your Title" \
  -F "tags=your,tags"

# Search for documents
curl -X POST "http://localhost:8000/api/v1/search/" \
  -H "Content-Type: application/json" \
  -d '{"query": "python", "search_type": "semantic"}'

# View knowledge graph
open http://localhost:8000/visualizer
```

## Use Cases

- **Academic Research**: Organize and explore research papers and data
- **Software Development**: Manage code repositories with semantic classification
- **Documentation Management**: Intelligently organize and search technical docs
- **Knowledge Discovery**: Find unexpected connections between documents

## Architecture

```
User Interface ──→ FastAPI Backend ──→ GraphDB Triplestore
                        │
                        ├── Semantic Annotator
                        ├── Search Engine  
                        ├── Knowledge Graph API
                        └── D3.js Visualizer
```

## Demo Workflow

1. **Upload**: Documents are automatically classified and semantically annotated
2. **Search**: Find documents using semantic or textual search
3. **Explore**: Interactive graph visualization shows relationships
4. **Analyze**: Get insights about knowledge structure and connections

## Educational Value

This system demonstrates key concepts in:
- Semantic web technologies and knowledge graphs
- Information retrieval and search systems
- Data visualization and human-computer interaction
- Modern web architecture and API design

---

*This project showcases how traditional document management can be enhanced with semantic technologies to create intelligent, interconnected knowledge systems.* 