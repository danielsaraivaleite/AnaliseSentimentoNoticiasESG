import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mp
import seaborn as sns
import datetime  as dt
from scipy import interpolate
import scipy.stats
from matplotlib.dates import YearLocator, MonthLocator, DateFormatter
from noticias_timeline import plota_timeline
from noticias_processamento_texto import remove_acentos, remove_termos_comuns, aplica_stemming_texto, remove_palavras_texto, conta_termos_esg, classifica_texto, classifica_textos_coletados, filtra_noticias_nao_relacionadas, filtra_noticias_sem_classificacao, conta_mencoes_empresas, filtra_citacao_relevante, trim_texto
from vaderSentimentptbr import SentimentIntensityAnalyzer 
from sumarizador_textrankptbr import summarize_text_rank 
from analise_sentimento_modelo import filtrar_noticias_pos_coleta, gera_curva_polaridade_media, pondera_polaridade_titulo_texto
import re


def plota_timeline_polaridade(dfEmpresa, sinal, numero_noticias=2, empresa='', imprime=True, arquivo=''):
    plt.style.use('seaborn-white')
    desc = ''
    dfTimeline = dfEmpresa
    if sinal >0:
        dfTimeline = dfEmpresa[dfEmpresa['polaridade'] > 0]
        desc = 'positivas'
    else:
        dfTimeline = dfEmpresa[dfEmpresa['polaridade'] < 0]
        desc = 'negativas'

    dfTimeline = dfTimeline.sort_values('polaridade',ascending = False).groupby(dfTimeline.data_publicacao.dt.date).head(1).sort_values(by='data_publicacao')
    dfTimeline = dfTimeline.sort_values('polaridade',ascending = False).groupby(dfTimeline.data_publicacao.dt.year).head(numero_noticias).sort_values(by='data_publicacao')
    dates = list(dfTimeline['data_publicacao'].dt.date)
    labels = list(dfTimeline.apply(lambda row : row['titulo'] + ' [' + row['classificacao']   + ' ' + '{:.2f}'.format(row['polaridade']) +   ']'    , axis=1))
    labels = [trim_texto(l) for l in labels]

    if imprime:
        for d, l in zip(dates, labels):
            print(d.strftime("%d/%m/%Y") + ": " + l)

    plota_timeline(dates, labels, 'Timeline de amostra de noticias ' + desc + ' para empresa '+ empresa.capitalize() + ' (2 notícias/ano)', arquivo)
    
    
    
def plota_polaridade_media(df, empresa, arquivo=''):

    # plota grafico polaridade media
    plt.style.use('seaborn-dark')

    ldfVisoesESG = [gera_curva_polaridade_media(df, empresa, 'ESG')]
    llabelVisoesESG = ['ESG Geral']

    for l in 'ESG':
        ldfVisoesESG.append( gera_curva_polaridade_media(df, empresa, l)  )
        llabelVisoesESG.append(l)

    # plotando o gráfico com a interpolação
    fig, ax = plt.subplots(2,2, figsize=(8, 6), sharex=True, sharey=True)
    l = 0
    for i in range(0,2):
        for j in range (0,2):
            if ldfVisoesESG[l] is not None and len(ldfVisoesESG[l]) > 0:
                ax[i,j].plot(ldfVisoesESG[l].index, ldfVisoesESG[l]['polaridade_fit'], label='Interpolação', color='green', linewidth=1)
                #ax[i,j].plot(ldfVisoesESG[l].index, ldfVisoesESG[l]['polaridade_ewma'], label='EWMA', color='black', linewidth=0.4)
                ax[i,j].scatter(ldfVisoesESG[l].index, ldfVisoesESG[l]['polaridade'], label='Ponto', s=2, color='blue', linewidth=0.2)
                # ajustando o visual do gráfico
                ax[i,j].set_title(llabelVisoesESG[l], fontsize=10)
                ax[i,j].tick_params(axis='x', labelrotation=90)
                ax[i,j].xaxis.set_major_locator(YearLocator() )
                ax[i,j].xaxis.set_major_formatter(DateFormatter('%Y'))
                ax[i,j].xaxis.set_minor_locator(MonthLocator())
            l = l+1
    plt.tight_layout()
    plt.ylim(-1, 1)
    fig.suptitle('Termômetro de polaridade das notícias da empresa '+empresa.capitalize()+' [-1 negativo, 0 neutro, +1 positivo]', y=1.01)
    plt.savefig(arquivo, bbox_inches='tight')
    plt.show()

    
def plotar_descricao_base(df, plotar_histograma=False, arquivo=''):
    sns.set_style("white")
    # agrupando por fonte, dimensao e datas
    dfFontes  = df.groupby("fonte").count().reset_index(drop=False)
    dfFontes['fonte'] = dfFontes.apply(lambda row : 'Outros' if row['titulo'] < 0.03 * np.sum(dfFontes['titulo']) else row['fonte'] , axis=1)
    dfFontes  = dfFontes.groupby("fonte").sum() 
    dfDimensoes  = df.groupby("classificacao").count()
    dfAnos = df.set_index("data_publicacao").groupby([pd.Grouper(freq="Y")]).count().sort_index()
    dfEmpresas  = df.groupby("empresa").count().sort_values(by=['titulo'], ascending=False).reset_index(drop=False)

    plt.figure(figsize = (10, 6))
    plt.subplot(2, 2, 1)
    plt.pie(dfFontes['titulo'], labels=dfFontes.index, autopct=lambda p: '{:.0f}'.format(p * np.sum(dfFontes['titulo']) / 100),  textprops={'fontsize': 8})
    plt.title('Distribuição por veículo (Total = '  + str(np.sum(dfFontes['titulo']))+ ')' )

    plt.subplot(2, 2, 2)
    plt.pie(dfDimensoes['titulo'], labels=dfDimensoes.index, autopct=lambda p: '{:.0f}'.format(p * np.sum(dfDimensoes['titulo']) / 100))
    plt.title('Distribuição por dimensão ESG (Total = '  + str(np.sum(dfDimensoes['titulo']))+ ')' )

    plt.subplot(2, 2, 3)
    y_pos = np.arange(len(dfAnos.index))
    plt.bar(y_pos, dfAnos['titulo']  )
    plt.box(False)
    plt.xticks(y_pos, dfAnos.index.year, rotation=90)
    plt.title('Distribuição por ano de publicação (Total = '  + str(np.sum(dfDimensoes['titulo']))+ ')' )

    plt.subplot(2, 2, 4)
    if plotar_histograma:
        df['polaridade'].plot.hist().set_ylabel('Frequência')
        plt.box(False)
        plt.title('Histograma de polaridade em todo período \n(sentimento +1 positivo -1 negativo)' )
    else:
        y_pos = np.arange(10)
        plt.bar(y_pos, dfEmpresas.head(10)['titulo']  )
        plt.box(False)
        plt.xticks(y_pos, dfEmpresas.head(10)['empresa'].str.capitalize(), rotation=90)
        plt.title('Empresas com mais notícias' )

    plt.savefig(arquivo, bbox_inches='tight')
    plt.show()