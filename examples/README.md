# Examples and Standalone Test Scripts

Este diretório contém exemplos de uso e scripts de teste standalone para validação do sistema.

## 📄 Documentos de Exemplo

- `example_document.txt` - Documento de texto de exemplo para testes

## 🔧 Scripts de Validação

### Testes de Providers
- `test_dynamic_provider.py` - Teste da seleção dinâmica de providers
- `test_future_providers.py` - Testes de novos providers futuros
- `test_gemini_direct.py` - Teste direto da integração Gemini
- `test_llm_providers.py` - Teste geral dos providers LLM
- `test_openai_direct.py` - Teste direto da integração OpenAI

### Testes de Interface
- `test_streamlit_ui.py` - Teste da interface Streamlit

## 📋 Como Usar

### Executar Testes de Providers
```bash
# Teste geral dos providers
python examples/test_llm_providers.py

# Teste específico do OpenAI
python examples/test_openai_direct.py

# Teste específico do Gemini  
python examples/test_gemini_direct.py
```

### Validar Configuração
```bash
# Usar os scripts de validação na pasta scripts/
python scripts/validate_providers.py
python scripts/verify_provider_readiness.py
```

## 📝 Nota

Estes scripts são independentes do sistema principal e servem para:
- Validação manual de configurações
- Testes exploratórios de funcionalidades
- Exemplos de uso da API
- Debugging de problemas específicos

Para testes automatizados completos, use:
```bash
pytest tests/
```