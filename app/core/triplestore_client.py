import httpx
import logging
from typing import Dict, List, Any, Optional, Tuple
from rdflib import Graph, Namespace
from SPARQLWrapper import SPARQLWrapper, JSON, POST, DIGEST, TURTLE
from app.config import settings

logger = logging.getLogger(__name__)

class TriplestoreClient:
    """Client for interacting with GraphDB triplestore"""
    
    def __init__(self):
        self.base_url = settings.TRIPLESTORE_URL
        self.repository = settings.TRIPLESTORE_REPOSITORY
        self.sparql_endpoint = f"{self.base_url}/repositories/{self.repository}"
        self.update_endpoint = f"{self.sparql_endpoint}/statements"
        self.WDO = Namespace(settings.WDO_NAMESPACE)
        self.SBEKMS = Namespace(settings.INSTANCE_NAMESPACE)
        
        # Initialize SPARQL wrapper
        self.query_wrapper = SPARQLWrapper(f"{self.sparql_endpoint}")
        self.query_wrapper.setReturnFormat(JSON)
        
        # Configure authentication if provided
        if settings.TRIPLESTORE_USERNAME and settings.TRIPLESTORE_PASSWORD:
            self.query_wrapper.setHTTPAuth(DIGEST)
            self.query_wrapper.setCredentials(
                settings.TRIPLESTORE_USERNAME, 
                settings.TRIPLESTORE_PASSWORD
            )
    
    async def test_connection(self) -> bool:
        """Test connection to GraphDB"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/rest/repositories")
                logger.info(f"GraphDB connection test: {response.status_code}")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to connect to GraphDB: {e}")
            return False
    
    async def repository_exists(self) -> bool:
        """Check if the SBEKMS repository exists"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/rest/repositories/{self.repository}")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to check repository existence: {e}")
            return False
    
    async def create_repository(self) -> bool:
        """Create SBEKMS repository if it doesn't exist"""
        try:
            repository_config = {
                "id": self.repository,
                "title": "SBEKMS Knowledge Base",
                "type": "graphdb",
                "location": "",
                "params": {
                    "ruleset": {
                        "label": "Ruleset",
                        "name": "ruleset",
                        "value": "rdfs"
                    },
                    "storage": {
                        "label": "Storage",
                        "name": "storage", 
                        "value": "file"
                    },
                    "enable-context-index": {
                        "label": "Use context index",
                        "name": "enable-context-index",
                        "value": "false"
                    }
                }
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/rest/repositories",
                    json=repository_config,
                    headers={'Content-Type': 'application/json'}
                )
                logger.info(f"Repository creation response: {response.status_code}")
                return response.status_code in [200, 201]
                
        except Exception as e:
            logger.error(f"Failed to create repository: {e}")
            return False
    
    async def initialize(self) -> bool:
        """Initialize triplestore connection and repository"""
        try:
            # Test connection
            if not await self.test_connection():
                logger.error("Cannot connect to GraphDB")
                return False
            
            # Check if repository exists, create if not
            if not await self.repository_exists():
                logger.info(f"Repository {self.repository} doesn't exist, creating...")
                if not await self.create_repository():
                    logger.error("Failed to create repository")
                    return False
                
                # Wait a bit for repository to be ready
                import asyncio
                await asyncio.sleep(2)
            
            logger.info("Triplestore initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize triplestore: {e}")
            return False
    
    async def add_triples(self, triples: List[Tuple]) -> bool:
        """Add RDF triples to the triplestore"""
        try:
            if not triples:
                return True
                
            # Convert triples to Turtle format
            graph = Graph()
            graph.bind("wdo", self.WDO)
            graph.bind("sbekms", self.SBEKMS)
            
            for triple in triples:
                graph.add(triple)
            
            turtle_data = graph.serialize(format='turtle')
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.update_endpoint,
                    headers={'Content-Type': 'text/turtle'},
                    content=turtle_data
                )
                
                success = response.status_code in [200, 204]
                if success:
                    logger.info(f"Added {len(triples)} triples successfully")
                else:
                    logger.error(f"Failed to add triples: {response.status_code} - {response.text}")
                
                return success
                
        except Exception as e:
            logger.error(f"Error adding triples: {e}")
            return False
    
    async def query(self, sparql_query: str) -> Dict[str, Any]:
        """Execute SPARQL SELECT query"""
        try:
            self.query_wrapper.setQuery(sparql_query)
            self.query_wrapper.setReturnFormat(JSON)
            
            results = self.query_wrapper.query().convert()
            logger.info(f"SPARQL query executed successfully, {len(results.get('results', {}).get('bindings', []))} results")
            return results
            
        except Exception as e:
            logger.error(f"SPARQL query failed: {e}")
            raise Exception(f"SPARQL query failed: {e}")
    
    async def construct_query(self, sparql_query: str) -> Graph:
        """Execute SPARQL CONSTRUCT query"""
        try:
            self.query_wrapper.setQuery(sparql_query)
            self.query_wrapper.setReturnFormat(TURTLE)
            
            results = self.query_wrapper.query()
            graph = Graph()
            graph.parse(data=results.serialize(), format='turtle')
            
            logger.info(f"SPARQL CONSTRUCT query executed successfully, {len(graph)} triples")
            return graph
            
        except Exception as e:
            logger.error(f"SPARQL CONSTRUCT query failed: {e}")
            raise Exception(f"SPARQL CONSTRUCT query failed: {e}")
    
    async def clear_repository(self) -> bool:
        """Clear all data from the repository (for testing)"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(self.update_endpoint)
                success = response.status_code in [200, 204]
                if success:
                    logger.info("Repository cleared successfully")
                else:
                    logger.error(f"Failed to clear repository: {response.status_code}")
                return success
                
        except Exception as e:
            logger.error(f"Error clearing repository: {e}")
            return False
    
    async def get_repository_stats(self) -> Dict[str, Any]:
        """Get repository statistics"""
        try:
            stats_query = """
            SELECT (COUNT(*) as ?triples) WHERE {
                ?s ?p ?o .
            }
            """
            
            results = await self.query(stats_query)
            bindings = results.get('results', {}).get('bindings', [])
            
            triple_count = 0
            if bindings:
                triple_count = int(bindings[0].get('triples', {}).get('value', 0))
            
            return {
                'repository': self.repository,
                'endpoint': self.sparql_endpoint,
                'triple_count': triple_count,
                'status': 'connected'
            }
            
        except Exception as e:
            logger.error(f"Failed to get repository stats: {e}")
            return {
                'repository': self.repository,
                'endpoint': self.sparql_endpoint,
                'status': 'error',
                'error': str(e)
            } 