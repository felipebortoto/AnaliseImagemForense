# Design: Extração e Análise Forense de Metadados em Mídias Digitais

## Context

A conformidade com a Cadeia de Custódia (Art. 158-A a 158-F do Código de Processo Penal) exige que nenhuma evidência digital seja adulterada durante o exame pericial. A motivação e o escopo funcional deste projeto estão detalhados em `proposal.md` e os requisitos normativos em `specs/forensic-evidence-analysis/spec.md`.

Este documento estabelece a arquitetura técnica para atender aos requisitos de integridade, extração de metadados, visualização interativa e geração de laudo estruturado.

## Goals / Non-Goals

**Goals:**
- Proteger integralmente o estado das mídias originais através de processamento em memória e verificação estrita de hash SHA-256 (pré e pós-extração).
- Suportar processamento simultâneo de lotes pontuais de 1 a 25 imagens comuns em investigações periciais (JPEG, PNG, TIFF).
- Gerar mapas interativos no Folium com traçado de trajetória cronológica entre pontos georreferenciados.
- Produzir laudo pericial em Markdown com espaçamento amplo e blocos destacados para conferência visual de hashes SHA-256.
- Disponibilizar interface web moderna e intuitiva usando FastAPI, HTML5, JavaScript e Tailwind CSS.

**Non-Goals:**
- Não contemplará processamento em larga escala (Big Data forense com milhares de imagens).
- Não realizará brute-force ou quebra de arquivos criptografados.
- Não alterará nem regravará tags EXIF nos arquivos originais.
- Não dependerá de banco de dados externo ou autenticação de usuários para esta fase inicial.

## Decisions

### 1. Separação de Camadas: FastAPI (Backend) + HTML/JS/Tailwind CSS (Frontend)
- **Decisão:** Utilizar FastAPI para fornecer endpoints assíncronos e servir a interface web estilizada com Tailwind CSS.
- **Alternativas consideradas:** Streamlit (descartado após preferência por layout customizado e desacoplado); Flask (FastAPI oferece validação nativa com Pydantic e alta performance assíncrona).
- **Impacto:** Arquitetura limpa com separação entre a lógica pericial e a camada de apresentação.

### 2. Fluxo em Memória e Leitura em Chunks de 64KB
- **Decisão:** Calcular o hash SHA-256 utilizando `hashlib.sha256()` lendo o buffer do arquivo em blocos binários de 64KB diretamente de `UploadFile.file` (ou `BytesIO`).
- **Alternativas consideradas:** Gravar cópia física temporária em disco antes do hash (risco desnecessário de alteração de timestamps do sistema de arquivos).
- **Impacto:** Zero alteração acidental no arquivo de origem e consumo de RAM previsível e baixo para até 25 fotos.

### 3. Extração EXIF com Pillow e Conversão Geodésica Rigorosa
- **Decisão:** Utilizar `PIL.Image.open(io.BytesIO(conteudo))` exclusivamente para leitura das tags EXIF (`DateTimeOriginal`, `Make`, `Model`, `GPSInfo`).
- **Lógica de Conversão GPS:**
  - Latitude: $Graus + \frac{Minutos}{60} + \frac{Segundos}{3600}$, invertida para negativo se `GPSLatitudeRef == 'S'`.
  - Longitude: $Graus + \frac{Minutos}{60} + \frac{Segundos}{3600}$, invertida para negativo se `GPSLongitudeRef == 'W'`.
- **Tratamento de Exceções:** Imagens sem EXIF ou sem coordenadas GPS são processadas normalmente quanto à integridade (hash) e listadas como "Sem coordenadas geográficas".

### 4. Apresentação Visual Espaçada dos Hashes no Laudo Markdown
- **Decisão:** Exibir os hashes SHA-256 inicial e final em blocos de citação e código monoespaçado individual (`> **SHA-256 Inicial:**` / `> \`hash\``) com linhas em branco de respiro, em vez de colunas estreitas de tabela Markdown.
- **Alternativas consideradas:** Tabela Markdown com coluna para hash (rejeitado por causar quebras feias de linha e fadiga visual na conferência dos 64 caracteres).
- **Impacto:** Legibilidade imediata para peritos, advogados e magistrados realizarem conferência lado a lado ou visual.

### 5. Renderização do Mapa Folium no Frontend
- **Decisão:** O backend gera o mapa via Folium e exporta o HTML em string ou arquivo temporário para ser renderizado dentro de um `<iframe>` responsivo na interface Tailwind.
- **Trajetória Cronológica:** Os pontos georreferenciados são ordenados por `DateTimeOriginal` e conectados por `folium.PolyLine(color='blue', weight=3, opacity=0.8)`.

## Risks / Trade-offs

- **[Imagens sem metadados EXIF (redes sociais)]** $\rightarrow$ *Mitigação:* A aplicação não falha; registra a ausência de metadados no laudo e mantém o registro da integridade criptográfica.
- **[EXIF com datas inválidas ou formatos divergentes]** $\rightarrow$ *Mitigação:* Parser resiliente com tratamento de `try/except` para converter formatos `YYYY:MM:DD HH:MM:SS` comuns e fallbacks seguros.
- **[Envio de arquivos não suportados (ex: executáveis ou vídeos)]** $\rightarrow$ *Mitigação:* Validação de MIME type e extensão de imagem no upload (`image/jpeg`, `image/png`, `image/tiff`), rejeitando arquivos inválidos com status 400.

