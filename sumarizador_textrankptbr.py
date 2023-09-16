'''
Módulo que implementa a chamada ao sumarizador TextRank para o Portugues
Fonte da implementação: https://github.com/summanlp/textrank
    
Artigo dos autores
Mihalcea, R., Tarau, P.: "Textrank: Bringing order into texts". 
In: Lin, D., Wu, D. (eds.) Proceedings of EMNLP 2004. pp. 404–411. 
Association for Computational Linguistics, Barcelona, Spain. July 2004.
    
Projeto Análise de sentimentos sobre notícias do tema ESG
Trabalho de conclusão de curso - MBA Digital Business USP Esalq'
'''


from summa import summarizer
import pandas as pd
import re
import numpy as np

RE_SENTENCE = re.compile('(\S.+?[.!?])(?=\s+|$)|(\S.+?)(?=[\n]|$)')
RE_PARAGRAPH = re.compile(r'(?s)((?:[^\n][\n]?)+)')
RE_WORDS = re.compile(r'\w+')


def get_sentences(text):
    for match in RE_SENTENCE.finditer(text):
        yield match.group()
        
def get_paragraphs(text):
    for match in RE_PARAGRAPH.finditer(text):
        yield match.group()
        
def split_text_to_pandas(text):
    linha = 0
    paragrafo = 0
    df = pd.DataFrame(columns=['P#', 'S#', 'W#', 'Sentenca'])
    for p in get_paragraphs(text):
        for s in get_sentences(p):
            words = len(re.findall(RE_WORDS, s))
            df = pd.concat([df, pd.DataFrame({'P#': [paragrafo], 'S#' : [linha], 'W#' : [words], 'Sentenca': [s]})], ignore_index=True )
            linha = linha+1
        paragrafo = paragrafo+1
    return df
        


def summarize_text_rank(text, compression=0.8, include_first_parag=True):
    '''
    Sumariza o texto
    '''
    dfTexto = split_text_to_pandas(text)
    
    if len(text) < 30 or len(dfTexto) < 7:
        return text
    else:
        sumario = summarizer.summarize(text, language='portuguese', scores=True, ratio=1.1)
        dfSumario = pd.DataFrame(sumario, columns=['Sentenca', 'TextRank'])
        dfTexto = pd.merge(left=dfTexto, right=dfSumario, how='left').fillna(0)

        df = dfTexto

        total_words = np.sum(df['W#'])

        if include_first_parag and np.sum(df[df['P#'] == 0]['W#']) >= (0.05 * total_words) :
            df['TextRank'] = df.apply(lambda row: 999 if row['P#'] == 0 else row['TextRank'], axis=1)

        df = df.sort_values(by=['TextRank', 'S#'], ascending=[False, True])

        df['SizeCum'] = df['W#'].cumsum()

        dfSelected = df[df['SizeCum'] <= ( compression * total_words + 1)]

        dfSelected = dfSelected.sort_values(by='S#')

        sumario = ''

        p_ant = 0

        for i, row in dfSelected.iterrows():

            if row['P#'] != p_ant:
                sumario = sumario + '\n'
                sumario = sumario + row['Sentenca']
                p_ant = row['P#']
            else:
                sumario = sumario + (' ' if i>0 else '') + row['Sentenca']


        return sumario




def teste_textrank():

    texto = '''A Ambev anunciou que quer zerar emissões de carbono de toda sua cadeia de valor até 2040. A meta envolve os escopos 1, 2 e 3, ou seja, emissões que a própria empresa produz, aquelas geradas de maneira indireta pela aquisição de energia e aquelas emitidas pelos demais terceiros que fazem parte da cadeia produtiva da companhia.

    Para zerar as emissões até a data prevista, a companhia estabeleceu um plano alinhado ao Science-based Targets Initiative (SBTi), que consiste em contribuir para conter o aquecimento global em 1,5 grau.

    Em setembro deste ano, a companhia divulgou sua primeira cervejaria e maltaria carbono neutro no Brasil. A empresa reduziu 90% das emissões de CO2 das unidades e passou a compensar os 10% remanescentes. Na época, o plano era de que, até o fim de 2021, mais quatro fábricas (Cuiabá, Macacu, Manaus e Maranhão) alcançassem o patamar de neutralidade de emissões – ou 18% da operação da Ambev, que tem 33 unidades.

    Produção neutra

    Na ocasião, a empresa afirmou querer chegar a 100% da produção neutra em carbono “o mais breve possível”. O maior desafio apontado foi o escopo 3 de emissões, aquelas geradas de forma indireta pela empresa, por meio de terceiros. Entre eles, caminhões da frota que entregam cerveja pelo País.

    Para especialistas, é sempre importante que a remuneração de executivos esteja atrelada às metas ambientais para garantir que haverá comprometimento da gestão em cumpri-las. No caso da Ambev, o vice-presidente e os diretores de Sustentabilidade e Suprimentos, além de diretores de Logística e de “Supply” têm metas diretamente ligadas à redução de carbono.

    Com informações de Estadão Conteúdo

    Imagem: ShutterStock

    Compartilhe isso: Facebook

    LinkedIn

    Twitter

    WhatsApp

    Telegram

    Pinterest

    Mais

    Imprimir

    '''

    return summarize_text_rank(texto, compression=0.8, include_first_parag=True)

