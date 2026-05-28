# TCC Energia — Localização Ótima de Usinas Renováveis

Projeto robusto para análise geoespacial e multicritério de locais ótimos para implantação de usinas solares, eólicas e híbridas no Brasil.

## Objetivo
Identificar e ranquear áreas candidatas para novas usinas renováveis considerando:

- potencial solar;
- potencial eólico;
- distância até subestações e linhas de transmissão;
- proximidade de centros de carga/demanda;
- restrições ambientais;
- custo estimado de conexão;
- pesos ajustáveis por cenário.

## Produtos gerados

1. Aplicativo web em Streamlit.
2. Pipeline Python modular.
3. Dados fictícios para teste imediato.
4. Exportação de resultados em CSV, GeoJSON e mapa HTML.
5. Estrutura completa sugerida para TCC.

## Avaliação da stack

A stack atual é adequada para o objetivo do projeto:

- `GeoPandas`, `Shapely` e `PyProj` resolvem bem o processamento vetorial e os cálculos em CRS projetado;
- `Rasterio` é a escolha prática para extrair potencial solar/eólico de rasters GeoTIFF;
- `Streamlit` entrega uma interface simples para ajustar cenários e pesos sem criar uma aplicação web complexa;
- `Folium` funciona bem para mapas interativos exploratórios;
- `Pandas`/`NumPy` são suficientes para ranking, normalização e exportações.

Para um TCC e um protótipo analítico, trocar para uma stack mais pesada, como backend web dedicado, banco espacial ou frontend separado, aumentaria a complexidade sem ganho proporcional. Essas tecnologias só passam a ser necessárias se o projeto evoluir para produção com muitos usuários, dados grandes ou ingestão contínua.

## Execução rápida

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/generate_mock_data.py
streamlit run app/main_streamlit.py
```

## Deploy no Streamlit Cloud

Use `app/main_streamlit.py` como arquivo principal. O projeto mantém apenas `requirements.txt` para o deploy porque o Streamlit Cloud prioriza `environment.yml` quando ele existe no repositório, o que pode deixar a implantação presa na etapa de resolução do ambiente Conda.

O repositório já inclui dados fictícios em `data/raw/` para o primeiro deploy funcionar sem etapa manual de ingestão. Depois, esses arquivos podem ser substituídos pelas bases reais indicadas abaixo.

## Estrutura

```text
TCC_Energia_Robusto/
├── app/
├── src/
├── scripts/
├── config/
├── data/
├── outputs/
├── notebooks/
├── docs/tcc/
├── tests/
└── README.md
```

## Dados reais esperados

| Camada | Formato recomendado | Caminho padrão |
|---|---|---|
| Subestações | GeoJSON/GPKG/SHP | data/raw/ons/subestacoes.geojson |
| Linhas de transmissão | GeoJSON/GPKG/SHP | data/raw/ons/linhas.geojson |
| Irradiância solar | GeoTIFF | data/raw/solar/irradiancia_global.tif |
| Velocidade do vento | GeoTIFF | data/raw/eolico/velocidade_vento.tif |
| Demanda/carga | GeoJSON ou CSV com coordenadas | data/raw/demanda/demanda.geojson |
| Restrições ambientais | GeoJSON/GPKG/SHP | data/raw/restricoes/restricoes.geojson |

## Metodologia resumida

O sistema gera uma malha de pontos candidatos, extrai os valores de potencial solar e eólico dos rasters, calcula distâncias em CRS projetado até rede e demanda, remove ou penaliza áreas restritas e calcula um score multicritério normalizado.

Melhorias metodológicas implementadas:

- normalização min-max com tratamento explícito para critérios sem variação e dados ausentes;
- normalização automática dos pesos informados, mantendo a importância relativa e garantindo score entre 0 e 1;
- cálculo de distância ao elemento mais próximo usando índice espacial (`sjoin_nearest`), mais escalável que medir todos os pontos contra uma geometria unificada;
- política configurável para restrições ambientais: exclusão dos pontos restritos ou penalização do score;
- exportação do indicador `is_restricted` e do fator de penalização para auditoria dos resultados;
- dashboard com distribuição de scores, top candidatos, mapa exportado e pesos normalizados.
