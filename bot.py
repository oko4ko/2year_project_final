from nltk.corpus import state_union

import config
import telebot
from telebot import types
from joblib import load
from sklearn.feature_extraction.text import TfidfVectorizer
from split_data import sentences #даём тестовую выборку пользователю и классификатору
from random import randint

bot = telebot.TeleBot(config.token)

menu_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
btn1 = types.KeyboardButton("Новая игра")
btn2 = types.KeyboardButton("Информация")
btn3 = types.KeyboardButton("Как играть")
menu_markup.add(btn1, btn2, btn3)


'''@bot.message_handler(commands=['start'])
def start(message):

    bot.send_message(message.chat.id, text="Привет! Для информации о боте введите команду /info".format(message.from_user))
    menu(message)'''

def predict_category(text):
    classifier = load('.\\classifier.joblib')
    vectorizer = load('.\\vectorizer.joblib')
    text_vec = vectorizer.transform([text])
    prediction = classifier.predict(text_vec)
    return prediction[0]

@bot.message_handler(commands=["start", "menu", "Назад в меню"])
def menu(message):
    bot.send_message(message.chat.id, "Меню бота", reply_markup=menu_markup)


@bot.message_handler(commands=["info", "Информация"])
def info(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn = types.KeyboardButton("Назад в меню")
    markup.add(btn)
    bot.send_message(message.chat.id, 'Вулф или компьютер? Проверьте, отличите ли вы предложение из книги Томаса Вулфа "Домой возврата нет" от созданного компьютером предложения с заменой слов на контекстные синонимы. Против вас будет играть программа-классификатор.', reply_markup=markup)

@bot.message_handler(commands=["how_to_play", "Как играть"])
def how_to_play(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn = types.KeyboardButton("Назад в меню")
    markup.add(btn)
    bot.send_message(message.chat.id,
                 'Чтобы начать игру, нажмите кнопку "Новая игра". Вам будет дано предложение. Ваша задача, определить, написано ли оно Томасом Вулфом (кнопка "Вулф") или компьютером (кнопка "Компьютер"). Игра будет идти до первого промаха. После каждого предложения вам скажут, совершил ли ошибку классификатор. В конце игры вам покажут ваш счёт и счёт классификатора.', reply_markup=markup)

@bot.message_handler(commands=["new_game", "Новая игра"])
def new_game(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn1 = types.KeyboardButton("Вулф")
    btn2 = types.KeyboardButton("Компьютер")
    markup.add(btn1, btn2)
    mesg = bot.send_message(message.chat.id, 'Начинаем!', reply_markup=markup)
    game(mesg, {'user_score': 0, 'classifier_score': 0, 'is_syn': 0, 'classifier_prediction': 0})


@bot.message_handler(commands=["game"])
def game(message, *args):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn1 = types.KeyboardButton("Вулф")
    btn2 = types.KeyboardButton("Компьютер")
    markup.add(btn1, btn2)
    user_score = args[0]['user_score']
    classifier_score = args[0]['classifier_score']
    classifier_prediction = args[0]['classifier_prediction']
    is_syn = args[0]['is_syn']

    if message.text != 'Начинаем!':
        mesg_text = ''
        if is_syn == 0:
            mesg_text += 'Автор предложения: Вулф.\n'
        else:
            mesg_text += 'Автор предложения: компьютер\n'
        user_prediction = 0 if message.text == 'Вулф' else 1

        if classifier_prediction != is_syn:
            mesg_text += f'Классификатор ошибся! \n'
        else:
            classifier_score += 1

        if user_prediction != is_syn:
            mesg_text += f'Вы проиграли. \nИтоговый счёт: {user_score} \nСчёт классификатора: {classifier_score}'
            menu(bot.send_message(message.chat.id, mesg_text, reply_markup=menu_markup))

        else:
            while True:
                state = randint(1, 1000000)
                sentence = list(sentences.sample(random_state=state).iloc[0])[0]
                is_syn = list(sentences.sample(random_state=state).iloc[0])[1]
                if sentence.count(' ') > 4:  # ищем достаточно длинные предложения
                    break

            classifier_prediction = predict_category(sentence)

            bot.send_message(message.chat.id, f'Счёт: {user_score + 1}')

            mesg = bot.send_message(message.chat.id, f'Ваше предложение: \n\n {sentence}')
            bot.register_next_step_handler(mesg, lambda m: game(m, {'user_score': user_score + 1, 'classifier_score': classifier_score,
                                                                    'is_syn': is_syn,
                                                                    'classifier_prediction': classifier_prediction}))


    else: #тут обработка первого предложения в игре
        while True:
            state = randint(1, 1000000)
            sentence = list(sentences.sample(random_state=state).iloc[0])[0]
            is_syn = list(sentences.sample(random_state=state).iloc[0])[1]
            if sentence.count(' ') > 4: #ищем достаточно длинные предложения
                    break
        classifier_prediction = predict_category(sentence)

        mesg = bot.send_message(message.chat.id, f'Ваше предложение: \n\n {sentence}')
        bot.register_next_step_handler(mesg, lambda m: game(m, {'user_score': 0, 'classifier_score': 0, 'is_syn': is_syn, 'classifier_prediction': classifier_prediction}))


@bot.message_handler(content_types=['text'])
def msg(message):
    if message.text == "Информация":
        info(message)
    elif message.text == "Новая игра":
        new_game(message)
    elif message.text == "Как играть":
        how_to_play(message)
    elif message.text == "Назад в меню":
        menu(message)


if __name__ == '__main__':
    bot.infinity_polling()