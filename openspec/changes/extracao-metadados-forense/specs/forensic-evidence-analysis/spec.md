# Spec Delta

## Purpose

Fornece capacidade de exame pericial digital para processamento de até 25 mídias, assegurando a inviolabilidade da cadeia de custódia (Art. 158-A do CPP) com cálculo estrito de SHA-256 pré e pós-análise, extração segura de metadados EXIF/GPS, visualização cronoespacial interativa e emissão de laudo técnico em Markdown com alta legibilidade.

## ADDED Requirements

### Requirement: Fixação Inicial de Hash Criptográfico
O sistema SHALL / DEVE calcular o hash SHA-256 do fluxo binário de cada mídia no momento do recebimento, antes de qualquer operação de leitura de metadados ou processamento.

#### Scenario: Fixação de hash em lote de imagens
- **WHEN** o usuário envia entre 1 e 25 imagens para exame pericial
- **THEN** o sistema gera o SHA-256 de 64 caracteres hexadecimais para cada arquivo a partir de seus bytes brutos

### Requirement: Verificação de Integridade Pós-Processamento
O sistema SHALL / DEVE recalcular o hash SHA-256 de cada mídia após a extração de metadados e atestar formalmente se a integridade foi 100% preservada.

#### Scenario: Sucesso na verificação de integridade
- **WHEN** a extração de metadados é concluída
- **THEN** o sistema compara o SHA-256 final com o inicial e marca o status da evidência como ÍNTEGRO

#### Scenario: Detecção de divergência de integridade
- **WHEN** o hash recalculado após o processamento diferir do hash inicial
- **THEN** o sistema emite alerta crítico de violação de custódia e rejeita a validação da evidência

### Requirement: Extração Segura de Metadados EXIF
O sistema SHALL / DEVE extrair metadados técnicos (data e hora original de captura, fabricante, modelo de câmera e software) exclusivamente em modo de leitura binária sem alterar o arquivo.

#### Scenario: Extração de metadados presentes
- **WHEN** a imagem contém cabeçalho EXIF válido
- **THEN** o sistema extrai DateTimeOriginal, Make e Model para exibição e documentação

#### Scenario: Imagem sem metadados EXIF
- **WHEN** a imagem foi submetida a stripping de metadados ou não possui cabeçalho EXIF
- **THEN** o sistema registra a ausência de metadados sem interromper o fluxo da cadeia de custódia

### Requirement: Conversão e Tratamento de Coordenadas Geodésicas
O sistema SHALL / DEVE converter as coordenadas de GPS presentes no EXIF (graus, minutos e segundos) em graus decimais aplicando sinal negativo para referências Sul (S) e Oeste (W).

#### Scenario: Conversão com sucesso de GPS no Hemisfério Sul
- **WHEN** o EXIF contém dados GPSLatitude e GPSLongitude com referências 'S' e 'W'
- **THEN** o sistema calcula a latitude e longitude decimal com sinal negativo

### Requirement: Mapeamento Interativo e Trajetória Cronológica
O sistema SHALL / DEVE gerar um mapa interativo contendo marcadores para as fotos georreferenciadas e uma linha contínua conectando os pontos na ordem cronológica de captura.

#### Scenario: Renderização de trajeto cronológico
- **WHEN** duas ou mais imagens possuem coordenadas geodésicas e datas de captura válidas
- **THEN** o sistema traça uma linha vetorial interligando os pontos em sequência temporal ascendente

### Requirement: Emissão de Laudo Pericial em Markdown com Hashes Espaçados
O sistema SHALL / DEVE gerar um laudo pericial em formato Markdown contendo os dados periciais, fundamentação legal e blocos com espaçamento amplo e individual para os hashes SHA-256 pré e pós-análise.

#### Scenario: Download do laudo pericial
- **WHEN** o usuário solicita o laudo pericial da análise
- **THEN** o sistema disponibiliza o download de um arquivo Markdown com blocos destacados e espaçados para cada hash de 64 caracteres

### Requirement: Interface Web de Exame Pericial
O sistema SHALL / DEVE disponibilizar interface web construída em HTML/JS e Tailwind CSS permitindo upload simultâneo de até 25 imagens e visualização imediata dos resultados.

#### Scenario: Recepção de lote de evidências na web
- **WHEN** o usuário seleciona ou arrasta até 25 imagens na interface web
- **THEN** a interface submete o lote ao backend FastAPI e exibe o mapa interativo e a tabela de integridade
