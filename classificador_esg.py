'''
Este módulo implementa o classificador semi-supervisionado para indicar se a noticia é E, S ou G, ou Outros
Autor: Daniel Saraiva Leite - 2023
Projeto Análise de sentimentos sobre notícias do tema ESG
Trabalho de conclusão de curso - MBA Digital Business USP Esalq
'''

from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score
import pandas as pd
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn import svm
import numpy as np
from noticias_processamento_texto import *
import pickle
import warnings
warnings.filterwarnings('ignore')



def determina_classe(classes, probs, threshold=0.3):  
    '''
    Determina a classe predita: E, S, G ou Outros
    Prob abaixo do threshold sao classificados como Outros
    '''
    if (np.max(probs) < threshold):
        return 'Outros'
    return classes[np.argmax(probs)]



def prob_threshold_dinamico(i, max_iter=10, initial_prob=0.7, max_prob=0.90):
    '''
    Define o threshold dinamico utilizado no treino semi-supervisionado
    A medida que as iterações avançam, as noticias não-rotuldas são incluidas apenas se
    sua probabilidade for acima do threshold
    '''
    return min(1, initial_prob + (max_prob-initial_prob)*((i)/(max_iter-1)), max_prob)



def treina_classificador_esg(df, df_nao_rotulado, col_texto, col_classe='Dimensão', modelo='SVC', max_iter=10, semi_supervisionado=True):
    '''
    Treina o classificador ESG no modelo semi-supervisionado
    Ou seja, utiliza-se iterativamente noticias nao rotuladas com alta probabilidade de estimativa
    para complementar a base de treino
    '''
    
    df = df.sample(frac=1).reset_index(drop=True)
    
    df['texto_ajustado'] = df[col_texto]
    
    part_train = df.sample(frac = 0.75)
    df_teste = df.drop(part_train.index)
    df = part_train
    
    df = df[~pd.isnull(df['texto_ajustado'])]
    df['texto_ajustado'] = df['texto_ajustado'].apply(str.lower)
    df['texto_ajustado'] = df['texto_ajustado'].apply(limpar_texto)
    df['texto_ajustado'] = df['texto_ajustado'].apply(lematizador)

    i = 0
    while(i < max_iter):
        print('### Iteração ' + str(i+1) + ' ####################################')
        
        df = df[~pd.isnull(df['texto_ajustado'])]
        df = df.loc[:, ['texto_ajustado', col_classe]]
        df = df.reset_index(drop=True)
        df = df.drop_duplicates()
        df = df.reset_index(drop=True)
        print('Tamanho base total rotulada: ' + str(len(df)))
        
        X_train, y_train = df['texto_ajustado'], df[col_classe]
    
        vect = TfidfVectorizer(ngram_range=(1,2), max_features=2000 , 
                               stop_words=lista_stopwords_classificador_esg())
        
        X_train_dtm = vect.fit_transform(X_train)
        
        model=None
        if modelo =='MultinomialNB':
            model = MultinomialNB()
        elif modelo == 'LogisticRegression':
            model = LogisticRegression(solver='lbfgs',random_state=0, C=0.1, penalty='l2',max_iter=1000)
            #model = LogisticRegression(max_iter=250)
        else:
            model = svm.SVC(kernel='linear', probability=True, C=0.2)
            
        model.fit(X_train_dtm, y_train)

        # treinamento
        probs = model.predict_proba(X_train_dtm)
        y_pred_class = np.array([determina_classe(model.classes_, p) for p in probs])

        print('Performance na base de treinamento')
        print('accuracy: ', accuracy_score(y_train, y_pred_class))
        print('precision: ', precision_score(y_train, y_pred_class, average='macro'))
        print('recall: ', recall_score(y_train, y_pred_class, average='macro'))
        print('f1: ', f1_score(y_train, y_pred_class, average='macro'))
        
        if semi_supervisionado:
            # incluindo instancias rotuladas automaticamente
            df_automatico = df_nao_rotulado
            if i <= 1:
                df_automatico = df_automatico[df_automatico['classificacao'] != 'Outros']
            df_automatico['texto_ajustado'] = df_automatico['texto_completo']
            df_automatico['texto_ajustado'] = df_automatico['texto_ajustado'].apply(str.lower)
            df_automatico['texto_ajustado'] = df_automatico['texto_ajustado'].apply(limpar_texto)
            df_automatico['texto_ajustado'] = df_automatico['texto_ajustado'].apply(lematizador)
            df_automatico = df_automatico.loc[:, ['texto_ajustado', 'classificacao']]
            df_automatico = df_automatico.rename(columns={'classificacao': col_classe})

            X_auto, y_auto = df_automatico['texto_ajustado'], df_automatico[col_classe]
            X_auto_dtm = vect.transform(X_auto)
            probs = model.predict_proba(X_auto_dtm)
            probs = [list(e) for e in list(probs)]
            df_automatico = pd.concat([df_automatico, pd.DataFrame({'classificacao_prevista': probs})], axis=1)
            df_automatico = df_automatico[~pd.isnull(df_automatico['classificacao_prevista'])]
            df_automatico['max_prob'] = df_automatico['classificacao_prevista'].apply(lambda x : np.max(list(x)))
            df_automatico = df_automatico[ df_automatico['max_prob'] >= prob_threshold_dinamico(i)]
            df_automatico['classificacao_prevista'] = df_automatico['classificacao_prevista'].apply(lambda x: determina_classe(model.classes_, x) )
            print('Incluindo ' + str(len(df_automatico)) + ' observações automáticas.')
            df_automatico = df_automatico.loc[:, ['texto_ajustado', col_classe]]
            df = pd.concat([df,df_automatico ]).reset_index(drop=True) # inclui
    
        # teste
        aplica_classificador_esg(vect, model, df_teste, 
                             comparar_com_real=True, col_texto_origem='texto_ajustado', 
                             col_texto_saida='texto_ajustado', col_classe_verdadeira='Dimensão')
        
        i = i+1
    
    return vect, model
    


def aplica_classificador_esg(vect, model, df_teste, 
                             comparar_com_real=True, col_texto_origem='texto_ajustado', 
                             col_texto_saida='texto_ajustado', col_classe_verdadeira='Dimensão'):
    '''
    Aplica um classificador ESG
    model e vect sao os modelos binarios (lidos com pickle)
    '''
    
    # teste
    df_teste[col_texto_saida] = df_teste[col_texto_origem].apply(str.lower)
    df_teste[col_texto_saida] = df_teste[col_texto_saida].apply(limpar_texto)
    df_teste[col_texto_saida] = df_teste[col_texto_saida].apply(lematizador)
    
    X_test = df_teste[col_texto_saida]
    X_test_dtm = vect.transform(X_test)
    probs = model.predict_proba(X_test_dtm)
    y_pred_class = np.array([determina_classe(model.classes_, p) for p in probs])
    
    if comparar_com_real:
        col_classe = col_classe_verdadeira
        y_test = df_teste[col_classe]
        print('Performance na base de teste - ' + str(len(df_teste)) + ' casos')
        print('accuracy: ', accuracy_score(y_test, y_pred_class))
        print('precision: ', precision_score(y_test, y_pred_class, average='macro'))
        print('recall: ', recall_score(y_test, y_pred_class, average='macro'))
        print('f1: ', f1_score(y_test, y_pred_class, average='macro')) 
    
    return y_pred_class





