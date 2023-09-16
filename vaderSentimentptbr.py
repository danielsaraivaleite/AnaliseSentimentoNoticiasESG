'''
FORK do projeto VADER e sua adaptação ao Portugues

Fonte: https://github.com/cjhutto/vaderSentiment
 
Projeto Análise de sentimentos sobre notícias do tema ESG
Trabalho de conclusão de curso - MBA Digital Business USP Esalq

Comentarios do autor:
If you use the VADER sentiment analysis tools, please cite:
Hutto, C.J. & Gilbert, E.E. (2014). VADER: A Parsimonious Rule-based Model for
Sentiment Analysis of Social Media Text. Eighth International Conference on
Weblogs and Social Media (ICWSM-14). Ann Arbor, MI, June 2014.
'''

import os
import re
import math
import string
import codecs
import json
from itertools import product
from inspect import getsourcefile
from io import open
import unicodedata
import unidecode

# ##Constants##

# (empirically derived mean sentiment intensity rating increase for booster words)
B_INCR = 0.293
B_DECR = -0.293

# (empirically derived mean sentiment intensity rating increase for using ALLCAPs to emphasize a word)
C_INCR = 0.733
N_SCALAR = -0.74

# print valences true or false
VERBOSE = False

# sintagmas de negação
NEGATE = [
            'dificilmente',
            'dificilmente e',
            'nao',
            'nao consegue',
            'nao conseguem',
            'nao conseguiam',
            'nao conseguirei',
            'nao conseguiriam',
            'nao consigo',
            'nao devem',
            'nao deverao',
            'nao deveriam',
            'nao devo',
            'nao e',
            'nao eh',
            'nao eram',
            'nao foram',
            'nao sao',
            'nao serao',
            'nao serei',
            'nao seria',
            'nao seriam',
            'nao sou',
            'nao seria',
            'nao farao',
            'nao farei',
            'nao faz',
            'nao faziam',
            'nao fez',
            'nao fiz',
            'nao ousa',
            'nao ousam',
            'nao ousaram',
            'nao ousarao',
            'nao ousariam',
            'nao ouso',
            'nao se pode',
            'nao se pode mais',
            'nao poderei',
            'nao poderao',
            'nao poderia',
            'nao poderiam',
            'nao podia',
            'nao posso',
            'nao tem',
            'nao tenho',
            'nao terei',
            'nao teria',
            'nao tinha',
            'nao tinham',
            'nao parece',
            'nao pareciam',
            'nao parecem',
            'nao parecerao',
            'nao pareceria',
            'nao pareceriam',
            'nao esta',
            'nao estao',
            'nao estarao',
            'nao estariam',
            'nao estavam',
            'nao estiveram',
            'raramente' ,
            'jamais',
            'nunca',
            'de modo algum',
            'tampouco',
            'de jeito nenhum'
    ]

# consideramos aqui adverbios de intensidade

BOOSTER_DICT = {    
    'absolutamente':  B_INCR,
    'altamente':  B_INCR,
    'bastante':  B_INCR,
    'completamente':  B_INCR,
    'consideravelmente':  B_INCR,
    'decididamente':  B_INCR,
    'demais':  B_INCR,
    'demasiado':  B_INCR,
    'demasiadamente':  B_INCR,
    'enormemente':  B_INCR,
    'especialmente':  B_INCR,
    'excepcionalmente':  B_INCR,
    'excessivamente':  B_INCR,
    'extremamente':  B_INCR,
    'fabulosamente':  B_INCR,
    'fortemente':  B_INCR,
    'grandemente':  B_INCR,
    'grandiosamente':  B_INCR,
    'incrivelmente':  B_INCR,
    'indiscutivelmente':  B_INCR,
    'inteiramente':  B_INCR,
    'intensamente':  B_INCR,
    'indubitavelmente':  B_INCR,
    'majoritariamente':  B_INCR,
    'muito muito':  B_INCR,
    'muito':  B_INCR,
    'o mais':  B_INCR,
    'particularmente':  B_INCR,
    'pra caramba':  B_INCR,
    'pra valer':  B_INCR,
    'predominantemente':  B_INCR,
    'profundamente':  B_INCR,
    'puramente':  B_INCR,
    'realmente':  B_INCR,
    'sem sombra de duvidas':  B_INCR,
    'sem sombra de duvida':  B_INCR,
    'substancialmente':  B_INCR,
    'surpreendentemente':  B_INCR,
    'tao':  B_INCR,
    'terrivelmente':  B_INCR,
    'tremendamente':  B_INCR,
    'bem pouquinho':  B_DECR,
    'dificilmente':  B_DECR,
    'discretamente':  B_DECR,
    'escassamente':  B_DECR,
    'fracamente':  B_DECR,
    'levemente':  B_DECR,
    'mais ou menos':  B_DECR,
    'muito pouco':  B_DECR,
    'ocasionalmente':  B_DECR,
    'parcialmente':  B_DECR,
    'pouco':  B_DECR,
    'pouquinho':  B_DECR,
    'quase':  B_DECR,
    'so o necessario':  B_DECR,
    'superficialmente':  B_DECR,
    'tantinho':  B_DECR,
    'um pouco':  B_DECR,
    'um pouquinho':  B_DECR,
    'um tantinho':  B_DECR,
    'um tanto quanto':  B_DECR,
    'um tanto':  B_DECR 
    }
    
    

# check for sentiment laden idioms that do not contain lexicon words (future work, not yet implemented)
SENTIMENT_LADEN_IDIOMS = {}

# check for special case idioms and phrases containing lexicon words
SPECIAL_CASES = { }


# #Static methods# #

# function to replace ignoring case
def replace_substring(test_str, subs, repl):
    # Replacing all occurrences of substring s1 with s2
    test_str = re.sub(r'(?i)'+repl, subs, test_str)
    return test_str

#function to remove accents 
def portuguese_preprocessing(text, lexicon):
    # Remove acentos
    text = unidecode.unidecode(text)
    
    return text

def negated(input_words, include_nt=True):
    """
    Determine if input contains negation words
    """
    input_words = [str(w).lower() for w in input_words]
    neg_words = []
    neg_words.extend(NEGATE)
    for word in neg_words:
        if word in input_words:
            return True
    #if include_nt:
    #    for word in input_words:
    #        if "n't" in word:
    #            return True
    '''if "least" in input_words:
        i = input_words.index("least")
        if i > 0 and input_words[i - 1] != "at":
            return True'''
    return False


def normalize(score, alpha=15):
    """
    Normalize the score to be between -1 and 1 using an alpha that
    approximates the max expected value
    """
    norm_score = score / math.sqrt((score * score) + alpha)
    if norm_score < -1.0:
        return -1.0
    elif norm_score > 1.0:
        return 1.0
    else:
        return norm_score


def allcap_differential(words):
    """
    Check whether just some words in the input are ALL CAPS
    :param list words: The words to inspect
    :returns: `True` if some but not all items in `words` are ALL CAPS
    """
    is_different = False
    allcap_words = 0
    for word in words:
        if word.isupper():
            allcap_words += 1
    cap_differential = len(words) - allcap_words
    if 0 < cap_differential < len(words):
        is_different = True
    return is_different


def scalar_inc_dec(word, valence, is_cap_diff):
    """
    Check if the preceding words increase, decrease, or negate/nullify the
    valence
    """
    scalar = 0.0
    word_lower = word.lower()
    if word_lower in BOOSTER_DICT:
        scalar = BOOSTER_DICT[word_lower]
        if valence < 0:
            scalar *= -1
        # check if booster/dampener word is in ALLCAPS (while others aren't)
        if word.isupper() and is_cap_diff:
            if valence > 0:
                scalar += C_INCR
            else:
                scalar -= C_INCR
    return scalar


def ngrams_preprocessing(tokens, lexicon, negations, boosters, max_lenghth=6):
    count = len(tokens)
    new_tokens = []
    
    #print('tokens: ' + str(tokens))

    
    i = 0
    while i < count:
        step = 1
        ngrams=[]
        
        ngrams = [   tokens[i+k]  for k in range(0, min(max_lenghth, count-i  ))   ]
        
        #print('ngrams: ' + str(i) + " " +  str(ngrams))
        
        for j in range(len(ngrams), 1, -1):  # find ngrams in lexicon or adverbs list
            ngram = ' '.join(ngrams[:j])
            ngram_adj =  unidecode.unidecode(ngram.lower())
            #print ('termo pesquisado ' + str(ngram_adj))
            if ngram_adj in lexicon or ngram_adj in negations or ngram_adj in boosters:
                new_tokens.append(ngram)
                step = j
                break
        if step == 1:  # only a single word
            new_tokens.append( tokens[i] )  
            
        i = i + step
        
    return new_tokens


class SentiText(object):
    """
    Identify sentiment-relevant string-level properties of input text.
    """

    def __init__(self, text, lexicon_keys):
        if not isinstance(text, str):
            text = str(text).encode('utf-8')
        self.text = text
        self.words_and_emoticons = self._words_and_emoticons(lexicon_keys)
        # doesn't separate words from\
        # adjacent punctuation (keeps emoticons & contractions)
        self.is_cap_diff = allcap_differential(self.words_and_emoticons)

    @staticmethod
    def _strip_punc_if_word(token):
        """
        Removes all trailing and leading punctuation
        If the resulting string has two or fewer characters,
        then it was likely an emoticon, so return original string
        (ie ":)" stripped would be "", so just return ":)"
        """
        stripped = token.strip(string.punctuation)
        if len(stripped) <= 2:
            return token
        return stripped

    def _words_and_emoticons(self, lexicon):
        """
        Removes leading and trailing puncutation
        Leaves contractions and most emoticons
            Does not preserve punc-plus-letter emoticons (e.g. :D)
        """
        wes = self.text.split()
        stripped = list(map(self._strip_punc_if_word, wes))
        
        stripped = ngrams_preprocessing(stripped, lexicon, NEGATE, BOOSTER_DICT )
        
        return stripped

class SentimentIntensityAnalyzer(object):
    """
    Give a sentiment intensity score to sentences.
    """

    def __init__(self, lexicon_file="datasets/vader_lexico_ptbr.txt", emoji_lexicon="datasets/emoji_utf8_lexicon.txt"):
        _this_module_file_path_ = os.path.abspath(getsourcefile(lambda: 0))
        #lexicon_full_filepath = os.path.join(os.path.dirname(_this_module_file_path_), lexicon_file)
        lexicon_full_filepath = lexicon_file
        with codecs.open(lexicon_full_filepath, encoding='utf-8') as f:
            self.lexicon_full_filepath = f.read()
        self.lexicon = self.make_lex_dict()

        #emoji_full_filepath = os.path.join(os.path.dirname(_this_module_file_path_), emoji_lexicon)
        emoji_full_filepath = emoji_lexicon
        with codecs.open(emoji_full_filepath, encoding='utf-8') as f:
            self.emoji_full_filepath = f.read()
        self.emojis = self.make_emoji_dict()

    def make_lex_dict(self):
        """
        Convert lexicon file to a dictionary
        """
        lex_dict = {}
        for line in self.lexicon_full_filepath.rstrip('\n').split('\n'):
            if not line:
                continue
            (word, measure) = line.strip().split('\t')[0:2]
            word = unidecode.unidecode(word.lower().strip())
            
            lex_dict[word] = float(measure)
        return lex_dict

    def make_emoji_dict(self):
        """
        Convert emoji lexicon file to a dictionary
        """
        emoji_dict = {}
        for line in self.emoji_full_filepath.rstrip('\n').split('\n'):
            (emoji, description) = line.strip().split('\t')[0:2]
            emoji_dict[emoji] = description
        return emoji_dict

    def polarity_scores(self, text):
        """
        Return a float for sentiment strength based on the input text.
        Positive values are positive valence, negative value are negative
        valence.
        """
        
        # convert emojis to their textual descriptions
        text_no_emoji = ""
        prev_space = True
        for chr in text:
            if chr in self.emojis:
                # get the textual description
                description = self.emojis[chr]
                if not prev_space:
                    text_no_emoji += ' '
                text_no_emoji += description
                prev_space = False
            else:
                text_no_emoji += chr
                prev_space = chr == ' '
        text = text_no_emoji.strip()
        
        # portuguese preprocessing
        text = portuguese_preprocessing(text, self.lexicon)

        sentitext = SentiText(text, self.lexicon)

        sentiments = []
        words_and_emoticons = sentitext.words_and_emoticons
        #print(words_and_emoticons)
        for i, item in enumerate(words_and_emoticons):
            valence = 0
            # check for vader_lexicon words that may be used as modifiers or negations
            if item.lower() in BOOSTER_DICT:
                sentiments.append(valence)
                continue
            # n/a for portuguese
            #if (i < len(words_and_emoticons) - 1 and item.lower() == "kind" and
            #        words_and_emoticons[i + 1].lower() == "of"):
            #    sentiments.append(valence)
            #    continue

            sentiments = self.sentiment_valence(valence, sentitext, item, i, sentiments)

        sentiments = self._but_check(words_and_emoticons, sentiments)

        valence_dict = self.score_valence(sentiments, text)

        return valence_dict

    def sentiment_valence(self, valence, sentitext, item, i, sentiments):
        is_cap_diff = sentitext.is_cap_diff
        words_and_emoticons = sentitext.words_and_emoticons
        item_lowercase = item.lower()
        if item_lowercase in self.lexicon:
            # get the sentiment valence 
            valence = self.lexicon[item_lowercase]
            if VERBOSE:
                print(item_lowercase + ' : '+ str(self.lexicon[item_lowercase]))

            # check for "no" as negation for an adjacent lexicon item vs "no" as its own stand-alone lexicon item
            #if item_lowercase == "no" and i != len(words_and_emoticons)-1 and words_and_emoticons[i + 1].lower() in self.lexicon:
            #    # don't use valence of "no" as a lexicon item. Instead set it's valence to 0.0 and negate the next item
            #    valence = 0.0
            #if (i > 0 and words_and_emoticons[i - 1].lower() == "no") \
            #   or (i > 1 and words_and_emoticons[i - 2].lower() == "no") \
            #   or (i > 2 and words_and_emoticons[i - 3].lower() == "no" and words_and_emoticons[i - 1].lower() in ["or", "nor"] ):
            #    valence = self.lexicon[item_lowercase] * N_SCALAR

            # check if sentiment laden word is in ALL CAPS (while others aren't)
            if item.isupper() and is_cap_diff:
                if valence > 0:
                    valence += C_INCR
                else:
                    valence -= C_INCR

            for start_i in range(0, 3):
                # dampen the scalar modifier of preceding words and emoticons
                # (excluding the ones that immediately preceed the item) based
                # on their distance from the current item.
                if i > start_i and words_and_emoticons[i - (start_i + 1)].lower() not in self.lexicon:
                    s = scalar_inc_dec(words_and_emoticons[i - (start_i + 1)], valence, is_cap_diff)
                    if start_i == 1 and s != 0:
                        s = s * 0.95
                    if start_i == 2 and s != 0:
                        s = s * 0.9
                    valence = valence + s
                    valence = self._negation_check(valence, words_and_emoticons, start_i, i)
                    if start_i == 2:
                        valence = self._special_idioms_check(valence, words_and_emoticons, i)

            # n/a for portuguese
            #valence = self._least_check(valence, words_and_emoticons, i)
        sentiments.append(valence)
        return sentiments

    def _least_check(self, valence, words_and_emoticons, i):
        # n/a for portuguese
        # check for negation case using "least"
        #if i > 1 and words_and_emoticons[i - 1].lower() not in self.lexicon \
        #        and words_and_emoticons[i - 1].lower() == "least":
        #    if words_and_emoticons[i - 2].lower() != "at" and words_and_emoticons[i - 2].lower() != "very":
        #        valence = valence * N_SCALAR
        #elif i > 0 and words_and_emoticons[i - 1].lower() not in self.lexicon \
        #        and words_and_emoticons[i - 1].lower() == "least":
        #    valence = valence * N_SCALAR
        return valence

    @staticmethod
    def _but_check(words_and_emoticons, sentiments):
        # check for modification in sentiment due to contrastive conjunction 'but'
        words_and_emoticons_lower = [str(w).lower() for w in words_and_emoticons]

        for conjuncao in ['mas', 'entretanto', 'todavia', 'porem', 'contudo']:
            if conjuncao in words_and_emoticons_lower:
                bi = words_and_emoticons_lower.index(conjuncao)
                for sentiment in sentiments:
                    si = sentiments.index(sentiment)
                    # limitamos a distancia pois nao pode ser feito para texto grande
                    if si < bi and (bi-si) < 10:
                        sentiments.pop(si)
                        sentiments.insert(si, sentiment * 0.5)
                    elif si > bi and (si-bi) < 10:
                        sentiments.pop(si)
                        sentiments.insert(si, sentiment * 1.5)
            return sentiments

    @staticmethod
    def _special_idioms_check(valence, words_and_emoticons, i):
        words_and_emoticons_lower = [str(w).lower() for w in words_and_emoticons]
        onezero = "{0} {1}".format(words_and_emoticons_lower[i - 1], words_and_emoticons_lower[i])

        twoonezero = "{0} {1} {2}".format(words_and_emoticons_lower[i - 2],
                                          words_and_emoticons_lower[i - 1], words_and_emoticons_lower[i])

        twoone = "{0} {1}".format(words_and_emoticons_lower[i - 2], words_and_emoticons_lower[i - 1])

        threetwoone = "{0} {1} {2}".format(words_and_emoticons_lower[i - 3],
                                           words_and_emoticons_lower[i - 2], words_and_emoticons_lower[i - 1])

        threetwo = "{0} {1}".format(words_and_emoticons_lower[i - 3], words_and_emoticons_lower[i - 2])

        sequences = [onezero, twoonezero, twoone, threetwoone, threetwo]

        for seq in sequences:
            if seq in SPECIAL_CASES:
                valence = SPECIAL_CASES[seq]
                break

        if len(words_and_emoticons_lower) - 1 > i:
            zeroone = "{0} {1}".format(words_and_emoticons_lower[i], words_and_emoticons_lower[i + 1])
            if zeroone in SPECIAL_CASES:
                valence = SPECIAL_CASES[zeroone]
        if len(words_and_emoticons_lower) - 1 > i + 1:
            zeroonetwo = "{0} {1} {2}".format(words_and_emoticons_lower[i], words_and_emoticons_lower[i + 1],
                                              words_and_emoticons_lower[i + 2])
            if zeroonetwo in SPECIAL_CASES:
                valence = SPECIAL_CASES[zeroonetwo]

        # check for booster/dampener bi-grams such as 'sort of' or 'kind of'
        n_grams = [threetwoone, threetwo, twoone]
        for n_gram in n_grams:
            if n_gram in BOOSTER_DICT:
                valence = valence + BOOSTER_DICT[n_gram]
        return valence

    @staticmethod
    def _sentiment_laden_idioms_check(valence, senti_text_lower):
        # Future Work
        # check for sentiment laden idioms that don't contain a lexicon word
        #idioms_valences = []
        #for idiom in SENTIMENT_LADEN_IDIOMS:
        #    if idiom in senti_text_lower:
        #        print(idiom, senti_text_lower)
        #        valence = SENTIMENT_LADEN_IDIOMS[idiom]
        #        idioms_valences.append(valence)
        #if len(idioms_valences) > 0:
        #    valence = sum(idioms_valences) / float(len(idioms_valences))
        return valence

    @staticmethod
    def _negation_check(valence, words_and_emoticons, start_i, i):
        words_and_emoticons_lower = [str(w).lower() for w in words_and_emoticons]
        if start_i == 0:
            if negated([words_and_emoticons_lower[i - (start_i + 1)]]):  # 1 word preceding lexicon word (w/o stopwords)
                valence = valence * N_SCALAR
        if start_i == 1:
            #if words_and_emoticons_lower[i - 2] == "never" and \
            #        (words_and_emoticons_lower[i - 1] == "so" or
            #         words_and_emoticons_lower[i - 1] == "this"):
            #    valence = valence * 1.25
            if words_and_emoticons_lower[i - 2] == "sem" and                     words_and_emoticons_lower[i - 1] == "duvida":
                valence = valence
            elif negated([words_and_emoticons_lower[i - (start_i + 1)]]):  # 2 words preceding the lexicon word position
                valence = valence * N_SCALAR
        if start_i == 2:
            #if words_and_emoticons_lower[i - 3] == "never" and \
            #        (words_and_emoticons_lower[i - 2] == "so" or words_and_emoticons_lower[i - 2] == "this") or \
            #        (words_and_emoticons_lower[i - 1] == "so" or words_and_emoticons_lower[i - 1] == "this"):
            #    valence = valence * 1.25
            if words_and_emoticons_lower[i - 3] == "sem" and                     (words_and_emoticons_lower[i - 2] == "duvida" or words_and_emoticons_lower[i - 1] == "duvida"):
                valence = valence
            elif negated([words_and_emoticons_lower[i - (start_i + 1)]]):  # 3 words preceding the lexicon word position
                valence = valence * N_SCALAR
        return valence

    def _punctuation_emphasis(self, text):
        # add emphasis from exclamation points and question marks
        ep_amplifier = self._amplify_ep(text)
        qm_amplifier = self._amplify_qm(text)
        punct_emph_amplifier = ep_amplifier + qm_amplifier
        return punct_emph_amplifier

    @staticmethod
    def _amplify_ep(text):
        # check for added emphasis resulting from exclamation points (up to 4 of them)
        ep_count = text.count("!")
        if ep_count > 4:
            ep_count = 4
        # (empirically derived mean sentiment intensity rating increase for
        # exclamation points)
        ep_amplifier = ep_count * 0.292
        return ep_amplifier

    @staticmethod
    def _amplify_qm(text):
        # check for added emphasis resulting from question marks (2 or 3+)
        qm_count = text.count("?")
        qm_amplifier = 0
        if qm_count > 1:
            if qm_count <= 3:
                # (empirically derived mean sentiment intensity rating increase for
                # question marks)
                qm_amplifier = qm_count * 0.18
            else:
                qm_amplifier = 0.96
        return qm_amplifier

    @staticmethod
    def _sift_sentiment_scores(sentiments):
        # want separate positive versus negative sentiment scores
        pos_sum = 0.0
        neg_sum = 0.0
        neu_count = 0
        for sentiment_score in sentiments:
            if sentiment_score > 0:
                pos_sum += (float(sentiment_score) + 1)  # compensates for neutral words that are counted as 1
            if sentiment_score < 0:
                neg_sum += (float(sentiment_score) - 1)  # when used with math.fabs(), compensates for neutrals
            if sentiment_score == 0:
                neu_count += 1
        return pos_sum, neg_sum, neu_count

    def score_valence(self, sentiments, text):
        if sentiments:
            sum_s = float(sum(sentiments))
            # compute and add emphasis from punctuation in text
            punct_emph_amplifier = self._punctuation_emphasis(text)
            if sum_s > 0:
                sum_s += punct_emph_amplifier
            elif sum_s < 0:
                sum_s -= punct_emph_amplifier

            compound = normalize(sum_s)
            # discriminate between positive, negative and neutral sentiment scores
            pos_sum, neg_sum, neu_count = self._sift_sentiment_scores(sentiments)

            if pos_sum > math.fabs(neg_sum):
                pos_sum += punct_emph_amplifier
            elif pos_sum < math.fabs(neg_sum):
                neg_sum -= punct_emph_amplifier

            total = pos_sum + math.fabs(neg_sum) + neu_count
            pos = math.fabs(pos_sum / total)
            neg = math.fabs(neg_sum / total)
            neu = math.fabs(neu_count / total)

        else:
            compound = 0.0
            pos = 0.0
            neg = 0.0
            neu = 0.0

        sentiment_dict =             {"neg": round(neg, 3),
             "neu": round(neu, 3),
             "pos": round(pos, 3),
             "compound": round(compound, 4)}

        return sentiment_dict



if __name__ == '__main__':
    pass



# teste
def teste_vader():

    sentences = ["VADER é inteligente, bonito e engraçado.",  # positive sentence example
                 "VADER é inteligente, bonito e engraçado!",  # punctuation emphasis handled correctly (sentiment intensity adjusted)
                 "VADER é muito inteligente, bonito e engraçado.", # booster words handled correctly (sentiment intensity adjusted)
                 "VADER é muito inteligente, bonito e ENGRAÇADO.",  # emphasis for ALLCAPS handled
                 "VADER é MUITO INTELIGENTE, bonito e ENGRAÇADO!!!", # combination of signals - VADER appropriately adjusts intensity
                 "VADER é MUITO INTELIGENTE, super bonito e MUITO ENGRAÇADO!!!", # booster words & punctuation make this close to ceiling for score
                 "VADER não é inteligente, bonito nem engraçado.",  # negation sentence example
                 "O livro era bom.",  # positive sentence
                 "Pelo menos não é um livro horrível.",  # negated negative sentence with contraction
                 "O livro era apenas bom.", # qualified positive sentence is handled correctly (intensity adjusted)
                 "O enredo foi bom, mas os personagens são pouco atraentes e o diálogo não é bom.", # mixed negation sentence
                 "Hoje é muito ruim!",  # negative slang with capitalization emphasis
                 "Hoje está sendo meio ruim! Mas eu vou superar.", # mixed sentiment example with slang and constrastive conjunction "but"
                 "Lembre-se de :) ou :D hoje!",  # emoticons handled
                 "Considera emojis utf-8 como  💘 e 💋 e 😁",  # emojis handled
                 "Nada mal"  # Capitalized negation
                 ]


    sa = SentimentIntensityAnalyzer() 

    return [s + "\t" + str(sa.polarity_scores(s)['compound']) for s in sentences]    

