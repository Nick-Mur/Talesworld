import telebot
import time
import sqlite3
import data.game.armors as armors
import data.game.weapons as weapons
import data.game.characters as characters
from telebot import types
from data.config import bot_token


# region DB
def create_nickname_table():
    conn = sqlite3.connect('data/database_talesworlds/data_talesworlds.sql')
    cur = conn.cursor()

    cur.execute('''CREATE TABLE IF NOT EXISTS users ( 
    user_id primary key, 
    nickname
    )''')
    conn.commit()
    cur.close()
    conn.close()


def insert_in_database(data: tuple, column: tuple, database: str, table: str):
    """
    Вставляет data в column в файл database в таблицу table
    """
    conn = sqlite3.connect(f'data/database_talesworlds/{database}')
    cur = conn.cursor()

    cur.execute(f'INSERT INTO {table} {column} VALUES {data}', )
    conn.commit()
    cur.close()
    conn.close()


def delete_in_database(data, column: str, database: str, table: str):
    """
    Удаляет data в column в файл database в таблицу table
    """
    conn = sqlite3.connect(f'data/database_talesworlds/{database}')
    cur = conn.cursor()
    try:
        cur.execute(f'DELETE FROM {table} WHERE {data} = {column}')
    except sqlite3.OperationalError:
        pass
    conn.commit()
    cur.close()
    conn.close()


# endregion

# telegram bot
bot = telebot.TeleBot(token=bot_token)
create_nickname_table()

# Game
MOVE = 0
HERO_CLASS = None
hero = characters.hero
monster = characters.monster


# region start_block
@bot.message_handler(commands=['start'])
def telegram_start(message):
    markup = types.ReplyKeyboardMarkup()
    start_game_btn = types.KeyboardButton('Начать игру')
    markup.add(start_game_btn)
    bot.send_message(
        message.chat.id,
        f'Здравствуй, {message.from_user.first_name}! Добро пожаловать в мой мир - Talesworld.\n'
        f'Зови меня сказочником или рассказчиком, сейчас я тебе расскажу одну историю. Готов ли ты?',
        reply_markup=markup
    )


# endregion


@bot.message_handler(content_types=['text'])
def telegram_handler(message):
    """
    Обработка любого отправленного текста
    """
    remove = types.ReplyKeyboardRemove()
    if message.text == 'Начать игру':
        bot.send_message(
            message.chat.id,
            '<b>Введи имя счастливца, что станет центром нашей истории</b>',
            parse_mode='html',
            reply_markup=remove
        )
        bot.register_next_step_handler(message, start_game)


def move():
    global MOVE
    MOVE += 1
    if MOVE == 2:
        MOVE = 0


@bot.message_handler(content_types=['text'])
def start_game(message):
    delete_in_database(
        data=message.from_user.id,
        column='user_id',
        database='data_talesworlds.sql',
        table='users'
    )

    if message.text.isalpha():
        hero.name = message.text

    insert_in_database(
        data=(message.from_user.id, hero.name),
        column=('user_id', 'nickname'),
        database='data_talesworlds.sql',
        table='users'
    )

    bot.send_message(
        message.chat.id,
        'В этих краях давно водились монстры, разбойники и прочая нечисть.\n'
        f'Ты, {hero.name}, недовольный крестьянин.\n'
        'Тебе нужен король, ведь ты хочешь высказать ему всё, что у тебя накопилось.\n'
        'Для этого ты готов пройти долгий и сложный путь.\n'
        'Но не бойся, на протяжении всего пути я буду с тобой.'
    )
    bot.send_message(
        message.chat.id,
        'Итак, пока мы только в "деревне, над которой не садится солнце", а из вещей у тебя только роба, да вилы.\n'
        'Но это ничего, не все великие герои с самого начала были таковыми, так что и тебе не стоит беспокоиться.\n'
        'Главное держись меня, лишь я на твоей стороне.'
    )
    bot.send_message(
        message.chat.id,
        'Смотри, тебе навстречу идёт монстр!\n'
        'Из рассказов, сказок и легенд, ты должен знать, когда монстры приходят в деревни к людям,'
        ' ничем хорошим это не кончается. \n'
        ''
    )
    markup = types.ReplyKeyboardMarkup()
    come_up_btn = types.KeyboardButton('Подойти')
    markup.add(come_up_btn)
    bot.send_message(
        message.chat.id,
        'Иди, разберись с ним!',
        reply_markup=markup
    )
    bot.register_next_step_handler(message, fight_with_monster)


@bot.message_handler(content_types=['text'])
def fight_with_monster(message):
    # region buttons
    remove = types.ReplyKeyboardRemove()
    markup = types.ReplyKeyboardMarkup()
    check_self_status_btn = types.KeyboardButton('Проверить своё состояние')
    check_inventory_btn = types.KeyboardButton('Проверить инвентарь')
    hit_btn = types.KeyboardButton('Ударить')
    check_enemy_status_btn = types.KeyboardButton('Проверить состояние противника')
    markup.add(check_self_status_btn)
    markup.add(check_inventory_btn)
    markup.add(hit_btn)
    markup.add(check_enemy_status_btn)
    # endregion
    if message.text == 'Подойти':
        bot.send_message(
            message.chat.id,
            'FIGHT!!!',
            reply_markup=remove
        )
        bot.send_message(
            message.chat.id,
            f'Что же ты сделаешь, {hero.name}?',
            reply_markup=markup
        )
    elif message.text == 'Проверить своё состояние':
        bot.send_message(
            message.chat.id,
            hero.check_status()
        )
    elif message.text == 'Ударить':
        damage = hero.attack(monster)
        bot.send_message(
            message.chat.id,
            f'Ты нанёс {damage} урона! Теперь у {monster.name} {monster.health} жизни и {monster.defence} брони.'
        )
        if monster.health > 0:
            damage = monster.attack(hero)
            bot.send_message(
                message.chat.id,
                f'{monster.name} нанёс {damage} урона! Теперь у тебя {hero.health} жизни и {hero.defence} брони.'
            )
        else:
            bot.send_message(
                message.chat.id,
                f'Монстр повержен.',
                reply_markup=remove
            )
            bot.register_next_step_handler(message, pursuit)
    elif message.text == 'Проверить инвентарь':
        text = list()
        text += hero.weapon.check_weapon() + ['\n'] + hero.armor.check_armor()
        text = ''.join(text)
        bot.send_message(
            message.chat.id,
            text
        )
    elif message.text == 'Проверить состояние противника':
        bot.send_message(
            message.chat.id,
            monster.check_status()
        )
    bot.register_next_step_handler(message, fight_with_monster)


@bot.message_handler(content_types=['text'])
def pursuit(message):
    pass


bot.infinity_polling()