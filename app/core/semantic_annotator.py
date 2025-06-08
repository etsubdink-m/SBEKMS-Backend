import logging
from typing import Any, Dict
from rdflib import  Literal, Namespace
from rdflib.namespace import RDF, RDFS, XSD, DCTERMS

from app.config import settings

logger = logging.getLogger(__name__)

class SemanticAnnotator:
    """Generates RDF triples from file metadata and stores them in triplestore"""
    
    def __init__(self):
        self.WDO = Namespace(settings.WDO_NAMESPACE)
        self.SBEKMS = Namespace(settings.INSTANCE_NAMESPACE)
        
    async def annotate_asset(self, metadata: Dict[str, Any], triplestore) -> int:
        """Generate and store RDF triples for an asset"""
        try:
            triples = []
            
            # Create asset URI
            asset_uri = self.SBEKMS[f"asset_{metadata.get('id', 'unknown')}"]
            
            # Basic asset triples
            triples.append((asset_uri, RDF.type, self.WDO.DigitalInformationCarrier))
            triples.append((asset_uri, RDFS.label, Literal(metadata.get("file_name", ""))))
            
            # File properties
            if metadata.get("file_size"):
                triples.append((asset_uri, self.WDO.hasFileSize, Literal(metadata["file_size"], datatype=XSD.integer)))
            
            if metadata.get("mime_type"):
                triples.append((asset_uri, self.WDO.hasMimeType, Literal(metadata["mime_type"])))
            
            # Enhanced WDO types
            wdo_classes = metadata.get("wdo_classes", [])
            for wdo_class in wdo_classes:
                if wdo_class != "DigitalInformationCarrier":  # Already added
                    class_uri = self.WDO[wdo_class]
                    triples.append((asset_uri, RDF.type, class_uri))
            
            # Content properties
            if metadata.get("line_count"):
                triples.append((asset_uri, self.WDO.hasLineCount, Literal(metadata["line_count"], datatype=XSD.integer)))
            
            # User metadata
            if metadata.get("title"):
                triples.append((asset_uri, DCTERMS.title, Literal(metadata["title"])))
            
            if metadata.get("description"):
                triples.append((asset_uri, DCTERMS.description, Literal(metadata["description"])))
            
            if metadata.get("author"):
                triples.append((asset_uri, DCTERMS.creator, Literal(metadata["author"])))
            
            # Tags
            for tag in metadata.get("tags", []):
                tag_uri = self.SBEKMS[f"tag_{tag.replace(' ', '_')}"]
                triples.append((asset_uri, self.WDO.hasTag, tag_uri))
                triples.append((tag_uri, RDF.type, self.WDO.Tag))
                triples.append((tag_uri, RDFS.label, Literal(tag)))
            
            # Temporal properties
            if metadata.get("created_at"):
                triples.append((asset_uri, DCTERMS.created, Literal(metadata["created_at"], datatype=XSD.dateTime)))
            
            # Store triples
            success = await triplestore.add_triples(triples)
            return len(triples) if success else 0
            
        except Exception as e:
            logger.error(f"Failed to annotate asset: {e}")
            return 0