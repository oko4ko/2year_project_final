import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report
from joblib import dump, load

df = pd.read_csv('.\\data2.csv', encoding='utf-8', on_bad_lines='skip', delimiter='|')
print(df.sample(10))
print(df.size)

#код во многом скопирован отсюда: https://www.geeksforgeeks.org/text-classification-using-scikit-learn-in-nlp/
vectorizer = TfidfVectorizer(max_df=0.7).fit(df['sentence'])
dump(vectorizer, '.\\vectorizer.joblib')

X = vectorizer.transform(df['sentence'])
y = df['is_syn']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=168)
classifier = SVC(kernel='linear')
classifier.fit(X_train, y_train)

y_pred = classifier.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
report = classification_report(y_test, y_pred)

print(f'Accuracy: {accuracy:.4f}')
print('Classification Report:')
print(report)

dump(classifier, '.\\classifier.joblib')

