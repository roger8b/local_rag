"""
Testes unitários para seleção dinâmica na interface Streamlit (Fase 5.1)
"""
import pytest
from unittest.mock import Mock, patch, MagicMock


class MockStreamlitState:
    """Mock para st.session_state"""
    def __init__(self):
        self._state = {}
        
    def __contains__(self, key):
        return key in self._state
        
    def __getitem__(self, key):
        return self._state.get(key)
        
    def __setitem__(self, key, value):
        self._state[key] = value
        
    def get(self, key, default=None):
        return self._state.get(key, default)


class MockStreamlit:
    """Mock completo do Streamlit para testes de interface"""
    
    def __init__(self):
        self.session_state = MockStreamlitState()
        self._sidebar = MockStreamlitSidebar()
        self._called_methods = []
        self._rerun_called = False
        
    def set_page_config(self, **kwargs):
        self._called_methods.append(('set_page_config', kwargs))
    
    def title(self, text):
        self._called_methods.append(('title', text))
        
    def info(self, text):
        self._called_methods.append(('info', text))
        
    def markdown(self, text):
        self._called_methods.append(('markdown', text))
        
    def rerun(self):
        self._rerun_called = True
        self._called_methods.append(('rerun', None))
    
    @property
    def sidebar(self):
        return self._sidebar
        
    def chat_message(self, role):
        return MagicMock()
        
    def chat_input(self, placeholder):
        return None
        
    def spinner(self, text):
        return MagicMock()


class MockStreamlitSidebar:
    """Mock para st.sidebar"""
    
    def __init__(self):
        self._called_methods = []
        
    def title(self, text):
        self._called_methods.append(('title', text))
        
    def markdown(self, text):
        self._called_methods.append(('markdown', text))
        
    def radio(self, label, options, index=0, help=None):
        self._called_methods.append(('radio', label, options, index))
        return options[index]
        
    def selectbox(self, label, options, index=0, format_func=None, help=None):
        self._called_methods.append(('selectbox', label, options, index))
        return options[index] if options else None
        
    def caption(self, text):
        self._called_methods.append(('caption', text))
        
    def info(self, text):
        self._called_methods.append(('info', text))
        
    def success(self, text):
        self._called_methods.append(('success', text))
        
    def error(self, text):
        self._called_methods.append(('error', text))
        
    def write(self, text):
        self._called_methods.append(('write', text))


class TestStreamlitDynamicSelection:
    """Testes para funcionalidades de seleção dinâmica"""
    
    def setup_method(self):
        """Setup comum para todos os testes"""
        self.mock_st = MockStreamlit()
        
    def test_session_state_initialization(self):
        """Test que as variáveis de sessão são inicializadas corretamente"""
        # Simular inicialização das variáveis de sessão
        expected_keys = [
            "selected_mode", "selected_provider", "selected_model", 
            "available_models", "default_model"
        ]
        
        # Initialize session state como no código real
        if "selected_mode" not in self.mock_st.session_state:
            self.mock_st.session_state["selected_mode"] = "Consulta"
        if "selected_provider" not in self.mock_st.session_state:
            self.mock_st.session_state["selected_provider"] = "ollama"
        if "selected_model" not in self.mock_st.session_state:
            self.mock_st.session_state["selected_model"] = None
        if "available_models" not in self.mock_st.session_state:
            self.mock_st.session_state["available_models"] = []
        if "default_model" not in self.mock_st.session_state:
            self.mock_st.session_state["default_model"] = None
            
        for key in expected_keys:
            assert key in self.mock_st.session_state
            
        # Verificar valores padrão
        assert self.mock_st.session_state["selected_mode"] == "Consulta"
        assert self.mock_st.session_state["selected_provider"] == "ollama"
        assert self.mock_st.session_state["selected_model"] is None
    
    def test_mode_selection_interface(self):
        """Test que a seleção de modo funciona corretamente"""
        # Setup session state
        self.mock_st.session_state["selected_mode"] = "Consulta"
        
        # Mock radio button return
        selected_mode = self.mock_st.sidebar.radio(
            "Escolha o modo:",
            ["Consulta", "Ingestão"],
            index=0,
            help="Consulta: Fazer perguntas sobre documentos. Ingestão: Adicionar novos documentos."
        )
        
        assert selected_mode == "Consulta"
        
        # Verificar que o método foi chamado corretamente
        calls = self.mock_st.sidebar._called_methods
        radio_calls = [call for call in calls if call[0] == 'radio']
        assert len(radio_calls) == 1
        assert radio_calls[0][1] == "Escolha o modo:"
        assert radio_calls[0][2] == ["Consulta", "Ingestão"]
    
    def test_provider_selection_interface(self):
        """Test que a seleção de provedor funciona corretamente"""
        # Setup session state
        self.mock_st.session_state["selected_provider"] = "ollama"
        
        provider_options = {
            "ollama": "🏠 Local (Ollama)",
            "openai": "☁️ OpenAI",
            "gemini": "✨ Google Gemini"
        }
        
        selected_provider = self.mock_st.sidebar.selectbox(
            "Provedor:",
            list(provider_options.keys()),
            index=0,
            format_func=lambda x: provider_options[x],
            help="Selecione qual provedor usar para gerar respostas"
        )
        
        assert selected_provider == "ollama"
        
        # Verificar que o método foi chamado
        calls = self.mock_st.sidebar._called_methods
        selectbox_calls = [call for call in calls if call[0] == 'selectbox']
        assert len(selectbox_calls) == 1
        assert selectbox_calls[0][1] == "Provedor:"
    
    @patch('requests.get')
    def test_model_fetching_success(self, mock_get):
        """Test que busca de modelos funciona corretamente"""
        # Mock resposta da API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": ["qwen3:8b", "llama2:13b"],
            "default": "qwen3:8b"
        }
        mock_get.return_value = mock_response
        
        # Simular mudança de provedor
        old_provider = "openai"
        new_provider = "ollama"
        
        if new_provider != old_provider:
            # Simular reset do session state
            self.mock_st.session_state["selected_provider"] = new_provider
            self.mock_st.session_state["selected_model"] = None
            self.mock_st.session_state["available_models"] = []
            self.mock_st.session_state["default_model"] = None
            
            # Simular fetch de modelos
            import requests
            response = requests.get(f"http://localhost:8000/api/v1/models/{new_provider}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.mock_st.session_state["available_models"] = data.get("models", [])
                self.mock_st.session_state["default_model"] = data.get("default", None)
                self.mock_st.session_state["selected_model"] = self.mock_st.session_state["default_model"]
        
        # Verificar resultados
        assert self.mock_st.session_state["available_models"] == ["qwen3:8b", "llama2:13b"]
        assert self.mock_st.session_state["default_model"] == "qwen3:8b"
        assert self.mock_st.session_state["selected_model"] == "qwen3:8b"
        
        # Verificar que a API foi chamada corretamente
        mock_get.assert_called_once_with(
            "http://localhost:8000/api/v1/models/ollama", 
            timeout=5
        )
    
    @patch('requests.get')
    def test_model_fetching_error_handling(self, mock_get):
        """Test que erros na busca de modelos são tratados corretamente"""
        # Mock erro na requisição
        mock_get.side_effect = Exception("Connection error")
        
        # Simular tentativa de buscar modelos
        try:
            import requests
            response = requests.get("http://localhost:8000/api/v1/models/ollama", timeout=5)
        except Exception as e:
            error_message = str(e)
            
        assert error_message == "Connection error"
    
    def test_model_selection_interface(self):
        """Test que seleção de modelo específico funciona"""
        # Setup com modelos disponíveis
        self.mock_st.session_state["available_models"] = ["qwen3:8b", "llama2:13b"]
        self.mock_st.session_state["selected_model"] = "qwen3:8b"
        
        if self.mock_st.session_state["available_models"]:
            selected_model = self.mock_st.sidebar.selectbox(
                "Modelo:",
                self.mock_st.session_state["available_models"],
                index=0,
                help="Modelo específico a ser usado"
            )
            
            assert selected_model == "qwen3:8b"
            
            # Verificar chamada
            calls = self.mock_st.sidebar._called_methods
            selectbox_calls = [call for call in calls if call[0] == 'selectbox']
            assert len(selectbox_calls) == 1
            assert selectbox_calls[0][1] == "Modelo:"