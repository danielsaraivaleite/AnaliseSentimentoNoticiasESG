'''
Módulo de grafico de timeline das noticias

Fontes para esse codigo:
https://stackoverflow.com/questions/35091557/replace-nth-occurrence-of-substring-in-string
https://dadoverflow.com/2021/08/17/making-timelines-with-python/

Projeto Análise de sentimentos sobre notícias do tema ESG
Trabalho de conclusão de curso - MBA Digital Business USP Esalq
'''

import matplotlib.pyplot as plt
from datetime import date
import numpy as np
from datetime import timedelta
import re

def replacenth(string, sub, wanted, n):
    # codigo adaptado de https://stackoverflow.com/questions/35091557/replace-nth-occurrence-of-substring-in-string
    where = [m.start() for m in re.finditer(sub, string)][n-1]
    before = string[:where]
    after = string[where:]
    after = after.replace(sub, wanted, 1)
    newString = before + after
    return (newString)

def ajusta_labels(labels):
    return [replacenth(l, ' ', '\n', int(l.count(' ')/2)) if int(l.count(' ')) > 10 else l  for l in labels ]


def plota_timeline(dates, labels, titulo, arquivo=''):
    '''
    Plota o timeline
    '''
    # codigo adaptado de: https://dadoverflow.com/2021/08/17/making-timelines-with-python/

    if len(dates) == 0:
        min_date = date.today()
        max_date = date.today()
    else:
        min_date = date(np.min(dates).year - 2, np.min(dates).month, np.min(dates).day)
        max_date = date(np.max(dates).year + 2, np.max(dates).month, np.max(dates).day)

    labels = ajusta_labels(labels)

    labels = ['{0:%d/%m/%Y}:{1}'.format(d, l) for l, d in zip (labels, dates)]

    fig, ax = plt.subplots(figsize=(10, 10), constrained_layout=True)
    _ = ax.set_xlim(-20, 20)
    _ = ax.set_ylim(min_date, max_date)
    _ = ax.axvline(0, ymin=0.05, ymax=0.95, c='blue', zorder=1)

    _ = ax.scatter(np.zeros(len(dates)), dates, s=120, c='lightblue', zorder=2)
    _ = ax.scatter(np.zeros(len(dates)), dates, s=30, c='darkblue', zorder=3)

    label_offsets = np.repeat(2.0, len(dates))
    label_offsets[1::2] = -2.0
    for i, (l, d) in enumerate(zip(labels, dates)):
        d = d - timedelta(days=90)
        align = 'right'
        if i % 2 == 0:
            align = 'left'
        _ = ax.text(label_offsets[i], d, l, ha=align,  fontsize=8)

    stems = np.repeat(2.0, len(dates))
    stems[1::2] *= -1.0
    x = ax.hlines(dates, 0, stems, color='darkblue')

    # hide lines around chart
    for spine in ["left", "top", "right", "bottom"]:
        _ = ax.spines[spine].set_visible(False)

    _ = ax.set_xticks([])
    _ = ax.set_yticks([])

    _ = ax.set_title(titulo,fontsize=12)

    if arquivo != '':
        plt.savefig(arquivo,  bbox_inches='tight')
        plt.close()

