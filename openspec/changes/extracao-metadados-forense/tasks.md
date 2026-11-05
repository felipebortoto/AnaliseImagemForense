# Tasks

## 1. Configuração do Projeto e Dependências

- [x] 1.1 Criar `requirements.txt` com as dependências (`pillow`, `folium`, `fastapi`, `uvicorn`, `jinja2`, `pytest`) e verificar instalação.
- [x] 1.2 Estruturar diretórios do projeto (`src/`, `tests/`, `output/`) e arquivos `__init__.py`.

## 2. Módulo de Integridade e Bloqueio de Custódia (src/integrity.py)

- [x] 2.1 Implementar `src/integrity.py` com cálculo de SHA-256 em blocos binários (64KB) e funções para bloqueio lógico/leitura estrita em modo somente-leitura.
- [x] 2.2 Implementar verificação comparativa pré e pós-processamento com validação do Art. 158-A do CPP e ateste de integridade (ÍNTEGRO / VIOLADO).

## 3. Engine de Extração de Metadados (src/extractor.py)

- [x] 3.1 Implementar `src/extractor.py` para leitura segura de metadados EXIF (`DateTimeOriginal`, `Make`, `Model`, `Software`) com tratamento de exceções para imagens sem metadados ou corrompidas.
- [x] 3.2 Implementar conversão de coordenadas GPS (DMS para graus decimais com sinal negativo para hemisférios Sul e Oeste) com fallback gracioso para fotos sem GPS.

## 4. Gerador de Mapa HTML e Relatórios (src/reporter.py)

- [x] 4.1 Implementar geração de mapa interativo HTML em `src/reporter.py` usando Folium com marcadores e PolyLine cronológica conectando os pontos.
- [x] 4.2 Implementar geração de relatório estruturado em formato JSON e Laudo Pericial em Markdown com amplo espaçamento para os hashes SHA-256.

## 5. Interface de Linha de Comando (main.py)

- [x] 5.1 Implementar CLI `main.py` com suporte ao argumento `--image` (arquivo individual ou múltiplos arquivos/glob) e opção para diretório de saída `--output`.
- [x] 5.2 Integrar o fluxo completo na CLI (Integridade pré -> Extração -> Integridade pós -> Mapa HTML -> Relatório JSON/MD) com exibição formatada no terminal.

## 6. Testes e Validação Forense

- [x] 6.1 Criar suite de testes em `tests/` cobrindo cálculo de hash, integridade de cadeia de custódia, extração com/sem EXIF e conversão de GPS.
- [x] 6.2 Executar testes e validar fluxo de ponta a ponta gerando artefatos forenses reais na pasta `output/`.
