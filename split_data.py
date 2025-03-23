import pandas as pd
from sklearn.model_selection import train_test_split #делим данные точно так же как и для обучения, но без векторизации, для предсказания


df = pd.read_csv('.\\data2.csv', encoding='utf-8', on_bad_lines='skip', delimiter='|')

X = df['sentence']
y = df['is_syn']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=168)

sentences = pd.DataFrame()
sentences = pd.DataFrame.assign(sentences, Sentences=X_test, is_syn=y_test)
