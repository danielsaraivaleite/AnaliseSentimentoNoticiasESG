import warnings
import pandas as pd
import numpy as np
import datetime  as dt
from scipy import interpolate
import scipy.stats
from matplotlib.dates import YearLocator, MonthLocator, DateFormatter
from noticias_timeline import plota_timeline
from noticias_processamento_texto import remove_acentos, remove_termos_comuns, aplica_stemming_texto, remove_palavras_texto, conta_termos_esg, classifica_texto, classifica_textos_coletados, filtra_noticias_nao_relacionadas, filtra_noticias_sem_classificacao, conta_mencoes_empresas, filtra_citacao_relevante, trim_texto
from vaderSentimentptbr import SentimentIntensityAnalyzer 
from sumarizador_textrankptbr import summarize_text_rank 
import re

'''
Realiza a aplicação do VADER adaptado ao português
'''
def polaridade_sentimento_vaderptbr(texto_completo, titulo, resumir=True):
    
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
    
    
'''
Realiza a ponderação titulo e texto
'''
def pondera_polaridade_titulo_texto(pol_titulo, pol_texto):
    # pondera heuristicamente titulo e texto
    return 0.2 * pol_titulo + 0.8 * pol_texto 
    

'''
Converte a polaridade do VADER em classe, de acordo com o estabelecido pelo autor
https://github.com/cjhutto/vaderSentiment
'''
def classifica_sentimento_vaderptbr(polaridade, label_pos='POS', label_neu='NEU', label_neg='NEG'):
    if polaridade <= 0.05:
        return label_neg
    elif polaridade > 0.05:
        return label_pos
    else:
        return label_neu

# gera a curva de polaridade média - modelo EWMA e interpolação
def gera_curva_polaridade_media(dfNoticiasComPolaridade, empresa, dimensao, maxima_data=None, alfa=0.25):
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
    #dfPolaridade = dfPolaridade.set_index('data_publicacao').groupby([pd.Grouper(freq="Q")]).agg({'polaridade' : 'sum', 'titulo': 'count'})
    dfPolaridade['polaridade'] = dfPolaridade['polaridade'] / dfPolaridade['titulo']
    dfPolaridade = dfPolaridade.sort_index()
    #dfPolaridade = dfPolaridade.interpolate(method='time').
    
    if len(dfPolaridade) <= 5:
        return None
    
    dfPolaridade['polaridade_ewma'] = dfPolaridade.ewm(alpha=alfa).mean()['polaridade']
    c = np.polyfit( np.linspace(0,1,len(dfPolaridade))  , dfPolaridade['polaridade_ewma'], 5) #polinomio grau X
    poly_eqn = np.poly1d(c)
    y_hat = poly_eqn(np.linspace(0,1,len(dfPolaridade)))
    dfPolaridade['polaridade_fit'] = y_hat    
    #dfPolaridade['polaridade_fit'] = dfPolaridade['polaridade_ewma']   
    
    return dfPolaridade



# filtros pos processamento (exclusoes)
def filtrar_noticias_pos_coleta(dfNoticias):
    dfFiltrado = filtra_citacao_relevante(noticias=dfNoticias, empresa='', listagem_empresas=[], threshold=1.1, aceitar_titulo=False, recalcular_contagem=False)
    dfFiltrado = dfFiltrado[dfFiltrado['empresa'] != 'sao carlos'] # termos comuns demais
    dfFiltrado = dfFiltrado[dfFiltrado['classificacao'] != 'Outros'] # nao relacionadas a ESG

    dfPadroesExcluir = pd.read_excel('datasets/palavras_chave_excluir_empresa.xlsx')
    dfFiltrado['excluir_texto'] = False
    dfFiltrado['excluir_titulo'] = False

    padrao = ''
    for emp in dfPadroesExcluir['empresa'].unique():
        lista_termos = list(  (dfPadroesExcluir[ dfPadroesExcluir['empresa'] == emp]['termo_excludente'].str.lower()) )
        lista_termos = [remove_acentos(t) for t in lista_termos]
        #lista_termos = [re.escape(t) for t in lista_termos]
        padrao = '|'.join(  lista_termos  ) 
        
        # filtra termos que sao associados incorretamente com uma empresa e sao falsos relevantes no texto
        dfFiltrado['excluir_texto'] =  ((dfFiltrado['excluir_texto']) | ((dfFiltrado['empresa'] == emp) & (dfFiltrado['texto_completo'].apply(remove_acentos).str.lower().str.contains(padrao, regex=True))))

        # filtra termos que sao associados incorretamente com uma empresa e sao falsos relevantes no titulo
        dfFiltrado['excluir_titulo'] =  ((dfFiltrado['excluir_titulo']) | ((dfFiltrado['empresa'] == emp) & (dfFiltrado['titulo'].apply(remove_acentos).str.lower().str.contains(padrao, regex=True))))
        
    
    dfFiltrado = dfFiltrado[~ dfFiltrado['excluir_texto'] ] 
    del dfFiltrado['excluir_texto']
    
    dfFiltrado = dfFiltrado[~ dfFiltrado['excluir_titulo'] ] 
    del dfFiltrado['excluir_titulo']
    
    return dfFiltrado



