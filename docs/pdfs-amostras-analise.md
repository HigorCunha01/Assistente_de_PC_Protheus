# Análise dos PDFs de amostra

## Resumo

Todos os 7 PDFs analisados têm texto extraível nativamente (`pdfplumber` lê tudo sem OCR).

## Documentos analisados

### 1. snd_347331.PDF (NFS-e Barueri-SP)
- Emissor: SND DISTRIBUIÇÃO DE PRODUTOS DE INFORMÁTICA — CNPJ 02.101.894/0004-84
- Tomador: RTT SOLUCOES INDUSTRIAIS LTDA — CNPJ 67.844.183/0001-00 → filial **03001**
- Número: 347331 | Total: R$ 86,00
- Item: POWER AUTOMATE PER USER WITH ATTENDED RPA PLAN
- **Parser:** `nfse_barueri.py`

### 2. solo network_177288.pdf (NFS-e Pinhais-PR)
- Emissor: SOLO NETWORK BRASIL S.A. — CNPJ 00.258.246/0001-68
- Tomador: RTT ENGINEERED SOLUTIONS LTDA — CNPJ 73.305.997/0001-61 → filial **01001**
- Número: 177288 | Total: R$ 5,57
- Item: SoloCloud — 31 dias — 01/03/2026 a 31/03/2026
- **Parser:** `nfse_pinhais.py`

### 3. blink telecom_14189335.pdf (Fatura)
- Emissor: BTT TELECOMUNICACOES S/A — CNPJ 39.565.567/0001-40
- Tomador: RTT SOLUCOES INDUSTRIAIS LTDA — CNPJ 67.844.183/0007-98 → filial **03002**
- Número: 14189335 | Total: R$ 308,00
- Item: Blink Fibra Link Semi Dedicado 300M
- **Parser:** `fatura_blink.py`
- ⚠️ Documento marcado como "sem valor fiscal" — nota informativa

### 4. save in cloud_261967.pdf (Fatura)
- Emissor: SaveInCloud — **CNPJ não consta no PDF**
- Tomador: Rema Tip Top Serviços de Vulcanização LTDA — CNPJ 73.305.997/0010-52 → filial **01010**
- Número: 261967 | Total: R$ 16.151,04
- 5 itens (Cloudlets, Public IP, SSL, External traffic, Licences)
- **Parser:** `fatura_saveincloud.py`
- ⚠️ Lookup de fornecedor por nome (sem CNPJ no PDF) — observação na ficha

### 5. NF Canaã Material_pc_021700_william.pdf (DANFE NF-e)
- Emissor: R. CANUTO DE BRITO SEGURANCA & SERVICOS — CNPJ 36.923.797/0001-46
- Tomador: RTT SOLUCOES INDUSTRIAIS LTDA — CNPJ 67.844.183/0009-50 → filial **03003**
- Número: 50 | Série: 5 | Total: R$ 1.608,20
- 3 itens (CABO SOHO, ELETRODUTO, BRAÇADEIRA)
- **Parser:** `danfe.py`

### 6. NF 1192.pdf (DANFE NF-e — via Bling)
- Emissor: Efigenia CPU e Tecnologia LTDA — CNPJ 61.346.226/0001-33
- Tomador: RTT SOLUCOES INDUSTRIAIS LTDA — CNPJ 67.844.183/0001-00 → filial **03001**
- Número: 1192 | Total: R$ 1.050,00
- 2 itens (BATERIA DELL, SSD M2 NVME 500Gb)
- **Parser:** `danfe.py`

### 7. NF 1193.pdf (DANFE NF-e — via Bling)
- Emissor: Efigenia CPU e Tecnologia LTDA — CNPJ 61.346.226/0001-33
- Tomador: RTT SOLUCOES INDUSTRIAIS LTDA — CNPJ 67.844.183/0001-00 → filial **03001**
- Número: 1193 | Total: R$ 4.720,00
- 2 itens (Memoria Crucial, Memoria Mancer Damon)
- **Parser:** `danfe.py`
- ⚠️ Layout do Bling cola código com descrição (`CFOP5102Memoria...`) — fallback regex pode pegar errado, parser por tabela funciona melhor.

## Desafios identificados

1. **Layouts heterogêneos** — cada município tem NFS-e diferente; cada DANFE pode variar em pequenos detalhes.
2. **CNPJ ausente** (caso SaveInCloud) — precisa de lookup por nome.
3. **Decimais misturados** — ponto vs vírgula no mesmo PDF (raro, mas acontece).
4. **Códigos grudados em descrição** (Bling) — `extract_tables` resolve melhor que regex de linha.
5. **Faturas multi-página** — todos os exemplos são 1 página, mas pode haver casos maiores.
