# PC para copia

Projeto simples para ler PDFs de uma pasta e gerar um Excel com:

- Nome do arquivo
- Filial
- Cod Fornecedor
- Pedido p/ copia
- Valor total do documento

Nao precisa subir frontend, backend, Docker ou servidor.

## 1. Instalar dependencias

Instale Python 3.12:

```powershell
winget install Python.Python.3.12
```

Instale Tesseract OCR para PDFs escaneados/imagem:

```powershell
winget install UB-Mannheim.TesseractOCR
```

Instale as dependencias Python:

```powershell
cd "C:\dev\protheus-pc\pc-copia-script"
python -m pip install -r requirements.txt
```

## 2. Colocar referencias

Coloque estas planilhas na pasta `referencias` deste projeto:

```text
Filiais.xlsx
Fornecedores.xlsx
Pedidos_de_Compra.xlsx
```

Exemplo:

```text
C:\dev\protheus-pc\pc-copia-script\referencias\Filiais.xlsx
C:\dev\protheus-pc\pc-copia-script\referencias\Fornecedores.xlsx
C:\dev\protheus-pc\pc-copia-script\referencias\Pedidos_de_Compra.xlsx
```

## 3. Rodar em uma pasta de PDFs

Entre na pasta onde estao os PDFs:

```powershell
cd "C:\Users\Usuario\Documents\Contas 2026\05 - MAIO"
```

Rode:

```powershell
python "C:\dev\protheus-pc\pc-copia-script\gerar_pcs_copia.py"
```

O Excel `pc_para_copia.xlsx` sera gerado nessa mesma pasta.

## 4. Rodar com dois cliques

Voce tambem pode copiar o arquivo `Gerar PC para copia.bat` para a pasta dos PDFs e dar dois cliques.
