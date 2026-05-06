# Roadmap

## Fase 0 — Setup ✅
- [x] Estrutura de pastas
- [x] docker-compose com 2 serviços (backend + frontend)
- [x] Volumes pra `data/referencias` e `data/tmp`
- [x] README e .env.example

## Fase 1 — Referências ✅ (MVP)
- [x] Endpoint `POST /referencias/upload/{tipo}` — recebe e valida planilha
- [x] Endpoint `GET /referencias/status` — quais planilhas estão presentes
- [x] Endpoints de listagem (`GET /referencias/filiais`, `/fornecedores`, `/pedidos-compra`)
- [x] Cache em memória com invalidação por mtime
- [x] Tela `/referencias` com upload das 3 planilhas

## Fase 2 — Extração de PDF ✅ (MVP, requer ajuste fino)
- [x] Pipeline `extractor.py` com detecção de tipo
- [x] Parser DANFE (NF-e produto) — calibrado com NF Canaã + NFs Bling
- [x] Parser NFS-e Barueri — calibrado com SND
- [x] Parser NFS-e Pinhais — calibrado com Solo Network
- [x] Parser Fatura Blink Telecom
- [x] Parser Fatura SaveInCloud
- [x] Parser genérico (fallback)
- [x] Tela `/processar` para upload múltiplo
- [x] Tela `/revisao` com edição de campos e itens

### Pendente Fase 2 (refinamento)
- [ ] Testes unitários por parser com PDFs de amostra
- [ ] Suporte a OCR (Tesseract) pra PDFs escaneados sem texto extraível
- [ ] Mais templates conforme novos fornecedores aparecerem
- [ ] Detecção de PDF multi-página (atualmente lê todas, mas não reconhece múltiplas notas no mesmo arquivo)

## Fase 3 — Consolidação + match ✅
- [x] Consolidação por (fornecedor, filial, tipo)
- [x] Match com pedidos antigos (descrição + preço com tolerância)
- [x] Transformação OBS_PEDIDO (próximo mês)

### Pendente Fase 3 (refinamento)
- [ ] UI permitir aceitar/rejeitar sugestão de PC
- [ ] Múltiplas sugestões de PC quando houver empate

## Fase 4 — Excel ✅
- [x] Geração com 2 abas (Pedidos + Itens)
- [x] Formatação básica (cabeçalho colorido, freeze panes, larguras)

### Pendente Fase 4 (refinamento)
- [ ] Aba "Resumo" com totais por filial/fornecedor
- [ ] Hyperlink entre abas (Pedidos → Itens daquele pedido)

## Fase 5 — Polimento (não iniciado)
- [ ] Logs estruturados no backend
- [ ] Página de "logs/erros" no frontend pra debug rápido
- [ ] Limpeza periódica de `data/tmp`
- [ ] Health check com mais detalhes
- [ ] Build de produção (frontend `next build`, multi-stage Docker)
