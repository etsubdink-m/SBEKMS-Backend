from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
import logging
import time
import json
from datetime import datetime

from app.models.common import (
    SuccessResponse, ErrorResponse, ResponseStatus,
    GraphQuery, GraphNode, GraphEdge, GraphAnalytics, 
    GraphVisualization, KnowledgeGraphResponse
)
from app.core.triplestore_client import TriplestoreClient
from app.core.ontology_manager import OntologyManager
from app.dependencies import get_triplestore_client, get_ontology_manager

router = APIRouter()
logger = logging.getLogger(__name__)

class KnowledgeGraphService:
    """Service for knowledge graph operations and visualization"""
    
    def __init__(self, triplestore: TriplestoreClient, ontology: OntologyManager):
        self.triplestore = triplestore
        self.ontology = ontology
        self.WDO_NS = "http://purl.example.org/web_dev_km_bfo#"
        self.SBEKMS_NS = "http://sbekms.example.org/instances/"
    
    async def get_knowledge_graph(self, query: GraphQuery) -> KnowledgeGraphResponse:
        """Get knowledge graph based on query parameters"""
        start_time = time.time()
        
        try:
            # Build appropriate SPARQL query based on query type
            if query.query_type == "neighborhood":
                sparql_query = self._build_neighborhood_query(query)
            elif query.query_type == "path":
                sparql_query = self._build_path_query(query)
            elif query.query_type == "cluster":
                sparql_query = self._build_cluster_query(query)
            else:  # full
                sparql_query = self._build_full_graph_query(query)
            
            # Execute query
            query_results = await self.triplestore.query(sparql_query)
            results = query_results.get('results', {}).get('bindings', [])
            
            # Process results into graph structure
            nodes, edges = self._process_graph_results(results, query)
            
            # Generate analytics
            analytics = self._calculate_graph_analytics(nodes, edges)
            
            # Create visualization config
            viz_config = GraphVisualization()
            
            # Calculate response time
            response_time = (time.time() - start_time) * 1000
            
            return KnowledgeGraphResponse(
                status=ResponseStatus.SUCCESS,
                graph={
                    "nodes": [node.dict() for node in nodes],
                    "edges": [edge.dict() for edge in edges]
                },
                analytics=analytics,
                visualization_config=viz_config,
                query_info={
                    "query_type": query.query_type,
                    "center_entity": query.center_entity,
                    "depth": query.depth,
                    "response_time_ms": response_time,
                    "total_results": len(results)
                }
            )
            
        except Exception as e:
            logger.error(f"Knowledge graph query failed: {e}")
            raise HTTPException(status_code=500, detail=f"Graph query failed: {str(e)}")
    
    def _build_neighborhood_query(self, query: GraphQuery) -> str:
        """Build SPARQL query for neighborhood exploration"""
        center_filter = ""
        if query.center_entity:
            center_filter = f"FILTER(?s = <{query.center_entity}> || ?o = <{query.center_entity}>)"
        
        return f"""
        PREFIX wdo: <{self.WDO_NS}>
        PREFIX sbekms: <{self.SBEKMS_NS}>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        
        SELECT DISTINCT ?s ?p ?o ?sLabel ?oLabel ?sType ?oType
        WHERE {{
            ?s ?p ?o .
            {center_filter}
            
            # Get labels
            OPTIONAL {{ ?s rdfs:label ?sLabel }}
            OPTIONAL {{ ?o rdfs:label ?oLabel }}
            
            # Get types
            OPTIONAL {{ ?s rdf:type ?sType }}
            OPTIONAL {{ ?o rdf:type ?oType }}
            
            # Filter out technical predicates if requested
            FILTER(?p != rdf:type || ?p = rdf:type)
        }}
        LIMIT {query.max_nodes * 2}
        """
    
    def _build_path_query(self, query: GraphQuery) -> str:
        """Build SPARQL query for path finding between entities"""
        if not query.source_entity or not query.target_entity:
            raise ValueError("Path queries require both source_entity and target_entity")
        
        return f"""
        PREFIX wdo: <{self.WDO_NS}>
        PREFIX sbekms: <{self.SBEKMS_NS}>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
        SELECT DISTINCT ?s ?p ?o ?sLabel ?oLabel ?sType ?oType
        WHERE {{
            # Find all connections involving either source or target entity
            {{
                # Direct connection from source to target
                <{query.source_entity}> ?p <{query.target_entity}> .
                BIND(<{query.source_entity}> AS ?s)
                BIND(<{query.target_entity}> AS ?o)
            }}
            UNION
            {{
                # Direct connection from target to source  
                <{query.target_entity}> ?p <{query.source_entity}> .
                BIND(<{query.target_entity}> AS ?s)
                BIND(<{query.source_entity}> AS ?o)
            }}
            UNION
            {{
                # Connections through intermediate nodes
                ?s ?p ?o .
                {{
                    <{query.source_entity}> ?p1 ?intermediate .
                    ?intermediate ?p2 <{query.target_entity}> .
                    FILTER(?s = <{query.source_entity}> || ?s = ?intermediate || ?s = <{query.target_entity}> ||
                           ?o = <{query.source_entity}> || ?o = ?intermediate || ?o = <{query.target_entity}>)
                }}
            }}
            
            OPTIONAL {{ ?s rdfs:label ?sLabel }}
            OPTIONAL {{ ?o rdfs:label ?oLabel }}
            OPTIONAL {{ ?s rdf:type ?sType }}
            OPTIONAL {{ ?o rdf:type ?oType }}
        }}
        LIMIT {query.max_nodes}
        """
    
    def _build_cluster_query(self, query: GraphQuery) -> str:
        """Build SPARQL query for cluster analysis"""
        return f"""
        PREFIX wdo: <{self.WDO_NS}>
        PREFIX sbekms: <{self.SBEKMS_NS}>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        
        SELECT DISTINCT ?s ?p ?o ?sLabel ?oLabel ?sType ?oType
        WHERE {{
            ?s ?p ?o .
            ?s rdf:type ?sType .
            ?o rdf:type ?oType .
            
            # Focus on same-type clustering
            FILTER(?sType = ?oType)
            
            OPTIONAL {{ ?s rdfs:label ?sLabel }}
            OPTIONAL {{ ?o rdfs:label ?oLabel }}
        }}
        LIMIT {query.max_nodes}
        """
    
    def _build_full_graph_query(self, query: GraphQuery) -> str:
        """Build SPARQL query for full graph overview"""
        return f"""
        PREFIX wdo: <{self.WDO_NS}>
        PREFIX sbekms: <{self.SBEKMS_NS}>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        
        SELECT DISTINCT ?s ?p ?o ?sLabel ?oLabel ?sType ?oType
        WHERE {{
            ?s ?p ?o .
            
            # Focus on core entities
            ?s rdf:type wdo:DigitalInformationCarrier .
            
            OPTIONAL {{ ?s rdfs:label ?sLabel }}
            OPTIONAL {{ ?o rdfs:label ?oLabel }}
            OPTIONAL {{ ?s rdf:type ?sType }}
            OPTIONAL {{ ?o rdf:type ?oType }}
            
            # Exclude some technical predicates for cleaner visualization
            FILTER(?p != <http://www.w3.org/1999/02/22-rdf-syntax-ns#type>)
        }}
        LIMIT {query.max_nodes}
        """
    
    def _process_graph_results(self, results: List[Dict], query: GraphQuery) -> tuple[List[GraphNode], List[GraphEdge]]:
        """Process SPARQL results into graph nodes and edges"""
        nodes_dict = {}
        edges_list = []
        
        for result in results:
            # Extract subject node
            subject_uri = result.get('s', {}).get('value', '')
            subject_label = result.get('sLabel', {}).get('value', self._extract_label_from_uri(subject_uri))
            subject_type = result.get('sType', {}).get('value', 'Unknown')
            
            if subject_uri and subject_uri not in nodes_dict:
                nodes_dict[subject_uri] = GraphNode(
                    id=subject_uri,
                    label=subject_label,
                    type=self._extract_class_name(subject_type),
                    properties={
                        "uri": subject_uri,
                        "full_type": subject_type
                    }
                )
            
            # Extract object node
            object_uri = result.get('o', {}).get('value', '')
            object_label = result.get('oLabel', {}).get('value', self._extract_label_from_uri(object_uri))
            object_type = result.get('oType', {}).get('value', 'Unknown')
            
            # Only create object node if it's a URI (not literal)
            if object_uri.startswith('http') and object_uri not in nodes_dict:
                nodes_dict[object_uri] = GraphNode(
                    id=object_uri,
                    label=object_label,
                    type=self._extract_class_name(object_type),
                    properties={
                        "uri": object_uri,
                        "full_type": object_type
                    }
                )
            
            # Extract relationship
            predicate_uri = result.get('p', {}).get('value', '')
            relationship_name = self._extract_relationship_name(predicate_uri)
            
            # Create edge if both nodes are URIs
            if subject_uri and object_uri.startswith('http'):
                edge = GraphEdge(
                    source=subject_uri,
                    target=object_uri,
                    relationship=relationship_name,
                    properties={
                        "predicate_uri": predicate_uri
                    }
                )
                edges_list.append(edge)
            
            # For literals, add as node property instead
            elif subject_uri and not object_uri.startswith('http'):
                if subject_uri in nodes_dict:
                    prop_name = self._extract_relationship_name(predicate_uri)
                    nodes_dict[subject_uri].properties[prop_name] = object_uri
        
        return list(nodes_dict.values()), edges_list
    
    def _calculate_graph_analytics(self, nodes: List[GraphNode], edges: List[GraphEdge]) -> GraphAnalytics:
        """Calculate graph analytics and statistics"""
        total_nodes = len(nodes)
        total_edges = len(edges)
        
        # Count node types
        node_types = {}
        for node in nodes:
            node_type = node.type
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        # Count relationship types
        relationship_types = {}
        for edge in edges:
            rel_type = edge.relationship
            relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1
        
        # Calculate degree statistics
        degree_count = {}
        for edge in edges:
            degree_count[edge.source] = degree_count.get(edge.source, 0) + 1
            degree_count[edge.target] = degree_count.get(edge.target, 0) + 1
        
        avg_degree = sum(degree_count.values()) / len(degree_count) if degree_count else 0
        max_degree = max(degree_count.values()) if degree_count else 0
        
        # Calculate density
        max_possible_edges = total_nodes * (total_nodes - 1) / 2 if total_nodes > 1 else 1
        density = total_edges / max_possible_edges if max_possible_edges > 0 else 0
        
        return GraphAnalytics(
            total_nodes=total_nodes,
            total_edges=total_edges,
            node_types=node_types,
            relationship_types=relationship_types,
            avg_degree=round(avg_degree, 2),
            max_degree=max_degree,
            connected_components=1,  # Simplified - would need more complex analysis
            density=round(density, 4)
        )
    
    def _extract_label_from_uri(self, uri: str) -> str:
        """Extract a readable label from URI"""
        if '#' in uri:
            return uri.split('#')[-1]
        elif '/' in uri:
            return uri.split('/')[-1]
        return uri
    
    def _extract_class_name(self, class_uri: str) -> str:
        """Extract class name from URI"""
        if not class_uri or class_uri == 'Unknown':
            return 'Resource'
        if '#' in class_uri:
            return class_uri.split('#')[-1]
        elif '/' in class_uri:
            return class_uri.split('/')[-1]
        return class_uri
    
    def _extract_relationship_name(self, predicate_uri: str) -> str:
        """Extract relationship name from predicate URI"""
        if '#' in predicate_uri:
            return predicate_uri.split('#')[-1]
        elif '/' in predicate_uri:
            return predicate_uri.split('/')[-1]
        return predicate_uri

# API Endpoints
@router.get("/health")
async def graph_health():
    """Graph API health check"""
    return {
        "status": "healthy", 
        "service": "knowledge-graph", 
        "version": "1.0.0",
        "features": ["visualization", "analytics", "exploration", "querying"]
    }

@router.post("/explore", response_model=KnowledgeGraphResponse)
async def explore_knowledge_graph(
    query: GraphQuery,
    triplestore: TriplestoreClient = Depends(get_triplestore_client),
    ontology: OntologyManager = Depends(get_ontology_manager)
):
    """
    Explore the knowledge graph with different query types:
    
    - **neighborhood**: Explore entities around a center node
    - **path**: Find paths between two entities  
    - **cluster**: Find clusters of related entities
    - **full**: Get overview of the entire knowledge graph
    """
    service = KnowledgeGraphService(triplestore, ontology)
    return await service.get_knowledge_graph(query)

@router.get("/neighborhood/{entity_id}")
async def get_entity_neighborhood(
    entity_id: str,
    depth: int = Query(2, ge=1, le=5, description="Exploration depth"),
    max_nodes: int = Query(50, ge=10, le=200, description="Maximum nodes"),
    triplestore: TriplestoreClient = Depends(get_triplestore_client),
    ontology: OntologyManager = Depends(get_ontology_manager)
):
    """Get the neighborhood graph around a specific entity"""
    query = GraphQuery(
        query_type="neighborhood",
        center_entity=entity_id,
        depth=depth,
        max_nodes=max_nodes
    )
    
    service = KnowledgeGraphService(triplestore, ontology)
    return await service.get_knowledge_graph(query)

@router.get("/analytics")
async def get_graph_analytics(
    triplestore: TriplestoreClient = Depends(get_triplestore_client),
    ontology: OntologyManager = Depends(get_ontology_manager)
):
    """Get comprehensive graph analytics and statistics"""
    try:
        # Get basic statistics
        stats_query = """
        SELECT 
            (COUNT(DISTINCT ?s) AS ?subjects)
            (COUNT(DISTINCT ?p) AS ?predicates)  
            (COUNT(DISTINCT ?o) AS ?objects)
            (COUNT(*) AS ?triples)
        WHERE {
            ?s ?p ?o .
        }
        """
        
        query_results = await triplestore.query(stats_query)
        results = query_results.get('results', {}).get('bindings', [])
        
        basic_stats = {}
        if results:
            result = results[0]
            basic_stats = {
                "total_subjects": int(result.get('subjects', {}).get('value', 0)),
                "total_predicates": int(result.get('predicates', {}).get('value', 0)),
                "total_objects": int(result.get('objects', {}).get('value', 0)),
                "total_triples": int(result.get('triples', {}).get('value', 0))
            }
        
        # Get type distribution
        type_query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        SELECT ?type (COUNT(?s) AS ?count)
        WHERE {
            ?s rdf:type ?type .
        }
        GROUP BY ?type
        ORDER BY DESC(?count)
        """
        
        type_results = await triplestore.query(type_query)
        type_bindings = type_results.get('results', {}).get('bindings', [])
        
        type_distribution = {}
        for binding in type_bindings:
            type_uri = binding.get('type', {}).get('value', '')
            count = int(binding.get('count', {}).get('value', 0))
            type_name = type_uri.split('#')[-1] if '#' in type_uri else type_uri.split('/')[-1]
            type_distribution[type_name] = count
        
        return SuccessResponse(
            message="Retrieved graph analytics",
            data={
                "basic_statistics": basic_stats,
                "type_distribution": type_distribution,
                "generated_at": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get graph analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@router.get("/entities")
async def list_entities(
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    limit: int = Query(50, ge=1, le=200, description="Maximum entities to return"),
    triplestore: TriplestoreClient = Depends(get_triplestore_client),
    ontology: OntologyManager = Depends(get_ontology_manager)
):
    """List all entities in the knowledge graph"""
    try:
        type_filter = ""
        if entity_type:
            type_filter = f"?entity rdf:type <{entity_type}> ."
        
        entities_query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX wdo: <http://purl.example.org/web_dev_km_bfo#>
        
        SELECT DISTINCT ?entity ?label ?type
        WHERE {{
            ?entity ?p ?o .
            {type_filter}
            
            OPTIONAL {{ ?entity rdfs:label ?label }}
            OPTIONAL {{ ?entity rdf:type ?type }}
            
            FILTER(isURI(?entity))
        }}
        ORDER BY ?label
        LIMIT {limit}
        """
        
        query_results = await triplestore.query(entities_query)
        results = query_results.get('results', {}).get('bindings', [])
        
        entities = []
        for result in results:
            entity_uri = result.get('entity', {}).get('value', '')
            label = result.get('label', {}).get('value', entity_uri.split('/')[-1])
            entity_type = result.get('type', {}).get('value', 'Unknown')
            
            entities.append({
                "id": entity_uri,
                "label": label,
                "type": entity_type.split('#')[-1] if '#' in entity_type else entity_type.split('/')[-1]
            })
        
        return SuccessResponse(
            message=f"Found {len(entities)} entities",
            data={"entities": entities}
        )
        
    except Exception as e:
        logger.error(f"Failed to list entities: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list entities: {str(e)}")