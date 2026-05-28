# Metodologia Detalhada

## 1. Entrada de dados

A metodologia utiliza dados vetoriais e raster:

- Subestações: pontos com tensão e localização.
- Linhas de transmissão: geometrias lineares.
- Potencial solar: raster GeoTIFF com irradiância.
- Potencial eólico: raster GeoTIFF com velocidade média do vento.
- Demanda: pontos ou polígonos representando centros de carga.
- Restrições: polígonos de áreas ambientalmente sensíveis.

## 2. Padronização espacial

Os dados são convertidos para:

- `EPSG:4326` para leitura e visualização;
- `EPSG:5880` para cálculo de distâncias em metros no Brasil.

## 3. Geração de pontos candidatos

É gerada uma malha regular sobre a área de estudo. Cada ponto representa uma possível região candidata.

## 4. Extração dos atributos energéticos

Para cada ponto candidato, são extraídos:

- irradiância solar no pixel correspondente;
- velocidade do vento no pixel correspondente.

## 5. Cálculo das distâncias

São calculadas:

- distância até a subestação ou linha mais próxima;
- distância até o centro de carga mais próximo.

As distâncias são calculadas no CRS projetado configurado (`EPSG:5880` por padrão), usando busca espacial do elemento mais próximo. Isso preserva unidades em metros e melhora a escalabilidade quando há muitos pontos candidatos ou muitos elementos de rede.

## 6. Estimativa de custo

O custo de conexão é estimado por:

```text
Custo = distância até rede (km) × custo médio por km
```

## 7. Restrições

A política de restrição ambiental é configurável:

- `exclude`: pontos dentro de áreas restritas são removidos da análise;
- `penalize`: pontos restritos permanecem no ranking, mas recebem um fator multiplicativo de penalização no score final.

A opção `exclude` é mais conservadora para áreas de impedimento legal. A opção `penalize` é útil quando a camada representa sensibilidade ambiental, custo de mitigação ou restrição ainda sujeita a validação.

## 8. Normalização

Cada variável é normalizada entre 0 e 1.

Variáveis benéficas:

- solar;
- vento.

Variáveis de custo:

- distância à rede;
- distância à carga;
- custo de conexão.

Critérios sem variação recebem valor neutro, evitando que uma camada constante domine o resultado. Critérios totalmente ausentes recebem score zero para não favorecer candidatos por falta de informação.

## 9. Score final

O score final é calculado por soma ponderada. Três cenários são implementados:

- Solar;
- Eólico;
- Híbrido.

Os pesos informados em cada cenário são normalizados automaticamente para soma igual a 1. Assim, o usuário pode ajustar valores relativos na interface sem precisar fechar manualmente a soma dos pesos.

## 10. Saídas

- Ranking CSV;
- Ranking GeoJSON;
- Mapa interativo HTML;
- Dashboard Streamlit.
