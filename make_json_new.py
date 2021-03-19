from random import randint, choice
import json
from datetime import datetime


class TimeTable:
    def __init__(self, inc_file, out_file):
        self.inc_file = inc_file
        self.out_file = out_file
        self.cities = {}
        # self.months = ['1_31', '2_28', '3_31', '4_30', '5_31', '6_30', '7_31', '8_31', '9_30',
        #                '10_31', '11_30', '12_31']
        self.months = ['2_28', '3_31', '4_30']

    def make_timetable(self):
        time_table = []
        for months in self.months:
            month, month_days = months.split('_')
            for _ in range(randint(1, 3)):  # сколько дней в неделю будет рейс
                for _ in range(randint(1, 3)):  # сколько раз в день будет рейс
                    hour = randint(0, 23)
                    minute = choice([0, 15, 30, 45])
                    for day in range(randint(1, 4), int(month_days), 7):  # сколько раз в неделю будет рейс
                        date = datetime(day=day, month=int(month), year=2021, hour=hour, minute=minute)
                        time_table.append(str(date))

        return sorted(time_table)

    def read_file(self):
        cities = []
        with open(self.inc_file, 'r', encoding='utf-8') as inc_file:
            for line in inc_file:
                city = line.split('\n')
                cities.append(city[0])

        return cities

    def prepare_data(self):
        cities_2 = self.read_file()
        city_data, arrival_city = [], {}
        for _ in range(15):
            city = cities_2.pop(0)
            if arrival_city != city:
                arrival_city[city] = self.make_timetable()

        city_data.append(arrival_city)
        return city_data

    def make_data(self):
        for city in self.read_file():
            for data in self.prepare_data():
                self.cities[city] = data

        cities_data = json.dumps(self.cities, indent=4, ensure_ascii=False)

        with open(self.out_file, 'w', encoding='utf8') as file:
            file.write(cities_data)


def make_data():
    time_table = TimeTable('Files/city_data.txt', 'Files/Cities_data.json')
    time_table.make_data()
