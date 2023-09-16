'''
Módulo que implementa o modelo de avaliação de sentimentos aplicado as noticias ESG
Autor: Daniel Saraiva Leite - 2023
Projeto Análise de sentimentos sobre notícias do tema ESG
Trabalho de conclusão de curso - MBA Digital Business USP Esalq
'''


import warnings
import pandas as pd
import numpy as np
import datetime  as dt
from scipy import interpolate
import scipy.stats
from scipy.interpolate import make_interp_spline
from matplotlib.dates import YearLocator, MonthLocator, DateFormatter
from noticias_timeline import plota_timeline
from noticias_processamento_texto import *
from vaderSentimentptbr import SentimentIntensityAnalyzer 
from sumarizador_textrankptbr import summarize_text_rank 
import re


def polaridade_sentimento_vaderptbr(texto_completo, titulo, resumir=True):
    '''
    Realiza a aplicação do VADER adaptado ao português
    '''
    
    s = SentimentIntensityAnalyzer() 
    if resumir:
        resumo = summarize_text_rank(texto_completo, compression=0.8, include_first_parag=True)
    else:
        resumo = texto_completo
        
    pol_texto = s.polarity_scores(resumo)['compound'] 
    
    if titulo is None:
        return pol_texto
    else:
        pol_titulo = s.polarity_scores(titulo)['compound'] 
        # pondera heuristicamente titulo e texto
        return pondera_polaridade_titulo_texto(pol_titulo, pol_texto)
    
    

def pondera_polaridade_titulo_texto(pol_titulo, pol_texto):
    '''
    Realiza a ponderação titulo e texto para calculo da polaridade do texto
    '''
    # pondera heuristicamente titulo e texto
    return 0.2 * pol_titulo + 0.8 * pol_texto 
    


def classifica_sentimento_vaderptbr(polaridade, label_pos='POS', label_neu='NEU', label_neg='NEG', threshold=0.05):
    '''
    Converte a polaridade do VADER em classe, de acordo com o estabelecido pelo autor
    https://github.com/cjhutto/vaderSentiment
    '''
    if polaridade < -1*threshold:
        return label_neg
    elif polaridade > threshold:
        return label_pos
    else:
        return label_neu

    

def gera_curva_polaridade_media(dfNoticiasComPolaridade, empresa, dimensao, maxima_data=None, alfa=0.1, grau_polinomio=5):
    '''
    Gera a curva de polaridade média - modelo EWMA e interpolação
    '''
    dfPolaridade = dfNoticiasComPolaridade
    
    if maxima_data is not None:
        dfPolaridade = dfPolaridade[dfPolaridade['data_publicacao'].dt.date <= maxima_data]
    
    if empresa != '':
        dfPolaridade = dfPolaridade[dfPolaridade['empresa'] == empresa]
    if dimensao != '' and dimensao != 'ESG':
        dfPolaridade = dfPolaridade[dfPolaridade['classificacao'] == dimensao]
        
    dfPolaridade['data_publicacao'] = pd.to_datetime(pd.to_datetime(dfPolaridade['data_publicacao']).dt.date)
    
    dfPolaridade = dfPolaridade.set_index('data_publicacao')
    dfPolaridade = dfPolaridade.groupby(by='data_publicacao').agg({'polaridade' : 'sum', 'titulo': 'count'})
    
    #dfPolaridade = dfPolaridade.set_index('data_publicacao').groupby([pd.Grouper(freq="D")]).agg({'polaridade' : 'sum', 'titulo': 'count'})
    dfPolaridade['polaridade'] = dfPolaridade['polaridade'] / dfPolaridade['titulo']
    dfPolaridade = dfPolaridade.sort_index()
    #dfPolaridade['polaridade'] = dfPolaridade.interpolate(method='time')['polaridade']
    
    if len(dfPolaridade) <= grau_polinomio:
        return None
    
    dfPolaridade['polaridade_ewma'] = dfPolaridade.ewm(alpha=alfa, adjust=True).mean()['polaridade']
 
    #c = np.polyfit( np.linspace(0,1,len(dfPolaridade))  , dfPolaridade['polaridade_ewma'], grau_polinomio) #polinomio grau X
    #poly_eqn = np.poly1d(c)
    #y_hat = poly_eqn(np.linspace(0,1,len(dfPolaridade)))
    #dfPolaridade['polaridade_fit'] = y_hat    
    
    dfPolaridade['polaridade_fit'] = dfPolaridade['polaridade_ewma']   
    

    return dfPolaridade



def filtrar_noticias_pos_coleta(dfNoticias):
    '''
    Filtros pos processamento (exclusoes) 
    O filtro serve para classificar fontes incorretas, empresas que tem termos comuns no seu nome
    e tambem noticias nao relacionadas aos temas E S ou G
    '''
    dfFiltrado = filtra_citacao_relevante(noticias=dfNoticias, empresa='', listagem_empresas=[], threshold=1.1, aceitar_titulo=False, recalcular_contagem=False)

    # filtra noticias nao relacionadas a ESG
    dfFiltrado = dfFiltrado[dfFiltrado['fonte'].str.lower() != 'Partido Comunista Brasileiro'.lower()] 
    dfFiltrado = dfFiltrado[dfFiltrado['fonte'].str.lower() != 'JDV - Jornal do Vale do Itapocu'.lower()] 
    dfFiltrado = dfFiltrado[dfFiltrado['fonte'].str.lower() != 'TJDFT'.lower()] 
    dfFiltrado = dfFiltrado[dfFiltrado['fonte'].str.lower() != 'Hotelier News'.lower()] 
    dfFiltrado = dfFiltrado[dfFiltrado['fonte'].str.lower() != 'Rede Brasil Atual'.lower()] 
    dfFiltrado = dfFiltrado[dfFiltrado['fonte'].str.lower() != 'MPF'.lower()] 
    dfFiltrado = dfFiltrado[dfFiltrado['fonte'].str.lower() != 'braskem.com.br'.lower()] 
    dfFiltrado = dfFiltrado[dfFiltrado['fonte'].str.lower() != 'PT'.lower()] 
    dfFiltrado = dfFiltrado[dfFiltrado['fonte'].str.lower() != 'Engeplus'.lower()] 
    dfFiltrado = dfFiltrado[dfFiltrado['fonte'].str.lower() != 'Gerdau'.lower()] 
    dfFiltrado = dfFiltrado[dfFiltrado['fonte'].str.lower() != 'Boatos.org'.lower()] 
    dfFiltrado = dfFiltrado[dfFiltrado['fonte'].str.lower() != 'Revista Hotéis'.lower()] 
    dfFiltrado = dfFiltrado[dfFiltrado['fonte'].str.lower() != 'PANROTAS'.lower()] 
    dfFiltrado = dfFiltrado[dfFiltrado['fonte'].str.lower() != 'bomdia.eu'] 
    
    
    
   
    dfFiltrado = dfFiltrado[~ ((dfFiltrado['fonte'].str.lower() == 'b3') &  (dfFiltrado['empresa'].str.lower() == 'b3'))     ] 
    
    
    # Outros - remove noticias com classificacao outros apos aplicacao do modelo de ML
    dfFiltrado = dfFiltrado[dfFiltrado['classificacao'] != 'Outros'] 
    
    
    # termos a excluir
    termos_excluir = ['nesta entrevista exclusiva', 'as ações que são apostas', 'morre o empresário', 
                      'morre o ex-', 'morre aos', 'você pode assistir aqui', 'black friday', 
                     'loja em metaverso', 'loja no metaverso', 'inaugura loja em', 'rock in rio',
                     'confira as vagas de emprego', 'frases de luiz barsi', 
                     'e mais empresas com vagas abertas', 'confira mais vagas em', 'veja mais vagas abertas em', 
                     'quarta-feira de cinzas', 'carnaval', 'o que abre e o que fecha']
    for t in termos_excluir:
        dfFiltrado = dfFiltrado[~dfFiltrado['texto_completo'].str.lower().str.contains(t)]
        
    for t in termos_excluir:
        dfFiltrado = dfFiltrado[~dfFiltrado['titulo'].str.lower().str.contains(t)]
    
   

    # trata empresas que estao associadas a termos genericos sem relacao com ela
    dfPadroesExcluir = pd.read_excel('datasets/palavras_chave_excluir_empresa.xlsx')
    dfFiltrado['excluir_texto'] = False
    dfFiltrado['excluir_titulo'] = False

    padrao = ''
    for emp in dfPadroesExcluir['empresa'].unique():
        lista_termos = list(  (dfPadroesExcluir[ dfPadroesExcluir['empresa'] == emp]['termo_excludente'].str.lower()) )
        lista_termos = [remove_acentos(t) for t in lista_termos]
        padrao = '|'.join(  lista_termos  ) 
        
        # filtra termos que sao associados incorretamente com uma empresa e sao falsos relevantes no texto
        dfFiltrado['excluir_texto'] =  ((dfFiltrado['excluir_texto']) | ((dfFiltrado['empresa'] == emp) & (dfFiltrado['texto_completo'].apply(remove_acentos).str.lower().str.contains(padrao, regex=True))))

        # filtra termos que sao associados incorretamente com uma empresa e sao falsos relevantes no titulo
        dfFiltrado['excluir_titulo'] =  ((dfFiltrado['excluir_titulo']) | ((dfFiltrado['empresa'] == emp) & (dfFiltrado['titulo'].apply(remove_acentos).str.lower().str.contains(padrao, regex=True))))
        
    
    dfFiltrado = dfFiltrado[~ dfFiltrado['excluir_texto'] ] 
    del dfFiltrado['excluir_texto']
    
    dfFiltrado = dfFiltrado[~ dfFiltrado['excluir_titulo'] ] 
    del dfFiltrado['excluir_titulo']

    # trata empresas que estao associadas a termos genericos, e que precisam de lista de palavras pra detecta-las
    # exemplo azul linhas aereas, ao buscar apenas por azul retorna-se muitas noticias nao relacionadas
    dfPadroesExcluir = pd.read_excel('datasets/palavras_chave_incluir_empresa.xlsx')
    dfFiltrado['excluir_texto'] = False

    padrao = ''
    for emp in dfPadroesExcluir['empresa'].unique():
        lista_termos = list(  (dfPadroesExcluir[ dfPadroesExcluir['empresa'] == emp]['termo_includente'].str.lower()) )
        lista_termos = [remove_acentos(t) for t in lista_termos]
        padrao = "|".join(  [r'\b' + x + r'\b' for x in lista_termos] )

            
        dfFiltrado['excluir_texto'] =  ((dfFiltrado['excluir_texto']) | ((dfFiltrado['empresa'] == emp) & (~dfFiltrado['texto_completo'].apply(remove_acentos).str.lower().str.contains(padrao, regex=True))))
    
    dfFiltrado = dfFiltrado[~ dfFiltrado['excluir_texto'] ] 
    del dfFiltrado['excluir_texto']
    
    dfFiltrado = dfFiltrado.reset_index(drop=True).drop_duplicates().reset_index(drop=True)
    
    
    return dfFiltrado



