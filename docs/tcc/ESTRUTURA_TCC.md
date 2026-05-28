# Estrutura Completa do TCC

## Título sugerido

**Localização ótima de usinas solares, eólicas e híbridas no Brasil por meio de análise geoespacial multicritério integrada à infraestrutura elétrica**

## Problema de pesquisa

Como identificar regiões tecnicamente mais adequadas para implantação de novas usinas renováveis considerando simultaneamente potencial solar, potencial eólico, infraestrutura elétrica, centros de carga, acesso territorial e restrições ambientais?

## Hipótese

A integração de dados solarimétricos, eólicos, territoriais, de demanda e da rede elétrica permite selecionar áreas candidatas mais viáveis do que análises baseadas apenas no potencial energético isolado.

## Objetivo geral

Desenvolver uma metodologia computacional para identificar e ranquear locais ótimos para implantação de usinas solares, eólicas e híbridas no Brasil, por meio de análise geoespacial multicritério.

## Objetivos específicos

1. Levantar bases geoespaciais de transmissão, subestações, potencial solar, potencial eólico, demanda, rodovias, recursos hídricos, áreas urbanas, declividade, uso do solo e restrições ambientais.
2. Padronizar os dados em sistemas de referência adequados.
3. Gerar uma malha de pontos candidatos.
4. Extrair o potencial energético e territorial de cada ponto candidato.
5. Calcular distâncias até rede elétrica, centros de carga, rodovias, água e áreas urbanas.
6. Aplicar restrições por exclusão ou penalização.
7. Padronizar critérios por funções fuzzy.
8. Aplicar modelo multicritério ponderado para ranquear os pontos.
9. Desenvolver aplicativo interativo em Streamlit para simulação de cenários.
10. Comparar resultados em cenários solar, eólico, híbrido, infraestrutura e ambiental.

## Justificativa

A expansão renovável depende não apenas do potencial de geração, mas também da capacidade de conexão ao sistema elétrico, proximidade dos centros consumidores, acesso territorial e restrições ambientais. Uma metodologia integrada pode apoiar decisões de planejamento, reduzir custos de conexão e melhorar a eficiência da expansão energética.

## Capítulos sugeridos

### 1. Introdução

- Contextualização da matriz elétrica brasileira.
- Crescimento das fontes renováveis.
- Desafio de localização e conexão.
- Problema, hipótese, objetivos e justificativa.

### 2. Revisão bibliográfica

- Planejamento da expansão da geração.
- Energia solar fotovoltaica.
- Energia eólica.
- Sistemas de transmissão e conexão.
- Análise geoespacial aplicada à energia.
- Métodos multicritério: Weighted Overlay, WLC, AHP e TOPSIS.
- Estudos correlatos.

### 3. Materiais e métodos

- Bases de dados utilizadas.
- Tratamento e padronização dos dados.
- Geração da malha candidata.
- Extração de valores raster.
- Cálculo de distâncias em CRS projetado.
- Critérios de viabilidade.
- Normalização fuzzy.
- Modelo de score multicritério.
- Arquitetura do aplicativo.

### 4. Resultados e discussão

- Mapas de potencial solar.
- Mapas de potencial eólico.
- Mapas de proximidade da rede.
- Mapas de aptidão territorial.
- Ranking de áreas candidatas.
- Comparação entre cenários solar, eólico, híbrido, infraestrutura e ambiental.
- Sensibilidade dos pesos.
- Discussão técnica e limitações.

### 5. Conclusão

- Síntese dos resultados.
- Contribuições do trabalho.
- Limitações.
- Trabalhos futuros.

## Fórmula base do score

O score final para cada ponto candidato é calculado por soma ponderada:

```text
S = Σ(w_i * C_i) * F_restricao
```

Onde:

- `C_i`: critério padronizado em escala 0-1;
- `w_i`: peso normalizado do critério;
- `F_restricao`: fator 1 para ponto não restrito ou fator de penalização quando essa política é usada.

Critérios implementados:

- `P_solar`: potencial solar;
- `P_eolico`: potencial eólico;
- `D_rede`: proximidade da rede elétrica;
- `D_carga`: proximidade aos centros de carga;
- `D_rodovia`: proximidade de rodovias;
- `D_agua`: proximidade de recursos hídricos;
- `D_urbano`: afastamento de áreas urbanas;
- `Declividade`: adequação topográfica;
- `Uso_solo`: aptidão territorial.

## Produto tecnológico

O produto tecnológico associado ao TCC é um aplicativo web em Streamlit capaz de:

- carregar bases geoespaciais;
- ajustar pesos por cenário;
- executar análise multicritério;
- visualizar mapa dos melhores locais;
- destacar no mapa o candidato selecionado no ranking;
- exportar ranking em CSV e GeoJSON.

## Limitações reconhecidas

- O custo de infraestrutura é simplificado.
- A capacidade remanescente real das subestações não é considerada por padrão.
- O licenciamento ambiental é representado por restrições espaciais.
- A aptidão de uso do solo depende da qualidade da base utilizada.
- O modelo não substitui estudos elétricos detalhados de fluxo de potência.

## Melhorias futuras

- Inserir capacidade disponível por subestação.
- Usar dados horários de geração e carga.
- Incluir fluxo de potência e restrições elétricas.
- Aplicar AHP formal com matriz de comparação pareada.
- Adicionar análise econômica com LCOE.
- Incluir cenários climáticos futuros.
