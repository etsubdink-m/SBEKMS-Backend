import logging
from typing import Dict, List, Set, Tuple, Optional
from pathlib import Path
from rdflib import Graph, Namespace, URIRef, Literal, BNode
from rdflib.namespace import RDF, RDFS, OWL
import owlrl
from app.config import settings

logger = logging.getLogger(__name__)

class OntologyManager:
    """Manages the Web Development Ontology (WDO) and related operations"""
    
    def __init__(self):
        self.graph = Graph()
        self.WDO = Namespace(settings.WDO_NAMESPACE)
        self.SBEKMS = Namespace(settings.INSTANCE_NAMESPACE)
        
        # Bind common namespaces
        self.graph.bind("wdo", self.WDO)
        self.graph.bind("sbekms", self.SBEKMS)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("owl", OWL)
        
        self.loaded = False
        self.classes = set()
        self.properties = set()
        self.object_properties = set()
        self.datatype_properties = set()
    
    async def load_ontology(self) -> bool:
        """Load the WDO ontology from file"""
        try:
            ontology_path = Path(settings.ONTOLOGY_PATH)
            
            if not ontology_path.exists():
                logger.error(f"Ontology file not found: {ontology_path}")
                return False
            
            logger.info(f"Loading ontology from: {ontology_path}")
            self.graph.parse(str(ontology_path), format="xml")
            
            # Apply OWL reasoning
            logger.info("Applying OWL reasoning...")
            owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(self.graph)
            
            # Extract ontology structure
            await self._extract_ontology_structure()
            
            self.loaded = True
            logger.info(f"Ontology loaded successfully: {len(self.graph)} triples, "
                       f"{len(self.classes)} classes, {len(self.properties)} properties")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load ontology: {e}")
            return False
    
    async def _extract_ontology_structure(self):
        """Extract classes and properties from the ontology"""
        try:
            # Extract classes
            for cls in self.graph.subjects(RDF.type, OWL.Class):
                if isinstance(cls, URIRef):
                    self.classes.add(cls)
            
            # Extract object properties
            for prop in self.graph.subjects(RDF.type, OWL.ObjectProperty):
                if isinstance(prop, URIRef):
                    self.object_properties.add(prop)
                    self.properties.add(prop)
            
            # Extract datatype properties
            for prop in self.graph.subjects(RDF.type, OWL.DatatypeProperty):
                if isinstance(prop, URIRef):
                    self.datatype_properties.add(prop)
                    self.properties.add(prop)
            
            logger.info(f"Extracted {len(self.classes)} classes and {len(self.properties)} properties")
            
        except Exception as e:
            logger.error(f"Failed to extract ontology structure: {e}")
    
    def get_classes(self) -> List[Dict]:
        """Get all ontology classes with their metadata"""
        if not self.loaded:
            return []
        
        classes_info = []
        for cls in self.classes:
            class_info = {
                'uri': str(cls),
                'local_name': cls.split('#')[-1] if '#' in str(cls) else cls.split('/')[-1],
                'label': self._get_label(cls),
                'comment': self._get_comment(cls),
                'subclass_of': self._get_subclass_relations(cls)
            }
            classes_info.append(class_info)
        
        return sorted(classes_info, key=lambda x: x['local_name'])
    
    def get_properties(self) -> List[Dict]:
        """Get all ontology properties with their metadata"""
        if not self.loaded:
            return []
        
        properties_info = []
        for prop in self.properties:
            prop_info = {
                'uri': str(prop),
                'local_name': prop.split('#')[-1] if '#' in str(prop) else prop.split('/')[-1],
                'label': self._get_label(prop),
                'comment': self._get_comment(prop),
                'type': 'ObjectProperty' if prop in self.object_properties else 'DatatypeProperty',
                'domain': self._get_domain(prop),
                'range': self._get_range(prop)
            }
            properties_info.append(prop_info)
        
        return sorted(properties_info, key=lambda x: x['local_name'])
    
    def _get_label(self, resource: URIRef) -> Optional[str]:
        """Get rdfs:label for a resource"""
        labels = list(self.graph.objects(resource, RDFS.label))
        return str(labels[0]) if labels else None
    
    def _get_comment(self, resource: URIRef) -> Optional[str]:
        """Get rdfs:comment for a resource"""
        comments = list(self.graph.objects(resource, RDFS.comment))
        return str(comments[0]) if comments else None
    
    def _get_subclass_relations(self, cls: URIRef) -> List[str]:
        """Get superclasses for a class"""
        superclasses = []
        for superclass in self.graph.objects(cls, RDFS.subClassOf):
            if isinstance(superclass, URIRef):
                superclasses.append(str(superclass))
        return superclasses
    
    def _get_domain(self, prop: URIRef) -> List[str]:
        """Get domain classes for a property"""
        domains = []
        for domain in self.graph.objects(prop, RDFS.domain):
            if isinstance(domain, URIRef):
                domains.append(str(domain))
        return domains
    
    def _get_range(self, prop: URIRef) -> List[str]:
        """Get range classes/datatypes for a property"""
        ranges = []
        for range_val in self.graph.objects(prop, RDFS.range):
            if isinstance(range_val, URIRef):
                ranges.append(str(range_val))
        return ranges
    
    def validate_triple(self, subject: URIRef, predicate: URIRef, obj) -> bool:
        """Validate if a triple conforms to the ontology"""
        if not self.loaded:
            return True  # Skip validation if ontology not loaded
        
        try:
            # Check if predicate exists in ontology
            if predicate not in self.properties:
                logger.warning(f"Unknown property: {predicate}")
                return False
            
            # Check domain restrictions
            domains = self._get_domain(predicate)
            if domains:
                subject_types = list(self.graph.objects(subject, RDF.type))
                if not any(str(domain) in [str(t) for t in subject_types] for domain in domains):
                    logger.warning(f"Domain violation for {predicate}: subject {subject} not in domain {domains}")
                    return False
            
            # Check range restrictions for object properties
            if predicate in self.object_properties:
                ranges = self._get_range(predicate)
                if ranges and isinstance(obj, URIRef):
                    obj_types = list(self.graph.objects(obj, RDF.type))
                    if not any(str(range_val) in [str(t) for t in obj_types] for range_val in ranges):
                        logger.warning(f"Range violation for {predicate}: object {obj} not in range {ranges}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating triple: {e}")
            return False
    
    def get_class_hierarchy(self) -> Dict:
        """Get the complete class hierarchy as a tree structure"""
        if not self.loaded:
            return {}
        
        hierarchy = {}
        
        def build_hierarchy(cls, visited=None):
            if visited is None:
                visited = set()
            
            if cls in visited:
                return {}
            
            visited.add(cls)
            
            class_name = cls.split('#')[-1] if '#' in str(cls) else cls.split('/')[-1]
            
            # Find subclasses
            subclasses = []
            for subclass in self.graph.subjects(RDFS.subClassOf, cls):
                if isinstance(subclass, URIRef) and subclass != cls:
                    subclasses.append(build_hierarchy(subclass, visited.copy()))
            
            return {
                'uri': str(cls),
                'name': class_name,
                'label': self._get_label(cls),
                'subclasses': subclasses
            }
        
        # Find root classes (classes without superclasses in WDO namespace)
        root_classes = []
        for cls in self.classes:
            superclasses = list(self.graph.objects(cls, RDFS.subClassOf))
            wdo_superclasses = [sc for sc in superclasses 
                              if isinstance(sc, URIRef) and str(sc).startswith(settings.WDO_NAMESPACE)]
            
            if not wdo_superclasses:
                root_classes.append(build_hierarchy(cls))
        
        return {
            'root_classes': root_classes,
            'total_classes': len(self.classes)
        }
    
    def suggest_classes_for_file(self, file_extension: str, file_name: str) -> List[str]:
        """Suggest appropriate WDO classes for a given file"""
        suggestions = []
        
        # Map file extensions to likely WDO classes
        extension_mapping = {
            '.py': [self.WDO.PythonSourceCodeFile],
            '.js': [self.WDO.JavaScriptSourceCodeFile],
            '.ts': [self.WDO.TypeScriptSourceCodeFile],
            '.jsx': [self.WDO.ReactSourceCodeFile],
            '.tsx': [self.WDO.ReactSourceCodeFile],
            '.java': [self.WDO.JavaSourceCodeFile],
            '.cpp': [self.WDO.CppSourceCodeFile],
            '.c': [self.WDO.CSourceCodeFile],
            '.css': [self.WDO.CSSFile],
            '.scss': [self.WDO.SCSSFile],
            '.html': [self.WDO.HTMLFile],
            '.md': [self.WDO.DocumentationFile],
            '.txt': [self.WDO.DocumentationFile],
            '.json': [self.WDO.ConfigurationFile],
            '.yml': [self.WDO.ConfigurationFile],
            '.yaml': [self.WDO.ConfigurationFile],
            '.svg': [self.WDO.AssetFile],
            '.png': [self.WDO.AssetFile],
            '.jpg': [self.WDO.AssetFile],
            '.jpeg': [self.WDO.AssetFile]
        }
        
        # Get suggestions based on file extension
        if file_extension.lower() in extension_mapping:
            suggestions.extend([str(cls) for cls in extension_mapping[file_extension.lower()]])
        
        # Add generic SourceCodeFile if it's a code file
        code_extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c']
        if file_extension.lower() in code_extensions:
            suggestions.append(str(self.WDO.SourceCodeFile))
        
        # Always add generic DigitalInformationCarrier
        suggestions.append(str(self.WDO.DigitalInformationCarrier))
        
        return list(set(suggestions))  # Remove duplicates
    
    async def get_ontology_stats(self) -> Dict:
        """Get comprehensive ontology statistics"""
        if not self.loaded:
            return {'loaded': False}
        
        return {
            'loaded': True,
            'total_triples': len(self.graph),
            'classes': len(self.classes),
            'object_properties': len(self.object_properties),
            'datatype_properties': len(self.datatype_properties),
            'total_properties': len(self.properties),
            'namespaces': dict(self.graph.namespaces()),
            'ontology_path': settings.ONTOLOGY_PATH
        } 