import gensim
import urllib.request
import zipfile

#копирую из тетрадки про семантические модели
urllib.request.urlretrieve('https://vectors.nlpl.eu/repository/20/180.zip', 'ruscorpora_upos_cbow_300_20_2019')

src = 'ruscorpora_upos_cbow_300_20_2019'

with zipfile.ZipFile(src, 'r') as zip_ref:
    zip_ref.extractall('.')

