from django.shortcuts import HttpResponse
from django.http import HttpResponseForbidden
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import time
from decimal import Decimal
from yandex_geocoder import Client
# import logging
import telebot
from telebot import apihelper, types
from account.models import Employee, Citizen, Subscription
from organizations.models import Organization
from appeals.models import Appeal
import random
import os

YANDEX_API_KEY = '815e5f3d-fab8-486b-924f-384c8bf11394'
API_TOKEN = settings.BOT_TOKEN
PROXY_HOST = '80.187.140.26'
PROXY_PORT = '8080'

# logger = telebot.logger
# telebot.logger.setLevel(logging.INFO)

apihelper.proxy = {'https': f'http://{PROXY_HOST}:{PROXY_PORT}/'}

bot = telebot.TeleBot(API_TOKEN)
# bot.enable_save_next_step_handlers(delay=2, filename='../profile.step.save')

# Заглушка для обработки заявок. Представлена в виде словаря, где ключи - это ID из справочника должностей
# В нашем случае 1 - Сантехник, 2 - Электрик
# TODO собрать датасет на основании поступивших обращений граждан всфере ЖКХ.
#  И с помощью собранного датасета натренировать бота правильно реагировать на запросы
stub_problems = {
    '1': [
        'поменять смеситель',
        'поменять батарею',
        'замена электрического счетчика',
    ],
    '2': [
        'поменять розетку',
        'поменять люстру',
        'замена счетчика воды',
        'прорыв трубы',
    ]
}


def delete_file(file_path: str):
    if os.path.exists(file_path):
        os.remove(file_path)


@bot.message_handler(commands=['help', 'start'])
def start(message):
    bot.send_message(message.chat.id, "Привет я бот, который будет помагать общаться с управляющими компаниями и ТСЖ."
                                      "Меня зовут Фёдор Ботов. А Вас как?")
    bot.register_next_step_handler(message, check_role)


def check_role(message):
    fio = message.text.split(' ')
    with open(settings.MEDIA_ROOT + f'{message.chat.id}.txt', 'w') as f:
        f.writelines([str(message.chat.id) + '\n', fio[0] + '\n', fio[1] + '\n'])
    markup = types.ReplyKeyboardMarkup()
    itembtncit = types.KeyboardButton('Житель города')
    itembtnhead = types.KeyboardButton('Старший по дому')
    itembtnemp = types.KeyboardButton('Сотрудник УК/ТСЖ')
    markup.row(itembtncit)
    markup.row(itembtnhead)
    markup.row(itembtnemp)
    bot.send_message(message.chat.id, "Кем Вы являетесь?", reply_markup=markup)
    bot.register_next_step_handler(message, query_text)


# @bot.message_handler(func=lambda message: message.text == 'Житель города', content_types=['text'])
def query_text(message):
    roles = {
        'Житель города': {'greet': 'Отлично, Вы житель!', 'role': 0},
        'Старший по дому': {'greet': 'Добро пожаловать!', 'role': 1},
        'Сотрудник УК/ТСЖ': {'greet': 'Приятно поработать!', 'role': 2},
    }
    with open(settings.MEDIA_ROOT + f'{message.chat.id}.txt', 'a') as f:
        f.writelines([str(roles[message.text]['role']) + '\n'])
    bot.send_message(message.chat.id, roles[message.text]['greet'])
    if message.text != 'Сотрудник УК/ТСЖ':
        markup = types.ReplyKeyboardMarkup(row_width=1)
        geo_button = types.KeyboardButton(text="Отправить местоположение", request_location=True)
        markup.add(geo_button)
        bot.send_message(message.chat.id, "Нажмите на кнопку и передайте координаты.", reply_markup=markup)
        bot.register_next_step_handler(message, location)
    else:
        lines = [line for line in open(settings.MEDIA_ROOT + f'{message.chat.id}.txt')]
        employee = Employee(external_id=lines[0], surname=lines[1], name=lines[2], tg_role=roles[message.text]['role'],
                            position_id=random.choice(
                                [1, 2]))  # TODO Хреновая реализация, но для ускорения разработки пока так
        employee.save()
        org = Organization.objects.get(pk=1)
        employee.organizations.add(org)
        delete_file(settings.MEDIA_ROOT + f'{message.chat.id}.txt')
        bot.send_message(message.chat.id, "Здесь Вы будете получать заявки для выполнения.",
                         reply_markup=types.ReplyKeyboardRemove())


# @bot.message_handler(content_types=["location"])
def location(message):
    if message.location is not None:
        # по координатам получаем адрес и присылаем человеку, ему останется проверить адрес и внести правки.
        client = Client(YANDEX_API_KEY)
        address = client.address(Decimal(message.location.longitude), Decimal(message.location.latitude))

        markup = types.ReplyKeyboardMarkup(row_width=1)
        yes_button = types.KeyboardButton(text='Да')
        no_button = types.KeyboardButton(text='Нет')
        markup.row(yes_button, no_button)
        bot.send_message(message.chat.id, address)  # 'Ваш адрес: г. Волгодонск, ул. Моская, д. 92'
        bot.send_message(message.chat.id, 'Верно ли определён Ваш адрес?', reply_markup=markup)
        with open(settings.MEDIA_ROOT + f'{message.chat.id}.txt', 'a') as f:
            f.writelines([address + '\n'])
        bot.register_next_step_handler(message, check_address)


def check_address(message):
    with open(settings.MEDIA_ROOT + f'{message.chat.id}.txt', 'a') as f:
        f.writelines([message.text + '\n'])
    if message.text == 'Да':
        bot.send_message(message.chat.id, 'Введите номер квартиры.',
                         reply_markup=types.ReplyKeyboardRemove())
    else:
        bot.send_message(message.chat.id, 'Введите свой адрес и номер квартиры.',
                         reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, finish_register)


def finish_register(message):
    bot.send_message(message.chat.id, 'Спасибо, что уделил мне время! Теперь можете оставить своё сообщение')
    time.sleep(3)
    bot.send_message(message.chat.id, 'Чуть не забыл самое главное, сообщения можно как писать так и наговаривать.'
                                      ' Не переживайте, я пойму)')
    file_path = settings.MEDIA_ROOT + f'{message.chat.id}.txt'
    lines = [line for line in open(file_path)]

    # Проверка регистрировался ли житель ранее, если да, то меняем его данные на вновь предоставленные
    if Citizen.objects.filter(external_id=message.chat.id).count() > 0:
        cit = Citizen.objects.get(external_id=message.chat.id)
    else:
        cit = Citizen()

    # TODO Здесь нужно дописать код по поиску организации(УК/ТСЖ), которая обслуживает указанный адрес

    cit.external_id = lines[0].strip('\n')
    cit.surname = lines[1].strip('\n')
    cit.name = lines[2].strip('\n')
    cit.tg_role = lines[3].strip('\n')
    cit.address = lines[4].strip('\n') + f', {message.text}' if lines[5].strip('\n') == 'Да' else f' {message.text}'
    cit.organization_id = 1
    cit.save()
    delete_file(file_path)


def get_right_role(right_text: str):
    for role, text_list in stub_problems.items():
        for text in text_list:
            if text.lower() == right_text.lower():
                return role


@bot.message_handler(func=lambda message: True, content_types=['text', 'voice'])
def echo_message(message):
    if Citizen.objects.filter(external_id=message.chat.id).count() > 0:
        citizen = Citizen.objects.get(external_id=message.chat.id)
        if message.content_type == 'voice':
            bot.send_message(message.chat.id, 'Обработка голоса!!!', reply_markup=types.ReplyKeyboardRemove())
            # TODO Здесь дописать код обработки голоса с использованием сервиса Yandex SpeechKit
        else:
            employee_role = get_right_role(message.text)
            if employee_role:
                bot.send_message(message.chat.id, 'Ваш запрос в работе!', reply_markup=types.ReplyKeyboardRemove())
                new_appeal = Appeal(
                    author=citizen,
                    # Пока чтовыбирается категория "Работы по договору".
                    # после обучения на датасетах можно будет это доверить боту
                    category_id=2,
                    description=message.text
                )
                new_appeal.save()
                # employee_role = get_right_role(message.text)
                employees = Employee.objects.filter(tg_role=2, position_id=employee_role)
                for employee in employees:
                    markup = types.InlineKeyboardMarkup()
                    subscribe_btn = types.InlineKeyboardButton('Принять в работу', callback_data='appeal_' + str(new_appeal.id))
                    cancel_bt = types.InlineKeyboardButton('Отклонить', callback_data=-1)
                    markup.add(subscribe_btn, cancel_bt)
                    # markup.add(cancel_bt)
                    text = f'Поступила новая заявка \n\n{message.text}'
                    text += f'\n\nАдрес: {citizen.address}'
                    bot.send_message(employee.external_id, text, reply_markup=markup)
                    bot.register_next_step_handler(message, subscription)
            else:
                bot.send_message(
                    message.chat.id,
                    'Я пока не знаю как обработать Ваш запрос, но я его передал квалифицированному сотруднику!',
                    reply_markup=types.ReplyKeyboardRemove()
                )

    else:
        bot.reply_to(message, 'Извините, Вы ещё не представились. Для этого нажмите /start',
                     reply_markup=types.ReplyKeyboardRemove())


@bot.callback_query_handler(func=lambda call: call.data.startswith('appeal_'))
def subscription(call):
    call_data = call.data.rsplit('_', maxsplit=1)
    if int(call_data[1]) > 0:

        # TODO проверка есть ли уже подписки на эту заявку!!!

        bot.answer_callback_query(call.id, text='Спасибо! Уточним пару моментов.')

        # TODO Проверка, если сотрудник не найден (мловероятно с учетом того, что он сам отвечает),
        #   но на случай ошибок связанных с БД
        employee = Employee.objects.get(external_id=call.message.chat.id)
        new_subscription = Subscription(
            appeal_id=call_data[1],
            employee=employee,
        )
        new_subscription.save()

        with open(settings.MEDIA_ROOT + f'{call.message.chat.id}_subscription.txt', 'w') as f:
            f.writelines([str(new_subscription.id)])
        markup = types.ReplyKeyboardMarkup(row_width=1)
        get_location = types.KeyboardButton('Проинформировать о своём местоположении', request_location=True)
        markup.add(get_location)
        bot.send_message(call.message.chat.id, 'Нужна информация где Вы находитесь.', reply_markup=markup)
        bot.register_next_step_handler(call.message, finish_subscription)
    else:
        bot.answer_callback_query(call.id, text='Очень жаль! ')
        time.sleep(3)
        bot.send_message(call.message.chat.id, 'Как будет что-то новое я Вам сообщу!')


# TODO Дать возможность пользователю выбор поделиться координатами или ввести адрес вручную
# @bot.message_handler(content_types=["location"])
def finish_subscription(message):
    if message.location is not None:
        lines = [line for line in open(settings.MEDIA_ROOT + f'{message.chat.id}_subscription.txt')]
        subscription_id = lines[0]

        appeal_subscription = Subscription.objects.get(pk=subscription_id)
        employee = Employee.objects.get(external_id=message.chat.id)

        # TODO Выстроить маршрут используя Яндекс API, с помощью модуля request построить маршрут и вернуть время
        #   передвижения travel_time. Сейчас используется заглушка, т.к. ограниченное время отведено на реализацию
        print(Decimal(message.location.longitude), Decimal(message.location.latitude))

        emp_markup = types.InlineKeyboardMarkup()
        complete_btn = types.InlineKeyboardButton('Услуга оказана', callback_data='complete_' + subscription_id)
        emp_markup.add(complete_btn)
        travel_time = '1ч. 13мин'
        bot.send_message(message.chat.id, 'Спасибо за предоставленную информацию.',
                         reply_markup=types.ReplyKeyboardRemove())
        bot.send_message(message.chat.id,
                         f'Отправляйтесь по указанному адресу! В вашем распоряжении есть {travel_time}',
                         reply_markup=emp_markup)
        text = 'Здравствуйте!'
        text += '\n\nНа Вашу заявку откликнулся специалист:'
        text += '\n\n' + employee.surname.strip('\n') + ' ' + employee.name.strip('\n')
        text += f'\n\n Он будет у Вас через {travel_time}'

        # Нужен ли здесь ReplyKeyboardRemove?
        bot.send_message(appeal_subscription.appeal.author.external_id, text, reply_markup=types.ReplyKeyboardRemove())
        delete_file(settings.MEDIA_ROOT + f'{message.chat.id}_subscription.txt')
    else:
        # TODO Продумать как сотруднику снова показать форму принятия в работу заявки
        bot.send_message(message.chat.id, "Произошла ошибка при определении Ваших координат!")


@bot.callback_query_handler(func=lambda call: call.data.startswith('complete_'))
def complete_event(call):
    bot.answer_callback_query(call.id, text='Принято')
    call_data = call.data.rsplit('_', maxsplit=1)
    completed_subscription = Subscription.objects.get(pk=call_data[1])
    bot.send_message(call.message.chat.id, 'Спасибо за проделанную работу! Если появится что-то новое, я Вам напишу!')

    rating_markup = types.InlineKeyboardMarkup()
    one_btn = types.InlineKeyboardButton('1', callback_data=f'rating_1|{completed_subscription.id}')
    two_btn = types.InlineKeyboardButton('2', callback_data=f'rating_2|{completed_subscription.id}')
    three_btn = types.InlineKeyboardButton('3', callback_data=f'rating_3|{completed_subscription.id}')
    four_btn = types.InlineKeyboardButton('4', callback_data=f'rating_4|{completed_subscription.id}')
    five_btn = types.InlineKeyboardButton('5', callback_data=f'rating_5|{completed_subscription.id}')
    rating_markup.add(one_btn, two_btn, three_btn, four_btn, five_btn)
    text = f'Ваша заявка: "{completed_subscription.appeal.description}" отработана. Пожалуйста оцените работу.'
    bot.send_message(completed_subscription.appeal.author.external_id, text, reply_markup=rating_markup)


def get_rate_description(rate: int):
    return {
        rate < 3: 'В будущем Вам надо постараться!',
        3 <= rate < 5: 'Хорошо, но есть куда стремиться!',
        5 == rate: 'Так держать, всё на высшем уровне!',
    }[True]


@bot.callback_query_handler(func=lambda call: call.data.startswith('rating_'))
def rate_appeal(call):
    call_data = call.data.rsplit('|', maxsplit=1)
    rating = call_data[0].rsplit('_', maxsplit=1)[1]
    subscription_id = call_data[1]
    rate_subscription = Subscription.objects.get(pk=subscription_id)
    bot.answer_callback_query(call.id, text='Принято')
    bot.send_message(call.message.chat.id, 'Спасибо за ответ! Ваше мнение очень важно для нас!')
    bot.send_message(call.message.chat.id, 'Обращайтесь ко мне в любое время!',
                     reply_markup=types.ReplyKeyboardRemove())

    bot.send_message(rate_subscription.employee.external_id,
                     f'Вам поставили оценку - {rating}\n\n{get_rate_description(int(rating))}',
                     reply_markup=types.ReplyKeyboardRemove())


@require_http_methods(['POST', 'GET'])
@csrf_exempt
def set_webhook(request):
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.body.decode('utf-8'))
        bot.process_new_updates([update])

        return HttpResponse("OK")
    return HttpResponseForbidden("BAD")
