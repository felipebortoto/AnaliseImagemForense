# Sistema de Análise de Imagem Forense e Cadeia de Custódia
Digital Forensics Image Analysis and Chain of Custody System

---

## Sumário / Table of Contents
1. [Documentação em Português](#versão-em-português)
   - [1. Visão Geral](#1-visão-geral)
   - [2. Fundamentação Jurídica e Pericial](#2-fundamentação-jurídica-e-pericial)
   - [3. Arquitetura do Sistema](#3-arquitetura-do-sistema)
   - [4. Tecnologias Utilizadas](#4-tecnologias-utilizadas)
   - [5. Estrutura de Diretórios](#5-estrutura-de-diretórios)
   - [6. Instalação e Configuração](#6-instalação-e-configuração)
   - [7. Guia de Execução](#7-guia-de-execução)
   - [8. Suíte de Testes](#8-suíte-de-testes)
2. [English Documentation](#english-version)
   - [1. Overview](#1-overview)
   - [2. Legal and Forensic Framework](#2-legal-and-forensic-framework)
   - [3. System Architecture](#3-system-architecture)
   - [4. Technology Stack](#4-technology-stack)
   - [5. Directory Structure](#5-directory-structure)
   - [6. Installation and Setup](#6-installation-and-setup)
   - [7. Execution Guide](#7-execution-guide)
   - [8. Test Suite](#8-test-suite)

---

# Versão em Português

## 1. Visão Geral

O **Sistema de Análise de Imagem Forense** é uma solução computacional voltada para a perícia digital e investigações que envolvem mídias fotográficas. O objetivo central do projeto é viabilizar a extração segura de metadados técnicos (EXIF e coordenadas de geolocalização por satélite) garantindo, de forma matematicamente auditável, que o arquivo original sob custódia não sofra nenhuma alteração física, lógica ou temporal durante todo o processo.

A ferramenta suporta o exame de arquivos individuais ou lotes de até 25 mídias, oferecendo duas formas de operação:
- Uma Interface de Linha de Comando (CLI) para automações laboratoriais e uso em terminais.
- Uma Interface Web Gráfica moderna com suporte a arrastar e soltar (drag & drop), visualização em mapa cartográfico interativo e emissão de laudo técnico pericial em Markdown com hashes espaçados.

---

## 2. Fundamentação Jurídica e Pericial

No ordenamento jurídico brasileiro, a Lei nº 13.964/2019 (conhecida como Pacote Anticrime) introduziu os Artigos 158-A a 158-F no Código de Processo Penal (CPP), formalizando a **Cadeia de Custódia** da prova pericial.

O Art. 158-A define a cadeia de custódia como:
> "O conjunto de todos os procedimentos utilizados para manter e documentar a história cronológica do vestígio coletado em locais ou em vítimas de crimes, para rastrear sua posse e manuseio a partir de seu reconhecimento até o descarte."

Para conferir validade jurídica ao vestígio digital, a ferramenta opera sob os seguintes pilares forenses:
1. **Fixação e Inviolabilidade:** No exato instante em que o arquivo é recebido, é calculado o hash criptográfico **SHA-256** diretamente do fluxo binário bruto.
2. **Exame Não Destrutivo:** A leitura dos metadados é feita exclusivamente em memória (`io.BytesIO`), sem abrir o arquivo em modo de escrita e sem modificar os carimbos de data e hora do sistema de arquivos.
3. **Verificação de Conformidade Pós-Exame:** Imediatamente após a extração, o hash SHA-256 do arquivo original é recalculado. O sistema afere se o hash pré-processamento é idêntico ao hash pós-processamento. Qualquer divergência indica quebra da cadeia de custódia e gera um alerta explícito de violação probatória.

---

## 3. Arquitetura do Sistema

O projeto é estruturado em módulos especializados e desacoplados:

### 3.1. Núcleo de Integridade (`src/integrity.py`)
Responsável pelo cálculo de hashes em blocos de 64 KB (65.536 bytes) para otimização de memória e proteção contra arquivos volumosos. Implementa a classe `IntegrityReport`, que formaliza o ateste de integridade (status ÍNTEGRO ou VIOLADO) segundo o Art. 158-A do CPP.

### 3.2. Engine de Extração de Metadados (`src/extractor.py`)
Utiliza a biblioteca Pillow para inspecionar os blocos IFD (Image File Directory) do padrão EXIF:
- **Dados do Dispositivo:** Fabricante (`Make`), Modelo (`Model`) e Software/Firmware.
- **Datas:** `DateTimeOriginal` e `DateTimeDigitized`, normalizadas para o padrão ISO 8601.
- **Geodésia e GPS:** Conversão de coordenadas em Graus, Minutos e Segundos (DMS) para Graus Decimais, aplicando sinal negativo para os hemisférios Sul (S) e Oeste (W).
- **Tratamento de Exceções:** Imagens sem EXIF (como fotos recebidas por aplicativos de mensageria que realizam compressão agressiva) são processadas com resiliência, registrando a ausência de metadados sem interromper a cadeia de custódia.

### 3.3. Gerador Cartográfico e Relatórios (`src/reporter.py`)
- **Mapeamento Espacial (Folium / Leaflet.js):** Constrói um mapa interativo contendo marcadores individuais para cada foto com GPS e uma linha temporal contínua (`PolyLine`) conectando os pontos na ordem cronológica de captura, permitindo reconstruir a rota percorrida pelo investigado.
- **Relatório Estruturado (JSON):** Exportação legível por máquinas com todos os campos da perícia.
- **Laudo Pericial (Markdown):** Documento formal estruturado para juntada em inquérito ou processo judicial. Apresenta seções de auditoria com blocos destacados e espaçamento generoso para a visualização dos 64 caracteres dos hashes SHA-256, facilitando a conferência visual por peritos e magistrados.

### 3.4. Interfaces de Acesso (`main.py` e `src/server.py`)
- **CLI (`main.py`):** Suporta argumentos flexíveis (`--image`, `--output`, `--title`, `--examiner`, `--strict`, `--web`).
- **Web (`src/server.py`):** Backend assíncrono construído em FastAPI com páginas estilizadas em Tailwind CSS.

---

## 4. Tecnologias Utilizadas

- **Linguagem:** Python 3.10 ou superior.
- **Framework Web:** FastAPI e Uvicorn (ASGI assíncrono).
- **Manipulação de Imagens e EXIF:** Pillow.
- **Geração Cartográfica:** Folium (com Leaflet.js).
- **Criptografia e Hashing:** Biblioteca padrão `hashlib` (SHA-256).
- **Interface Front-end:** HTML5, JavaScript moderno e Tailwind CSS (via CDN).
- **Testes Automatizados:** Pytest.

---

## 5. Estrutura de Diretórios

```text
AnaliseImagemForense/
├── main.py                     # Ponto de entrada CLI e acionador do servidor web
├── requirements.txt            # Declaração das dependências do ecossistema Python
├── README.md                   # Documentação técnica e operacional
├── src/
│   ├── __init__.py             # Inicializador do pacote principal
│   ├── integrity.py            # Bloqueio de custódia e cálculo criptográfico de hashes
│   ├── extractor.py            # Parser EXIF, conversão DMS-Decimal e tolerância a falhas
│   ├── reporter.py             # Renderizador de mapa Folium, relatórios JSON e Laudo MD
│   ├── server.py               # Aplicação web FastAPI e endpoints multipart
│   └── templates/
│       └── index.html          # Interface gráfica web responsiva em Tailwind CSS
├── tests/
│   ├── __init__.py             # Inicializador da suíte de testes
│   ├── test_integrity.py       # Testes unitários de hashing e assertividade da custódia
│   ├── test_extractor.py       # Testes de conversão geodésica e imagens sem metadados
│   ├── test_reporter.py        # Testes de geração de mapa HTML e relatórios
│   └── test_main.py            # Testes de integração da CLI
└── output/                     # Diretório padrão para laudos, mapas e relatórios gerados
```

---

## 6. Instalação e Configuração

### 6.1. Clonagem e Acesso ao Projeto
Abra o terminal do sistema operacional e navegue até a pasta do projeto:
```bash
cd AnaliseImagemForense
```

### 6.2. Criação do Ambiente Virtual
Recomenda-se o uso de um ambiente virtual isolado:

No Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

No Linux ou macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 6.3. Instalação dos Pacotes
Instale as dependências declaradas no `requirements.txt`:
```bash
pip install -r requirements.txt
```

---

## 7. Guia de Execução

### 7.1. Execução via Linha de Comando (CLI)

Para examinar uma ou mais imagens pontuais e gerar o laudo pericial:

```bash
python main.py --image caminho/para/foto1.jpg caminho/para/foto2.png --output output --title "Operacao Rastro Digital" --examiner "Perito Oficial"
```

Parâmetros disponíveis:
- `-i, --image`: Caminho para uma ou mais imagens (suporta caminhos literais ou padrões glob como `fotos/*.jpg`).
- `-o, --output`: Diretório onde os artefatos periciais serão gravados (padrão: `output/`).
- `--title`: Título do caso ou operação para identificação no laudo.
- `--examiner`: Nome do perito ou setor responsável pelo exame.
- `--strict`: Caso haja qualquer divergência no hash pré/pós, o processo é abortado com código de saída de erro.
- `--web`: Inicializa o servidor web gráfico em vez do modo linha de comando.
- `--port`: Porta TCP para o servidor web (padrão: `8000`).

Artefatos gerados automaticamente na pasta informada:
- `mapa_evidencias.html`: Mapa cartográfico interativo navegável via navegador.
- `relatorio_pericial.json`: Dados estruturados da perícia em JSON.
- `laudo_pericial.md`: Laudo pericial formal em Markdown.

### 7.2. Execução da Interface Web Gráfica

Para iniciar o servidor web interativo:

```bash
python main.py --web
```

Em seguida, abra o navegador web e acesse:
```text
http://127.0.0.1:8000
```

Fluxo de utilização na interface:
1. Arraste e solte até 25 fotografias na área indicada.
2. Clique no botão **Executar Exame Pericial e Fixação de Custódia**.
3. Explore os resultados nas abas:
   - **Mapa Cronológico Espacial:** visualização geográfica dos pontos e rota traçada.
   - **Auditoria Criptográfica de Hashes:** conferência detalhada dos hashes pré e pós-análise com espaçamento visual.
   - **Prévia do Laudo (.md):** leitura prévia do documento formal.
4. Clique em **Baixar Laudo** para realizar o download imediato do arquivo `.md`.

---

## 8. Suíte de Testes

Os testes automatizados cobrem a lógica criptográfica, a resiliência do parser de metadados e a execução dos relatórios:

```bash
pytest
```

---
---

# English Version

## 1. Overview

The **Digital Forensics Image Analysis System** is a technical framework designed for computer forensics and investigative operations involving image media. The primary goal of this project is to enable safe extraction of technical metadata (EXIF tags and satellite GPS coordinates) while providing mathematically verifiable proof that the original evidentiary file was not physically, logically, or chronologically modified during examination.

The system supports individual evidence files as well as batches of up to 25 media items, offering two operational interfaces:
- A Command Line Interface (CLI) for automated processing and laboratory workflows.
- A modern Graphical Web Interface featuring drag-and-drop batch upload, interactive geospatial mapping, and automated generation of formal Markdown forensic reports with spacious cryptographic hash presentation.

---

## 2. Legal and Forensic Framework

In Brazilian criminal procedural law, Federal Law No. 13,964/2019 introduced Articles 158-A through 158-F into the Criminal Procedure Code (Código de Processo Penal - CPP), formally instituting the **Chain of Custody** for physical and digital evidence.

Article 158-A establishes:
> "The chain of custody consists of the set of all procedures used to maintain and document the chronological history of evidence collected at crime scenes or from victims, tracking possession and handling from initial recognition to final disposal."

To uphold strict evidentiary standards (compatible with ISO/IEC 27037 principles), this software enforces three operational rules:
1. **Immediate Cryptographic Sealing:** As soon as an evidentiary file is received, its **SHA-256** hash is computed directly from raw binary chunks.
2. **Strict Read-Only Inspection:** Metadata parsing is conducted purely in memory (`io.BytesIO`), without opening the storage file with write permissions and without mutating filesystem MACB (Modified, Accessed, Created) timestamps.
3. **Post-Analysis Integrity Verification:** Following metadata extraction, the SHA-256 digest of the source file is re-calculated. The system formally asserts that initial and post-examination hashes match with zero bit divergence. Any detected discrepancy immediately raises a custody violation alert.

---

## 3. System Architecture

The codebase is organized into modular and decoupled components:

### 3.1. Integrity Module (`src/integrity.py`)
Handles cryptographic hashing using 64 KB (65,536 bytes) chunks to ensure memory efficiency and accommodate high-resolution files. Implements the `IntegrityReport` class, which formalizes custody preservation status (INTACT vs. VIOLATED) under statutory rules.

### 3.2. Metadata Extraction Engine (`src/extractor.py`)
Leverages the Pillow library to inspect EXIF Image File Directories (IFD):
- **Device Attributes:** Make, Model, and Firmware/Software.
- **Timestamps:** `DateTimeOriginal` and `DateTimeDigitized`, standardized into ISO 8601 strings.
- **Geodesic Coordinates:** Conversion of Degrees, Minutes, and Seconds (DMS) tuples into Decimal Degrees, applying negative signs for Southern (S) and Western (W) coordinates.
- **Fault Tolerance:** Media lacking EXIF data (e.g., compressed images transmitted through messaging apps) are safely processed without crashing, documenting the absence of metadata while maintaining chain of custody records.

### 3.3. Cartographic & Reporting Engine (`src/reporter.py`)
- **Spatial Mapping (Folium / Leaflet.js):** Generates standalone interactive HTML maps displaying indexed markers for GPS-enabled images, interconnected by a dashed chronological trajectory (`PolyLine`) sorted by original capture time.
- **Structured Report (JSON):** Machine-readable export compiling custody and technical details.
- **Forensic Report (Markdown):** Formally structured technical document formatted with spacious, clear code blocks for 64-character SHA-256 strings, allowing straightforward visual auditing by judicial authorities.

### 3.4. Access Interfaces (`main.py` and `src/server.py`)
- **CLI (`main.py`):** Configurable command-line parser supporting flags (`--image`, `--output`, `--title`, `--examiner`, `--strict`, `--web`).
- **Web (`src/server.py`):** Asynchronous FastAPI application delivering a Tailwind CSS responsive dashboard.

---

## 4. Technology Stack

- **Language:** Python 3.10 or higher.
- **Web Framework:** FastAPI and Uvicorn.
- **Image & EXIF Parsing:** Pillow.
- **Geospatial Visualization:** Folium (Leaflet.js).
- **Cryptography:** Standard Python `hashlib` (SHA-256).
- **Front-end UI:** HTML5, Modern JavaScript, Tailwind CSS (via CDN).
- **Test Automation:** Pytest.

---

## 5. Directory Structure

```text
AnaliseImagemForense/
├── main.py                     # CLI entrypoint and web server launcher
├── requirements.txt            # Python ecosystem dependencies
├── README.md                   # Bilingual technical and operational manual
├── src/
│   ├── __init__.py             # Package initializer
│   ├── integrity.py            # Chain of custody locking and SHA-256 calculation
│   ├── extractor.py            # Safe EXIF parser, DMS-to-decimal conversion
│   ├── reporter.py             # Folium HTML map generator, JSON and MD reports
│   ├── server.py               # FastAPI backend and multipart upload routes
│   └── templates/
│       └── index.html          # Tailwind CSS responsive web dashboard
├── tests/
│   ├── __init__.py             # Test suite initializer
│   ├── test_integrity.py       # Unit tests for hashing and integrity validation
│   ├── test_extractor.py       # Unit tests for GPS conversion and metadata parsing
│   ├── test_reporter.py        # Unit tests for map and report builders
│   └── test_main.py            # Integration tests for CLI operations
└── output/                     # Default output directory for reports and maps
```

---

## 6. Installation and Setup

### 6.1. Clone and Access the Repository
Open a terminal and navigate to the project directory:
```bash
cd AnaliseImagemForense
```

### 6.2. Virtual Environment Configuration
It is recommended to deploy within an isolated virtual environment:

On Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

On Linux or macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 6.3. Dependency Installation
Install required packages using pip:
```bash
pip install -r requirements.txt
```

---

## 7. Execution Guide

### 7.1. Running via Command Line (CLI)

To examine one or more specific images and generate reports:

```bash
python main.py --image path/to/image1.jpg path/to/image2.png --output output --title "Digital Forensic Case" --examiner "Lead Examiner"
```

Available Flags:
- `-i, --image`: One or more image file paths (supports direct paths or glob patterns such as `evidence/*.jpg`).
- `-o, --output`: Destination directory for output artifacts (default: `output/`).
- `--title`: Title of the forensic case or investigative operation.
- `--examiner`: Name of the forensic investigator or institution.
- `--strict`: Aborts execution with a non-zero exit code if hash verification fails.
- `--web`: Starts the web application server instead of CLI batch execution.
- `--port`: TCP port for the web service (default: `8000`).

Generated Artifacts in the Output Directory:
- `mapa_evidencias.html`: Interactive cartographic map viewable in any web browser.
- `relatorio_pericial.json`: Comprehensive machine-readable inspection data in JSON.
- `laudo_pericial.md`: Formal forensic report rendered in Markdown.

### 7.2. Running the Graphical Web Interface

To start the local web application:

```bash
python main.py --web
```

Next, open your preferred browser and navigate to:
```text
http://127.0.0.1:8000
```

Operational Steps:
1. Drag and drop up to 25 images onto the upload dropzone.
2. Click **Executar Exame Pericial e Fixação de Custódia** (Execute Forensic Examination).
3. Review results in the tabbed interface:
   - **Chronological Map:** Geospatial marker layout and chronologically ordered route line.
   - **Cryptographic Custody Audit:** Itemized custody cards displaying initial and final SHA-256 hashes with spacious visual separation.
   - **Report Preview:** Formatted Markdown report viewer.
4. Click **Baixar Laudo** to download the `laudo_pericial_custodia.md` document.

---

## 8. Test Suite

Execute automated unit and integration tests across the codebase:

```bash
pytest
```

