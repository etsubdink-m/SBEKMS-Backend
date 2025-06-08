from functools import lru_cache
from app.core.triplestore_client import TriplestoreClient
from app.core.ontology_manager import OntologyManager

# Singleton instances
_triplestore_client = None
_ontology_manager = None

@lru_cache()
def get_triplestore_client() -> TriplestoreClient:
    """Get triplestore client singleton"""
    global _triplestore_client
    if _triplestore_client is None:
        _triplestore_client = TriplestoreClient()
    return _triplestore_client

@lru_cache()
def get_ontology_manager() -> OntologyManager:
    """Get ontology manager singleton"""
    global _ontology_manager
    if _ontology_manager is None:
        _ontology_manager = OntologyManager()
    return _ontology_manager 