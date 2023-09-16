'''
Módulo de grafico de wordcloud das noticias
Autor: Daniel Saraiva Leite - 2023
Projeto Análise de sentimentos sobre notícias do tema ESG
Trabalho de conclusão de curso - MBA Digital Business USP Esalq'
'''

import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from nltk.corpus import stopwords 
import nltk
import re
from noticias_processamento_texto import lista_stopwords_classificador_esg, lematizador

nltk.download('stopwords')
sw = stopwords.words('portuguese')
sw.append('empresa')
sw.append('empresas')
sw.append('companhia')
sw.append('mercado')
sw.append('ainda')
sw.append('cliente')
sw.append('disse')
sw.append('investimento')
sw.append('negócio')
sw.append('brasil')
sw.append('banco')
sw.append('produto')
sw = sw+lista_stopwords_classificador_esg()

def plotar_word_cloud(df, empresa, dimensao, arquivo = 'images/wordcloud.png', lematizar=False):
    '''
    Plota o wordcloud para noticias de uma unica empresa
    '''
    text = ''
    text=df['texto_completo'].str.cat(sep=' ')
    text=text.lower()
    text=' '.join([word for word in text.split()])
    if text is None or text == '':
        text = 'sem ocorrências'
    if lematizar:
        text = lematizador(text)

    for w in empresa.split(' '):
        text = re.sub(r'\b' + w + r'\b', '', text)

    wordcloud = WordCloud(max_font_size=50, max_words=100, background_color="white", stopwords = sw).generate(text)
    plt.figure(figsize=(10,5))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.savefig(arquivo, bbox_inches='tight')
    plt.show()
    