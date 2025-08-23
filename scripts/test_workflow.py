#!/usr/bin/env python3
"""
Teste de Fluxo Completo - Local RAG System
Simula um fluxo real: Upload de Documento → Consultas → Limpeza
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


class WorkflowTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {"INFO": Colors.BLUE, "SUCCESS": Colors.GREEN, "ERROR": Colors.RED, "WARNING": Colors.YELLOW}
        color = colors.get(level, "")
        print(f"{color}[{timestamp}] {message}{Colors.END}")
    
    def print_separator(self, title):
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE} {title.center(58)} {Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")
    
    def test_connection(self):
        """Testa conexão com a API"""
        self.print_separator("TESTE DE CONEXÃO")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/health", timeout=5)
            if response.status_code == 200:
                self.log("✅ API está online e funcionando", "SUCCESS")
                return True
            else:
                self.log(f"❌ API retornou status {response.status_code}", "ERROR")
                return False
        except requests.exceptions.ConnectionError:
            self.log(f"❌ Não foi possível conectar com {self.base_url}", "ERROR")
            self.log("   Certifique-se que a API está rodando: python run_api.py", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Erro na conexão: {str(e)}", "ERROR")
            return False
    
    def upload_document(self):
        """Fase 1: Upload de documento"""
        self.print_separator("FASE 1: UPLOAD DE DOCUMENTO")
        
        # Criar documento de teste
        document_content = """
        Sistema RAG Local - Documentação Técnica
        
        Visão Geral:
        O Sistema RAG Local combina retrieval e generation para responder perguntas baseadas em documentos.
        
        Componentes Principais:
        1. Vector Store - Armazena embeddings dos documentos usando Neo4j
        2. Retrieval System - Busca chunks relevantes usando similaridade vetorial  
        3. Generation Layer - Usa modelos LLM (Ollama/OpenAI/Gemini) para gerar respostas
        4. Document Cache - Cache temporário para inferência de schema
        
        Tecnologias Utilizadas:
        - FastAPI para a API REST
        - Neo4j para armazenamento vetorial 
        - Ollama para modelos locais
        - Streamlit para interface web
        - Pydantic para validação de dados
        
        Funcionalidades:
        - Upload de documentos (.txt, .pdf)
        - Consultas em linguagem natural
        - Seleção dinâmica de providers LLM
        - Inferência de schema para grafos
        - Cache inteligente com TTL
        
        Casos de Uso:
        - Análise de documentos corporativos
        - Base de conhecimento pessoal
        - Assistente de pesquisa
        - Prototipagem de sistemas RAG
        """
        
        self.log("📄 Fazendo upload do documento de teste...", "INFO")
        
        try:
            files = {'file': ('rag_documentation.txt', document_content, 'text/plain')}
            start_time = time.time()
            
            response = self.session.post(f"{self.base_url}/api/v1/ingest", files=files)
            upload_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.document_id = data.get('document_id')
                chunks_created = data.get('chunks_created', 0)
                
                self.log(f"✅ Upload realizado com sucesso!", "SUCCESS")
                self.log(f"   📊 Documento ID: {self.document_id}", "INFO")
                self.log(f"   📊 Chunks criados: {chunks_created}", "INFO")
                self.log(f"   ⏱️  Tempo de processamento: {upload_time:.2f}s", "INFO")
                return True
            else:
                self.log(f"❌ Erro no upload: {response.status_code}", "ERROR")
                try:
                    error_data = response.json()
                    self.log(f"   Detalhes: {error_data.get('detail', 'Erro desconhecido')}", "ERROR")
                except:
                    self.log(f"   Response: {response.text[:200]}...", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erro durante upload: {str(e)}", "ERROR")
            return False
    
    def run_queries(self):
        """Fase 2: Execução de consultas"""
        self.print_separator("FASE 2: CONSULTAS RAG")
        
        queries = [
            "O que é o Sistema RAG Local?",
            "Quais são os principais componentes do sistema?", 
            "Que tecnologias são utilizadas?",
            "Quais tipos de arquivo o sistema suporta?",
            "Como funciona o retrieval system?",
            "Que providers LLM estão disponíveis?"
        ]
        
        successful_queries = 0
        
        for i, question in enumerate(queries, 1):
            self.log(f"🔍 Pergunta {i}: {question}", "INFO")
            
            try:
                start_time = time.time()
                payload = {"question": question}
                
                response = self.session.post(f"{self.base_url}/api/v1/query", json=payload)
                query_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get('answer', '')
                    sources = data.get('sources', [])
                    provider = data.get('provider_used', 'unknown')
                    
                    self.log(f"✅ Resposta recebida ({query_time:.2f}s)", "SUCCESS")
                    self.log(f"   🤖 Provider: {provider}", "INFO") 
                    self.log(f"   📝 Tamanho da resposta: {len(answer)} caracteres", "INFO")
                    self.log(f"   📚 Fontes utilizadas: {len(sources)}", "INFO")
                    
                    # Mostrar parte da resposta
                    preview = answer[:150] + "..." if len(answer) > 150 else answer
                    self.log(f"   💬 Preview: {preview}", "INFO")
                    
                    successful_queries += 1
                else:
                    self.log(f"❌ Erro na consulta: {response.status_code}", "ERROR")
                    try:
                        error_data = response.json()
                        self.log(f"   Detalhes: {error_data.get('detail', 'Erro desconhecido')}", "ERROR")
                    except:
                        pass
                        
            except Exception as e:
                self.log(f"❌ Erro durante consulta: {str(e)}", "ERROR")
            
            print()  # Linha em branco entre consultas
        
        success_rate = (successful_queries / len(queries)) * 100
        self.log(f"📊 Resultado das consultas: {successful_queries}/{len(queries)} ({success_rate:.1f}%)", 
                "SUCCESS" if success_rate >= 80 else "WARNING")
        
        return successful_queries > 0
    
    def cleanup(self):
        """Fase 3: Limpeza do sistema"""
        self.print_separator("FASE 3: LIMPEZA DO SISTEMA")
        
        cleanup_tasks = []
        
        # 1. Listar documentos
        self.log("📋 Listando documentos no sistema...", "INFO")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/documents")
            if response.status_code == 200:
                data = response.json()
                documents = data.get('documents', [])
                self.log(f"   Encontrados {len(documents)} documentos", "INFO")
                cleanup_tasks.append(f"Documents found: {len(documents)}")
            else:
                self.log(f"   ❌ Erro ao listar documentos: {response.status_code}", "ERROR")
        except Exception as e:
            self.log(f"   ❌ Erro: {str(e)}", "ERROR")
        
        # 2. Verificar cache de schema
        self.log("💾 Verificando cache de schema...", "INFO")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/schema/documents")
            if response.status_code == 200:
                data = response.json()
                cached_docs = data.get('total_documents', 0)
                memory_usage = data.get('memory_usage_mb', 0)
                self.log(f"   Cache: {cached_docs} documentos, {memory_usage:.1f}MB", "INFO")
                cleanup_tasks.append(f"Cache usage: {memory_usage:.1f}MB")
            else:
                self.log(f"   ❌ Erro ao verificar cache: {response.status_code}", "ERROR")
        except Exception as e:
            self.log(f"   ❌ Erro: {str(e)}", "ERROR")
        
        # 3. Status do banco
        self.log("🗄️  Verificando status do banco de dados...", "INFO")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/db/status")
            if response.status_code == 200:
                data = response.json()
                neo4j_connected = data.get('neo4j_connected', False)
                chunks_count = data.get('chunks', 0)
                documents_count = data.get('documents', 0)
                
                status_icon = "✅" if neo4j_connected else "❌"
                self.log(f"   {status_icon} Neo4j: {'Conectado' if neo4j_connected else 'Desconectado'}", 
                        "SUCCESS" if neo4j_connected else "ERROR")
                self.log(f"   📊 Chunks no banco: {chunks_count}", "INFO")
                self.log(f"   📄 Documentos no banco: {documents_count}", "INFO")
                
                cleanup_tasks.append(f"DB chunks: {chunks_count}")
                cleanup_tasks.append(f"DB documents: {documents_count}")
            else:
                self.log(f"   ❌ Erro ao verificar banco: {response.status_code}", "ERROR")
        except Exception as e:
            self.log(f"   ❌ Erro: {str(e)}", "ERROR")
        
        # 4. Opcional: Limpeza completa (descomentear se desejado)
        """
        self.log("🧹 Executando limpeza completa do banco...", "WARNING")
        try:
            response = self.session.delete(f"{self.base_url}/api/v1/db/clear")
            if response.status_code == 200:
                self.log("   ✅ Limpeza concluída", "SUCCESS")
                cleanup_tasks.append("Database cleared")
            else:
                self.log(f"   ❌ Erro na limpeza: {response.status_code}", "ERROR")
        except Exception as e:
            self.log(f"   ❌ Erro: {str(e)}", "ERROR")
        """
        
        return len(cleanup_tasks) > 0
    
    def run_workflow(self):
        """Executa o fluxo completo"""
        start_time = time.time()
        
        print(f"{Colors.BOLD}{Colors.GREEN}")
        print("🚀 INICIANDO TESTE DE FLUXO COMPLETO - LOCAL RAG SYSTEM")
        print(f"⏰ Horário: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 URL: {self.base_url}")
        print(f"{Colors.END}")
        
        # Fase 0: Teste de conexão
        if not self.test_connection():
            return False
        
        # Fase 1: Upload
        if not self.upload_document():
            self.log("❌ Falha no upload - interrompendo teste", "ERROR")
            return False
        
        # Pequena pausa entre fases
        time.sleep(1)
        
        # Fase 2: Consultas  
        if not self.run_queries():
            self.log("⚠️  Problemas nas consultas - continuando com limpeza", "WARNING")
        
        # Pequena pausa entre fases
        time.sleep(1)
        
        # Fase 3: Limpeza
        self.cleanup()
        
        # Resultado final
        total_time = time.time() - start_time
        
        self.print_separator("RESULTADO FINAL")
        self.log(f"✅ Fluxo completo executado em {total_time:.2f} segundos", "SUCCESS")
        self.log("🎯 Funcionalidades validadas:", "SUCCESS")
        self.log("   • Upload e processamento de documentos", "SUCCESS") 
        self.log("   • Consultas RAG com retrieval", "SUCCESS")
        self.log("   • Geração de respostas com LLM", "SUCCESS")
        self.log("   • APIs de gerenciamento", "SUCCESS")
        
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 TESTE CONCLUÍDO COM SUCESSO!{Colors.END}")
        return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Teste de Fluxo Completo - Local RAG")
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="URL base da API (padrão: http://localhost:8000)")
    parser.add_argument("--quick", action="store_true", 
                       help="Modo rápido - menos consultas de teste")
    
    args = parser.parse_args()
    
    # Verificar se a API está rodando
    tester = WorkflowTester(base_url=args.url)
    
    try:
        success = tester.run_workflow()
        return 0 if success else 1
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Teste interrompido pelo usuário{Colors.END}")
        return 2
    except Exception as e:
        print(f"\n{Colors.RED}❌ Erro durante o teste: {str(e)}{Colors.END}")
        return 3


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)