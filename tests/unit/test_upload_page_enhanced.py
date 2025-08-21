"""
Testes unitários para página de upload aprimorada com seleção individual de modelos
"""
import pytest
from unittest.mock import Mock, patch, MagicMock


class MockStreamlitEnhanced:
    """Mock aprimorado do Streamlit para nova interface de upload"""
    
    def __init__(self):
        self._called_methods = []
        self._selectbox_values = {}
        self._file_uploader_value = None
        self._button_clicked = False
        self._columns_created = []
        
    def title(self, text):
        self._called_methods.append(('title', text))
        
    def subheader(self, text):
        self._called_methods.append(('subheader', text))
        
    def markdown(self, text):
        self._called_methods.append(('markdown', text))
        
    def columns(self, count):
        cols = [MockColumn() for _ in range(count)]
        self._columns_created.append(cols)
        return cols
    
    def selectbox(self, label, options, format_func=None, key=None, help=None, index=0):
        value = options[index] if options else None
        self._selectbox_values[key or label] = value
        self._called_methods.append(('selectbox', label, options, key))
        return value
    
    def caption(self, text):
        self._called_methods.append(('caption', text))
        
    def write(self, text):
        self._called_methods.append(('write', text))
        
    def info(self, text):
        self._called_methods.append(('info', text))
        
    def success(self, text):
        self._called_methods.append(('success', text))
        
    def error(self, text):
        self._called_methods.append(('error', text))
        
    def warning(self, text):
        self._called_methods.append(('warning', text))
        
    def file_uploader(self, label, type=None, help=None):
        self._called_methods.append(('file_uploader', label, type))
        return self._file_uploader_value
        
    def button(self, label, disabled=False):
        self._called_methods.append(('button', label, disabled))
        return self._button_clicked
        
    def metric(self, label, value, delta=None, help=None):
        self._called_methods.append(('metric', label, value))
        
    def progress(self, value):
        return MockProgress()
        
    def empty(self):
        return MockEmpty()
        
    def spinner(self, text):
        return MockSpinner()
        
    def expander(self, label):
        return MockExpander()


class MockColumn:
    """Mock para colunas do Streamlit"""
    def __init__(self):
        self._called_methods = []
        
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        pass
        
    def markdown(self, text):
        self._called_methods.append(('markdown', text))
        
    def selectbox(self, label, options, index=0, key=None, help=None):
        value = options[index] if options else None
        self._called_methods.append(('selectbox', label, options, key))
        return value
        
    def caption(self, text):
        self._called_methods.append(('caption', text))
        
    def write(self, text):
        self._called_methods.append(('write', text))
        
    def error(self, text):
        self._called_methods.append(('error', text))
        
    def info(self, text):
        self._called_methods.append(('info', text))
        
    def metric(self, label, value, delta=None, help=None):
        self._called_methods.append(('metric', label, value))


class MockProgress:
    def progress(self, value):
        pass
    def empty(self):
        pass


class MockEmpty:
    def text(self, value):
        pass
    def empty(self):
        pass


class MockSpinner:
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass


class MockExpander:
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def write(self, text):
        pass


class MockUploadedFile:
    """Mock para arquivo enviado via Streamlit"""
    def __init__(self, name, content, size_mb=1.0):
        self.name = name
        self._content = content if isinstance(content, bytes) else content.encode()
        self._size_mb = size_mb
        
    def read(self):
        return self._content
        
    def seek(self, position):
        pass


class TestEnhancedUploadPage:
    """Testes para funcionalidades aprimoradas da página de upload"""
    
    def setup_method(self):
        """Setup comum para todos os testes"""
        self.mock_st = MockStreamlitEnhanced()
        self.mock_rag_client = Mock()
        
    def test_enhanced_interface_structure(self):
        """Test que nova interface tem estrutura correta"""
        from src.ui.pages.document_upload import render_page
        
        with patch('requests.get') as mock_get:
            # Mock API responses for models
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "models": ["model1", "model2"], 
                "default": "model1"
            }
            
            render_page(rag_client=self.mock_rag_client, st=self.mock_st)
            
            # Verificar que título foi atualizado
            title_calls = [call for call in self.mock_st._called_methods if call[0] == 'title']
            assert len(title_calls) > 0
            assert "Upload de Documentos" in title_calls[0][1]
            
            # Verificar que subheader de configuração está presente
            subheader_calls = [call for call in self.mock_st._called_methods if call[0] == 'subheader']
            config_subheaders = [call for call in subheader_calls if "Configuração de Modelos" in call[1]]
            assert len(config_subheaders) > 0
            
            # Verificar que colunas foram criadas (para embedding e LLM)
            assert len(self.mock_st._columns_created) > 0
    
    @patch('requests.get')
    def test_embedding_provider_selection(self, mock_get):
        """Test seleção de provedor de embedding"""
        from src.ui.pages.document_upload import render_page
        
        # Mock API response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "models": ["nomic-embed-text", "all-minilm"], 
            "default": "nomic-embed-text"
        }
        
        render_page(rag_client=self.mock_rag_client, st=self.mock_st)
        
        # Verificar que selectbox de embedding provider foi criado
        selectbox_calls = [call for call in self.mock_st._called_methods if call[0] == 'selectbox']
        embedding_calls = [call for call in selectbox_calls if "embedding_provider_selector" in str(call)]
        assert len(embedding_calls) > 0
    
    @patch('requests.get')  
    def test_llm_provider_selection(self, mock_get):
        """Test seleção de provedor LLM"""
        from src.ui.pages.document_upload import render_page
        
        # Mock API response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "models": ["gpt-4o-mini", "gpt-4o"], 
            "default": "gpt-4o-mini"
        }
        
        render_page(rag_client=self.mock_rag_client, st=self.mock_st)
        
        # Verificar que selectbox de LLM provider foi criado
        selectbox_calls = [call for call in self.mock_st._called_methods if call[0] == 'selectbox']
        llm_calls = [call for call in selectbox_calls if "llm_provider_selector" in str(call)]
        assert len(llm_calls) > 0
    
    @patch('requests.get')
    def test_model_fetching_functionality(self, mock_get):
        """Test que modelos LLM são buscados da API"""
        from src.ui.pages.document_upload import _fetch_llm_models_for_provider
        
        # Mock successful API call
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": ["model1", "model2", "model3"],
            "default": "model1"
        }
        mock_get.return_value = mock_response
        
        result = _fetch_llm_models_for_provider("ollama")
        
        assert "models" in result
        assert "default" in result
        assert result["models"] == ["model1", "model2", "model3"]
        assert result["default"] == "model1"
        
        # Verificar que API foi chamada corretamente
        mock_get.assert_called_once_with("http://localhost:8000/api/v1/models/ollama", timeout=5)
    
    def test_embedding_model_fetching_fallback(self):
        """Test fallback para modelos de embedding"""
        from src.ui.pages.document_upload import _fetch_embedding_models_for_provider
        
        # Test fallback para ollama
        result = _fetch_embedding_models_for_provider("ollama")
        assert "models" in result
        assert "nomic-embed-text" in result["models"]
        
        # Test fallback para openai
        result = _fetch_embedding_models_for_provider("openai")  
        assert "models" in result
        assert "text-embedding-3-small" in result["models"]
        assert "text-embedding-3-large" in result["models"]
        assert "text-embedding-ada-002" in result["models"]
    
    @patch('requests.get')
    def test_llm_model_fetching_fallback(self, mock_get):
        """Test fallback para modelos LLM quando API não está disponível"""
        from src.ui.pages.document_upload import _fetch_llm_models_for_provider
        
        # Mock API failure
        mock_get.side_effect = Exception("Connection error")
        
        # Test fallback para ollama
        result = _fetch_llm_models_for_provider("ollama")
        assert "models" in result
        assert "qwen3:8b" in result["models"]
        
        # Test fallback para openai
        result = _fetch_llm_models_for_provider("openai")  
        assert "models" in result
        assert "gpt-4o-mini" in result["models"]
    
    def test_openai_embedding_models_available(self):
        """Test que modelos de embedding OpenAI estão disponíveis"""
        from src.ui.pages.document_upload import _fetch_embedding_models_for_provider
        
        result = _fetch_embedding_models_for_provider("openai")
        assert "models" in result
        assert "default" in result
        
        # Verificar que todos os modelos de embedding OpenAI estão presentes
        expected_models = ["text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002"]
        for model in expected_models:
            assert model in result["models"], f"Modelo {model} não encontrado nos modelos OpenAI"
        
        # Verificar que o modelo padrão é correto
        assert result["default"] == "text-embedding-3-small"
    
    @patch('requests.get')
    def test_provider_status_checking(self, mock_get):
        """Test verificação de status dos provedores"""
        from src.ui.pages.document_upload import _get_provider_status
        
        # Test Ollama online
        mock_get.return_value.status_code = 200
        status, desc = _get_provider_status("ollama")
        assert status == "🟢"
        assert "Online" in desc
        
        # Test Ollama offline
        mock_get.side_effect = Exception("Connection refused")
        status, desc = _get_provider_status("ollama")
        assert status == "🔴"
        assert "Offline" in desc
    
    @patch('requests.get')
    @patch('os.getenv')
    def test_openai_provider_status(self, mock_getenv, mock_get):
        """Test status do provedor OpenAI"""
        from src.ui.pages.document_upload import _get_provider_status
        
        # Test com API key configurada
        mock_getenv.return_value = "sk-test-key-123456789012345678901234567890"
        status, desc = _get_provider_status("openai")
        assert status == "🟢"
        assert "Configurado" in desc
        
        # Test sem API key
        mock_getenv.return_value = None
        status, desc = _get_provider_status("openai")
        assert status == "🔴"
        assert "não configurada" in desc
    
    @patch('requests.get')
    def test_file_upload_with_models(self, mock_get):
        """Test upload de arquivo com modelos selecionados"""
        from src.ui.pages.document_upload import render_page
        
        # Mock API responses
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "models": ["nomic-embed-text"], 
            "default": "nomic-embed-text"
        }
        
        # Setup file upload
        test_file = MockUploadedFile("test.txt", "Test content", 0.1)
        self.mock_st._file_uploader_value = test_file
        self.mock_st._button_clicked = True
        
        # Setup mock client response
        self.mock_rag_client.upload_file.return_value = {
            "ok": True, 
            "data": {"chunks_created": 3, "document_id": "test-123"}
        }
        
        render_page(rag_client=self.mock_rag_client, st=self.mock_st)
        
        # Verificar que upload_file foi chamado com parâmetros corretos
        self.mock_rag_client.upload_file.assert_called_once()
        call_args = self.mock_rag_client.upload_file.call_args
        
        # Verificar argumentos da chamada
        assert len(call_args[0]) >= 2  # file_content, filename
        assert call_args[1]["embedding_provider"] in ["ollama", "openai"]
        assert "model_name" in call_args[1]
    
    @patch('requests.get')
    def test_simplified_documentation_present(self, mock_get):
        """Test que documentação simplificada está presente"""
        from src.ui.pages.document_upload import render_page
        
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"models": ["model1"], "default": "model1"}
        
        render_page(rag_client=self.mock_rag_client, st=self.mock_st)
        
        # Verificar que documentação simplificada está presente
        markdown_calls = [call for call in self.mock_st._called_methods if call[0] == 'markdown']
        simple_docs = [call for call in markdown_calls if "Embedding" in call[1] and "LLM" in call[1]]
        assert len(simple_docs) > 0
        
        # Verificar que menciona seções embedding e LLM
        embedding_docs = [call for call in markdown_calls if "🔍 **Embedding**" in call[1]]
        llm_docs = [call for call in markdown_calls if "🤖 **LLM**" in call[1]]
        assert len(embedding_docs) > 0
        assert len(llm_docs) > 0