# TCC Energia - Localização Ótima de Usinas Renováveis

Projeto para análise geoespacial e multicritério de locais candidatos à implantação de usinas solares, eólicas e híbridas no Brasil.

## Objetivo

Identificar e ranquear áreas candidatas considerando:

- potencial solar;
- potencial eólico;
- proximidade da rede elétrica;
- proximidade de centros de carga;
- acesso rodoviário;
- acesso a recursos hídricos quando aplicável;
- afastamento de áreas urbanas;
- declividade;
- aptidão do uso do solo;
- restrições ambientais;
- custo estimado de infraestrutura.

## Stack

A stack atual continua adequada para o objetivo do TCC:

- `GeoPandas`, `Shapely` e `PyProj` para processamento vetorial e cálculo de distâncias em CRS projetado;
- `Rasterio` para amostrar rasters de irradiância, vento, declividade e aptidão territorial;
- `Streamlit` para uma interface simples de cenários e pesos;
- `PyDeck` para mapa interativo no app, com visualização por pontos ou mapa de calor e destaque do candidato selecionado no ranking;
- `Folium` para exportação de mapa HTML;
- `Pandas`, `NumPy` e `Plotly` para ranking, scoring e gráficos.

Trocar para banco espacial, backend web separado ou frontend dedicado só faz sentido se o projeto evoluir para produção com dados muito grandes, múltiplos usuários ou ingestão contínua.

## Execução rápida

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/generate_mock_data.py
streamlit run app/main_streamlit.py
```

## Deploy no Streamlit Cloud

Use `app/main_streamlit.py` como **Main file path**.

O repositório usa `requirements.txt`. Não mantenha `environment.yml` no repositório, porque o Streamlit Cloud prioriza esse arquivo e pode ficar preso na resolução Conda.

No primeiro boot, se os caminhos esperados em `data/raw/` não existirem, o app gera dados mock sem sobrescrever arquivos reais já presentes.

## Metodologia

A metodologia implementada segue uma análise multicritério espacial com Weighted Linear Combination (WLC), compatível com a lógica SIG + AHP discutida na literatura, mas adaptada ao objetivo deste trabalho: avaliar potencial solar e eólico, inclusive em cenários híbridos.

Fluxo:

1. Carregamento das camadas vetoriais e raster.
2. Conversão para CRS projetado (`EPSG:5880`) nos cálculos de distância.
3. Geração de malha regular de pontos candidatos.
4. Exclusão ou penalização de pontos em áreas restritas.
5. Amostragem dos rasters de solar, vento, declividade e aptidão do uso do solo.
6. Cálculo de distâncias à rede, demanda, rodovias, água e áreas urbanas.
7. Padronização fuzzy dos critérios para escala 0-1.
8. Soma ponderada dos critérios conforme cenário.
9. Classificação de aptidão em escala 1-9 e exportação do ranking.

## Cenários

- `solar`: prioriza irradiância e viabilidade territorial.
- `eolico`: prioriza velocidade do vento e viabilidade territorial.
- `hibrido`: equilibra solar, vento e infraestrutura.
- `infraestrutura`: prioriza conexão, demanda e acesso.
- `ambiental`: prioriza uso do solo, declividade e afastamento urbano.

## Dados reais esperados

| Camada | Formato recomendado | Caminho padrão |
|---|---|---|
| Subestações | GeoJSON/GPKG/SHP | `data/raw/ons/subestacoes.geojson` |
| Linhas de transmissão | GeoJSON/GPKG/SHP | `data/raw/ons/linhas.geojson` |
| Irradiância solar | GeoTIFF | `data/raw/solar/irradiancia_global.tif` |
| Velocidade do vento | GeoTIFF | `data/raw/eolico/velocidade_vento.tif` |
| Demanda/carga | GeoJSON/GPKG/SHP | `data/raw/demanda/demanda.geojson` |
| Rodovias | GeoJSON/GPKG/SHP | `data/raw/infra/rodovias.geojson` |
| Recursos hídricos | GeoJSON/GPKG/SHP | `data/raw/hidrografia/recursos_hidricos.geojson` |
| Áreas urbanas | GeoJSON/GPKG/SHP | `data/raw/urbano/areas_urbanas.geojson` |
| Declividade | GeoTIFF | `data/raw/topografia/declividade_percent.tif` |
| Aptidão do uso do solo | GeoTIFF | `data/raw/uso_solo/aptidao_solo.tif` |
| Restrições ambientais | GeoJSON/GPKG/SHP | `data/raw/restricoes/restricoes.geojson` |

## Saídas

- Ranking CSV;
- Ranking GeoJSON;
- mapa HTML;
- dashboard Streamlit com seleção no ranking, destaque do ponto no mapa, mapa de calor e explicação metodológica no fim da página.
