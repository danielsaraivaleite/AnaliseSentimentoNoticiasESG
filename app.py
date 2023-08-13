from flask import Flask, render_template, request
import matplotlib.pyplot as plt
import os
import pandas as pd
import datetime as dt
from vaderSentimentptbr import SentimentIntensityAnalyzer
from noticias_graficos import plota_polaridade_media, plotar_descricao_base, plota_timeline_polaridade

base_noticias_saida = 'datasets/sentimento_base_noticias.xlsx'
df = pd.read_excel(base_noticias_saida)

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():

    # carrega lista de empresas
    nomes_empresas = list(df.sort_values(by='empresa')['empresa'].drop_duplicates())

    # processa a busca
    if request.method == 'POST':
        empresa = request.form.get('nomes')

        dfEmpresa = df[df['empresa'] == empresa]

        # converte a tabela pra dicionario permitindo a exibicao
        tabela_dados_pos = dfEmpresa[dfEmpresa.polaridade>=0].to_dict(orient='records')
        tabela_dados_neg = dfEmpresa[dfEmpresa.polaridade<0].to_dict(orient='records')

        # ultima noticia
        ultima_data = dfEmpresa['data_publicacao'].max().strftime('%d/%m/%Y')

        # plota grafico polaridade media
        graph_path = (os.path.join('static', 'images', 'grafico_polaridade.png'))
        plota_polaridade_media(df, empresa, graph_path)

        # base de dados
        plotar_descricao_base(dfEmpresa, plotar_histograma=True, arquivo=r'static/images/grafico_base_dados.png')

        # timeline
        plota_timeline_polaridade(dfEmpresa, +1, numero_noticias=2, empresa=empresa, imprime=False, arquivo=os.path.join('static', 'images', 'grafico_timeline_pos.png') )
        plota_timeline_polaridade(dfEmpresa, -1, numero_noticias=2, empresa=empresa, imprime=False, arquivo=os.path.join('static', 'images', 'grafico_timeline_neg.png') )


        return render_template('index.html', nomes=nomes_empresas, tabela_pos=tabela_dados_pos, tabela_neg=tabela_dados_neg, empresa_selecionada=empresa, ultima_data=ultima_data)

    return render_template('index.html', nomes=nomes_empresas)


if __name__ == '__main__':
    app.run(debug=True)
