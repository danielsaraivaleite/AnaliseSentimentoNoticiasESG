'''
Aplicativo WEB em FLASK para apresentar a analise de sentimento das noticias
Autor: Daniel Saraiva Leite - 2023
Projeto Análise de sentimentos sobre notícias do tema ESG
Trabalho de conclusão de curso - MBA Digital Business USP Esalq
'''


from flask import Flask, render_template, request
import os
import pandas as pd
import datetime as dt
from analise_sentimento_modelo import gera_curva_polaridade_media
from noticias_graficos import *
from noticias_wordcloud import *

base_noticias_saida = 'datasets/sentimento_base_noticias.xlsx'
df = pd.read_excel(base_noticias_saida)

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    '''
    Página principal do app que mostra o sentimento das noticias
    O resultado mostrado da analise ja foi previamente gerado nas Jupyter notebooks do projeto
    '''
    # carrega lista de empresas
    nomes_empresas = list(df.sort_values(by='empresa')['empresa'].drop_duplicates())

    # processa a busca
    if request.method == 'POST':
        empresa = request.form.get('nomes')

        dfEmpresa = df[df['empresa'] == empresa]

        # adiciona o formato de exibicao
        dfEmpresa['formato'] = dfEmpresa['polaridade'].apply(formato_tabela)

        # converte a tabela pra dicionario permitindo a exibicao
        tabela_dados_pos = dfEmpresa[dfEmpresa.polaridade>0.05].to_dict(orient='records')
        tabela_dados_neg = dfEmpresa[dfEmpresa.polaridade<-0.05].to_dict(orient='records')

        # ultima noticia
        ultima_data = dfEmpresa['data_publicacao'].max().strftime('%d/%m/%Y')

        # plota grafico polaridade media
        lista_dfs_polaridade = [gera_curva_polaridade_media(df, empresa, 'ESG'),
                                gera_curva_polaridade_media(df, empresa, 'E'),
                                gera_curva_polaridade_media(df, empresa, 'S'),
                                gera_curva_polaridade_media(df, empresa, 'G')]
        graph_path = (os.path.join('static', 'images', 'grafico_polaridade.png'))
        plota_polaridade_media_sintetico(df, empresa, arquivo=graph_path, lista_dfs_polaridade=lista_dfs_polaridade)
        # plota os gauges
        plotar_gauge_polaridade(df, empresa=empresa, dimensao='ESG', df_pol=lista_dfs_polaridade[0], arquivo=os.path.join('static', 'images', 'gauge_esg.png'))
        plotar_gauge_polaridade(df, empresa=empresa, dimensao='E', df_pol=lista_dfs_polaridade[1], arquivo=os.path.join('static', 'images', 'gauge_e.png'))
        plotar_gauge_polaridade(df, empresa=empresa, dimensao='S', df_pol=lista_dfs_polaridade[2], arquivo=os.path.join('static', 'images', 'gauge_s.png'))
        plotar_gauge_polaridade(df, empresa=empresa, dimensao='G', df_pol=lista_dfs_polaridade[3], arquivo=os.path.join('static', 'images', 'gauge_g.png'))

        # base de dados
        plotar_descricao_base(dfEmpresa, plotar_histograma=True, arquivo=r'static/images/grafico_base_dados.png')

        # timeline
        plota_timeline_polaridade(dfEmpresa, +1, numero_noticias=2, empresa=empresa, imprime=False, arquivo=os.path.join('static', 'images', 'grafico_timeline_pos.png') )
        plota_timeline_polaridade(dfEmpresa, -1, numero_noticias=2, empresa=empresa, imprime=False, arquivo=os.path.join('static', 'images', 'grafico_timeline_neg.png') )

        # wordclouds
        plotar_word_cloud(dfEmpresa, empresa=empresa, dimensao='E', arquivo=os.path.join('static', 'images', 'wordcloud_E.png'))
        plotar_word_cloud(dfEmpresa, empresa=empresa, dimensao='S', arquivo=os.path.join('static', 'images', 'wordcloud_S.png'))
        plotar_word_cloud(dfEmpresa, empresa=empresa, dimensao='G', arquivo=os.path.join('static', 'images', 'wordcloud_G.png'))

        return render_template('index.html', nomes=nomes_empresas, tabela_pos=tabela_dados_pos,
                                tabela_neg=tabela_dados_neg, empresa_selecionada=empresa, ultima_data=ultima_data)

    return render_template('index.html', nomes=nomes_empresas)


def formato_tabela(n):
    '''
    Define o Formato da tabela (heatmap) de acordo com polaridade
    '''
    cor_fundo = 'bg-success p-2'
    text = 'text-dark'
    opacidade = 'bg-opacity-10'
    if (n < 0):
        cor_fundo = 'bg-danger p-2'
        n = -1 * n

    if n >= 0.75:
        opacidade = ''
        text = 'text-white'
    elif n >= 0.5 and n<0.75:
        text = 'text-white'
        opacidade = 'bg-opacity-75'
    elif n >= 0.25 and n<0.5:
        opacidade = 'bg-opacity-50'
    elif n >= 0.10 and n<0.25:
        opacidade = 'bg-opacity-25'
    return cor_fundo + ' ' + text + ' ' + opacidade



if __name__ == '__main__':
    app.run(debug=True)
