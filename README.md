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

## Execução rápida

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/generate_mock_data.py
streamlit run app/main_streamlit.py
```

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

O sistema gera uma malha de pontos candidatos, extrai os valores de potencial solar e eólico dos rasters, calcula distâncias geodésicas até rede e demanda, remove ou penaliza áreas restritas e calcula um score multicritério normalizado.

