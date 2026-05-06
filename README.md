# Protheus PC — Extrator de Pedidos de Compra

Sistema web que processa documentos fiscais (NF-e, NFS-e, faturas, notas de débito) em PDF e gera um arquivo Excel com os dados estruturados, prontos para criação de pedidos de compra no ERP Protheus.

## Stack

- **Backend:** Python 3.11 + FastAPI + pdfplumber + openpyxl
- **Frontend:** Next.js 14 (App Router) + TypeScript + Tailwind + shadcn/ui
- **Storage:** Volumes Docker (sem banco de dados)
- **Deploy:** Docker Compose

## Funcionalidades

1. Upload de planilhas de referência (Filiais, Fornecedores, Pedidos de Compra) — armazenadas em volume Docker.
2. Upload de múltiplos PDFs de NF/NFS-e/fatura.
3. Extração automática de campos (CNPJ, número, itens, valores) com parsers específicos por tipo.
4. Consolidação de documentos do mesmo fornecedor + filial + tipo (produto/serviço).
5. Match com pedidos antigos: sugere PC para cópia quando há histórico compatível.
6. Tela de revisão para correção manual antes de gerar o Excel.
7. Download do Excel com cabeçalho do pedido + itens + sugestão de PC + obs com mês ajustado.

## Como rodar

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Documentação interativa da API: http://localhost:8000/docs

## Estrutura

```
protheus-pc/
├── backend/         # FastAPI + extractors
├── frontend/        # Next.js 14
├── data/
│   ├── referencias/ # planilhas .xlsx (volume)
│   └── tmp/         # arquivos temporários (volume)
├── docs/            # documentação técnica
└── docker-compose.yml
```

## Atualização de planilhas

Pela UI: `/referencias` → faz upload de cada uma das 3 planilhas. Os arquivos são salvos em `data/referencias/` e ficam disponíveis para o backend ler em cada processamento.

## Roadmap

- [x] Fase 0: Setup (Docker, estrutura, configs)
- [ ] Fase 1: Tela de import de planilhas
- [ ] Fase 2: Pipeline de extração de PDF + revisão
- [ ] Fase 3: Consolidação + match
- [ ] Fase 4: Geração do Excel
- [ ] Fase 5: Polimento e testes

Detalhes em [docs/roadmap.md](docs/roadmap.md).
