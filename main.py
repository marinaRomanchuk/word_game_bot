import telebot
import csv
import enchant
from telebot import types
import config

token = config.BOT_TOKEN
bot = telebot.TeleBot(token)

dictionary = enchant.Dict("en_US")
dictionary_rus = enchant.Dict("ru_RU")
dict_word = {}
common_list_ind = []
common_list_names = []
ind_game = []
names_game = []
current = 1
word = ""
common_set = set()


@bot.message_handler(content_types=['text'])
def start(message):
    if message.text == '/reg':
        bot.send_message(message.from_user.id, f"Nice to see you, {message.from_user.first_name}")
        bot.send_message(message.from_user.id, f"Enter '/users' to see the list of players")
        save_into_file(message)
    elif message.text == '/start':
        bot.send_message(message.from_user.id, f"Enter '/reg' to start working with bot")
    elif message.text == '/users':
        get_users(message)
    elif message.text == '/play':
        if len(ind_game) == 2:
            bot.send_message(message.from_user.id, f"Enter starting word")
            bot.register_next_step_handler(message, defining)
        else:
            bot.send_message(message.from_user.id, f"The opponent wasn't chosen")


def get_users(message):
    results = []
    str_to_print = ""
    count = 1
    with open('data.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    for i in results:
        str_to_print = f"{str_to_print}{count}. {i.get('name')}\n"
        common_list_ind.append(i.get('id'))
        common_list_names.append(i.get('name'))
        count += 1
    bot.send_message(message.from_user.id, str_to_print)
    bot.send_message(message.from_user.id, "Please, choose a partner")
    bot.register_next_step_handler(message, start_game)


def start_game(message):
    ind = 1
    try:
        ind = int(message.text)
    except Exception:
        bot.send_message(message.from_user.id, 'Enter numbers')
        bot.register_next_step_handler(message, start_game)
    if ind < 1 or ind > len(common_list_ind):
        bot.send_message(message.from_user.id, 'There is no player with such number, try again')
        bot.register_next_step_handler(message, start_game)
    ind -= 1

    keyboard = telebot.types.InlineKeyboardMarkup()
    key_yes = types.InlineKeyboardButton(text='Play!', callback_data='/play')
    keyboard.add(key_yes)
    question = f"Enter '/play' to start the game with {message.from_user.first_name}"
    bot.send_message(common_list_ind[ind], text=question, reply_markup=keyboard)

    ind_game.append(message.from_user.id)
    ind_game.append(int(common_list_ind[ind]))

    names_game.append(message.from_user.first_name)
    names_game.append(common_list_names[ind])
    bot.register_next_step_handler(message, game)


def check_letters_in_word(input_word: str) -> bool:
    temp_dict = dict_word.copy()
    for i in input_word:
        if i not in temp_dict or temp_dict.get(i) == 0:
            return False
        else:
            temp_dict[i] -= 1
    return True


def check_existance(input_word: str) -> bool:
    return dictionary.check(input_word) or dictionary_rus.check(input_word)


def check_word(input_word: str, current: int) -> str:
    if input_word in common_set:
        return "This word was used, try again"

    if check_letters_in_word(input_word):
        if check_existance(input_word):
            bot.send_message(ind_game[1 - current], f"New word of your opponent is {input_word}")
            bot.send_message(ind_game[1 - current], f"It's your turn now")
            common_set.add(input_word)
            return "ok"
        else:
            return "Such word doesn't exist"
    return "It can't be here, check your input"


def game(message):
    inp = message.text.lower()
    global current
    if inp == '/stop':
        bot.send_message(message.from_user.id, "You lost the game")
        bot.send_message(ind_game[1 - current], "You won the game")
        bot.register_next_step_handler(message, start)
    # print(inp)

    if current == ind_game.index(message.from_user.id):
        result_string = check_word(inp, current)
        if result_string == "ok":
            current = 1 - current
        else:
            bot.send_message(message.from_user.id, result_string)
    else:
        bot.send_message(message.from_user.id, f"It's not your turn now")
    bot.register_next_step_handler(message, game)


def defining(message):
    global word
    global current
    word = message.text
    bot.send_message(ind_game[0], f"The chosen word for game is {word}, it's your turn")

    list_word = list(word)
    set_word = set(list_word)
    global dict_word
    for letter in set_word:
        dict_word[letter] = list_word.count(letter)

    current = 1 - current
    bot.register_next_step_handler(message, game)


def save_into_file(message):
    results = []
    try:
        with open('data.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append(row)
    except FileNotFoundError:
        with open('data.csv', 'w') as f:
            fieldnames = ['id', 'name', 'surname']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
    results = str(results)
    if results.find(str(message.from_user.id)) == -1:
        common_dict = {"id": message.from_user.id,
                       "name": message.from_user.first_name,
                       "surname": message.from_user.last_name}
        with open('data.csv', 'a') as f:
            fieldnames = ['id', 'name', 'surname']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writerow(common_dict)


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    if call.data == "/play" and len(ind_game) == 2:
        bot.send_message(call.message.chat.id, f"Enter starting word")
        bot.register_next_step_handler(call.message, defining)
    else:
        bot.send_message(call.message.chat.id, f"The opponent wasn't chosen")


bot.polling(none_stop=True, interval=0)
