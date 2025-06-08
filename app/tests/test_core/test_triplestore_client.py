import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS

from app.core.triplestore_client import TriplestoreClient
from app.config import settings


@pytest.fixture
def triplestore_client():
    """Create a TriplestoreClient instance for testing"""
    return TriplestoreClient()


@pytest.fixture
def sample_triples():
    """Sample RDF triples for testing"""
    WDO = Namespace("http://purl.example.org/web_dev_km_bfo#")
    SBEKMS = Namespace("http://sbekms.example.org/instances/")
    
    return [
        (SBEKMS.asset_123, RDF.type, WDO.DigitalInformationCarrier),
        (SBEKMS.asset_123, RDFS.label, Literal("test.py")),
        (SBEKMS.asset_123, WDO.hasFileSize, Literal(1024))
    ]


class TestTriplestoreClient:
    """Test cases for TriplestoreClient"""
    
    @patch('httpx.AsyncClient.get')
    async def test_test_connection_success(self, mock_get, triplestore_client):
        """Test successful connection to GraphDB"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = await triplestore_client.test_connection()
        assert result is True
        mock_get.assert_called_once()
    
    @patch('httpx.AsyncClient.get')
    async def test_test_connection_failure(self, mock_get, triplestore_client):
        """Test failed connection to GraphDB"""
        mock_get.side_effect = Exception("Connection failed")
        
        result = await triplestore_client.test_connection()
        assert result is False
    
    @patch('httpx.AsyncClient.post')
    async def test_add_triples_success(self, mock_post, triplestore_client, sample_triples):
        """Test successful addition of RDF triples"""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response
        
        result = await triplestore_client.add_triples(sample_triples)
        assert result is True
        mock_post.assert_called_once()
    
    @patch('httpx.AsyncClient.post')
    async def test_add_triples_failure(self, mock_post, triplestore_client, sample_triples):
        """Test failed addition of RDF triples"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response
        
        result = await triplestore_client.add_triples(sample_triples)
        assert result is False
    
    def test_serialize_triples(self, triplestore_client, sample_triples):
        """Test serialization of RDF triples to Turtle format"""
        turtle_data = triplestore_client._serialize_triples(sample_triples)
        
        assert isinstance(turtle_data, str)
        assert "DigitalInformationCarrier" in turtle_data
        assert "test.py" in turtle_data
        assert "1024" in turtle_data
    
    @patch('httpx.AsyncClient.post')
    async def test_query_sparql_success(self, mock_post, triplestore_client):
        """Test successful SPARQL query execution"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": {
                "bindings": [
                    {"s": {"value": "http://example.org/asset1"}}
                ]
            }
        }
        mock_post.return_value = mock_response
        
        query = "SELECT ?s WHERE { ?s a <http://example.org/Asset> }"
        result = await triplestore_client.query_sparql(query)
        
        assert result is not None
        assert "results" in result
        mock_post.assert_called_once() 