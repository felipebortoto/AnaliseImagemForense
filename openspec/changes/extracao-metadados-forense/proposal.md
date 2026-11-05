# Proposal: Extração e Análise Forense de Metadados em Mídias Digitais

## Why

Mídias digitais recolhidas em investigações criminais demandam extração rigorosa de metadados sem que os arquivos originais sofram qualquer alteração ou corrupção, em estrita observância à Cadeia de Custódia estabelecida pelo Código de Processo Penal Brasileiro (Art. 158-A a 158-F, Lei 13.964/2019). Esta proposta introduz uma solução web pericial capaz de calcular a integridade criptográfica (SHA-256 pré e pós-processamento), extrair metadados e dados georreferenciados (EXIF) de até 25 imagens por lote, plotar trajetos cronológicos em mapas interativos e emitir laudos técnicos estruturados em Markdown com ampla legibilidade pericial.

## What Changes

- **Núcleo de Custódia Criptográfica**: Leitura em fluxo binário e fixação imediata do hash SHA-256 de cada imagem antes de qualquer análise, com rechecagem comparativa estrita pós-processamento para atestar inviolabilidade.
- **Extração Forense de Metadados**: Parsing seguro de metadados EXIF via Pillow (dados do dispositivo, data/hora original da captura e dados geodésicos GPS), convertendo coordenadas DMS para graus decimais com adequação aos hemisférios.
- **Backend FastAPI**: Endpoints para recepção em lote (1 a 25 imagens pontuais), orquestração da cadeia de custódia, geração de visualização e exportação de laudo.
- **Frontend Interativo (HTML/JS + Tailwind CSS)**: Interface web para upload via drag & drop, inspeção do status de integridade de cada evidência e visualização do mapa espacial.
- **Mapeamento Cronológico (Folium)**: Renderização de mapa interativo com marcadores georreferenciados e traçado cronológico (PolyLine) ordenado pela data/hora dos registros.
- **Emissão de Laudo em Markdown**: Geração de laudo pericial técnico em Markdown contendo badges de status e blocos destacados com espaçamento amplo para os hashes SHA-256 (64 caracteres hexadecimais), facilitando conferência e auditoria judicial.

## Capabilities

### New Capabilities
- `forensic-evidence-analysis`: Processamento pericial de imagens digitais com validação estrita de integridade via SHA-256 (Cadeia de Custódia Art. 158-A CPP), extração segura de metadados EXIF/GPS, mapeamento cronoespacial interativo via Folium e geração de laudo pericial em Markdown com hashes espaçados.

### Modified Capabilities
<!-- Nenhuma capacidade existente modificada (projeto inicial) -->

## Impact

- **Dependências Novas**: `fastapi`, `uvicorn`, `python-multipart`, `pillow`, `folium`, `jinja2`.
- **APIs**: Novo endpoint `POST /api/analyze` para recepção multipart das imagens e retorno estruturado dos metadados, mapa e laudo.
- **Arquivos/Sistemas**: Criação da aplicação web com arquitetura backend em FastAPI e frontend baseado em templates/estáticos com Tailwind CSS.

