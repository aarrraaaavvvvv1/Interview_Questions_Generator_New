import os
from typing import List, Dict, Optional
import json

class RAGHandler:
    """
    RAG Handler using ChromaDB for long-term knowledge persistence
    This implementation allows the knowledge base to grow and stay current over time
    """
    
    def __init__(self):
        """Initialize RAG handler with ChromaDB backend"""
        try:
            import chromadb
            self.chroma_client = chromadb.Client()
            self.collection = self.chroma_client.get_or_create_collection(name="interview_knowledge_base")
            self.initialized = True
        except ImportError:
            print("ChromaDB not installed. Using fallback knowledge base.")
            self.initialized = False
            self.knowledge_base = self._initialize_fallback_kb()
    
    def _initialize_fallback_kb(self) -> Dict:
        """Fallback knowledge base for when ChromaDB is not available"""
        return {
            "python": {
                "fundamentals": "Python is a high-level, interpreted programming language known for readability. Key concepts: variables, data types, functions, classes, modules",
                "data_structures": "Core Python data structures: lists (ordered, mutable), tuples (ordered, immutable), dictionaries (key-value pairs), sets (unique items)",
                "best_practices": "Follow PEP 8 style guide, use virtual environments (venv), write docstrings, implement error handling with try-except blocks"
            },
            "data_science": {
                "numpy": "NumPy provides ndarray for numerical computing, efficient operations on arrays, linear algebra, random number generation",
                "pandas": "Pandas provides DataFrame and Series for data manipulation, cleaning, analysis, grouping, merging operations",
                "machine_learning": "ML process: data collection, preprocessing, feature engineering, model training, evaluation, hyperparameter tuning"
            },
            "web_development": {
                "django": "Django MVC framework for building robust web applications with ORM, admin panel, authentication, URL routing",
                "fastapi": "FastAPI modern Python web framework for building APIs with automatic documentation, async support, type hints",
                "rest_api": "REST principles: stateless, use HTTP methods (GET, POST, PUT, DELETE), resource-oriented design, status codes"
            },
            "javascript": {
                "fundamentals": "JS is a dynamic language: variables (var, let, const), functions, objects, arrays, events, DOM manipulation",
                "async": "Asynchronous patterns: callbacks, promises, async/await for handling operations that take time",
                "frameworks": "Popular frameworks: React (component-based), Vue (progressive), Angular (full-featured), Next.js (React meta-framework)"
            },
            "system_design": {
                "scalability": "Design principles: horizontal scaling (add more servers), caching, database optimization, load balancing",
                "databases": "SQL (ACID properties) vs NoSQL (flexibility), indexing, normalization, sharding strategies",
                "architecture": "MVC, microservices, serverless, event-driven architectures, design patterns"
            }
        }
    
    def retrieve_context(self, topic: str, subtopics: List[str]) -> str:
        """Retrieve relevant context from knowledge base"""
        try:
            if self.initialized:
                return self._retrieve_from_chroma(topic, subtopics)
            else:
                return self._retrieve_from_fallback(topic, subtopics)
        except Exception as e:
            print(f"RAG retrieval error: {str(e)}")
            return ""
    
    def _retrieve_from_chroma(self, topic: str, subtopics: List[str]) -> str:
        """Retrieve from ChromaDB collection"""
        try:
            import chromadb
            
            query_text = f"{topic} {' '.join(subtopics)}"
            
            results = self.collection.query(
                query_texts=[query_text],
                n_results=5
            )
            
            if results and results['documents']:
                context_parts = results['documents'][0]
                return " ".join(context_parts[:3])
            
            return ""
        except Exception as e:
            print(f"ChromaDB query error: {str(e)}")
            return ""
    
    def _retrieve_from_fallback(self, topic: str, subtopics: List[str]) -> str:
        """Retrieve from fallback knowledge base"""
        try:
            context_parts = []
            topic_lower = topic.lower()
            
            for key, content in self.knowledge_base.items():
                if key in topic_lower or topic_lower in key:
                    for subtopic in subtopics:
                        subtopic_lower = subtopic.lower()
                        if subtopic_lower in content:
                            context_parts.append(content[subtopic_lower])
            
            if not context_parts:
                context_parts.append(f"Information about {topic}")
            
            return " ".join(context_parts[:3])
        except:
            return ""
    
    def add_documents(self, documents: List[Dict]) -> bool:
        """Add documents to ChromaDB for long-term knowledge growth"""
        if not self.initialized:
            return False
        
        try:
            import chromadb
            
            for doc in documents:
                self.collection.add(
                    ids=[doc.get('id', '')],
                    documents=[doc.get('content', '')],
                    metadatas=[doc.get('metadata', {})]
                )
            
            return True
        except Exception as e:
            print(f"Error adding documents to ChromaDB: {str(e)}")
            return False
    
    def update_knowledge_base(self, new_documents: List[Dict]) -> bool:
        """Update knowledge base with new documents"""
        return self.add_documents(new_documents)
