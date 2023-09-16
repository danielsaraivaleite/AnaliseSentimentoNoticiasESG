# Análise de sentimento sobre notícias ESG
Trabalho de conclusão de curso da USP-ESALQ referente ao tema de analise de sentimento sobre notícias do tema ESG

## Resumo

O tema ESG (“Environmental, Social and Governance”) vem ganhando importância no Brasil e no mundo. Nos últimos anos, diversas empresas tem buscado divulgar aos seus “stakeholders” que investem no tema e que são sustentáveis. Em paralelo, ferramentas tem surgido para avaliar o grau de aderência às práticas ESG dessas empresas, mas ainda existem disparidades metodológicas e assimetria de informação. É nesse contexto em que este trabalho se insere, ao propor a utilização de um algoritmo para analisar o sentimento sobre as notícias divulgadas de uma empresa, de forma a classificar sua avaliação ESG. O algoritmo proposto foi implementado e disponibilizado publicamente, e aplicado em uma coleção de textos jornalísticos extraídos da Internet para as empresas brasileiras listadas na B3. As classificações obtidas foram comparados com rankings ESG existentes, e também tiveram seu comportamento avaliado em estudos de caso. Os resultados sugerem que a abordagem proposta não é substituta em relação à avaliação tradicional, mas é complementar e útil por sua tempestividade.

## Funcionamento do algoritmo
O algoritmo tem a seguinte lógica e passos:

- As notícias foram previamente coletadas de diversas fontes, utilizando o GoogleNews. Foram selecionadas apenas as notícias que continham termos relacionados aos assuntos ESG
- São excluídos textos que versavam sobre mais de uma empresa.
- Cada notícia é classificada entre em uma das dimensões - E, S ou G - de acordo com a maior ocorrência de termos.
- É aplicada uma versão adaptada e enriquecida para o Português do algoritmo VADER. Este algoritmo utiliza um conjunto de heuristicas e um grande léxico para determinar o sentimento de cada texto, atribuindo um score (polaridade), que vai de -1 (mais negativo) até +1 (mais positivo). Ao redor de 0, o sentimento é considerado neutro.
- É calculada uma curva de polaridade média para cada empresa no tempo, representando o sentimento médio das notícias. A curva é tratada com o modelo de média móvel EWMA.

- As notícias foram previamente coletadas de diversas fontes, utilizando o GoogleNews. Foram selecionadas apenas as notícias que continham termos relacionados aos assuntos ESG
- São excluídos textos que versavam sobre mais de uma empresa.
- Cada notícia é classificada entre em uma das dimensões - E, S ou G - de acordo com um algoritmo de aprendizado de máquina semi-supervisionado .
- É aplicada uma versão adaptada e enriquecida para o Português do algoritmo VADER. Este algoritmo utiliza um conjunto de heuristicas e um grande léxico para determinar o sentimento de cada texto, atribuindo um score (polaridade), que vai de -1 (mais negativo) até +1 (mais positivo). Ao redor de 0, o sentimento é considerado neutro.
- É calculada uma curva de polaridade média para cada empresa no tempo, representando o sentimento médio das notícias. A curva é tratada com o modelo de média móvel EWMA

## Arquitetura

### Etapa de coleta das notícias

![image](https://github.com/danielsaraivaleite/AnaliseSentimentoNoticiasESG/assets/131724461/0f577fee-58e1-4bc6-9480-938da02e692d)

### Construção do classificador ESG (com aprendizado de máquina)

![image](https://github.com/danielsaraivaleite/AnaliseSentimentoNoticiasESG/assets/131724461/60d20a11-1bba-4107-bc15-5fda517dce5f)

### Adaptação do algortimo do VADER ao português

![image](https://github.com/danielsaraivaleite/AnaliseSentimentoNoticiasESG/assets/131724461/0027eafd-a894-44f1-b798-86d3a439ecc0)

### Validação do algortimo do VADER com outras fontes de dados

![image](https://github.com/danielsaraivaleite/AnaliseSentimentoNoticiasESG/assets/131724461/b55f17a8-a63b-463f-87f6-12e76fe290c6)

### Aplicação da análise de sentimento às notícias ESG e resultados

![image](https://github.com/danielsaraivaleite/AnaliseSentimentoNoticiasESG/assets/131724461/781b339d-0edc-496f-8450-a3c9477186ac)
