#!/usr/bin/env python3.7

from random import randint
import logging

import requests
from pony.orm import db_session

import handlers
import settings
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

from models import UserState, Ticket

log = logging.getLogger("bot")


def configure_logging():
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    stream_handler.setLevel(logging.INFO)
    log.addHandler(stream_handler)

    file_handler = logging.FileHandler("bot_log")
    file_handler.setFormatter(logging.Formatter("%(asktime)s %(levelname)s %(message)s"))
    file_handler.setLevel(logging.DEBUG)
    log.addHandler(file_handler)
    log.setLevel(logging.DEBUG)


class Bot:
    """
    Сценарий заказа авиабилетов на самолет через vk.com
    Use python3.7
    """

    def __init__(self, group_id, token):
        """
        :param group_id: group id из группы vk
        :param token: секретный токен
        """
        self.group_id = group_id
        self.token = token
        self.vk = vk_api.VkApi(token=self.token)
        self.long_poll = VkBotLongPoll(self.vk, self.group_id)
        self.api = self.vk.get_api()
        self.default_steps = ['step_5', 'step_6', 'step_7']  # при изменении данных, эти шаги по дефолту не меняются,
        # пользователь их заного не проходит

    def run(self):
        """Запуск бота"""
        for event in self.long_poll.listen():
            try:
                self.on_event(event)
            except Exception as exc:
                log.exception("Ошибка в обработке события", exc)

    @db_session
    def on_event(self, event: VkBotEventType):
        """
        Отправляет сообщение назад, если сообщение текстовое
        :param event: VkBotMessageEvent object
        :return: None
        """
        if event.type != VkBotEventType.MESSAGE_NEW:
            log.info(f'Мы пока не умеем обрабатывать событие такого типа, {event.type}')
            return

        user_id = event.object.peer_id
        text = event.object.text
        state = UserState.get(user_id=str(user_id))

        for intent in settings.INTENTS:
            log.debug(f'User gets {intent}')
            if any(token in text.lower() for token in intent['tokens']):
                if intent['answer']:
                    self.send_text(intent['answer'], user_id)
                else:
                    self.start_scenario(user_id, intent['scenario'], text)
                break
        else:
            if state is not None:
                self.continue_scenario(text, state, user_id)
            else:
                self.send_text(settings.DEFAULT_ANSWER, user_id)

    def send_text(self, text_to_send, user_id):
        self.api.messages.send(message=text_to_send,
                               random_id=randint(0, 2 ** 20),
                               peer_id=user_id)

    def send_image(self, image, user_id):
        upload_url = self.api.photos.getMessagesUploadServer()['upload_url']
        upload_data = requests.post(url=upload_url, files={'photo': ('image.png', image, 'image/png')}).json()
        image_data = self.api.photos.saveMessagesPhoto(**upload_data)
        owner_id = image_data[0]['owner_id']
        media_id = image_data[0]['id']
        attachment = f'photo{owner_id}_{media_id}'

        self.api.messages.send(attachment=attachment,
                               random_id=randint(0, 2 ** 20),
                               peer_id=user_id)

    def send_step(self, step, user_id, text, context):
        if 'text' in step:
            self.send_text(step['text'].format(**context), user_id)
        if 'image' in step:
            handler = getattr(handlers, step['image'])
            image = handler(text, context)
            self.send_image(image, user_id)

    def start_scenario(self, user_id, scenario_name, text):
        scenario = settings.SCENARIOS[scenario_name]
        first_step = scenario['first_step']
        step = scenario['steps'][first_step]
        UserState(user_id=str(user_id), scenario_name=scenario_name, step_name=first_step, context={})
        self.send_step(step, user_id, text, context={})

    def continue_scenario(self, text, state, user_id):
        steps = settings.SCENARIOS[state.scenario_name]["steps"]
        step = steps[state.step_name]
        handler = getattr(handlers, step['handler'])
        response = handler(text, state.context)
        if response == 'next':  # step complete
            next_step = steps[step['next_step']]
            self.send_step(next_step, user_id, text, state.context)
            if next_step['next_step']:
                # switch to next step
                state.step_name = step['next_step']
            else:
                # finish scenario
                done_steps = state.context["done_steps"]
                log.info(f'{done_steps}')
                Ticket(
                    dep_city=done_steps['dep_city'],
                    dest_city=done_steps['dest_city'],
                    fly_date=done_steps['fly_date'],
                    flight=done_steps['flight'],
                    places=done_steps['places'],
                    comment=done_steps['comment'],
                    name=done_steps['name'],
                    phone_number=done_steps['phone_number']
                )
                state.delete()

        elif response == 'back':  # step back
            next_step = steps[step['prev_step']]
            state.step_name = step['prev_step']
            self.send_step(next_step, user_id, text, state.context)

        elif response == 'change':  # change data
            next_step = state.context['next_step']
            step = steps[next_step]
            state.step_name = next_step
            self.send_step(step, user_id, text, state.context)
            if next_step in self.default_steps:
                step['next_step'] = 'step_8'

        elif response == 'return':  # extra step for incorrect data
            step = steps['step_8*']
            state.step_name = 'step_8*'
            self.send_step(step, user_id, text, state.context)
        else:
            text_to_send = step['failure_text'].format(**state.context)
            self.send_text(text_to_send, user_id)


if __name__ == "__main__":
    bot = Bot(settings.GROUP_ID, settings.TOKEN)
    bot.run()
