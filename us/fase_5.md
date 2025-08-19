```markdown
## Refinamento Colaborativo: Histórias da Fase 5: Suporte para Documentos PDF

---
### História 1: Ingestão e Consulta de Documentos PDF
* **Tipo:** Funcional

#### Parte 1: Especificação Funcional (Visão do Product Owner)
* **História de Usuário:** Como um Usuário Final, eu quero fazer o upload de documentos no formato PDF, para que eu possa consultar o conteúdo de relatórios, manuais e artigos, que são os formatos mais comuns que eu utilizo no meu trabalho.
* **Requisitos / Detalhes:**
    * A interface web de upload de documentos deve ser atualizada para permitir a seleção de arquivos `.pdf`, além dos já suportados `.txt`.
    * O backend (endpoint `/ingest`) deve ser capaz de identificar o tipo de arquivo recebido (PDF ou TXT) e usar o método de extração de texto apropriado.
    * O texto extraído dos PDFs deve ser processado pelo mesmo pipeline de chunking, embedding e armazenamento já existente.
    * A funcionalidade de upload e processamento de arquivos `.txt` não deve ser afetada.
    * Após o upload bem-sucedido de um PDF, seu conteúdo deve estar imediatamente disponível para consulta na interface de chat.
* **Critérios de Aceite (ACs):**
    * **AC 1:** Dado que estou na página de upload, quando abro o seletor de arquivos, então a lista de tipos de arquivo permitidos inclui `.pdf`.
    * **AC 2:** Dado que eu seleciono e envio um documento PDF válido através da interface, então o upload é concluído com sucesso e recebo uma mensagem de confirmação.
    * **AC 3:** Dado que fiz o upload de um relatório em PDF sobre os resultados do Q3, quando vou para a página de chat e pergunto "Quais foram os principais resultados do Q3?", então recebo uma resposta relevante baseada no conteúdo do PDF.
    * **AC 4:** Dado que a nova funcionalidade foi implementada, quando eu faço o upload de um arquivo `.txt`, então o processo funciona exatamente como antes.
* **Definição de 'Pronto' (DoD Checklist):**
    * [ ] Código revisado por um par (PR aprovado).
    * [ ] Testes manuais de ponta a ponta foram realizados para o fluxo de PDF (upload, consulta) e o fluxo de TXT (regressão).
    * [ ] A extração de texto de um PDF de exemplo foi validada como correta.
    * [ ] Não introduziu bugs de regressão.

#### Parte 2: Especificação Técnica (Visão do Engenheiro)
* **Abordagem Técnica Proposta:**
    * Modificaremos o serviço de ingestão no backend para adotar uma abordagem de "fábrica" ou "estratégia", onde o carregador de documento apropriado (para TXT ou PDF) é selecionado com base na extensão do arquivo. A interface do Streamlit exigirá apenas uma pequena alteração para permitir o novo tipo de arquivo.
* **Backend:**
    * - **Dependências:** Adicionar a biblioteca `pypdf` ao arquivo `requirements.txt`. Esta é a dependência subjacente usada pelo `PyPDFLoader` do LangChain.
    * - **Serviço de Ingestão (`src/application/services/ingestion_service.py`):**
        * Refatorar a lógica para inspecionar a extensão do nome do arquivo (`upload_file.filename`).
        * Implementar uma lógica de seleção de carregador (loader):
            * Se a extensão for `.pdf`, instanciar `langchain_community.document_loaders.PyPDFLoader`.
            * Se a extensão for `.txt`, usar o `TextLoader` existente.
            * Se for um tipo de arquivo não suportado, lançar uma exceção que será tratada pela camada da API.
        * O restante do serviço (chunking, embedding, etc.) receberá os dados extraídos pelo loader de forma agnóstica à fonte.
    * - **API (`/ingest`):** Nenhuma mudança significativa é necessária no controlador do endpoint. Ele continuará a passar o objeto `UploadFile` para o serviço de ingestão, que agora contém a lógica para lidar com múltiplos formatos.
* **Frontend (Streamlit UI):**
    * - **Página de Upload (`src/ui/pages/01_document_upload.py`):**
        * Localizar o componente `st.file_uploader`.
        * Atualizar o parâmetro `type` para incluir a nova extensão: `st.file_uploader("Escolha seu documento", type=['txt', 'pdf'])`.
* **Banco de Dados:**
    * - Nenhuma alteração de schema é necessária. O texto extraído de PDFs será tratado e armazenado em nós `:Chunk` da mesma forma que o texto de arquivos `.txt`.
* **Questões em Aberto / Riscos:**
    * - **Qualidade da Extração de Texto:** A extração de texto de PDFs pode ser falha, especialmente em documentos com layouts complexos (múltiplas colunas, tabelas, imagens). A qualidade das respostas do sistema dependerá diretamente da qualidade dessa extração. Se os resultados não forem satisfatórios, talvez precisemos investigar bibliotecas de parsing mais robustas (como `unstructured.io`) no futuro.
    * - **Performance de Ingestão:** O parsing de arquivos PDF é computacionalmente mais caro do que a leitura de texto simples. Isso aumentará o tempo de resposta do endpoint síncrono `/ingest`, elevando o risco de timeouts para o usuário em arquivos grandes ou complexos.

---
```

# Plano de Implementação TDD - Fase 5: Suporte para Documentos PDF

## 1. Configuração Inicial
```bash
# Adicionar dependência
echo "pypdf>=3.0.0" >> requirements.txt
pip install pypdf
```

## 2. Sequência de Implementação TDD

### PASSO 1: Testes de Validação de Tipo de Arquivo
**Arquivo:** `tests/unit/test_file_validation.py`

```python
# RED: Escrever testes que falham
def test_is_valid_pdf_file():
    """Testa se arquivos PDF são reconhecidos como válidos"""
    assert is_valid_file_type("document.pdf") == True
    assert is_valid_file_type("document.PDF") == True
    assert is_valid_file_type("my-file.pdf") == True

def test_is_valid_txt_file():
    """Testa se arquivos TXT continuam sendo válidos"""
    assert is_valid_file_type("document.txt") == True
    assert is_valid_file_type("document.TXT") == True

def test_invalid_file_types():
    """Testa rejeição de tipos não suportados"""
    assert is_valid_file_type("image.jpg") == False
    assert is_valid_file_type("document.docx") == False

# GREEN: Implementar função
# Arquivo: src/application/services/ingestion_service.py
def is_valid_file_type(filename: str) -> bool:
    return filename.lower().endswith(('.txt', '.pdf'))
```

### PASSO 2: Testes do Document Loader Factory
**Arquivo:** `tests/unit/test_document_loader_factory.py`

```python
# RED: Escrever testes para factory de loaders
def test_get_loader_for_pdf():
    """Testa criação de loader para PDF"""
    loader = DocumentLoaderFactory.get_loader("document.pdf", b"content")
    assert isinstance(loader, PDFDocumentLoader)

def test_get_loader_for_txt():
    """Testa criação de loader para TXT"""
    loader = DocumentLoaderFactory.get_loader("document.txt", b"content")
    assert isinstance(loader, TextDocumentLoader)

def test_get_loader_unsupported_type():
    """Testa exceção para tipo não suportado"""
    with pytest.raises(ValueError, match="Unsupported file type"):
        DocumentLoaderFactory.get_loader("document.docx", b"content")

# GREEN: Implementar factory
# Arquivo: src/application/services/document_loaders.py
class DocumentLoaderFactory:
    @staticmethod
    def get_loader(filename: str, content: bytes):
        if filename.lower().endswith('.pdf'):
            return PDFDocumentLoader(content)
        elif filename.lower().endswith('.txt'):
            return TextDocumentLoader(content)
        else:
            raise ValueError(f"Unsupported file type: {filename}")
```

### PASSO 3: Testes de Extração de Texto
**Arquivo:** `tests/unit/test_text_extraction.py`

```python
# RED: Testes para extração de texto
def test_pdf_text_extraction():
    """Testa extração de texto de PDF"""
    pdf_content = create_sample_pdf_bytes()  # Helper para criar PDF de teste
    loader = PDFDocumentLoader(pdf_content)
    text = loader.extract_text()
    assert "sample text" in text
    assert len(text) > 0

def test_txt_text_extraction():
    """Testa extração de texto de TXT"""
    txt_content = b"This is sample text content"
    loader = TextDocumentLoader(txt_content)
    text = loader.extract_text()
    assert text == "This is sample text content"

# GREEN: Implementar loaders
# Arquivo: src/application/services/document_loaders.py
from abc import ABC, abstractmethod
from pypdf import PdfReader
import io

class DocumentLoader(ABC):
    @abstractmethod
    def extract_text(self) -> str:
        pass

class PDFDocumentLoader(DocumentLoader):
    def __init__(self, content: bytes):
        self.content = content
    
    def extract_text(self) -> str:
        pdf_file = io.BytesIO(self.content)
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()

class TextDocumentLoader(DocumentLoader):
    def __init__(self, content: bytes):
        self.content = content
    
    def extract_text(self) -> str:
        return self.content.decode('utf-8')
```

### PASSO 4: Testes de Integração do Serviço
**Arquivo:** `tests/integration/test_ingestion_service_pdf.py`

```python
# RED: Testes de integração
@pytest.mark.asyncio
async def test_ingest_pdf_document():
    """Testa ingestão completa de PDF"""
    service = IngestionService()
    pdf_content = create_sample_pdf_bytes()
    
    result = await service.ingest_from_file_upload(
        pdf_content, 
        "test.pdf",
        embedding_provider="ollama"
    )
    
    assert result["status"] == "success"
    assert result["chunks_created"] > 0
    assert result["document_id"] is not None

@pytest.mark.asyncio
async def test_txt_ingestion_still_works():
    """Testa regressão - TXT deve continuar funcionando"""
    service = IngestionService()
    txt_content = b"Sample text content for testing"
    
    result = await service.ingest_from_file_upload(
        txt_content,
        "test.txt", 
        embedding_provider="ollama"
    )
    
    assert result["status"] == "success"

# GREEN: Refatorar IngestionService
# Arquivo: src/application/services/ingestion_service.py
async def ingest_from_file_upload(self, file_content: bytes, filename: str, embedding_provider: str = "ollama"):
    if not is_valid_file_type(filename):
        raise ValueError(f"Unsupported file type: {filename}")
    
    # Usar factory para obter loader apropriado
    loader = DocumentLoaderFactory.get_loader(filename, file_content)
    text_content = loader.extract_text()
    
    # Continuar com pipeline existente
    return await self.ingest_from_content(text_content, filename, embedding_provider)
```

### PASSO 5: Testes da API
**Arquivo:** `tests/integration/test_api_pdf_upload.py`

```python
# RED: Testes da API
@pytest.mark.asyncio
async def test_api_upload_pdf():
    """Testa upload de PDF via API"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        pdf_content = create_sample_pdf_bytes()
        files = {"file": ("test.pdf", pdf_content, "application/pdf")}
        
        response = await client.post(
            "/api/v1/ingest",
            files=files,
            data={"embedding_provider": "ollama"}
        )
        
        assert response.status_code == 201
        assert response.json()["status"] == "success"

@pytest.mark.asyncio
async def test_api_reject_unsupported_file():
    """Testa rejeição de arquivo não suportado"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        files = {"file": ("test.docx", b"content", "application/docx")}
        
        response = await client.post("/api/v1/ingest", files=files)
        
        assert response.status_code == 415
        assert "Unsupported file type" in response.json()["detail"]

# GREEN: Já deve funcionar se os passos anteriores foram implementados
```

### PASSO 6: Testes da Interface Streamlit
**Arquivo:** `tests/ui/test_document_upload_pdf.py`

```python
# RED: Testes da UI
def test_file_uploader_accepts_pdf(monkeypatch):
    """Testa que file_uploader aceita PDFs"""
    mock_st = create_mock_streamlit()
    mock_client = create_mock_rag_client()
    
    # Simular seleção de arquivo PDF
    mock_st.file_uploader.return_value = MockUploadedFile(
        name="test.pdf",
        content=b"pdf content"
    )
    
    render_page(rag_client=mock_client, st=mock_st)
    
    # Verificar que file_uploader foi chamado com tipos corretos
    mock_st.file_uploader.assert_called_with(
        "Selecione um arquivo de texto (.txt) ou PDF (.pdf)",
        type=['txt', 'pdf'],
        help="Arquivos de texto (.txt) e PDF (.pdf) são permitidos"
    )

# GREEN: Atualizar UI
# Arquivo: src/ui/pages/document_upload.py
uploaded_file = st.file_uploader(
    "Selecione um arquivo de texto (.txt) ou PDF (.pdf)",
    type=['txt', 'pdf'],
    help="Arquivos de texto (.txt) e PDF (.pdf) são permitidos"
)
```

### PASSO 7: Testes End-to-End
**Arquivo:** `tests/e2e/test_pdf_workflow.py`

```python
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_pdf_workflow():
    """Testa fluxo completo: upload PDF → consulta → resposta"""
    # 1. Upload PDF
    pdf_content = create_pdf_with_content("O céu é azul devido ao espalhamento de Rayleigh")
    upload_response = await upload_document(pdf_content, "physics.pdf")
    assert upload_response["status"] == "success"
    
    # 2. Aguardar processamento
    await asyncio.sleep(2)
    
    # 3. Fazer consulta
    query_response = await query_rag("Por que o céu é azul?")
    
    # 4. Verificar resposta
    assert "Rayleigh" in query_response["answer"]
    assert len(query_response["sources"]) > 0
```

## 3. Ordem de Execução

1. **Criar branch de feature:**
   ```bash
   git checkout -b feature/pdf-support
   ```

2. **Executar ciclo TDD para cada passo:**
   ```bash
   # Para cada passo:
   pytest tests/unit/test_xxx.py -v  # RED
   # Implementar código mínimo
   pytest tests/unit/test_xxx.py -v  # GREEN
   # Refatorar se necessário
   ```

3. **Executar suite completa após cada implementação:**
   ```bash
   pytest tests/ -v --cov=src
   ```

4. **Validação manual:**
   - Iniciar API: `python run_api.py`
   - Iniciar UI: `streamlit run streamlit_app.py`
   - Testar upload de PDF e TXT
   - Fazer consultas sobre conteúdo

## 4. Checklist de Validação

### Testes Automatizados
- [ ] Todos os testes unitários passando
- [ ] Todos os testes de integração passando
- [ ] Cobertura de código > 80%
- [ ] Nenhuma regressão em funcionalidade TXT

### Validação Manual
- [ ] Upload de PDF funciona via API
- [ ] Upload de PDF funciona via UI
- [ ] Consultas retornam conteúdo do PDF
- [ ] Upload de TXT continua funcionando
- [ ] Mensagens de erro apropriadas para tipos não suportados

### Documentação
- [ ] README atualizado com suporte a PDF
- [ ] Docstrings em novos métodos
- [ ] Comentários em lógica complexa

## 5. Rollback Plan

Se houver problemas em produção:
1. Reverter para branch main
2. Hotfix temporário: desabilitar PDF no file_uploader
3. Investigar e corrigir em ambiente de desenvolvimento
4. Re-deploy após validação completa