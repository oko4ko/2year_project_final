from nltk.tokenize import word_tokenize
from synonyms import synonym
import csv
import pandas as pd

df = pd.DataFrame(columns=['sentence', ['is_synonym']])

list_data = []

with open('.\\book.txt', encoding='utf-8') as f:
    s = f.read()
    s = s.replace('\n', ' ')
    for p in ['.', '?', '!']:
        s = s.replace(p, p + 'ඞ')
    s = s.split('ඞ')

    for sentence in s:
        try:
            if len(sentence) > 3: #много предложений из одних точек можно удалить
                synonymmed = synonym(sentence)
                list_data.append({'sentence': sentence, 'is_syn': 0})
                list_data.append({'sentence': synonymmed, 'is_syn': 1})
        except Exception as e:
            print(e)
            print(sentence)

print(list_data)

with open('.\\data2.csv', 'w', newline='', encoding = 'utf-8') as csvfile:
    fieldnames = ['sentence', 'is_syn']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter='|')
    writer.writeheader()
    writer.writerows(list_data)
    df.to_csv('.\\data.csv')
