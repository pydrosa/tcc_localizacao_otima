# Estrutura Completa do TCC

## Título sugerido
**Localização ótima de usinas solares e eólicas no Brasil por meio de análise geoespacial multicritério integrada à infraestrutura elétrica**

## Problema de pesquisa
Como identificar regiões tecnicamente mais adequadas para implantação de novas usinas renováveis considerando simultaneamente potencial solar/eólico, proximidade da rede elétrica, centros de carga e restrições ambientais?

## Hipótese
A integração de dados solarimétricos, eólicos, de demanda e da rede elétrica permite selecionar áreas candidatas mais viáveis do que análises baseadas apenas no potencial energético isolado.

## Objetivo geral
Desenvolver uma metodologia computacional para identificar e ranquear locais ótimos para implantação de usinas solares, eólicas e híbridas no Brasil, por meio de análise geoespacial e multicritério.

## Objetivos específicos
1. Levantar bases geoespaciais de transmissão, subestações, potencial solar, potencial eólico, demanda e restrições ambientais.
2. Padronizar os dados em sistema de referência geográfica/projetada adequado.
3. Gerar uma malha de pontos candidatos.
4. Extrair o potencial energético de cada ponto candidato.
5. Calcular distâncias até rede elétrica e centros de carga.
6. Estimar custo de conexão simplificado.
7. Aplicar modelo multicritério ponderado para ranquear os pontos.
8. Desenvolver aplicativo interativo em Streamlit para simulação de cenários.
9. Validar os resultados por cenários solar, eólico e híbrido.

## Justificativa
A expansão renovável depende não apenas do potencial de geração, mas também da capacidade de conexão ao sistema elétrico e da proximidade dos centros consumidores. Uma metodologia integrada pode apoiar decisões de planejamento, reduzir custos de conexão e melhorar a eficiência da expansão energética.

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
- Métodos multicritério: Weighted Overlay, AHP, TOPSIS.
- Estudos correlatos.

### 3. Materiais e métodos
- Bases de dados utilizadas.
- Tratamento e padronização dos dados.
- Geração da malha candidata.
- Extração de valores raster.
- Cálculo de distância geodésica/projetada.
- Critérios de viabilidade.
- Modelo de score multicritério.
- Arquitetura do aplicativo.

### 4. Resultados e discussão
- Mapas de potencial solar.
- Mapas de potencial eólico.
- Mapas de proximidade da rede.
- Ranking de áreas candidatas.
- Comparação entre cenários solar, eólico e híbrido.
- Sensibilidade dos pesos.
- Discussão técnica e limitações.

### 5. Conclusão
- Síntese dos resultados.
- Contribuições do trabalho.
- Limitações.
- Trabalhos futuros.

## Fórmula base do score

O score final para cada ponto candidato pode ser definido como:

```text
S = w1 * P_solar + w2 * P_eolico + w3 * D_rede + w4 * D_carga + w5 * C_conexao
```

Onde:

- `P_solar`: potencial solar normalizado;
- `P_eolico`: potencial eólico normalizado;
- `D_rede`: score de proximidade à rede;
- `D_carga`: score de proximidade aos centros de carga;
- `C_conexao`: score de menor custo de conexão;
- `w`: pesos definidos pelo cenário.

## Produto tecnológico
O produto tecnológico associado ao TCC é um aplicativo web em Streamlit capaz de:

- carregar bases geoespaciais;
- ajustar pesos por cenário;
- executar análise multicritério;
- visualizar mapa dos melhores locais;
- exportar ranking em CSV e GeoJSON.

## Limitações reconhecidas
- O custo de conexão é simplificado.
- A capacidade remanescente real das subestações não é considerada por padrão.
- O licenciamento ambiental é representado apenas por restrições espaciais.
- O modelo não substitui estudos elétricos detalhados de fluxo de potência.

## Melhorias futuras
- Inserir capacidade disponível por subestação.
- Usar dados horários de geração e carga.
- Incluir fluxo de potência e restrições elétricas.
- Aplicar AHP/TOPSIS formal.
- Adicionar análise econômica com LCOE.
- Incluir cenários climáticos futuros.
