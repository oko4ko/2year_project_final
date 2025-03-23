import gensim
import pymorphy3
from pymorphy3 import MorphAnalyzer
from nltk.tokenize import word_tokenize
from glue import glue


model = gensim.models.KeyedVectors.load_word2vec_format('model.bin', binary=True)
morph = MorphAnalyzer()

sentence = ' - Верно вы сказали, что он призрак, который бродит вокруг этого дома, - тихо сказала вдова.'
def synonym(sentence):
    sentence = sentence.replace('ё', 'е') # жаль, что так пришлось, но иногда в корпусе нет слов с ё
    sentence_tokens = word_tokenize(sentence, language='russian')
    sentence_pymorphy = [morph.parse(w)[0] for w in sentence_tokens]
    sentence_pymorphy = [{'lemma': w.normal_form.replace('ё', 'е'), 'word': w.word.replace('ё', 'е'), 'tag': w.tag} for w in sentence_pymorphy] # иногда в корпусе нет букв ё
    old_sentence_pymorphy = sentence_pymorphy

    #меняем существительные
    for i in range(len(sentence_pymorphy)):
        word = sentence_pymorphy[i]
        if word['tag'].POS == 'NOUN' and sentence_tokens[i].islower():
            lemma = word['lemma'] + '_NOUN'
            new_lemma = lemma
            try: #проверяем, есть ли слово в словаре
                model.most_similar(lemma, topn=10)
            except:
                continue
            for j in model.most_similar(lemma, topn=10):
                if 'NOUN' in j[0] \
                        and morph.parse(j[0][:j[0].find('_')])[0].inflect({word['tag'].case, word['tag'].number}) is not None\
                        and morph.parse(j[0][:j[0].find('_')])[0].inflect({word['tag'].case, word['tag'].number}).tag.POS == 'NOUN'\
                        and morph.parse(j[0][:j[0].find('_')])[0].inflect({word['tag'].case, word['tag'].number})[0] != word['word']:
                    #избавляемся от аббревиатур, глаголов, маскирующихся под существительные, и тех же самых слов
                    new_lemma = j[0]
                    break
                #не думаю, что первые 10 похожих слов - другой части речи, но тогда просто не буду заменять его
            new_lemma = morph.parse(new_lemma[:new_lemma.find('_')])[0]
            sentence_tokens[i] = new_lemma.inflect({word['tag'].case, word['tag'].number})[0]


    #меняем прилагательные
    changed_adjectives = []
    changed_shorts = []
    for i in range(len(sentence_pymorphy)):
        word = sentence_pymorphy[i]


        if 'Apro'  not in word['tag'].grammemes: #не меняем местоименные прилагательные
            if word['tag'].POS in ['ADJF', 'ADJS']:
                lemma = word['lemma'] + '_ADJ'
                new_lemma = lemma
                try:  # проверяем, есть ли слово в словаре
                    model.most_similar(lemma, topn=10)
                except:
                    continue
                for j in model.most_similar(lemma, topn=10):
                    if 'ADJ' in j[0] and 'ADJ' in morph.parse(j[0][:j[0].find('_')])[0].tag.POS: #многие наречия почему-то попадают под прилагательные по корпусу
                        new_lemma = j[0]
                        if word['tag'].number != 'plur':
                            if word['tag'].POS == 'ADJF':
                                changed_adjectives.append(i)
                            else:
                                changed_shorts.append(i)
                        break
                new_lemma = morph.parse(new_lemma[:new_lemma.find('_')])[0]
                if word['tag'].POS == 'ADJF':
                    sentence_tokens[i] = new_lemma.inflect({word['tag'].case, word['tag'].number})[0]
                else:
                    sentence_tokens[i] = new_lemma.word

    for i in range(len(sentence_pymorphy)):
        word = sentence_pymorphy[i]
        if 'Apro' in word['tag'].grammemes and 'ADJS' not in word['tag'].grammemes: #также согласуем местоимённые прилагательные
            changed_adjectives.append(i)
        elif 'ADJS' in word['tag'].grammemes:
            changed_shorts.append(i)


    #согласуем полные прилагательные по роду (только атрибутивные употребления)
    for i in changed_adjectives:
        adj = sentence_tokens[i]
        adj = morph.parse(adj)[0]
        old_adj = old_sentence_pymorphy[i]
        fl = 0
        for j in range(i + 1, len(sentence_pymorphy)):
            word = sentence_tokens[j]
            word = morph.parse(word)[0]
            old_word = old_sentence_pymorphy[j]
            if 'ADJ' not in str(old_word['tag'].POS) and old_sentence_pymorphy[j]['tag'].case == old_adj['tag'].case: #падеж смотрим по старому слову
                args = {old_adj['tag'].case, adj.tag.number}
                if word.tag.gender is not None and adj.tag.number != 'plur':
                    args.add(word.tag.gender)

                try:
                    sentence_tokens[i] = adj.inflect(args).word
                except:
                    print('EXCEPTION ADJECTIVE INFLECTION', args, adj)
                fl = 1
                break
        # в противном случае просто оставлю форму как была
        if fl == 0:
            args = {adj.tag.case, adj.tag.number}
            if adj.tag.gender is not None and adj.tag.number != 'plur':
                args.add(adj.tag.gender)
            try:
                sentence_tokens[i] = adj.inflect(args).word
            except:
                print('EXCEPTION ADJECTIVE INFLECTION', args, adj)


    #согласуем краткие прилагательные по роду
    for i in changed_shorts:
        adj = sentence_tokens[i]
        adj = morph.parse(adj)[0]
        fl = 0
        closest = -1
        for j in range(len(sentence_pymorphy)):

            word = sentence_pymorphy[j]
            #ищем ближайшее слово в именительном падеже (сработает не всегда, но достаточно часто)
            if word['tag'].POS == 'NOUN' and sentence_pymorphy[j]['tag'].case == 'nomn':
                if closest == -1 or abs(j - i) < abs(closest - i):
                    closest = j

        word = sentence_tokens[closest]


        word = morph.parse(word)[0]
        if closest == -1:
            word = adj
        args = {adj.tag.number}
        try:
            adj.inflect({'ADJS'}).word
            args.add({'ADJS'})
        except:
            pass
        if word.tag.gender is not None and adj.tag.number != 'plur':
            args.add(word.tag.gender)
        if word.tag.gender is not None and adj.tag.number != 'plur':
            sentence_tokens[i] = adj.inflect(args).word
        else:
            sentence_tokens[i] = adj.inflect(args).word




    #меняем причастия
    changed_partics = []
    changed_shortparts = []
    for i in range(len(sentence_pymorphy)):
        word = sentence_pymorphy[i]
        if word['tag'].POS in ['PRTF', 'PRTS']:
            lemma = word['lemma'] + '_VERB'
            new_lemma = lemma
            try: #проверяем, есть ли слово в словаре
                model.most_similar(lemma, topn=10)
            except:
                continue
            for j in model.most_similar(lemma, topn=10):
                #ищем глаголы нужного вида, чтобы не было проблем с залогом (и смыслом)
                if 'VERB' in j[0] and morph.parse(j[0][:j[0].find('_')])[0].tag.aspect == word['tag'].aspect and ('ся' in j[0] or 'сь' in j[0]) == ('ся' in word['lemma'] or 'сь' in word['lemma']):
                    new_lemma = j[0]
                    if word['tag'].number != 'plur':
                        if word['tag'].POS == 'PRTF':
                            changed_partics.append(i)
                        else:
                            changed_partics.append(i)
                            changed_shortparts.append(i)
                        break
                #не думаю, что первые 10 похожих слов - другой части речи, но тогда просто не буду заменять его
            new_lemma = morph.parse(new_lemma[:new_lemma.find('_')])[0]
            if word['tag'].POS == 'PRTF':
                try:
                    sentence_tokens[i] = new_lemma.inflect({word['tag'].voice, word['tag'].case, word['tag'].number})[0]
                except:
                    try:
                        sentence_tokens[i] = new_lemma.inflect({word['tag'].case, word['tag'].number})[0]
                    except: #кринж такое писать, но так отлавливаю слова которые не могут быть кратким причастием
                        sentence_tokens[i] = new_lemma.word

            else:
                sentence_tokens[i] = new_lemma.word



    #согласуем причастия по роду
    for i in changed_partics:
        adj = sentence_tokens[i]
        adj = morph.parse(adj)[0]
        old_adj = old_sentence_pymorphy[i]
        fl = 0
        closest = -1
        for j in range(len(sentence_pymorphy)):
            word = sentence_tokens[j]
            word = morph.parse(word)[0]

            case = 'nomn' if i in changed_shortparts else old_adj['tag'].case
            #ищем ближайшее слово в нужном падеже (сработает не всегда, но достаточно часто)
            if ('NOUN' in str(word.tag.POS) or 'PRO' in str(word.tag.POS)) and old_sentence_pymorphy[j]['tag'].case == case:
                if closest == -1 or abs(j - i) < abs(closest - i):
                    closest = j
        word = sentence_tokens[closest]
        word = morph.parse(word)[0]
        if closest == -1:
            word = adj
        infl = 'PRTS' if i in changed_shortparts else old_adj['tag'].case

        args = set()
        if word.tag.gender is not None and word.tag.number != 'plur':
            args.add(word.tag.gender)
        for arg in [infl, adj.tag.voice, word.tag.number]:
            if arg is not None:
                args.add(arg)
        try:
            sentence_tokens[i] = adj.inflect(args).word
        except:
            print('EXCEPTION PARTICIPLE INFLECTION:', args, adj)


    #меняем глаголы
    changed_verbpst = []
    for i in range(len(sentence_pymorphy)):
        word = sentence_pymorphy[i]
        if word['tag'].POS in ['VERB'] and word['lemma'] != 'быть':
            lemma = word['lemma'] + '_VERB'
            new_lemma = lemma
            try: #проверяем, есть ли слово в словаре
                model.most_similar(lemma, topn=10)
            except:
                continue
            for j in model.most_similar(lemma, topn=30):
                #ищем глаголы нужного вида, чтобы не было проблем с залогом (и смыслом)
                if 'VERB' in j[0] and morph.parse(j[0][:j[0].find('_')])[0].tag.aspect == word['tag'].aspect and ('ся' in j[0] or 'сь' in j[0]) == ('ся' in word['lemma'] or 'сь' in word['lemma']):
                    new_lemma = j[0]
                    if word['tag'].tense == 'past' and word['tag'].number != 'plur':
                        changed_verbpst.append(i)
                    break
                #не думаю, что первые 10 похожих слов - другой части речи, но тогда просто не буду заменять его
            new_lemma = morph.parse(new_lemma[:new_lemma.find('_')])[0]

            args = {word['tag'].number, word['tag'].mood}

            if word['tag'].mood == 'impr':
                args.add('excl') #исключаем формы типа укроемте, которые почему-то в приоритете перед укройте



            if word['tag'].tense is not None:
                args.add(word['tag'].tense)

            if word['tag'].tense == 'past':
                if word['tag'].gender is not None:
                    args.add(word['tag'].gender)
            else:
                if word['tag'].person is not None:
                    args.add(word['tag'].person)

            try:
                sentence_tokens[i] = new_lemma.inflect(args)[0]
            except:
                print('EXCEPTION VERB CHANGE', args, new_lemma)
        elif word['lemma'] == 'быть' and word['tag'].tense == 'past':
            changed_verbpst.append(i)

    #согласуем глаголы прошедшего времени по роду
    for i in changed_verbpst:
        vb = sentence_tokens[i]
        for k in morph.parse(vb):
            if k.tag.POS == 'VERB': #проверяем омонимию глаголов и существительных типа распил-распил
                vb = k
        fl = 0
        closest = -1
        for j in range(len(sentence_tokens)): #ожидаем увидеть подлежащее в начале
            word = sentence_tokens[j]
            word = morph.parse(word)[0]
            #ищем ближайшее слово в нужном падеже (сработает не всегда, но достаточно часто)
            if 'ADJ' not in str(word.tag.POS) and old_sentence_pymorphy[j]['tag'].case == 'nomn': #по ближайшему слову в именительном падеже, но приоритет у слов слева
                if (closest == -1 or abs(j - i) < abs(closest - i)) and (j < i or closest == -1):
                    closest = j

        word = sentence_tokens[closest]
        word = morph.parse(word)[0]

        if closest == -1: #отлавливаем предложения без явного подлежащего
            word = vb

        args = set()
        if word.tag.number is not None:
            args.add(word.tag.number)
        if word.tag.gender is not None and word.tag.number != 'plur':
            args.add(word.tag.gender)
        try:
            sentence_tokens[i] = vb.inflect(args).word
        except:
            print('EXCEPTION: VERB INFL', args, vb)


    #меняем наречия
    for i in range(len(sentence_pymorphy)):
        word = sentence_pymorphy[i]
        if word['tag'].POS == 'ADVB' and sentence_tokens[i].islower() and len(word['word']) > 4:
            lemma = word['lemma'] + '_ADV'
            new_lemma = lemma
            try: #проверяем, есть ли слово в словаре
                model.most_similar(lemma, topn=10)
            except:
                continue
            for j in model.most_similar(lemma, topn=10):
                if 'ADV' in j[0]:
                    new_lemma = j[0]
                    break
            new_lemma = morph.parse(new_lemma[:new_lemma.find('_')])[0]
            sentence_tokens[i] = new_lemma.word

    # меняем инфинитивы
    for i in range(len(sentence_pymorphy)):
        word = sentence_pymorphy[i]
        if word['tag'].POS == 'INFN' and sentence_tokens[i].islower():
            lemma = word['lemma'] + '_VERB'
            new_lemma = lemma
            try: #проверяем, есть ли слово в словаре
                model.most_similar(lemma, topn=10)
            except:
                continue
            for j in model.most_similar(lemma, topn=10):
                if 'VERB' in j[0] and morph.parse(j[0][:j[0].find('_')])[0].tag.aspect == word['tag'].aspect:
                    new_lemma = j[0]
                    break
            new_lemma = morph.parse(new_lemma[:new_lemma.find('_')])[0]
            sentence_tokens[i] = new_lemma.word


    return glue(sentence_tokens)


#sentence =  'Никаких благожелательных слов, никакой прискорбия из учтивости, два фразы - и это.'
#print(sentence)
#print(synonym(sentence))

a = morph.parse('вдохнувший')[0].tag.aspect
#a = a.inflect({'pssv'})[0]
#print(a)

#print(model.most_similar('проигрывать_VERB', topn=10))

