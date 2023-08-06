import warnings
import numpy as np
import pandas as pd
import re
import unidecode
import datetime as dt
from noticias_google_buscador import busca_noticias_google_news
from noticias_processamento_texto import remove_acentos, remove_termos_comuns, aplica_stemming_texto, remove_palavras_texto, conta_termos_esg, classifica_texto, classifica_textos_coletados, filtra_noticias_nao_relacionadas, filtra_noticias_sem_classificacao, conta_mencoes_empresas, filtra_citacao_relevante, remove_nome_composto

warnings.filterwarnings('ignore')
arquivo_termos_esg = 'datasets/palavras_chave_esg.xlsx'
base_noticias = 'datasets/base_noticias.xlsx'


'''
Obtem relação de empresas listadas na B3
'''
def recupera_lista_empresas_B3():
    df = pd.read_html('https://www.dadosdemercado.com.br/bolsa/acoes')[0].loc[:, ['Código', 'Nome']].sort_values(by='Nome')

    df = pd.merge(left=df, right=pd.read_excel('datasets/EscoreB3.xlsx'), on='Código', how='left')
    
    df['Nome'] = df['Nome'].replace('AMER3', 'Lojas Americanas')
    df['Nome'] = df['Nome'].replace('VBBR3', 'VIBRA ENERGIA S.A.')
    df['Nome'] = df['Nome'].replace('RaiaDrogasil', 'Raia Drogasil')
    
    df.to_excel('datasets/lista_empresas.xlsx')
    

    
    return df[df['Nome'] != 'B3']


'''
Busca as noticias do google 
'''
def busca_noticias_google_periodo(termo, atualiza=False, ultima_data=None):
    
    if not atualiza:
        df = busca_noticias_google_news(termo, '')  # busca sem data

        hoje = dt.datetime.now()
        for i in range(1, 15):   # busca 14 periodos de 6 meses
            dt_defasada = hoje - dt.timedelta(i * 180)

            dfNovaPesquisa = busca_noticias_google_news(termo, dt_defasada.strftime("%Y-%m-%d"))

            if len(dfNovaPesquisa) > 0:
                df = pd.concat([df, dfNovaPesquisa ])
    else:
        if ultima_data is not None:
            df = busca_noticias_google_news(palavras=termo, data_limite=ultima_data.strftime("%Y-%m-%d"), after=True)
        else:
            df = busca_noticias_google_news(palavras=termo)
            
          
            
    if len(df) > 0:

        df  = filtra_noticias_sites_especificos(df)

        df['fonte'] = df['fonte'].apply(lambda x : x['title'])

        df = df.drop_duplicates().reset_index(drop=True)
    
    return df



'''
Busca notícias de uma empresa relacionadas ao tema ESG
'''
def busca_noticias_google_esg(empresa_pesquisada, atualiza=False, ultima_data=None):
    dfTermos = pd.read_excel(arquivo_termos_esg)
    
    empresa_pesquisada_aju = empresa_pesquisada.replace(' ', '+')

    dfESG = busca_noticias_google_periodo(empresa_pesquisada_aju + '+ESG', atualiza, ultima_data)

    for letra in 'ESG':
        q = remove_acentos(empresa_pesquisada_aju + '+('+ '|'.join(''+ dfTermos[letra][dfTermos[letra].notnull()] +'').replace(' ', '+') + ')')
        dfLetra = busca_noticias_google_periodo(q, atualiza, ultima_data)
        
        if len(dfLetra) > 0:
            dfESG = pd.concat([dfESG,dfLetra]).drop_duplicates().reset_index(drop=True)
            
    if len(dfESG) > 0:
        dfESG = dfESG.sort_values(by='data_publicacao')  #ordena

        dfESG['empresa'] = remove_acentos(empresa_pesquisada.lower())
    
    return dfESG

'''
Filtra determinados sites
'''
def filtra_noticias_sites_especificos(noticias):
    df = noticias
    df = df[df['fonte'].str['href'].str.contains('xpi.')==False]
    df = df[df['fonte'].str['href'].str.contains('estrategiaconcursos')==False]
    df = df[df['fonte'].str['href'].str.contains('conjur')==False]
    df = df[df['fonte'].str['href'].str.contains('gov.br')==False]
    df = df[df['fonte'].str['href'].str.contains('portogente')==False]
    df = df[df['fonte'].str['href'].str.contains('stj.')==False]
    df = df[df['fonte'].str['href'].str.contains('pcb.')==False]

    return df

'''
Faz o scrapping de cada noticias utilizando biblioteca 
https://newspaper.readthedocs.io/en/latest/
'''
def recupera_noticias_completas(noticias, apenas_titulos):
    
    import pandas as pd
    from newspaper import Article 
    
    if apenas_titulos: # nao extrai conteudo
        df = noticias
        df['texto_completo'] = df['titulo']
        
        return df
    
    df = noticias
    textos = []

    for i in range(0, len(df)):
        url = df.iloc[i]['url']
        article = Article(url, language='pt')
        try:
            article.download()
            article.parse()
            textos.append(article.text)       
        except:
            textos.append('')     
    
    df['texto_completo'] = textos
    
    df = df[ (df['texto_completo'] != '')]
    
    return df


'''
Processa as noticias de uma empresa de acordo com o processo descrito neste trabalho
'''
def processa_busca_empresa(empresa, dfEmpresasListadas, atualiza=False, apenas_titulos=False):
    #print('Buscando noticia empresa ' + empresa + ' ' + str(dt.datetime.now()))
    df = busca_noticias_google_esg(empresa, atualiza)
    #print('recuperando texto noticia empresa ' + empresa + ' ' + str(dt.datetime.now()))
    df = recupera_noticias_completas(df, apenas_titulos)
    if len(df) > 0:
        #print('filtando texto noticia empresa ' + empresa + ' ' + str(dt.datetime.now()))
        df = filtra_noticias_nao_relacionadas(df, empresa, apenas_titulos)
        if not apenas_titulos:
            df = filtra_citacao_relevante(df, empresa, dfEmpresasListadas )
        #print('classifica texto noticia empresa ' + empresa + ' ' + str(dt.datetime.now()))
        df = classifica_textos_coletados(df, apenas_titulos)
        #df = filtra_noticias_sem_classificacao(df, empresa)
        #print('fim texto noticia empresa ' + empresa + ' ' + str(dt.datetime.now()))
    return df  

