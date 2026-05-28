# Metodologia Detalhada

## 1. Entrada de dados

A metodologia utiliza dados vetoriais e raster:

- subestações e linhas de transmissão;
- potencial solar em raster GeoTIFF;
- potencial eólico em raster GeoTIFF;
- demanda ou centros de carga;
- rodovias;
- recursos hídricos;
- áreas urbanas;
- declividade em raster;
- aptidão do uso do solo em raster;
- restrições ambientais ou legais.

## 2. Padronização espacial

Os dados são lidos no CRS de origem e convertidos para:

- `EPSG:4326` na visualização e na amostragem dos rasters mock;
- `EPSG:5880` nos cálculos de distância.

O uso de CRS projetado evita medir distâncias em graus geográficos.

## 3. Pontos candidatos

É gerada uma malha regular sobre a área de estudo. Cada ponto representa uma região candidata. O espaçamento da malha é configurável na interface e no arquivo `config/config.yaml`.

## 4. Restrições

A camada de restrições pode ser tratada de duas formas:

- `exclude`: remove pontos dentro de áreas restritas;
- `penalize`: mantém os pontos, mas multiplica o score por um fator de penalização.

A opção `exclude` é a recomendada quando a camada representa impedimento legal ou ambiental forte. A opção `penalize` é útil para camadas de sensibilidade ou incerteza.

## 5. Critérios avaliados

Os critérios implementados são:

- maior irradiância solar;
- maior velocidade média do vento;
- menor distância à rede elétrica;
- menor distância à demanda;
- menor distância a rodovias;
- menor distância a recursos hídricos quando houver peso para esse critério;
- maior afastamento de áreas urbanas;
- menor declividade;
- maior aptidão do uso do solo.

O custo de infraestrutura é exportado e pode ser usado como critério, mas os cenários padrão evitam dar peso simultâneo ao custo e às distâncias que formam esse custo para não duplicar o mesmo efeito.

## 6. Padronização fuzzy

Cada critério é convertido para escala 0-1 com funções fuzzy lineares e limites configuráveis:

- critérios de benefício, como solar e vento, crescem de 0 a 1;
- critérios de custo, como distância e declividade, decrescem de 1 a 0;
- distância urbana cresce de 0 a 1, pois o afastamento reduz conflito de uso.

Essa abordagem é mais estável que min-max puro, pois o score não depende apenas dos valores extremos do conjunto carregado.

## 7. Soma ponderada

O score final é calculado por Weighted Linear Combination:

```text
score = soma(peso_normalizado_i * criterio_i) * fator_restricao
```

Os pesos são normalizados automaticamente para soma 1. Isso permite testar cenários sem exigir que o usuário feche a soma manualmente.

## 8. Cenários

Os cenários implementados são:

- `solar`;
- `eolico`;
- `hibrido`;
- `infraestrutura`;
- `ambiental`.

O cenário híbrido é o principal para o objetivo do trabalho porque combina potencial solar, potencial eólico, infraestrutura e aptidão territorial.

## 9. Classificação

Além do score contínuo 0-1, o modelo calcula uma classe de aptidão de 1 a 9:

```text
classe = teto(score * 9)
```

Essa classe facilita a leitura cartográfica e a comparação entre áreas.

## 10. Saídas

O pipeline gera:

- ranking CSV;
- ranking GeoJSON;
- mapa HTML;
- dashboard Streamlit com gráficos, tabela selecionável e mapa com destaque do candidato selecionado.
