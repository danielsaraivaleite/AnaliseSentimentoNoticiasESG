'''
Módulo que trata a plotagens dos graficos das noticias (exceto wordcloud)
Autor: Daniel Saraiva Leite - 2023
Projeto Análise de sentimentos sobre notícias do tema ESG
Trabalho de conclusão de curso - MBA Digital Business USP Esalq
'''

import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mp
import matplotlib.patches as mpatches
import seaborn as sns
import datetime  as dt
from scipy import interpolate
import scipy.stats
from matplotlib.dates import YearLocator, MonthLocator, DateFormatter
from noticias_timeline import plota_timeline
from noticias_processamento_texto import remove_acentos, remove_termos_comuns, aplica_stemming_texto, remove_palavras_texto, conta_termos_esg, classifica_texto, classifica_textos_coletados, filtra_noticias_nao_relacionadas, filtra_noticias_sem_classificacao, conta_mencoes_empresas, filtra_citacao_relevante, trim_texto
from vaderSentimentptbr import SentimentIntensityAnalyzer 
from sumarizador_textrankptbr import summarize_text_rank 
from analise_sentimento_modelo import *
import math
import re


def plota_timeline_polaridade(dfEmpresa, sinal, numero_noticias=2, empresa='', imprime=True, arquivo=''):
    '''
    Plota timeline de noticias
    '''
    plt.style.use('seaborn-white')
    desc = ''
    dfTimeline = dfEmpresa
    if sinal >0:
        dfTimeline = dfEmpresa[dfEmpresa['polaridade'] > 0]
        desc = 'positivas'
    else:
        dfTimeline = dfEmpresa[dfEmpresa['polaridade'] < 0]
        desc = 'negativas'
        
    
    ascendente = False
    if sinal <0:
        ascendente = True

    dfTimeline = dfTimeline.sort_values('polaridade',ascending = ascendente).groupby(dfTimeline.data_publicacao.dt.date).head(1).sort_values(by='data_publicacao')
    dfTimeline = dfTimeline.sort_values('polaridade',ascending = ascendente).groupby(dfTimeline.data_publicacao.dt.year).head(numero_noticias).sort_values(by='data_publicacao')
    dates = list(dfTimeline['data_publicacao'].dt.date)
    labels = list(dfTimeline.apply(lambda row : row['titulo'] + ' [' + row['classificacao']   + ' ' + '{:.2f}'.format(row['polaridade']) +   ']'    , axis=1))
    labels = [trim_texto(l) for l in labels]

    if imprime:
        for d, l in zip(dates, labels):
            print(d.strftime("%d/%m/%Y") + ": " + l)

    plota_timeline(dates, labels, 'Timeline de amostra de noticias ' + desc + ' para empresa '+ empresa.capitalize() + ' (2 notícias/ano)', arquivo)
    
    
    
def plota_polaridade_media(df, empresa, arquivo='', lista_dfs_polaridade=None):
    '''
    Plota grafico de polaridade media (em 4 quadrantes), separando geral, e, s e g
    '''

    # plota grafico polaridade media
    plt.style.use('seaborn-dark')
    
    ldfVisoesESG = None
    if lista_dfs_polaridade is not None:
        ldfVisoesESG = lista_dfs_polaridade
        
    if ldfVisoesESG is None:
        ldfVisoesESG = [gera_curva_polaridade_media(df, empresa, 'ESG')]
    llabelVisoesESG = ['ESG Geral']

    for l in 'ESG':
        if len(ldfVisoesESG) < 4:
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
    fig.suptitle('Histórico de polaridade das notícias da empresa '+empresa.capitalize()+' [-1 negativo, 0 neutro, +1 positivo]', y=1.01)
    plt.savefig(arquivo, bbox_inches='tight')
    plt.show()

    
def plota_polaridade_media_sintetico(df, empresa, arquivo='', lista_dfs_polaridade=None):
    '''
    Plota grafico de polaridade media (em 1 quadrante), separando geral, e, s e g
    '''
    sns.set_style("darkgrid")
    
    if lista_dfs_polaridade is not None and len(lista_dfs_polaridade) == 4:
        dfEWMA_ESG, dfEWMA_E, dfEWMA_S, dfEWMA_G = lista_dfs_polaridade[0], lista_dfs_polaridade[1], lista_dfs_polaridade[2], lista_dfs_polaridade[3]
    else:
        dfEWMA_ESG = gera_curva_polaridade_media(df, empresa, 'ESG')
        dfEWMA_E = gera_curva_polaridade_media(df, empresa, 'E')
        dfEWMA_S = gera_curva_polaridade_media(df, empresa, 'S')
        dfEWMA_G = gera_curva_polaridade_media(df, empresa, 'G')
    
    dfPontos = df[df.empresa == empresa]
    dfPontos_E = dfPontos[dfPontos['classificacao'] == 'E']
    dfPontos_S = dfPontos[dfPontos['classificacao'] == 'S']
    dfPontos_G = dfPontos[dfPontos['classificacao'] == 'G']

    fig, ax = plt.subplots(1,1, figsize=(9, 6), sharex=True, sharey=True)
    if dfEWMA_ESG is not None and len(dfEWMA_ESG) > 0:
        ax.plot(dfEWMA_ESG.index, dfEWMA_ESG['polaridade_fit'], label='Polaridade Média ESG Geral', color='dimgray', linewidth=1.5)
    
    if dfEWMA_E is not None and len(dfEWMA_E) > 0:
        ax.plot(dfEWMA_E.index, dfEWMA_E['polaridade_fit'], label='E', color='green', linewidth=0.6)
        
    if len(dfPontos_E) > 0:
        ax.scatter(dfPontos_E['data_publicacao'], dfPontos_E['polaridade'], s=3, color='green')
    
    if dfEWMA_S is not None and len(dfEWMA_S) > 0:
        ax.plot(dfEWMA_S.index, dfEWMA_S['polaridade_fit'], label='S', color='blue', linewidth=0.6)
        
    if len(dfPontos_S) > 0:
        ax.scatter(dfPontos_S['data_publicacao'], dfPontos_S['polaridade'], s=3, color='blue')
    
    if dfEWMA_G is not None and len(dfEWMA_G) > 0:
        ax.plot(dfEWMA_G.index, dfEWMA_G['polaridade_fit'], label='G', color='brown', linewidth=0.6)
        
    if len(dfPontos_G) > 0:
        ax.scatter(dfPontos_G['data_publicacao'], dfPontos_G['polaridade'], s=3, color='brown')

    # ajustando o visual do gráfico
    ax.tick_params(axis='x', labelrotation=90)
    ax.xaxis.set_major_locator(YearLocator() )
    ax.xaxis.set_major_formatter(DateFormatter('%Y'))
    ax.xaxis.set_minor_locator(MonthLocator())

    plt.tight_layout()
    plt.ylim(-1, 1)
    fig.suptitle('Histórico de polaridade das notícias da empresa '+empresa.capitalize()+' [-1 negativo, 0 neutro, +1 positivo]', y=1.01)

    box = ax.get_position()
    ax.set_position([box.x0, box.y0 + box.height * 0.1,
                     box.width, box.height * 0.9])

    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1),
              fancybox=True, shadow=True, ncol=4, frameon=True, facecolor='white')

    if arquivo != '':
        plt.savefig(arquivo, bbox_inches='tight')

    plt.show()
    
    
def plotar_descricao_base(df, plotar_histograma=False, arquivo=''):
    '''
    Plota grafico em 4 quadrantes com descricao da base
    '''    
    sns.set_style("white")
    # agrupando por fonte, dimensao e datas
    dfFontes  = df.groupby("fonte").count().reset_index(drop=False)
    dfFontes['fonte'] = dfFontes.apply(lambda row : 'Outros' if row['titulo'] < 0.03 * np.sum(dfFontes['titulo']) else row['fonte'] , axis=1)
    dfFontes  = dfFontes.groupby("fonte").sum() 
    dfDimensoes  = df.groupby("classificacao").count()
    dfAnos = df.set_index("data_publicacao").groupby([pd.Grouper(freq="Y")]).count().sort_index()
    dfEmpresas  = df.groupby("empresa").count().sort_values(by=['titulo'], ascending=False).reset_index(drop=False)

    plt.figure(figsize = (14, 6))
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
    
    
    
def plotar_gauge_polaridade(df, empresa, df_pol=None, dimensao='ESG', arquivo=''):
    '''
    Plota gauge da ultima polaridade
    Fonte https://coderzcolumn.com/tutorials/data-science/gauge-chart-using-matplotlib
    '''
    
    pol = 0
    df_curva = None
    
    if df_pol is None:
        df_curva = gera_curva_polaridade_media(df, empresa, dimensao)
    else:
        df_curva = df_pol
        
        

    coordenada = None
    if len(df) > 0 and  (df_curva is not None) and len(df_curva) > 0:
        pol = df_curva.iloc[-1].polaridade_fit
        coordenada = (3.14-3.14*pol)/2
        

    colors = ['#4dab6d', "#72c66e", "#c1da64", "#f6ee54", "#fabd57", "#f36d54", "#ee4d55"]

    values = [1, 0.7, 0.4, 0.15, -0.15 , -0.4, -0.7 , -1]
    x_axis_vals = [0, 0.44, 0.88,1.32,1.76,2.2,2.64, 3.14]

    fig = plt.figure(figsize=(7,4))

    ax = fig.add_subplot(projection="polar");

    ax.bar(x=x_axis_vals[:-1], width=0.5, height=0.5, bottom=2,
           linewidth=3, edgecolor="white",
           color=colors, align="edge");

    for loc, val in zip(x_axis_vals, values):
        plt.annotate(val, xy=(loc, 2.5), ha="right" if val<=20 else "left", weight='bold');

    texto = f"{pol:.2f}"

    if coordenada is not None:
        plt.annotate(texto, xytext=(0,0), xy=(coordenada, 2.0),
                     arrowprops=dict(arrowstyle="wedge, tail_width=0.2", color="black", shrinkA=0),
                     bbox=dict(boxstyle="circle", facecolor="black", linewidth=1.0, ),
                     fontsize=18, color="white", ha="center"
                    );
    else:
        plt.annotate('N/D', xytext=(0,0), xy=(0, 2.0),

                     bbox=dict(boxstyle="circle", facecolor="black", linewidth=1.0, ),
                     fontsize=18, color="white", ha="center"
                    );   

    if dimensao == 'ESG':
        dimensao = 'ESG Geral'
        
    plt.title(dimensao, loc="center", pad=20, fontsize=16);

    ax.set_axis_off()
    
    if arquivo != '':
        plt.savefig(arquivo, bbox_inches='tight')


    plt.show()

    
def plotar_correlacao_rankings(correls=None, arq='datasets/resultado_correlacao.xlsx', sig=0.05, qtd_media_anual=18):
    '''
    Plota matrizes de correlação com significancia
    '''
    
    sns.set()
    sns.set(font_scale=1.15)


    if correls is None:
        correls = pd.read_excel(arq)

    correls['Ranking A'] = correls['Ranking A'].str.replace("/", "\n/", regex=False).str.replace('(', '\n(', regex=False)
    correls['Ranking B'] = correls['Ranking B'].str.replace("/", "\n/", regex=False).str.replace('(', '\n(', regex=False)

    fig = plt.figure(figsize=(30,16))
    fig.tight_layout(pad=50)

    for i, alfa in enumerate(correls.Alfa.unique()):
        plt.subplot(2,3,i+1) 

        correls_alfa = correls[correls.Alfa == alfa]
        correls_alfa = pd.concat([correls_alfa, pd.DataFrame({'Alfa': [alfa]*len(correls_alfa) , 'Ranking A': correls_alfa['Ranking B'],
                                                       'Ranking B' : correls_alfa['Ranking A'], 'Correlação': correls_alfa['Correlação'],
                                                             'P-valor': correls_alfa['P-valor'] })])
        
        
        ranks = list(set(list(correls_alfa['Ranking A']) + list(correls_alfa['Ranking B'])))
        correls_alfa = pd.concat([correls_alfa, pd.DataFrame({'Alfa': [alfa]*len(ranks) , 'Ranking A': ranks,
                                                       'Ranking B' : ranks, 'Correlação': [1.0]*len(ranks),
                                                             'P-valor': [0.0]*len(ranks)
                                                             })])
        correls_alfa.drop_duplicates(inplace=True, ignore_index=True)    
        correls_alfa = correls_alfa.reset_index()
        correls_alfa_sig = correls_alfa[correls_alfa['P-valor'] <= 0.05].pivot_table(values='Correlação', index='Ranking A', columns='Ranking B')

        ax = sns.heatmap(correls_alfa_sig, vmin = -1, vmax = 1 , annot = True, fmt=".2%", cmap='coolwarm', 
                         linecolor="w", linewidths=1.5, annot_kws={"fontsize":15})
        
        correls_alfa_nsig = correls_alfa[correls_alfa['P-valor'] > 0.05].pivot_table(values='Correlação', index='Ranking A', columns='Ranking B')
        
        # nao significantes
        ax2 = sns.heatmap(correls_alfa_nsig, annot=True, fmt=".2%",  cbar=False,
            cmap=sns.color_palette("Greys", n_colors=1, desat=1), linecolor="w", linewidths=1.5, annot_kws={"fontsize":15})
        

        colors = [sns.color_palette("Greys", n_colors=1, desat=1)[0]]
        texts = ["Não sig. 95% IC"]
        patches = [ mpatches.Patch(color=colors[i], label="{:s}".format(texts[i]) ) for i in range(len(texts)) ]
        plt.legend(handles=patches, bbox_to_anchor=(1.215, 1.05), loc='center')
        
        per = ' ano'
        #n = (2 * (1/alfa)-1)/18   # tempo amostra
        meia_vida = (-math.log(2)/math.log(1-alfa))/qtd_media_anual
        if meia_vida >1:
            meia_vida = round(meia_vida, 0)
        else:     
            per = ' meses'
            meia_vida = meia_vida * 12
            if meia_vida < 1:
                meia_vida = round(meia_vida*30, 0)
                per = ' dias'
        meia_vida = round(meia_vida, 0)
        plt.title("Correlação para EWMA com " + r'$\alpha$ = ' + str(alfa) + " (" +  r'$t_\frac{1}{2} \backsim$' + " " + str(int(meia_vida)) + per + ")")

        ax.set_ylabel('')    
        ax.set_xlabel('')


    plt.show()

    sns.set(font_scale=1)
    