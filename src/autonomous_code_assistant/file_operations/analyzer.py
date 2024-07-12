"""Intelligent code analyzer for language detection and dependency analysis."""

import re
from pathlib import Path
from typing import Any

from ..exceptions import FileOperationError


class CodeAnalyzer:
    """Intelligent code analyzer for understanding code structure and dependencies."""
    
    # Language detection patterns
    LANGUAGE_PATTERNS = {
        'python': {
            'extensions': ['.py', '.pyx', '.pyi'],
            'patterns': [
                r'^\s*import\s+\w+',
                r'^\s*from\s+\w+\s+import',
                r'^\s*def\s+\w+\s*\(',
                r'^\s*class\s+\w+\s*[\(:]',
                r'^\s*if\s+__name__\s*==\s*["\']__main__["\']',
            ],
            'keywords': ['def', 'class', 'import', 'from', 'if', 'elif', 'else', 'for', 'while', 'try', 'except']
        },
        'javascript': {
            'extensions': ['.js', '.mjs'],
            'patterns': [
                r'^\s*function\s+\w+\s*\(',
                r'^\s*const\s+\w+\s*=',
                r'^\s*let\s+\w+\s*=',
                r'^\s*var\s+\w+\s*=',
                r'^\s*import\s+.*\s+from\s+["\']',
                r'^\s*export\s+',
            ],
            'keywords': ['function', 'const', 'let', 'var', 'import', 'export', 'if', 'else', 'for', 'while']
        },
        'typescript': {
            'extensions': ['.ts', '.tsx'],
            'patterns': [
                r'^\s*interface\s+\w+\s*{',
                r'^\s*type\s+\w+\s*=',
                r'^\s*enum\s+\w+\s*{',
                r':\s*\w+\s*[=;]',
                r'^\s*import\s+.*\s+from\s+["\']',
            ],
            'keywords': ['interface', 'type', 'enum', 'function', 'const', 'let', 'import', 'export']
        },
        'java': {
            'extensions': ['.java'],
            'patterns': [
                r'^\s*public\s+class\s+\w+',
                r'^\s*private\s+\w+\s+\w+',
                r'^\s*public\s+static\s+void\s+main',
                r'^\s*package\s+\w+',
                r'^\s*import\s+\w+',
            ],
            'keywords': ['public', 'private', 'protected', 'class', 'interface', 'package', 'import']
        },
        'go': {
            'extensions': ['.go'],
            'patterns': [
                r'^\s*package\s+\w+',
                r'^\s*import\s+["\(]',
                r'^\s*func\s+\w+\s*\(',
                r'^\s*type\s+\w+\s+struct',
                r'^\s*var\s+\w+\s+\w+',
            ],
            'keywords': ['package', 'import', 'func', 'type', 'struct', 'var', 'const']
        },
        'rust': {
            'extensions': ['.rs'],
            'patterns': [
                r'^\s*fn\s+\w+\s*\(',
                r'^\s*struct\s+\w+\s*{',
                r'^\s*impl\s+\w+\s*{',
                r'^\s*use\s+\w+',
                r'^\s*mod\s+\w+',
            ],
            'keywords': ['fn', 'struct', 'impl', 'use', 'mod', 'let', 'mut']
        },
    }
    
    # Common dependency patterns
    DEPENDENCY_PATTERNS = {
        'python': [
            r'^\s*import\s+(\w+(?:\.\w+)*)',
            r'^\s*from\s+(\w+(?:\.\w+)*)\s+import',
        ],
        'javascript': [
            r'^\s*import\s+.*\s+from\s+["\']([^"\']+)["\']',
            r'^\s*const\s+.*\s*=\s*require\s*\(\s*["\']([^"\']+)["\']\s*\)',
        ],
        'typescript': [
            r'^\s*import\s+.*\s+from\s+["\']([^"\']+)["\']',
        ],
        'java': [
            r'^\s*import\s+([\w\.]+)',
        ],
        'go': [
            r'^\s*import\s+["\']([^"\']+)["\']',
            r'^\s*import\s+\w+\s+["\']([^"\']+)["\']',
        ],
        'rust': [
            r'^\s*use\s+([\w:]+)',
        ],
    }
    
    def detect_language(self, filepath: str | Path, content: str | None = None) -> str | None:
        """
        Detect the programming language of a file.
        
        Args:
            filepath: Path to the file
            content: Optional file content (will be read if not provided)
            
        Returns:
            Detected language name or None if not detected
            
        Raises:
            FileOperationError: If file cannot be analyzed
        """
        filepath = Path(filepath)
        
        # First try extension-based detection
        extension = filepath.suffix.lower()
        for lang, config in self.LANGUAGE_PATTERNS.items():
            if extension in config['extensions']:
                return lang
        
        # If no content provided, try to read it
        if content is None:
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(8192)  # Read first 8KB for analysis
            except Exception as e:
                raise FileOperationError(
                    f"Failed to read file for language detection: {str(e)}",
                    filepath=str(filepath),
                    operation="language_detection",
                    original_error=e
                )
        
        # Pattern-based detection
        language_scores = {}
        for lang, config in self.LANGUAGE_PATTERNS.items():
            score = 0
            
            # Check patterns
            for pattern in config['patterns']:
                matches = len(re.findall(pattern, content, re.MULTILINE))
                score += matches * 2
            
            # Check keywords (less weight)
            for keyword in config['keywords']:
                # Look for keywords as whole words
                matches = len(re.findall(rf'\b{re.escape(keyword)}\b', content))
                score += matches
            
            if score > 0:
                language_scores[lang] = score
        
        # Return the language with the highest score
        if language_scores:
            return max(language_scores, key=language_scores.get)
        
        return None
    
    def extract_dependencies(self, filepath: str | Path, content: str | None = None) -> list[str]:
        """
        Extract dependencies from a code file.
        
        Args:
            filepath: Path to the file
            content: Optional file content (will be read if not provided)
            
        Returns:
            List of dependency names
            
        Raises:
            FileOperationError: If file cannot be analyzed
        """
        language = self.detect_language(filepath, content)
        if not language:
            return []
        
        if content is None:
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception as e:
                raise FileOperationError(
                    f"Failed to read file for dependency extraction: {str(e)}",
                    filepath=str(filepath),
                    operation="dependency_extraction",
                    original_error=e
                )
        
        dependencies = set()
        patterns = self.DEPENDENCY_PATTERNS.get(language, [])
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for match in matches:
                # Clean up the dependency name
                dependency = match.strip()
                if dependency and not dependency.startswith('.'):  # Skip relative imports
                    dependencies.add(dependency)
        
        return sorted(list(dependencies))
    
    def analyze_file_structure(self, filepath: str | Path, content: str | None = None) -> dict[str, Any]:
        """
        Analyze the structure of a code file.
        
        Args:
            filepath: Path to the file
            content: Optional file content (will be read if not provided)
            
        Returns:
            Dictionary with structural analysis
            
        Raises:
            FileOperationError: If file cannot be analyzed
        """
        filepath = Path(filepath)
        
        if content is None:
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception as e:
                raise FileOperationError(
                    f"Failed to read file for structure analysis: {str(e)}",
                    filepath=str(filepath),
                    operation="structure_analysis",
                    original_error=e
                )
        
        lines = content.splitlines()
        
        analysis = {
            'filepath': str(filepath),
            'language': self.detect_language(filepath, content),
            'dependencies': self.extract_dependencies(filepath, content),
            'line_count': len(lines),
            'char_count': len(content),
            'blank_lines': sum(1 for line in lines if not line.strip()),
            'comment_lines': self._count_comment_lines(lines, self.detect_language(filepath, content)),
        }
        
        # Language-specific analysis
        language = analysis['language']
        if language == 'python':
            analysis.update(self._analyze_python_structure(content))
        elif language in ['javascript', 'typescript']:
            analysis.update(self._analyze_js_structure(content))
        
        return analysis
    
    def _count_comment_lines(self, lines: list[str], language: str | None) -> int:
        """Count comment lines based on language."""
        if not language:
            return 0
        
        comment_count = 0
        comment_prefixes = {
            'python': ['#'],
            'javascript': ['//', '/*', '*'],
            'typescript': ['//', '/*', '*'],
            'java': ['//', '/*', '*'],
            'go': ['//', '/*', '*'],
            'rust': ['//', '/*', '*'],
        }
        
        prefixes = comment_prefixes.get(language, [])
        for line in lines:
            stripped = line.strip()
            if stripped and any(stripped.startswith(prefix) for prefix in prefixes):
                comment_count += 1
        
        return comment_count
    
    def _analyze_python_structure(self, content: str) -> dict[str, Any]:
        """Analyze Python-specific structure."""
        functions = len(re.findall(r'^\s*def\s+\w+\s*\(', content, re.MULTILINE))
        classes = len(re.findall(r'^\s*class\s+\w+\s*[\(:]', content, re.MULTILINE))
        
        return {
            'functions': functions,
            'classes': classes,
        }
    
    def _analyze_js_structure(self, content: str) -> dict[str, Any]:
        """Analyze JavaScript/TypeScript-specific structure."""
        functions = len(re.findall(r'^\s*function\s+\w+\s*\(', content, re.MULTILINE))
        arrow_functions = len(re.findall(r'\w+\s*=\s*\([^)]*\)\s*=>', content))
        classes = len(re.findall(r'^\s*class\s+\w+', content, re.MULTILINE))
        
        return {
            'functions': functions,
            'arrow_functions': arrow_functions,
            'classes': classes,
        }
