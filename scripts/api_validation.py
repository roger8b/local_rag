#!/usr/bin/env python3
"""
API Validation Script - Local RAG System
Simula chamadas reais para validar todas as funcionalidades do sistema
"""

import json
import time
import requests
from datetime import datetime


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'


class APIValidator:
    """Validates Local RAG System APIs through real HTTP calls"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.results = []
        self.test_data = {}
        
    def log(self, message: str, level: str = "INFO"):
        """Log colored messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = {
            "INFO": Colors.BLUE,
            "SUCCESS": Colors.GREEN,
            "WARNING": Colors.YELLOW,
            "ERROR": Colors.RED,
            "HEADER": Colors.PURPLE + Colors.BOLD
        }.get(level, Colors.WHITE)
        
        print(f"{color}[{timestamp}] {level}: {message}{Colors.END}")
        
    def record_result(self, test_name: str, success: bool, details: str, response_time: float = 0):
        """Record test result"""
        self.results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response_time": response_time,
            "timestamp": datetime.now().isoformat()
        })
        
        status = "✅ PASS" if success else "❌ FAIL"
        self.log(f"{status} {test_name} ({response_time:.2f}s): {details}", 
                "SUCCESS" if success else "ERROR")
    
    def test_health_endpoints(self) -> bool:
        """Test basic health and info endpoints"""
        self.log("Testing Health Endpoints", "HEADER")
        
        # Test root endpoint
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.record_result("Root Endpoint", True, 
                                 f"Status: {data.get('status', 'unknown')}", response_time)
            else:
                self.record_result("Root Endpoint", False, 
                                 f"Status code: {response.status_code}", response_time)
        except Exception as e:
            self.record_result("Root Endpoint", False, f"Exception: {str(e)}")
            
        # Test health endpoint
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/api/v1/health")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                self.record_result("Health Endpoint", True, "System is healthy", response_time)
                return True
            else:
                self.record_result("Health Endpoint", False, 
                                 f"Status code: {response.status_code}", response_time)
                return False
        except Exception as e:
            self.record_result("Health Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_models_endpoint(self) -> bool:
        """Test models listing endpoint"""
        self.log("Testing Models Endpoints", "HEADER")
        
        providers = ["ollama", "openai", "gemini"]
        success_count = 0
        
        for provider in providers:
            try:
                start_time = time.time()
                response = self.session.get(f"{self.base_url}/api/v1/models/{provider}")
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    models_count = len(data.get('models', []))
                    self.record_result(f"Models - {provider}", True, 
                                     f"Found {models_count} models", response_time)
                    success_count += 1
                else:
                    self.record_result(f"Models - {provider}", False, 
                                     f"Status: {response.status_code}", response_time)
            except Exception as e:
                self.record_result(f"Models - {provider}", False, f"Exception: {str(e)}")
        
        return success_count > 0
    
    def test_schema_upload_api(self) -> bool:
        """Test schema upload functionality (História 7)"""
        self.log("Testing Schema Upload API (História 7)", "HEADER")
        
        # Create test files
        test_files = {
            "test_document.txt": "This is a test document for schema inference.\n\nIt contains multiple lines and some sample content about companies, people, and technologies.\n\nJohn Smith works at TechCorp developing React applications.",
            "test_document.pdf": b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 44 >>\nstream\nBT\n/F1 12 Tf\n100 100 Td\n(Sample PDF content) Tj\nET\nendstream\nendobj\ntrailer\n<< /Size 5 /Root 1 0 R >>\n"
        }
        
        uploaded_keys = []
        
        for filename, content in test_files.items():
            try:
                start_time = time.time()
                
                # Prepare file for upload
                if filename.endswith('.txt'):
                    files = {'file': (filename, content, 'text/plain')}
                else:
                    files = {'file': (filename, content, 'application/pdf')}
                
                response = self.session.post(f"{self.base_url}/api/v1/schema/upload", files=files)
                response_time = time.time() - start_time
                
                if response.status_code == 201:
                    data = response.json()
                    key = data.get('key')
                    file_size = data.get('file_size_bytes', 0)
                    text_stats = data.get('text_stats', {})
                    processing_time = data.get('processing_time_ms', 0)
                    
                    uploaded_keys.append(key)
                    self.test_data[f'upload_key_{filename}'] = key
                    
                    details = f"Key: {key[:8]}..., Size: {file_size}B, Chars: {text_stats.get('total_chars', 0)}, Processing: {processing_time:.1f}ms"
                    self.record_result(f"Upload - {filename}", True, details, response_time)
                else:
                    self.record_result(f"Upload - {filename}", False, 
                                     f"Status: {response.status_code}", response_time)
            except Exception as e:
                self.record_result(f"Upload - {filename}", False, f"Exception: {str(e)}")
        
        # Test list documents
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/api/v1/schema/documents")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                doc_count = data.get('total_documents', 0)
                memory_usage = data.get('memory_usage_mb', 0)
                details = f"Documents: {doc_count}, Memory: {memory_usage:.1f}MB"
                self.record_result("List Documents", True, details, response_time)
            else:
                self.record_result("List Documents", False, 
                                 f"Status: {response.status_code}", response_time)
        except Exception as e:
            self.record_result("List Documents", False, f"Exception: {str(e)}")
        
        return len(uploaded_keys) > 0
    
    def test_schema_inference_api(self) -> bool:
        """Test schema inference functionality (Histórias 6 & 8)"""
        self.log("Testing Schema Inference API (Histórias 6 & 8)", "HEADER")
        
        success_count = 0
        
        # Test 1: Direct text inference
        try:
            start_time = time.time()
            payload = {
                "text": "Maria Silva is a software engineer at DataTech Inc. She specializes in Python development and works with PostgreSQL databases. DataTech Inc. provides analytics solutions for retail companies.",
                "max_sample_length": 200
            }
            
            response = self.session.post(f"{self.base_url}/api/v1/schema/infer", json=payload)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                node_labels = data.get('node_labels', [])
                relationship_types = data.get('relationship_types', [])
                source = data.get('source', 'unknown')
                model_used = data.get('model_used', 'unknown')
                
                details = f"Nodes: {len(node_labels)}, Relations: {len(relationship_types)}, Source: {source}, Model: {model_used}"
                self.record_result("Schema Inference - Direct Text", True, details, response_time)
                success_count += 1
            else:
                self.record_result("Schema Inference - Direct Text", False, 
                                 f"Status: {response.status_code}", response_time)
        except Exception as e:
            self.record_result("Schema Inference - Direct Text", False, f"Exception: {str(e)}")
        
        # Test 2: Document key inference with percentage (História 8)
        if 'upload_key_test_document.txt' in self.test_data:
            try:
                start_time = time.time()
                payload = {
                    "document_key": self.test_data['upload_key_test_document.txt'],
                    "sample_percentage": 75,
                    "llm_provider": "ollama"
                }
                
                response = self.session.post(f"{self.base_url}/api/v1/schema/infer", json=payload)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    node_labels = data.get('node_labels', [])
                    relationship_types = data.get('relationship_types', [])
                    document_info = data.get('document_info', {})
                    
                    details = f"Nodes: {len(node_labels)}, Relations: {len(relationship_types)}, Sample: {document_info.get('sample_percentage', 0)}%"
                    self.record_result("Schema Inference - Document Key + Percentage", True, details, response_time)
                    success_count += 1
                else:
                    self.record_result("Schema Inference - Document Key + Percentage", False, 
                                     f"Status: {response.status_code}", response_time)
            except Exception as e:
                self.record_result("Schema Inference - Document Key + Percentage", False, f"Exception: {str(e)}")
        
        # Test 3: Provider selection (História 8)
        try:
            start_time = time.time()
            payload = {
                "text": "OpenAI is a research company. Sam Altman is the CEO. They developed ChatGPT using transformer architecture.",
                "sample_percentage": 100,
                "llm_provider": "openai",
                "llm_model": "gpt-4o-mini"
            }
            
            response = self.session.post(f"{self.base_url}/api/v1/schema/infer", json=payload)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                model_used = data.get('model_used', 'unknown')
                processing_time = data.get('processing_time_ms', 0)
                
                details = f"Model: {model_used}, Processing: {processing_time:.1f}ms"
                self.record_result("Schema Inference - Provider Selection", True, details, response_time)
                success_count += 1
            else:
                self.record_result("Schema Inference - Provider Selection", False, 
                                 f"Status: {response.status_code}", response_time)
        except Exception as e:
            self.record_result("Schema Inference - Provider Selection", False, f"Exception: {str(e)}")
        
        return success_count > 0
    
    def test_document_ingestion_api(self) -> bool:
        """Test document ingestion functionality"""
        self.log("Testing Document Ingestion API", "HEADER")
        
        try:
            start_time = time.time()
            
            # Create a test document
            test_content = """
            Local RAG System Documentation
            
            This is a comprehensive guide to understanding and using the Local RAG (Retrieval-Augmented Generation) system.
            
            Architecture Overview:
            The system consists of several key components:
            1. Vector Retriever - handles document similarity search
            2. Response Generator - generates answers using LLM providers
            3. Document Cache - manages temporary document storage
            4. Schema Inference - analyzes document structure for graph modeling
            
            Supported Providers:
            - Ollama: Local LLM provider
            - OpenAI: GPT models 
            - Gemini: Google's language models
            """
            
            files = {'file': ('rag_documentation.txt', test_content, 'text/plain')}
            
            response = self.session.post(f"{self.base_url}/api/v1/ingest", files=files)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                filename = data.get('filename', 'unknown')
                chunks_created = data.get('chunks_created', 0)
                document_id = data.get('document_id', 'unknown')
                
                self.test_data['ingested_doc_id'] = document_id
                
                details = f"Status: {status}, Filename: {filename}, Chunks: {chunks_created}, ID: {document_id[:8]}..."
                self.record_result("Document Ingestion", True, details, response_time)
                return True
            else:
                self.record_result("Document Ingestion", False, 
                                 f"Status: {response.status_code}", response_time)
                return False
        except Exception as e:
            self.record_result("Document Ingestion", False, f"Exception: {str(e)}")
            return False
    
    def test_query_api(self) -> bool:
        """Test query functionality"""
        self.log("Testing Query API", "HEADER")
        
        queries = [
            "What is the Local RAG system?",
            "What providers are supported?",
            "How does the vector retriever work?",
            "What components make up the architecture?"
        ]
        
        success_count = 0
        
        for i, question in enumerate(queries, 1):
            try:
                start_time = time.time()
                payload = {
                    "question": question,
                    "provider": "ollama"
                }
                
                response = self.session.post(f"{self.base_url}/api/v1/query", json=payload)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get('answer', '')
                    sources_count = len(data.get('sources', []))
                    provider_used = data.get('provider_used', 'unknown')
                    
                    details = f"Answer length: {len(answer)} chars, Sources: {sources_count}, Provider: {provider_used}"
                    self.record_result(f"Query {i}", True, details, response_time)
                    success_count += 1
                else:
                    self.record_result(f"Query {i}", False, 
                                     f"Status: {response.status_code}", response_time)
            except Exception as e:
                self.record_result(f"Query {i}", False, f"Exception: {str(e)}")
        
        return success_count > 0
    
    def test_documents_management(self) -> bool:
        """Test document management endpoints"""
        self.log("Testing Document Management", "HEADER")
        
        success_count = 0
        
        # Test list documents
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/api/v1/documents")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                documents = data.get('documents', [])
                
                details = f"Found {len(documents)} documents"
                self.record_result("List Documents", True, details, response_time)
                success_count += 1
                
                # Test document chunks if we have documents
                if documents:
                    doc_id = documents[0].get('id')
                    if doc_id:
                        try:
                            start_time = time.time()
                            response = self.session.get(f"{self.base_url}/api/v1/documents/{doc_id}/chunks")
                            response_time = time.time() - start_time
                            
                            if response.status_code == 200:
                                chunks_data = response.json()
                                chunks_count = len(chunks_data.get('chunks', []))
                                
                                details = f"Document {doc_id[:8]}... has {chunks_count} chunks"
                                self.record_result("Document Chunks", True, details, response_time)
                                success_count += 1
                            else:
                                self.record_result("Document Chunks", False, 
                                                 f"Status: {response.status_code}", response_time)
                        except Exception as e:
                            self.record_result("Document Chunks", False, f"Exception: {str(e)}")
            else:
                self.record_result("List Documents", False, 
                                 f"Status: {response.status_code}", response_time)
        except Exception as e:
            self.record_result("List Documents", False, f"Exception: {str(e)}")
        
        return success_count > 0
    
    def test_admin_endpoints(self) -> bool:
        """Test database admin endpoints"""
        self.log("Testing Admin Endpoints", "HEADER")
        
        success_count = 0
        
        # Test DB status
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/api/v1/db/status")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                neo4j_connected = data.get('neo4j_connected', False)
                chunks = data.get('chunks', 0)
                
                details = f"Neo4j: {neo4j_connected}, Chunks: {chunks}"
                self.record_result("DB Status", True, details, response_time)
                success_count += 1
            else:
                self.record_result("DB Status", False, 
                                 f"Status: {response.status_code}", response_time)
        except Exception as e:
            self.record_result("DB Status", False, f"Exception: {str(e)}")
        
        return success_count > 0
    
    def cleanup_test_data(self):
        """Clean up test data created during validation"""
        self.log("Cleaning up test data", "HEADER")
        
        # Remove uploaded documents from schema cache
        for key_name, key_value in self.test_data.items():
            if key_name.startswith('upload_key_') and key_value:
                try:
                    start_time = time.time()
                    response = self.session.delete(f"{self.base_url}/api/v1/schema/documents/{key_value}")
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        self.record_result(f"Cleanup - {key_name}", True, 
                                         f"Removed document {key_value[:8]}...", response_time)
                    else:
                        self.record_result(f"Cleanup - {key_name}", False, 
                                         f"Status: {response.status_code}", response_time)
                except Exception as e:
                    self.record_result(f"Cleanup - {key_name}", False, f"Exception: {str(e)}")
    
    def generate_report(self) -> dict:
        """Generate comprehensive validation report"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        avg_response_time = sum(r['response_time'] for r in self.results if r['response_time'] > 0) / max(1, len([r for r in self.results if r['response_time'] > 0]))
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": round(success_rate, 2),
                "average_response_time": round(avg_response_time, 3),
                "validation_time": datetime.now().isoformat()
            },
            "results": self.results,
            "recommendations": []
        }
        
        # Add recommendations based on results
        if failed_tests > 0:
            report["recommendations"].append("Review failed tests and check system configuration")
        
        if avg_response_time > 2.0:
            report["recommendations"].append("Consider optimizing API response times")
        
        if success_rate < 90:
            report["recommendations"].append("System requires attention - multiple test failures detected")
        elif success_rate == 100:
            report["recommendations"].append("System is fully operational and ready for production")
        
        return report
    
    def run_validation(self, include_cleanup: bool = True) -> dict:
        """Run complete API validation suite"""
        self.log("Starting Local RAG System API Validation", "HEADER")
        self.log(f"Target URL: {self.base_url}", "INFO")
        
        validation_start = time.time()
        
        # Run all validation tests
        test_functions = [
            self.test_health_endpoints,
            self.test_models_endpoint,
            self.test_schema_upload_api,
            self.test_schema_inference_api,
            self.test_document_ingestion_api,
            self.test_query_api,
            self.test_documents_management,
            self.test_admin_endpoints
        ]
        
        for test_func in test_functions:
            try:
                test_func()
            except Exception as e:
                self.log(f"Test function {test_func.__name__} failed: {str(e)}", "ERROR")
        
        # Cleanup if requested
        if include_cleanup:
            self.cleanup_test_data()
        
        validation_time = time.time() - validation_start
        self.log(f"Validation completed in {validation_time:.2f} seconds", "INFO")
        
        # Generate and return report
        report = self.generate_report()
        
        # Print summary
        self.log("=== VALIDATION SUMMARY ===", "HEADER")
        self.log(f"Total Tests: {report['summary']['total_tests']}", "INFO")
        self.log(f"Passed: {report['summary']['passed']}", "SUCCESS")
        if report['summary']['failed'] > 0:
            self.log(f"Failed: {report['summary']['failed']}", "ERROR")
        self.log(f"Success Rate: {report['summary']['success_rate']}%", 
                "SUCCESS" if report['summary']['success_rate'] >= 90 else "WARNING")
        self.log(f"Average Response Time: {report['summary']['average_response_time']}s", "INFO")
        
        return report


def main():
    """Main validation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Local RAG System API Validator")
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="Base URL of the API server (default: http://localhost:8000)")
    parser.add_argument("--no-cleanup", action="store_true", 
                       help="Skip cleanup of test data")
    parser.add_argument("--output", "-o", help="Save report to JSON file")
    parser.add_argument("--quiet", "-q", action="store_true", 
                       help="Reduce output verbosity")
    
    args = parser.parse_args()
    
    # Create validator
    validator = APIValidator(base_url=args.url)
    
    try:
        # Run validation
        report = validator.run_validation(include_cleanup=not args.no_cleanup)
        
        # Save report if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            validator.log(f"Report saved to {args.output}", "SUCCESS")
        
        # Exit with appropriate code
        success_rate = report['summary']['success_rate']
        exit_code = 0 if success_rate >= 90 else 1
        
        if not args.quiet:
            if exit_code == 0:
                validator.log("✅ API Validation PASSED", "SUCCESS")
            else:
                validator.log("❌ API Validation FAILED", "ERROR")
        
        return exit_code
        
    except KeyboardInterrupt:
        validator.log("Validation interrupted by user", "WARNING")
        return 2
    except Exception as e:
        validator.log(f"Validation failed with exception: {str(e)}", "ERROR")
        return 3


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)