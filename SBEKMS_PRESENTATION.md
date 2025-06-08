# SBEKMS: Semantic-Based Explicit Knowledge Management System
## MSc Presentation & Demo Guide

---

## 🎯 **System Overview**

SBEKMS is a **Semantic-Based Explicit Knowledge Management System** that automatically transforms document uploads into a searchable knowledge graph. It combines traditional file storage with **semantic web technologies** to create rich, interconnected knowledge representations.

 "SBEKMS is a knowledge graph construction system that transforms document uploads into a structured RDF knowledge base. While initial classification uses rule-based heuristics, the system creates rich semantic relationships and enables sophisticated graph-based querying, visualization, and knowledge discovery through W3C semantic web standards."

### **Core Value Proposition**
- **Automatic Semantic Annotation**: Upload any document and get instant semantic classification
- **Intelligent Search**: Find documents by meaning, not just keywords
- **Visual Knowledge Exploration**: Interactive graph visualization of document relationships
- **Standards-Based**: Uses W3C semantic web standards (RDF, SPARQL, OWL)

---

## 🏗️ **System Architecture**

```
[User Interface] ──→ [FastAPI Backend] ──→ [GraphDB Triplestore]
                            │
                            ├── Semantic Annotator
                            ├── Search Engine  
                            ├── Knowledge Graph API
                            └── D3.js Visualizer
```

### **Core Components**

1. **FastAPI Backend**: RESTful API server handling all operations
2. **GraphDB**: RDF triplestore storing semantic knowledge
3. **Semantic Annotator**: Converts documents to RDF triples
4. **Search Engine**: Semantic + textual search capabilities
5. **Graph Visualizer**: Interactive D3.js knowledge graph

---

## 🔧 **Core Functionalities**

### 1. **Document Upload & Semantic Annotation**

**What it does**: When you upload a document, the system:
- Analyzes file type, size, and metadata
- Classifies content using WDO (Web Development Ontology)
- Generates semantic tags and relationships
- Stores everything as RDF triples in the knowledge graph

**Example**: Upload `test.py` → System identifies it as `PythonSourceCodeFile` → Creates semantic relationships → Links to concepts like "programming", "python", "source-code"

### 2. **Semantic Search**

**What it does**: Find documents by meaning and relationships, not just exact text matches:
- **Semantic Search**: "Show me all documentation files" → Finds .md, .txt, .rst files
- **Textual Search**: "python" → Finds files containing the word "python"  
- **Hybrid Search**: Combines both approaches for best results

**Example**: Search for "documentation" finds all docs even if they don't contain that exact word, because the system understands their semantic type.

### 3. **Knowledge Graph Visualization**

**What it does**: Shows how documents relate to each other and to concepts:
- **Full Graph**: Overview of entire knowledge base
- **Neighborhood**: Explore connections around specific entities
- **Clusters**: Group related documents by type or topic
- **Interactive**: Click, zoom, drag to explore relationships

**Example**: Visual graph shows `test.py` connected to tags like "python", "demo", "testing" with relationship lines you can follow.

---

## 📋 **Step-by-Step Demo Guide**

### **Prerequisites Setup**

```bash
# 1. Start the system
make restart

# 2. Verify services are running
curl http://localhost:8000/health
```

### **Demo 1: Document Upload & Semantic Annotation**

**Goal**: Show how documents get automatically semantically annotated

#### **Step 1: Create Test Documents**

Create these test files in your workspace:

**File 1: `demo_script.py`**
```python
#!/usr/bin/env python3
"""
Demo Python script for SBEKMS testing
This script demonstrates basic Python functionality
"""

def hello_world():
    """Simple greeting function"""
    print("Hello from SBEKMS!")
    return "Success"

if __name__ == "__main__":
    hello_world()
```

**File 2: `project_readme.md`**
```markdown
# SBEKMS Demo Project

This project demonstrates the semantic knowledge management capabilities.

## Features
- Automatic document classification
- Semantic search
- Knowledge graph visualization

## Technologies
- Python
- FastAPI
- GraphDB
- D3.js
```

**File 3: `config.json`**
```json
{
  "project": "SBEKMS Demo",
  "version": "1.0.0",
  "description": "Configuration for semantic knowledge management",
  "settings": {
    "debug": true,
    "semantic_analysis": true
  }
}
```

#### **Step 2: Upload Documents via API**

```bash
# Upload Python file
curl -X POST "http://localhost:8000/api/v1/assets/upload" \
  -F "file=@demo_script.py" \
  -F "title=Demo Python Script" \
  -F "description=Example Python script for testing" \
  -F "tags=python,demo,testing" \
  -F "author=Demo User"

# Upload Markdown file  
curl -X POST "http://localhost:8000/api/v1/assets/upload" \
  -F "file=@project_readme.md" \
  -F "title=Project Documentation" \
  -F "description=README documentation" \
  -F "tags=documentation,readme,markdown" \
  -F "author=Demo User"

# Upload JSON config
curl -X POST "http://localhost:8000/api/v1/assets/upload" \
  -F "file=@config.json" \
  -F "title=Project Configuration" \
  -F "description=Project settings file" \
  -F "tags=configuration,settings,json" \
  -F "author=Demo User"
```

#### **Step 3: Observe Semantic Annotation Results**

Each upload response shows:
```json
{
  "message": "Asset 'demo_script.py' uploaded and annotated successfully",
  "data": {
    "asset_type": "SOURCE_CODE",
    "wdo_classes": [
      "DigitalInformationCarrier",
      "SourceCodeFile", 
      "PythonSourceCodeFile"
    ],
    "rdf_triples_count": 15,
    "semantic_tags": ["python", "demo", "testing"]
  }
}
```

**Key Points to Highlight**:
- System automatically classified Python file as `PythonSourceCodeFile`
- Generated 15 RDF triples representing relationships
- Connected file to semantic concepts through tags

### **Demo 2: Semantic Search**

**Goal**: Show different search capabilities

#### **Step 1: Semantic Search by Type**

```bash
# Find all source code files
curl -X POST "http://localhost:8000/api/v1/search/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SourceCode",
    "search_type": "semantic",
    "limit": 10
  }'
```

**Expected Result**: Returns `demo_script.py` because system understands it's source code, even though filename doesn't contain "source code"



#### **Step 2: Textual Search**

```bash
# Find files containing "python"
curl -X POST "http://localhost:8000/api/v1/search/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "python", 
    "search_type": "textual",
    "limit": 10
  }'
```

**Expected Result**: Returns both Python file and README (mentions Python)

#### **Step 3: Advanced Search with Filters**

```bash
# Find documentation files by a specific author
curl -X POST "http://localhost:8000/api/v1/search/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "documentation",
    "search_type": "semantic",
    "file_types": ["md"],
    "author": "Demo User",
    "limit": 10
  }'
```

**Key Points to Highlight**:
- Semantic search understands meaning beyond keywords
- Can filter by multiple criteria simultaneously  
- Results include relevance scoring and highlights

Use these working search examples:


// ✅ Find source code files
{"query": "SourceCodeFile", "search_type": "semantic"}

// ✅ Find Python files specifically  
{"query": "PythonSourceCodeFile", "search_type": "semantic"}

// ✅ Find by partial match
{"query": "SourceCode", "search_type": "semantic"}

// ✅ Find by filename
{"query": "demo", "search_type": "textual"}

// ✅ Find by technology
{"query": "python", "search_type": "semantic"}

### **Demo 3: Knowledge Graph Visualization**

**Goal**: Show interactive knowledge graph exploration

#### **Step 1: Access the Visualizer**

1. Open browser to: `http://localhost:8000/visualizer`
2. Wait for graph to load (shows uploaded documents and their relationships)

#### **Step 2: Explore Full Graph**

- **Action**: Select "Full Graph" mode
- **Expected**: See all uploaded files as nodes connected to their semantic tags
- **Highlight**: Point out connections between files and concept tags

#### **Step 3: Entity Neighborhood Exploration**

```bash
# Get neighborhood data for Python file (use actual URI from upload response)
curl "http://localhost:8000/api/v1/graph/neighborhood/sbekms_instance_demo_script_py?depth=2&max_nodes=20"
```

- **Action**: In visualizer, click on the Python file node
- **Expected**: Graph highlights immediate connections (tags, file type, etc.)
- **Highlight**: Show how you can explore relationships interactively

#### **Step 4: Search and Focus**

- **Action**: Use search box in visualizer to find specific entities
- **Expected**: Graph zooms to and highlights matching nodes
- **Highlight**: Dynamic filtering and exploration capabilities

### **Demo 4: Graph Analytics**

**Goal**: Show knowledge graph insights

```bash
# Get graph analytics
curl "http://localhost:8000/api/v1/graph/analytics"
```

**Expected Response**:
```json
{
  "total_nodes": 12,
  "total_edges": 24, 
  "average_degree": 4.0,
  "graph_density": 0.364,
  "node_types": {
    "DigitalInformationCarrier": 3,
    "SemanticTag": 9
  },
  "most_connected_entities": [
    {"entity": "demo_script.py", "connections": 6},
    {"entity": "python", "connections": 4}
  ]
}
```

**Key Points to Highlight**:
- System provides quantitative analysis of knowledge structure
- Identifies most important/connected entities
- Shows knowledge density and distribution

---

## 🎯 **Key Demo Talking Points**

### **1. Automatic Intelligence**
- "Notice how we didn't tell the system this was Python code - it figured that out automatically"
- "The semantic classification happens instantly during upload"

### **2. Rich Relationships**  
- "Each document isn't just stored - it's connected to concepts and other documents"
- "The graph shows meaningful relationships, not just folder structures"

### **3. Powerful Search**
- "You can search by what documents ARE, not just what they contain"
- "The system understands synonyms and related concepts"

### **4. Visual Discovery**
- "The graph visualization lets you discover connections you might not have thought of"
- "You can explore the knowledge base interactively, following relationships"

### **5. Standards-Based**
- "Built on W3C semantic web standards (RDF, SPARQL, OWL)"
- "Knowledge is portable and can integrate with other semantic systems"

---

## 🔍 **Technical Validation Points**

### **Verify System is Working**

1. **Check API Health**: `curl http://localhost:8000/health`
2. **Verify GraphDB**: `curl http://localhost:8000/api/v1/system/triplestore/status`  
3. **Test Upload**: Upload a simple text file
4. **Test Search**: Search for uploaded content
5. **View Graph**: Open visualizer and confirm nodes appear

### **Troubleshooting**

- **No results in search**: Check if documents were uploaded successfully
- **Empty graph**: Verify triplestore connection and data upload
- **Visualizer not loading**: Confirm static files are served correctly

---

## 📊 **Demo Success Metrics**

By the end of the demo, you should have shown:

✅ **Document Upload**: 3+ files with different types  
✅ **Semantic Classification**: Automatic type detection  
✅ **Search Functionality**: Semantic vs textual differences  
✅ **Graph Visualization**: Interactive knowledge exploration  
✅ **Analytics**: Quantitative insights about knowledge structure  

---

## 🎓 **Educational Value**

This system demonstrates key concepts in:

- **Semantic Web Technologies**: RDF, SPARQL, ontologies
- **Knowledge Management**: Automatic classification and relationship discovery  
- **Information Retrieval**: Advanced search beyond keyword matching
- **Data Visualization**: Interactive graph exploration
- **Modern Web Architecture**: RESTful APIs, microservices, containerization

The SBEKMS showcases how traditional document management can be enhanced with semantic technologies to create intelligent, interconnected knowledge systems. 