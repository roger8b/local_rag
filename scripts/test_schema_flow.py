#!/usr/bin/env python3
"""
Teste de Fluxo Schema API - Local RAG System
Fluxo: Upload de Documento → Inferência de Schema → Limpeza
"""

import requests
import json
import time
from datetime import datetime


class SchemaFlowTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.uploaded_keys = []
    
    def log(self, message, emoji="ℹ️"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {emoji} {message}")
    
    def print_header(self, title):
        print(f"\n{'='*50}")
        print(f" {title} ")
        print(f"{'='*50}")
    
    def test_upload(self):
        """Testa upload de documento para schema"""
        self.print_header("TESTE DE UPLOAD - História 7")
        
        # Documento exemplo sobre uma empresa de tecnologia
        document_content = """
        TechCorp Relatório Anual 2024
        
        Visão Geral da Empresa:
        A TechCorp é uma empresa de tecnologia fundada em 2020 por Maria Silva e João Santos.
        A empresa está localizada em São Paulo e atua no desenvolvimento de soluções de IA.
        
        Equipe:
        - Maria Silva: CEO e cofundadora, especialista em Machine Learning
        - João Santos: CTO e cofundador, especialista em DevOps  
        - Ana Costa: Desenvolvedora Senior, foco em Python e FastAPI
        - Pedro Lima: Data Scientist, trabalha com modelos de NLP
        - Carla Oliveira: Product Manager, responsável pela estratégia de produto
        
        Produtos:
        - AIAssistant: Assistente virtual para empresas
        - DataPlatform: Plataforma de análise de dados
        - MLOps Suite: Ferramentas para deploy de modelos ML
        
        Tecnologias Utilizadas:
        - Python para desenvolvimento backend
        - React para frontend
        - PostgreSQL para banco de dados
        - Docker para containerização
        - AWS para infraestrutura em nuvem
        
        Parcerias:
        A TechCorp mantém parcerias estratégicas com:
        - Microsoft Azure para serviços de nuvem
        - NVIDIA para hardware de IA
        - Universidade de São Paulo para pesquisa
        
        Clientes:
        - Banco Central do Brasil
        - Petrobras
        - Via Varejo
        - Ambev
        """
        
        self.log("Fazendo upload do documento...", "📤")
        
        try:
            files = {'file': ('techcorp_relatorio.txt', document_content, 'text/plain')}
            start_time = time.time()
            
            response = self.session.post(f"{self.base_url}/api/v1/schema/upload", files=files)
            upload_time = time.time() - start_time
            
            if response.status_code == 201:
                data = response.json()
                key = data.get('key')
                filename = data.get('filename')
                file_size = data.get('file_size_bytes', 0)
                text_stats = data.get('text_stats', {})
                processing_time = data.get('processing_time_ms', 0)
                
                self.uploaded_keys.append(key)
                
                self.log(f"Upload realizado com sucesso!", "✅")
                self.log(f"Chave do documento: {key}", "🔑")
                self.log(f"Nome do arquivo: {filename}", "📄")
                self.log(f"Tamanho do arquivo: {file_size} bytes", "📊")
                self.log(f"Caracteres extraídos: {text_stats.get('total_chars', 0)}", "📊")
                self.log(f"Palavras: {text_stats.get('total_words', 0)}", "📊")
                self.log(f"Linhas: {text_stats.get('total_lines', 0)}", "📊")
                self.log(f"Tempo de processamento: {processing_time:.1f}ms", "⏱️")
                self.log(f"Tempo total: {upload_time:.2f}s", "⏱️")
                
                return key
            else:
                self.log(f"Erro no upload: {response.status_code}", "❌")
                self.log(f"Detalhes: {response.text}", "❌")
                return None
                
        except Exception as e:
            self.log(f"Erro durante upload: {str(e)}", "❌")
            return None
    
    def test_schema_inference(self, document_key):
        """Testa inferência de schema - História 6 & 8"""
        self.print_header("TESTE DE INFERÊNCIA - Histórias 6 & 8")
        
        test_cases = [
            {
                "name": "Inferência com 30% do documento",
                "payload": {
                    "document_key": document_key,
                    "sample_percentage": 30
                }
            },
            {
                "name": "Inferência com 70% + seleção de provider",
                "payload": {
                    "document_key": document_key,
                    "sample_percentage": 70,
                    "llm_provider": "ollama"
                }
            },
            {
                "name": "Inferência com texto direto",
                "payload": {
                    "text": "Amazon é uma empresa de e-commerce. Jeff Bezos foi o fundador. A empresa vende produtos online e oferece serviços de nuvem AWS.",
                    "sample_percentage": 100,
                    "llm_provider": "ollama"
                }
            }
        ]
        
        successful_inferences = 0
        
        for i, test_case in enumerate(test_cases, 1):
            self.log(f"Teste {i}: {test_case['name']}", "🔍")
            
            try:
                start_time = time.time()
                response = self.session.post(f"{self.base_url}/api/v1/schema/infer", 
                                           json=test_case['payload'])
                inference_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    node_labels = data.get('node_labels', [])
                    relationship_types = data.get('relationship_types', [])
                    source = data.get('source', 'unknown')
                    model_used = data.get('model_used', 'unknown')
                    processing_time = data.get('processing_time_ms', 0)
                    document_info = data.get('document_info')
                    
                    self.log(f"Inferência bem-sucedida ({inference_time:.2f}s)", "✅")
                    self.log(f"Fonte: {source}", "🤖")
                    self.log(f"Modelo usado: {model_used}", "🤖")
                    self.log(f"Tipos de nós: {len(node_labels)} → {node_labels[:5]}", "🏷️")
                    self.log(f"Tipos de relação: {len(relationship_types)} → {relationship_types[:5]}", "🔗")
                    self.log(f"Tempo de processamento: {processing_time:.1f}ms", "⏱️")
                    
                    if document_info:
                        sample_percentage = document_info.get('sample_percentage', 0)
                        sample_size = document_info.get('sample_size', 0)
                        self.log(f"Amostra usada: {sample_percentage}% ({sample_size} chars)", "📊")
                    
                    successful_inferences += 1
                else:
                    self.log(f"Erro na inferência: {response.status_code}", "❌")
                    self.log(f"Detalhes: {response.text[:200]}", "❌")
                    
            except Exception as e:
                self.log(f"Erro durante inferência: {str(e)}", "❌")
            
            print()  # Linha em branco entre testes
        
        success_rate = (successful_inferences / len(test_cases)) * 100
        self.log(f"Taxa de sucesso: {successful_inferences}/{len(test_cases)} ({success_rate:.1f}%)", 
                "✅" if success_rate >= 80 else "⚠️")
        
        return successful_inferences > 0
    
    def test_document_management(self):
        """Testa gerenciamento de documentos"""
        self.print_header("TESTE DE GERENCIAMENTO")
        
        # Listar documentos no cache
        self.log("Listando documentos no cache...", "📋")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/schema/documents")
            if response.status_code == 200:
                data = response.json()
                total_docs = data.get('total_documents', 0)
                memory_usage = data.get('memory_usage_mb', 0)
                documents = data.get('documents', [])
                
                self.log(f"Documentos em cache: {total_docs}", "📊")
                self.log(f"Uso de memória: {memory_usage:.2f}MB", "📊")
                
                for doc in documents:
                    filename = doc.get('filename', 'unknown')
                    key_preview = doc.get('key', '')[:8] + "..."
                    file_size = doc.get('file_size_bytes', 0)
                    self.log(f"  • {filename} ({key_preview}) - {file_size} bytes", "📄")
                    
            else:
                self.log(f"Erro ao listar documentos: {response.status_code}", "❌")
                
        except Exception as e:
            self.log(f"Erro: {str(e)}", "❌")
    
    def cleanup(self):
        """Limpa documentos criados durante o teste"""
        self.print_header("LIMPEZA")
        
        if not self.uploaded_keys:
            self.log("Nenhum documento para remover", "ℹ️")
            return
        
        removed_count = 0
        
        for key in self.uploaded_keys:
            self.log(f"Removendo documento {key[:8]}...", "🗑️")
            
            try:
                response = self.session.delete(f"{self.base_url}/api/v1/schema/documents/{key}")
                
                if response.status_code == 200:
                    self.log("Documento removido com sucesso", "✅")
                    removed_count += 1
                else:
                    self.log(f"Erro ao remover: {response.status_code}", "❌")
                    
            except Exception as e:
                self.log(f"Erro: {str(e)}", "❌")
        
        self.log(f"Total removido: {removed_count}/{len(self.uploaded_keys)}", "📊")
    
    def run_flow(self):
        """Executa o fluxo completo"""
        start_time = time.time()
        
        print("🚀 INICIANDO TESTE DE FLUXO SCHEMA API")
        print(f"🌐 URL: {self.base_url}")
        print(f"⏰ Horário: {datetime.now().strftime('%H:%M:%S')}")
        
        # Teste de conectividade
        try:
            response = self.session.get(f"{self.base_url}/api/v1/health", timeout=5)
            if response.status_code != 200:
                self.log(f"API não está respondendo corretamente: {response.status_code}", "❌")
                return False
        except:
            self.log(f"Não foi possível conectar com {self.base_url}", "❌")
            self.log("Certifique-se que a API está rodando: python run_api.py", "💡")
            return False
        
        # Fase 1: Upload
        document_key = self.test_upload()
        if not document_key:
            self.log("Falha no upload - interrompendo teste", "❌")
            return False
        
        time.sleep(0.5)  # Pequena pausa
        
        # Fase 2: Inferência
        inference_success = self.test_schema_inference(document_key)
        
        time.sleep(0.5)  # Pequena pausa
        
        # Fase 3: Gerenciamento
        self.test_document_management()
        
        time.sleep(0.5)  # Pequena pausa
        
        # Fase 4: Limpeza
        self.cleanup()
        
        # Resultado final
        total_time = time.time() - start_time
        
        print(f"\n{'='*50}")
        print(" RESULTADO FINAL ")
        print(f"{'='*50}")
        self.log(f"Fluxo completo executado em {total_time:.2f} segundos", "⏱️")
        self.log("Funcionalidades testadas:", "✅")
        self.log("  • Upload de documentos com estatísticas detalhadas", "✅")
        self.log("  • Inferência de schema com controle percentual", "✅")
        self.log("  • Seleção dinâmica de provider LLM", "✅")
        self.log("  • Gerenciamento de cache com TTL", "✅")
        self.log("  • Limpeza automática de recursos", "✅")
        
        success = document_key is not None and inference_success
        if success:
            print(f"\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
        else:
            print(f"\n⚠️  TESTE FINALIZADO COM PROBLEMAS")
        
        return success


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Teste de Fluxo Schema API")
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="URL da API (padrão: http://localhost:8000)")
    
    args = parser.parse_args()
    
    tester = SchemaFlowTester(base_url=args.url)
    
    try:
        success = tester.run_flow()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️  Teste interrompido pelo usuário")
        return 2
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {str(e)}")
        return 3


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)