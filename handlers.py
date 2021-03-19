#!/usr/bin/env python3.7
import locale
import re
import json
from datetime import datetime
from make_json_new import make_data as md_flights
from generate_ticket import make_ticket


class Dispatcher:
    md_flights()
    locale.setlocale(locale.LC_ALL, "ru")

    def __init__(self, data):
        self.departure_cities = None
        self.data = data
        self.current_date = datetime.now()

    def read_data(self):
        with open(self.data, 'r', encoding='utf-8') as data_file:
            self.departure_cities = json.load(data_file)
        return self.departure_cities


disp = Dispatcher('Files/Cities_data.json')
disp.read_data()
RE_NAME = r'^[\w\-\s]{3,30}$'
RE_NUMBER = r'[1-5]'
MAX_DATE = '30-04-2021'
RE_PHONE_NUMBER = re.compile(r"\+?\d[\( -]?\d{3}[\) -]?\d{3}[ -]?\d{2}[ -]?\d{2}")


def check_step(text):
    """
    check_step - функция, которая принимает на вход text (текст входящего сообщения), проверяет text на конкретные
    команды от пользователя, и в случае их нахождения возвращает ключи:
    'back' - шаг назад,
    'return' - изменить данные конкретного шага
     False - если делать ничего не нужно
    """
    if text.lower() == 'назад':
        return 'back'
    elif text == '/return':
        return 'return'
    else:
        return False


"""
Handler - функция, которая принимает на вход text (текст входящего сообщения) и context (dict) и возвращает:
результат функции check_step, если пришла конкретная команда от пользователя,
'next' - если шаг пройден,
- False - если данные введены неправильно,
"""


def handle_name(text, context):
    check = check_step(text)
    if not check:
        match = re.match(RE_NAME, text)
        if match:
            context['done_steps']['name'] = text
            context['input_data'] = make_data(context)
            return 'next'
        else:
            return False
    else:
        return check


def handle_departure_city(text, context):
    check = check_step(text)
    if not check:
        try:
            """Эта конструкция для того, чтобы можно было ввести номер города из списка"""
            city = context["departure_cities"].split('\n')[int(text) - 1].split('.')[1][1:]
            text = city
        except Exception:
            pass
        cities = disp.departure_cities
        if text in cities.keys():
            context['destination_cities_data'] = cities[text]
            context['done_steps'] = {}
            context['done_steps']['dep_city'] = text
            context['input_data'] = make_data(context)
            context['destination_city'] = text
            return 'next'
        else:
            context['departure_cities'] = str()
            for number, city in enumerate(cities.keys()):
                context['departure_cities'] += f'{number + 1}. {city}\n'
            context['error'] = f'К сожалению, введенный вами город не распознан.\n' \
                               f'Доступны следующие варианты городов, из которых есть ' \
                               f'рейсы:\n{context["departure_cities"]}'
            return False
    else:
        return check


def handle_destination_city(text, context):
    check = check_step(text)
    if not check:
        try:
            """Эта конструкция для того, чтобы можно было ввести номер города из списка"""
            city = context["destination_cities"].split('\n')[int(text) - 1].split('.')[1][1:]
            text = city
        except Exception:
            pass
        if context['done_steps']['dep_city'] == text:
            context['error'] = f'Вы уже находитесь в {text}. Попробуйте еще раз'
            return False
        cities = context['destination_cities_data']
        if text in cities.keys():
            context['done_steps']['dest_city'] = text
            context['arrival_city'] = cities[text]
            context['input_data'] = make_data(context)
            return 'next'
        else:
            context['destination_cities'] = str()
            for number, city in enumerate(cities.keys()):
                context['destination_cities'] += f'{number + 1}. {city}\n'
            context['error'] = f'К сожалению, нет прямого рейса между {context["done_steps"]["dep_city"]}' \
                               f' и {text}. Доступны следующие варианты городов,' \
                               f' в которые есть прямые рейсы:\n{context["destination_cities"]}'
            return False
    else:
        return check


def handle_input_date(text, context):
    check = check_step(text)
    if not check:
        max_date = datetime.strptime(MAX_DATE, "%d-%m-%Y")
        try:
            input_date = datetime.strptime(text, "%d-%m-%Y")
            if input_date > max_date:
                context['error'] = f'К сожалению, после {MAX_DATE} рейсы еще не сформированы. ' \
                                   f'Выберите дату до {MAX_DATE}'
                return False
            elif input_date < disp.current_date:
                context['error'] = 'К сожалению, отправить вас в прошлое мы не можем. Попробуйте еще раз'
                return False
            else:
                data = []
                for flight in context['arrival_city']:
                    date = datetime.strptime(flight, "%Y-%m-%d %H:%M:%S")
                    app_flight = str(date.strftime('%d %B %Y, %H:%M, %a'))
                    data.append(app_flight) if date >= input_date else None
                context['flights_data'] = data[:5]
                context['flights'] = str()
                for number, flight in enumerate(context['flights_data']):
                    context['flights'] += f'{number + 1}. {flight}\n'
                context['done_steps']['fly_date'] = text
                context['input_data'] = make_data(context)
                return 'next'

        except ValueError:
            context['error'] = 'Неверный формат. Введите дату в формате dd-mm-yyyy'
            return False
    else:
        return check


def handle_flight_number(text, context):
    check = check_step(text)
    if not check:
        lenn = len(context['flights_data'])
        if lenn > 0:
            re_flight_number = f'[1-{lenn}]'
            match = re.match(re_flight_number, text)
            if match and len(text) == 1:
                try:
                    context['done_steps']['flight'] = context['flights_data'][int(text) - 1]
                    context['input_data'] = make_data(context)
                    return 'next'
                except ValueError:
                    context['error'] = f'Введите значение от 1 до {lenn}'
                    return False
            else:
                context['error'] = f'Введите значение от 1 до {lenn}'
                return False
        else:
            context['error'] = f'К сожалению, на выбранную вами дату нет сформированных рейсов'
    else:
        return check


def handle_places(text, context):
    check = check_step(text)
    if not check:
        match = re.match(RE_NUMBER, text)
        if match and len(text) == 1:
            context['done_steps']['places'] = int(text)
            context['input_data'] = make_data(context)
            return 'next'
        else:
            return False
    else:
        return check


def make_data(context):
    n = len(context['done_steps'])
    context['input_data'] = str()
    for number in range(n):
        context['input_data'] += {
            0: '1. Город отправления: {dep_city}\n',
            1: '2. Город назначения: {dest_city}\n',
            2: '3. Желаемая дата вылета: {fly_date}\n',
            3: '4. Рейс: {flight}\n',
            4: '5. Мест: {places}\n',
            5: '6. Комментарий: {comment}\n',
            6: '7. ФИО: {name}\n'
        }[number].format(**context['done_steps'])
    return context['input_data']


def handle_comment(text, context):
    check = check_step(text)
    if not check:
        context['done_steps']['comment'] = str(text)
        context['input_data'] = make_data(context)
        return 'next'
    else:
        return check


def check_data(text, context):
    check = check_step(text)
    if not check:
        yes_variables = ["да", "верно", "правильно"]
        no_variables = ["нет", "не верно"]
        if text.lower() in yes_variables:
            return 'next'
        elif text.lower() in no_variables:
            return 'return'
        else:
            return False
    else:
        return check


def change_data(text, context):
    lenn = len(context['done_steps'])
    re_changes = f'[1-{lenn}]'
    match = re.match(re_changes, text)
    if match:
        context['next_step'] = f'step_{text}'
        return 'change'
    else:
        context['error'] = f'Введено неверное значение. Введите число от 1 до {lenn}'
        return False


def handle_phone_number(text, context):
    check = check_step(text)
    if not check:
        number = re.match(RE_PHONE_NUMBER, text)
        if number:
            context['done_steps']['phone_number'] = text
            return 'next'
        else:
            context['error'] = f'Введенный номер {text} не соответствует формату +7-123-456-78-90. Попробуйте еще раз'
            return False
    else:
        return check


def generate_ticket(text, context):
    data = context['done_steps']
    return make_ticket(fio=data['name'], from_=data['dep_city'], to=data['dest_city'], date=data['fly_date'])
