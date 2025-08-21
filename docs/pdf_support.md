# Suporte para Documentos PDF

## Visão Geral

O sistema suporta ingestão e processamento de documentos PDF além de arquivos de texto simples. A extração de texto de PDFs é realizada usando a biblioteca `pypdf`, fornecendo uma solução local e eficiente para processamento de documentos.

## Implementação

### Arquitetura

O suporte ao PDF foi implementado usando o padrão Strategy/Factory:

```python
DocumentLoaderFactory
    ├── PDFDocumentLoader (pypdf)
    └── TextDocumentLoader (texto simples)
```

### Fluxo de Processamento

1. **Validação**: Verifica se o arquivo tem extensão `.pdf` ou `.txt`
2. **Factory**: Seleciona o loader apropriado baseado na extensão
3. **Extração**: Usa `pypdf.PdfReader` para extrair texto de PDFs
4. **Pipeline**: O texto extraído segue o mesmo pipeline de chunking e embedding

### Exemplo de Uso

**Interface Streamlit:**
- O file uploader aceita tipos `['txt', 'pdf']`
- Interface atualizada para mencionar suporte ao PDF

**API REST:**
```bash
curl -X POST "http://localhost:8000/api/v1/ingest" \
  -F "file=@documento.pdf;type=application/pdf" \
  -F "embedding_provider=ollama"
```

## Limitações e Considerações

### Qualidade da Extração
- PDFs com layouts complexos (tabelas, múltiplas colunas) podem ter extração de texto imprecisa
- Imagens e gráficos são ignorados (apenas texto é extraído)
- PDFs escaneados (imagens) não são suportados (não há OCR)

### Performance
- Processamento de PDFs é computacionalmente mais caro que texto simples
- Arquivos grandes podem causar timeout em uploads síncronos
- Recomenda-se dividir PDFs muito grandes em seções menores

### Dependências
- `pypdf>=3.0.0` (já incluído no requirements.txt)
- Compatível com Python 3.8+

## Testes

A implementação inclui uma suite completa de testes:

- **Testes Unitários**: Validação de tipos, factory pattern, extração de texto
- **Testes de Integração**: Pipeline completo de ingestão
- **Testes da API**: Endpoints HTTP com PDFs
- **Testes End-to-End**: Fluxo completo upload → consulta

Total: 17 novos testes específicos para PDF, todos passando.

## Roadmap Futuro

### Melhorias Planejadas
- Suporte a OCR para PDFs escaneados
- Processamento assíncrono para arquivos grandes
- Extração de metadados (autor, título, data de criação)
- Suporte a outros formatos (DOCX, PPTX)
- Biblioteca de parsing mais robusta (ex: `unstructured.io`)

### Considerações de Escalabilidade
- Para produção, considerar processamento assíncrono com filas
- Cache de documentos processados para evitar re-processamento
- Monitoring de performance e qualidade de extração