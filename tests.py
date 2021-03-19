import locale
from copy import deepcopy
from datetime import datetime
from unittest import TestCase
from unittest.mock import patch, Mock

from pony.orm import db_session, rollback
from vk_api.bot_longpoll import VkBotMessageEvent

import settings
from generate_ticket import make_ticket
from handlers import disp, MAX_DATE
from bot import Bot


def isolate_db(test_func):
    def wrapper(*args, **kwargs):
        with db_session:
            test_func(*args, **kwargs)
            rollback()

    return wrapper


class Test1(TestCase):
    RAW_EVENT = {'type': 'message_new',
                 'object': {'date': 1608819492, 'from_id': 361443073, 'id': 1153, 'out': 0, 'peer_id': 361443073,
                            'text': '123', 'conversation_message_id': 1102, 'fwd_messages': [], 'important': False,
                            'random_id': 0, 'attachments': [], 'is_hidden': False},
                 'group_id': 199325514}
    max_data = MAX_DATE
    locale.setlocale(locale.LC_ALL, "ru")

    flight_data = {  # данные по рейсам
        'all_cities': str(),
        'dep_cities': str(),
        'dep_city': str(),
        'dest_city': str(),
        'input_date': str(),
        'flights_data': None,
        'flights': str(),
        'flight': None
    }

    errors = {}

    def test_run(self):
        count = 5
        obj = {'a': 1}
        events = [obj] * count
        long_poller_mock = Mock(return_value=events)
        long_poller_listen_mock = Mock()
        long_poller_listen_mock.listen = long_poller_mock

        with patch('bot.vk_api.VkApi'):
            with patch('bot.VkBotLongPoll', return_value=long_poller_listen_mock):
                bot = Bot('', '')
                bot.on_event = Mock()
                bot.send_image = Mock()
                bot.run()

                bot.on_event.assert_called()
                bot.on_event.assert_any_call(obj)
                assert bot.on_event.call_count == count

    def prepare_data_for_tests(self):
        all_cities_data = disp.departure_cities
        self.flight_data['dep_city'] = self.INPUTS['test_msg_dep_city_2']
        self.flight_data['dest_city'] = self.INPUTS['test_msg_dest_city_3']
        for number, city in enumerate(all_cities_data.keys()):
            self.flight_data['all_cities'] += f'{number + 1}. {city}\n'
        dep_cities_data = all_cities_data[self.INPUTS['test_msg_dep_city_2']]
        dest_cities_data = dep_cities_data[self.INPUTS['test_msg_dest_city_3']]
        for number, city in enumerate(dep_cities_data.keys()):
            self.flight_data['dep_cities'] += f'{number + 1}. {city}\n'
        input_date = datetime.strptime(self.INPUTS['test_msg_date_4'], "%d-%m-%Y")
        all_flights = []
        for flight in dest_cities_data:
            date = datetime.strptime(flight, "%Y-%m-%d %H:%M:%S")
            app_flight = str(date.strftime('%d %B %Y, %H:%M, %a'))
            all_flights.append(app_flight) if date >= input_date else None
        self.flight_data['flights_data'] = all_flights[:5]
        for number, flight in enumerate(self.flight_data['flights_data']):
            self.flight_data['flights'] += f'{number + 1}. {flight}\n'
        self.flight_data['flight'] = self.flight_data["flights_data"][int(self.INPUTS['test_msg_flight_number_2']) - 1]
        return self.flight_data

    def make_errors(self):
        data = self.prepare_data_for_tests()
        self.errors['err_dep_city'] = f'К сожалению, введенный вами город не распознан.\n' \
                                      f'Доступны следующие варианты городов, из которых есть рейсы:' \
                                      f'\n{data["all_cities"]}'
        self.errors['err_dest_city_1'] = f'К сожалению, нет прямого рейса между {self.INPUTS["test_msg_dep_city_2"]}' \
                                         f' и {self.INPUTS["test_msg_dest_city_1"]}. Доступны следующие варианты' \
                                         f' городов, в которые есть прямые рейсы:\n{self.flight_data["dep_cities"]}'
        self.errors[
            'err_dest_city_2'] = f'Вы уже находитесь в {self.INPUTS["test_msg_dest_city_2"]}. Попробуйте еще раз'
        self.errors['err_date_1'] = 'Неверный формат. Введите дату в формате dd-mm-yyyy'
        self.errors['err_date_2'] = 'К сожалению, отправить вас в прошлое мы не можем. Попробуйте еще раз'
        self.errors['err_date_3'] = f'К сожалению, после {self.max_data} рейсы еще не сформированы. ' \
                                    f'Выберите дату до {self.max_data}'
        self.errors['err_flight_number_1'] = f'Введите значение от 1 до {len(self.flight_data["flights_data"])}'
        self.errors['err_phone_number_1'] = f'Введенный номер {self.INPUTS["test_msg_phone_number_1"]}' \
                                            f' не соответствует формату +7-123-456-78-90. Попробуйте еще раз'
        return self.errors

    INPUTS = {
        'test_msg_1': 'Привет',
        'test_msg_help': 'помощь',
        'test_msg_2': 'бла бла бла',
        'test_msg_start': 'старт',
        'test_msg_dep_city_1': 'asdsdsg',
        'test_msg_dep_city_2': 'Москва',
        'test_msg_dest_city_1': 'лвоаыва',
        'test_msg_dest_city_2': 'Москва',
        'test_msg_dest_city_3': 'Архангельск',
        'test_msg_date_1': '23.03.2021',
        'test_msg_date_2': '13-03-2000',
        'test_msg_date_3': '23-03-2022',
        'test_msg_date_4': '23-03-2021',
        'test_msg_flight_number_1': '6',
        'test_msg_flight_number_2': '1',
        'test_msg_place_number_1': '8',
        'test_msg_place_number_2': '2',
        'test_msg_comment': '123',
        'test_name_1': '12',
        'test_name_2': 'Вася',
        'test_msg_correct': 'да',
        'test_msg_phone_number_1': '12345',
        'test_msg_phone_number_2': '+7-123-451-12-23',
    }

    def collect_ticket_data(self):
        data = {
            'Город отправления': self.INPUTS['test_msg_dep_city_2'],
            'Город назначения': self.INPUTS['test_msg_dest_city_3'],
            'Желаемая дата вылета': self.INPUTS['test_msg_date_4'],
            'Рейс': self.flight_data['flight'],
            'Мест': self.INPUTS['test_msg_place_number_2'],
            'Комментарий': self.INPUTS['test_msg_comment'],
            'ФИО': self.INPUTS['test_name_2'],
        }
        text_data, n = str(), 1
        for item, value in data.items():
            text_data += f'{n}. {item}: {value}\n'
            n += 1
        return text_data

    @isolate_db
    def test_run_ok(self):
        send_mock = Mock()
        api_mock = Mock()
        api_mock.messages.send = send_mock
        self.make_errors()
        text_data = self.collect_ticket_data()
        expected_outputs = [
            settings.INTENTS[0]['answer'],
            settings.INTENTS[1]['answer'],
            settings.DEFAULT_ANSWER,
            settings.SCENARIOS['make a ticket']['steps']['step_1']['text'],
            settings.SCENARIOS['make a ticket']['steps']['step_1']['failure_text'].format(
                error=self.errors['err_dep_city']),
            settings.SCENARIOS['make a ticket']['steps']['step_2']['text'],
            settings.SCENARIOS['make a ticket']['steps']['step_2']['failure_text'].format(
                error=self.errors['err_dest_city_1']),
            settings.SCENARIOS['make a ticket']['steps']['step_2']['failure_text'].format(
                error=self.errors['err_dest_city_2']),
            settings.SCENARIOS['make a ticket']['steps']['step_3']['text'],
            settings.SCENARIOS['make a ticket']['steps']['step_3']['failure_text'].format(
                error=self.errors['err_date_1']),
            settings.SCENARIOS['make a ticket']['steps']['step_3']['failure_text'].format(
                error=self.errors['err_date_2']),
            settings.SCENARIOS['make a ticket']['steps']['step_3']['failure_text'].format(
                error=self.errors['err_date_3']),
            settings.SCENARIOS['make a ticket']['steps']['step_4']['text'].format(
                flights=self.flight_data['flights']),
            settings.SCENARIOS['make a ticket']['steps']['step_4']['failure_text'].format(
                error=self.errors['err_flight_number_1']),
            settings.SCENARIOS['make a ticket']['steps']['step_5']['text'],
            settings.SCENARIOS['make a ticket']['steps']['step_5']['failure_text'],
            settings.SCENARIOS['make a ticket']['steps']['step_6']['text'],
            settings.SCENARIOS['make a ticket']['steps']['step_7']['text'],
            settings.SCENARIOS['make a ticket']['steps']['step_7']['failure_text'],
            settings.SCENARIOS['make a ticket']['steps']['step_8']['text'].format(input_data=text_data),
            settings.SCENARIOS['make a ticket']['steps']['step_9']['text'],
            settings.SCENARIOS['make a ticket']['steps']['step_9']['failure_text'].format(
                error=self.errors['err_phone_number_1']),
            settings.SCENARIOS['make a ticket']['steps']['step_10']['text'],
        ]
        events = []
        for input_text in self.INPUTS.values():
            event = deepcopy(self.RAW_EVENT)
            event['object']['text'] = input_text
            events.append(VkBotMessageEvent(event))

        long_poller_mock = Mock()
        long_poller_mock.listen = Mock(return_value=events)

        with patch('bot.VkBotLongPoll', return_value=long_poller_mock):
            bot = Bot('', '')
            bot.api = api_mock
            bot.send_image = Mock()
            bot.run()

        assert send_mock.call_count == len(self.INPUTS)

        real_outputs = []
        for call in send_mock.call_args_list:
            args, kwargs = call
            real_outputs.append(kwargs['message'])
        assert real_outputs == expected_outputs

    def test_image_generation(self):
        ticket_file = make_ticket(
            fio='Клементьев Данила Сергеевич',
            from_='Moscow',
            to='London',
            date='27/02/2020'
        )

        with open('files/test_ticket.png', 'rb') as expected_file:
            expected_bytes = expected_file.read()

        assert ticket_file.read() == expected_bytes
