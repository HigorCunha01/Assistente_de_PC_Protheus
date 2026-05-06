# Arquitetura

## Visão geral

```
┌────────────────┐         ┌─────────────────────┐
│   Next.js UI   │ ◄─────► │   FastAPI Backend   │
│  - Login (—)   │  REST   │  - Auth (—)         │
│  - Importar    │  +JSON  │  - Import planilhas │
│    planilha    │         │  - Pipeline PDF     │
│  - Upload PDFs │         │  - Match/sugestão   │
│  - Revisão     │         │  - Geração Excel    │
│  - Download    │         └──────────┬──────────┘
│    Excel       │                    │
└────────────────┘         ┌──────────┴──────────┐
                           │  Volumes Docker     │
                           │  - data/referencias │
                           │  - data/tmp         │
                           └─────────────────────┘
```

Sem banco de dados. Sem login. Estado entre upload e download fica no `sessionStorage` do navegador. Planilhas de referência ficam em volume Docker.

## Fluxo de uma sessão

1. Usuário acessa `/`. Frontend chama `GET /health` e mostra status das planilhas.
2. Se faltar alguma: vai pra `/referencias` e faz upload das 3 planilhas (.xlsx).
3. Em `/processar`: arrasta N PDFs.
4. Frontend chama `POST /processamentos/extrair` com os arquivos.
5. Backend processa cada PDF:
   - `pdfplumber` extrai texto
   - `detector.detectar_tipo` classifica em `danfe_nfe`, `nfse`, `fatura`, `nota_debito` ou `desconhecido`
   - Pipeline tenta parsers específicos primeiro, fallback `generic`
   - Enriquecimento: lookup de filial e fornecedor nas planilhas
   - Retorna `FichaPedido` por documento
6. Frontend redireciona pra `/revisao` com as fichas em `sessionStorage`.
7. Usuário corrige campos/itens e clica em "Gerar Excel".
8. Frontend envia fichas pra `POST /processamentos/gerar-excel`.
9. Backend consolida (`consolidator`), busca pedido antigo (`pc_matcher`), transforma OBS (`obs_mes_transformer`), monta Excel (`excel_generator`) e retorna o blob.

## Módulos do backend

| Módulo | Responsabilidade |
|---|---|
| `app/config.py` | Variáveis de ambiente (paths, limites, CORS) |
| `app/api/health.py` | Health check + status das referências |
| `app/api/referencias.py` | Upload e leitura das planilhas |
| `app/api/processamentos.py` | Endpoints de extração e geração |
| `app/services/referencias.py` | Leitura com cache das planilhas |
| `app/services/pdf/detector.py` | Detecta tipo do documento |
| `app/services/pdf/extractor.py` | Pipeline de extração |
| `app/services/pdf/parsers/*.py` | Parsers por tipo/fornecedor |
| `app/services/pdf/utils.py` | Regex de CNPJ, parse decimal BR, etc |
| `app/services/consolidator.py` | Agrupa fichas compatíveis |
| `app/services/pc_matcher.py` | Sugere PC pra cópia |
| `app/services/obs_mes_transformer.py` | Avança mês na OBS_PEDIDO |
| `app/services/excel_generator.py` | Gera .xlsx final |

## Como adicionar um novo parser

1. Crie `app/services/pdf/parsers/<nome>.py` exportando `parse(texto, caminho) -> ParseResult`.
2. Adicione ao dicionário `PARSERS_POR_TIPO` em `app/services/pdf/extractor.py`.
3. Recomende: confiança >= 0.5 quando o parser realmente reconhecer o documento; < 0.5 quando não.
4. Calibre com 1+ PDFs reais.
