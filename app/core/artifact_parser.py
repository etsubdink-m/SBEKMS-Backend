import os
import logging
import hashlib
import mimetypes
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import ast
import re
import json
import yaml

logger = logging.getLogger(__name__)

class FileMetadata:
    """Container for file metadata"""
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file_name = self.file_path.name
        self.file_extension = self.file_path.suffix.lower()
        self.file_size = 0
        self.mime_type = ""
        self.encoding = "utf-8"
        self.checksum = ""
        self.creation_time = None
        self.modification_time = None
        
        # Content analysis
        self.line_count = 0
        self.character_count = 0
        self.word_count = 0
        
        # Code-specific metadata
        self.programming_language = None
        self.functions = []
        self.classes = []
        self.imports = []
        self.comments = []
        self.dependencies = []
        
        # Documentation metadata
        self.headings = []
        self.links = []
        self.images = []
        
        # Configuration metadata
        self.config_keys = []
        self.config_values = {}

class ArtifactParser:
    """Parses uploaded files and extracts semantic metadata"""
    
    def __init__(self):
        self.supported_extensions = {
            # Programming languages
            '.py': 'python',
            '.js': 'javascript', 
            '.ts': 'typescript',
            '.jsx': 'react',
            '.tsx': 'react-typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            
            # Web technologies
            '.html': 'html',
            '.htm': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.sass': 'sass',
            '.less': 'less',
            
            # Documentation
            '.md': 'markdown',
            '.txt': 'text',
            '.rst': 'restructuredtext',
            '.adoc': 'asciidoc',
            
            # Configuration
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.ini': 'ini',
            '.env': 'environment',
            '.config': 'config',
            
            # Assets
            '.svg': 'svg',
            '.png': 'image',
            '.jpg': 'image',
            '.jpeg': 'image',
            '.gif': 'image',
            '.ico': 'icon'
        }
    
    async def parse_file(self, file_path: str, content: bytes = None) -> FileMetadata:
        """Parse a file and extract all available metadata"""
        try:
            metadata = FileMetadata(file_path)
            
            # Get basic file information
            await self._extract_basic_metadata(metadata)
            
            # Read file content if not provided
            if content is None:
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                except Exception as e:
                    logger.error(f"Failed to read file {file_path}: {e}")
                    return metadata
            
            # Calculate checksum
            metadata.checksum = hashlib.sha256(content).hexdigest()
            
            # Detect encoding and decode content
            text_content = await self._decode_content(content, metadata)
            
            if text_content:
                # Extract text statistics
                await self._extract_text_statistics(metadata, text_content)
                
                # Language-specific parsing
                await self._parse_by_language(metadata, text_content)
            
            logger.info(f"Parsed file: {metadata.file_name} ({metadata.file_size} bytes, {metadata.programming_language})")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to parse file {file_path}: {e}")
            raise Exception(f"File parsing failed: {e}")
    
    async def _extract_basic_metadata(self, metadata: FileMetadata):
        """Extract basic file system metadata"""
        try:
            if metadata.file_path.exists():
                stat = metadata.file_path.stat()
                metadata.file_size = stat.st_size
                metadata.creation_time = datetime.fromtimestamp(stat.st_ctime)
                metadata.modification_time = datetime.fromtimestamp(stat.st_mtime)
            
            # Detect MIME type
            metadata.mime_type, _ = mimetypes.guess_type(str(metadata.file_path))
            if not metadata.mime_type:
                metadata.mime_type = "application/octet-stream"
            
            # Determine programming language
            metadata.programming_language = self.supported_extensions.get(
                metadata.file_extension, 'unknown'
            )
            
        except Exception as e:
            logger.error(f"Failed to extract basic metadata: {e}")
    
    async def _decode_content(self, content: bytes, metadata: FileMetadata) -> Optional[str]:
        """Decode file content to text"""
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    text_content = content.decode(encoding)
                    metadata.encoding = encoding
                    return text_content
                except UnicodeDecodeError:
                    continue
            
            # If all encodings fail, return None (binary file)
            logger.warning(f"Could not decode content for {metadata.file_name}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to decode content: {e}")
            return None
    
    async def _extract_text_statistics(self, metadata: FileMetadata, content: str):
        """Extract basic text statistics"""
        try:
            metadata.character_count = len(content)
            metadata.line_count = content.count('\n') + 1
            metadata.word_count = len(content.split())
            
        except Exception as e:
            logger.error(f"Failed to extract text statistics: {e}")
    
    async def _parse_by_language(self, metadata: FileMetadata, content: str):
        """Parse content based on detected language"""
        try:
            if metadata.programming_language == 'python':
                await self._parse_python(metadata, content)
            elif metadata.programming_language in ['javascript', 'typescript']:
                await self._parse_javascript(metadata, content)
            elif metadata.programming_language == 'markdown':
                await self._parse_markdown(metadata, content)
            elif metadata.programming_language == 'json':
                await self._parse_json(metadata, content)
            elif metadata.programming_language == 'yaml':
                await self._parse_yaml(metadata, content)
            elif metadata.programming_language in ['css', 'scss']:
                await self._parse_css(metadata, content)
            elif metadata.programming_language == 'html':
                await self._parse_html(metadata, content)
            else:
                # Generic text parsing
                await self._parse_generic_code(metadata, content)
                
        except Exception as e:
            logger.error(f"Failed to parse {metadata.programming_language} content: {e}")
    
    async def _parse_python(self, metadata: FileMetadata, content: str):
        """Parse Python source code"""
        try:
            # Parse AST
            tree = ast.parse(content)
            
            # Extract functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        'name': node.name,
                        'line': node.lineno,
                        'args': [arg.arg for arg in node.args.args],
                        'docstring': ast.get_docstring(node)
                    }
                    metadata.functions.append(func_info)
                
                elif isinstance(node, ast.ClassDef):
                    class_info = {
                        'name': node.name,
                        'line': node.lineno,
                        'bases': [base.id if isinstance(base, ast.Name) else str(base) 
                                for base in node.bases],
                        'docstring': ast.get_docstring(node)
                    }
                    metadata.classes.append(class_info)
                
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            metadata.imports.append(alias.name)
                    else:
                        module = node.module or ''
                        for alias in node.names:
                            metadata.imports.append(f"{module}.{alias.name}")
            
            # Extract comments
            metadata.comments = re.findall(r'#\s*(.+)', content)
            
            # Extract dependencies from common patterns
            metadata.dependencies = list(set(metadata.imports))
            
        except SyntaxError as e:
            logger.warning(f"Python syntax error in {metadata.file_name}: {e}")
        except Exception as e:
            logger.error(f"Failed to parse Python code: {e}")
    
    async def _parse_javascript(self, metadata: FileMetadata, content: str):
        """Parse JavaScript/TypeScript source code"""
        try:
            # Extract function declarations
            func_pattern = r'(?:function\s+(\w+)|(\w+)\s*:\s*function|(\w+)\s*=\s*(?:function|\(.*?\)\s*=>))'
            functions = re.findall(func_pattern, content)
            metadata.functions = [{'name': f[0] or f[1] or f[2]} for f in functions if any(f)]
            
            # Extract class declarations
            class_pattern = r'class\s+(\w+)(?:\s+extends\s+(\w+))?'
            classes = re.findall(class_pattern, content)
            metadata.classes = [{'name': c[0], 'extends': c[1]} for c in classes]
            
            # Extract imports/requires
            import_patterns = [
                r'import\s+.*?\s+from\s+[\'"](.+?)[\'"]',
                r'require\([\'"](.+?)[\'"]\)',
                r'import\s+[\'"](.+?)[\'"]'
            ]
            
            for pattern in import_patterns:
                imports = re.findall(pattern, content)
                metadata.imports.extend(imports)
            
            # Extract comments
            metadata.comments = re.findall(r'//\s*(.+)', content)
            metadata.comments.extend(re.findall(r'/\*\s*(.+?)\s*\*/', content, re.DOTALL))
            
            metadata.dependencies = list(set(metadata.imports))
            
        except Exception as e:
            logger.error(f"Failed to parse JavaScript code: {e}")
    
    async def _parse_markdown(self, metadata: FileMetadata, content: str):
        """Parse Markdown documentation"""
        try:
            # Extract headings
            headings = re.findall(r'^(#{1,6})\s+(.+)', content, re.MULTILINE)
            metadata.headings = [{'level': len(h[0]), 'text': h[1]} for h in headings]
            
            # Extract links
            links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
            metadata.links = [{'text': l[0], 'url': l[1]} for l in links]
            
            # Extract images
            images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content)
            metadata.images = [{'alt': i[0], 'src': i[1]} for i in images]
            
        except Exception as e:
            logger.error(f"Failed to parse Markdown: {e}")
    
    async def _parse_json(self, metadata: FileMetadata, content: str):
        """Parse JSON configuration files"""
        try:
            data = json.loads(content)
            metadata.config_values = data
            metadata.config_keys = list(self._flatten_json_keys(data))
            
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in {metadata.file_name}: {e}")
        except Exception as e:
            logger.error(f"Failed to parse JSON: {e}")
    
    async def _parse_yaml(self, metadata: FileMetadata, content: str):
        """Parse YAML configuration files"""
        try:
            data = yaml.safe_load(content)
            if isinstance(data, dict):
                metadata.config_values = data
                metadata.config_keys = list(self._flatten_json_keys(data))
            
        except yaml.YAMLError as e:
            logger.warning(f"Invalid YAML in {metadata.file_name}: {e}")
        except Exception as e:
            logger.error(f"Failed to parse YAML: {e}")
    
    async def _parse_css(self, metadata: FileMetadata, content: str):
        """Parse CSS/SCSS stylesheets"""
        try:
            # Extract CSS rules
            selectors = re.findall(r'([^{]+)\s*{', content)
            metadata.config_keys = [s.strip() for s in selectors]
            
            # Extract comments
            metadata.comments = re.findall(r'/\*\s*(.+?)\s*\*/', content, re.DOTALL)
            
        except Exception as e:
            logger.error(f"Failed to parse CSS: {e}")
    
    async def _parse_html(self, metadata: FileMetadata, content: str):
        """Parse HTML files"""
        try:
            # Extract images
            images = re.findall(r'<img[^>]+src=[\'"]([^"\']+)[\'"][^>]*>', content)
            metadata.images = [{'src': img} for img in images]
            
            # Extract links
            links = re.findall(r'<a[^>]+href=[\'"]([^"\']+)[\'"][^>]*>([^<]*)</a>', content)
            metadata.links = [{'url': l[0], 'text': l[1]} for l in links]
            
        except Exception as e:
            logger.error(f"Failed to parse HTML: {e}")
    
    async def _parse_generic_code(self, metadata: FileMetadata, content: str):
        """Generic parsing for unknown file types"""
        try:
            # Extract simple patterns that might indicate structure
            lines = content.split('\n')
            
            # Look for function-like patterns
            func_patterns = [
                r'def\s+(\w+)',  # Python-style
                r'function\s+(\w+)',  # JS-style
                r'(\w+)\s*\([^)]*\)\s*{',  # C-style
            ]
            
            for pattern in func_patterns:
                functions = re.findall(pattern, content)
                metadata.functions.extend([{'name': f} for f in functions])
            
            # Extract comment-like patterns
            comment_patterns = [
                r'//\s*(.+)',  # C-style
                r'#\s*(.+)',   # Python-style
                r'/\*\s*(.+?)\s*\*/',  # Block comments
            ]
            
            for pattern in comment_patterns:
                comments = re.findall(pattern, content, re.DOTALL)
                metadata.comments.extend(comments)
            
        except Exception as e:
            logger.error(f"Failed to parse generic code: {e}")
    
    def _flatten_json_keys(self, data: Dict, prefix: str = '') -> List[str]:
        """Flatten nested JSON keys"""
        keys = []
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            keys.append(full_key)
            
            if isinstance(value, dict):
                keys.extend(self._flatten_json_keys(value, full_key))
        
        return keys
    
    def get_suggested_wdo_classes(self, metadata: FileMetadata) -> List[str]:
        """Suggest appropriate WDO classes for the parsed file"""
        suggestions = []
        
        # Map file types to WDO classes
        language_mapping = {
            'python': 'PythonSourceCodeFile',
            'javascript': 'JavaScriptSourceCodeFile', 
            'typescript': 'TypeScriptSourceCodeFile',
            'react': 'ReactSourceCodeFile',
            'java': 'JavaSourceCodeFile',
            'cpp': 'CppSourceCodeFile',
            'c': 'CSourceCodeFile',
            'css': 'CSSFile',
            'scss': 'SCSSFile', 
            'html': 'HTMLFile',
            'markdown': 'DocumentationFile',
            'json': 'ConfigurationFile',
            'yaml': 'ConfigurationFile',
            'image': 'AssetFile'
        }
        
        # Primary class based on language
        if metadata.programming_language in language_mapping:
            suggestions.append(language_mapping[metadata.programming_language])
        
        # Always include generic classes
        suggestions.extend([
            'DigitalInformationCarrier',
            'InformationContentEntity'
        ])
        
        # Add specific classes based on content analysis
        if metadata.functions:
            suggestions.append('FunctionDefinitionContent')
        
        if metadata.classes:
            suggestions.append('ClassDefinitionContent')
        
        if metadata.config_keys:
            suggestions.append('ConfigurationContent')
        
        return list(set(suggestions)) 