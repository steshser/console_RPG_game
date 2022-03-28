# -*- coding: utf-8 -*-

# Подземелье было выкопано ящеро-подобными монстрами рядом с аномальной рекой, постоянно выходящей из берегов.
# Из-за этого подземелье регулярно затапливается, монстры выживают, но не герои, рискнувшие спуститься к ним в поисках
# приключений.
# Почуяв безнаказанность, ящеры начали совершать набеги на ближайшие деревни. На защиту всех деревень не хватило
# солдат и вас, как известного в этих краях героя, наняли для их спасения.
#
# Карта подземелья представляет собой json-файл под названием rpg.json. Каждая локация в лабиринте описывается объектом,
# в котором находится единственный ключ с названием, соответствующем формату "Location_<N>_tm<T>",
# где N - это номер локации (целое число), а T (вещественное число) - это время,
# которое необходимо для перехода в эту локацию. Например, если игрок заходит в локацию "Location_8_tm30000",
# то он тратит на это 30000 секунд.
# По данному ключу находится список, который содержит в себе строки с описанием монстров а также другие локации.
# Описание монстра представляет собой строку в формате "Mob_exp<K>_tm<M>", где K (целое число) - это количество опыта,
# которое получает игрок, уничтожив данного монстра, а M (вещественное число) - это время,
# которое потратит игрок для уничтожения данного монстра.
# Например, уничтожив монстра "Boss_exp10_tm20", игрок потратит 20 секунд и получит 10 единиц опыта.
# Гарантируется, что в начале пути будет две локации и один монстр
# (то есть в коренном json-объекте содержится список, содержащий два json-объекта, одного монстра и ничего больше).
#
# На прохождение игры игроку дается 123456.0987654321 секунд.
# Цель игры: за отведенное время найти выход ("Hatch")
#
# По мере прохождения вглубь подземелья, оно начинает затапливаться, поэтому
# в каждую локацию можно попасть только один раз,
# и выйти из нее нельзя (то есть двигаться можно только вперед).
#
# Чтобы открыть люк ("Hatch") и выбраться через него на поверхность, нужно иметь не менее 280 очков опыта.
# Если до открытия люка время заканчивается - герой задыхается и умирает, воскрешаясь перед входом в подземелье,
# готовый к следующей попытке (игра начинается заново).
#
# Гарантируется, что искомый путь только один, и будьте аккуратны в рассчетах!
# При неправильном использовании библиотеки decimal человек, играющий с вашим скриптом рискует никогда не найти путь.
#
# Также, при каждом ходе игрока ваш скрипт должен запоминать следущую информацию:
# - текущую локацию
# - текущее количество опыта
# - текущие дату и время (для этого используйте библиотеку datetime)
# После успешного или неуспешного завершения игры вам необходимо записать
# всю собранную информацию в csv файл dungeon.csv.
# Названия столбцов для csv файла: current_location, current_experience, current_date
#
#
# Пример взаимодействия с игроком:
#
# Вы находитесь в Location_0_tm0
# У вас 0 опыта и осталось 123456.0987654321 секунд до наводнения
# Прошло времени: 00:00
#
# Внутри вы видите:
# — Вход в локацию: Location_1_tm1040
# — Вход в локацию: Location_2_tm123456
# Выберите действие:
# 1.Атаковать монстра
# 2.Перейти в другую локацию
# 3.Сдаться и выйти из игры
#
# Вы выбрали переход в локацию Location_2_tm1234567890
#
# Вы находитесь в Location_2_tm1234567890
# У вас 0 опыта и осталось 0.0987654321 секунд до наводнения
# Прошло времени: 20:00
#
# Внутри вы видите:
# — Монстра Mob_exp10_tm10
# — Вход в локацию: Location_3_tm55500
# — Вход в локацию: Location_4_tm66600
# Выберите действие:
# 1.Атаковать монстра
# 2.Перейти в другую локацию
# 3.Сдаться и выйти из игры
#
# Вы выбрали сражаться с монстром
#
# Вы находитесь в Location_2_tm0
# У вас 10 опыта и осталось -9.9012345679 секунд до наводнения
#
# Вы не успели открыть люк!!! НАВОДНЕНИЕ!!! Алярм!
#
# У вас темнеет в глазах... прощай, принцесса...
# Но что это?! Вы воскресли у входа в пещеру... Не зря матушка дала вам оберег :)
# Ну, на этот-то раз у вас все получится! Трепещите, монстры!
# Вы осторожно входите в пещеру... (текст умирания/воскрешения можно придумать свой ;)
#
# Вы находитесь в Location_0_tm0
# У вас 0 опыта и осталось 123456.0987654321 секунд до наводнения
# Прошло уже 0:00:00
# Внутри вы видите:
#  ...
#  ...
#
# и так далее...
import json
import re
import csv
from decimal import Decimal, getcontext

REMAINING_TIME = '123456.0987654321'
EXPERIENCE_FOR_WIN = 280
OUT_CSV_FILE = 'dungeon.csv'
RPG_JSON_FILE = 'rpg.json'


# если изначально не писать число в виде строки - теряется точность!


class ActionError(Exception):
    pass


class GameRPG:

    def __init__(self, remaining_time, file, writer):
        self.file = file
        self.game_data_dict = {'current_location': self.file, 'current_experience': 0, 'current_date': 0}
        self.remaining_time = Decimal(remaining_time)
        self.next_locations_list = []
        self.actions_dict = {}
        self.run = True
        self.mobs_defeated = 0
        getcontext().prec = 17
        self.writer = writer
        self.current_location_for_print = 'Location_0_tm0'

    def check_time_remaining(self):
        if self.remaining_time < 0:
            print('Вы не успели открыть люк!!! НАВОДНЕНИЕ!!! Алярм! \n '
                  'У вас темнеет в глазах... прощай, принцесса... Но что это?! \n '
                  'Вы воскресли у входа в пещеру... Не зря матушка дала вам оберег :) \n '
                  'Ну, на этот-то раз у вас все получится! Трепещите, монстры! Вы осторожно входите в пещеру...')
            self.game_data_dict['current_location'] = self.file
            self.current_location_for_print = 'Location_0_tm0'
            self.remaining_time = REMAINING_TIME

    def print_information(self):
        print(f"Вы находитесь в {self.current_location_for_print}\n "
              f"У вас {self.game_data_dict['current_experience']} опыта и осталось {self.remaining_time} "
              f"секунд до наводнения\n Прошло уже {self.game_data_dict['current_date']} секунд\n Внутри вы видите:")
        current_location = self.game_data_dict['current_location']
        number_of_locations = len(current_location)
        if len(self.next_locations_list) == 0:
            self.mobs_defeated = 0
            if isinstance(current_location, dict):
                for key in current_location.keys():
                    self.next_locations_list.append(key)
            elif isinstance(current_location, list):
                for i in range(number_of_locations):
                    if isinstance(current_location[i], dict):
                        for key in current_location[i].keys():
                            self.next_locations_list.append(key)
                    else:
                        self.next_locations_list.append(current_location[i])
        for element in range(len(self.next_locations_list)):
            if re.search(r'Mob\w[a-zA-Z0-9_]|Boss\w[a-zA-Z0-9_]', self.next_locations_list[element]):
                print(f'— Монстра {self.next_locations_list[element]}')
            elif re.search(r'Location\w[a-zA-Z0-9_]', self.next_locations_list[element]):
                print(f'— Вход в локацию: {self.next_locations_list[element]}')
            elif re.search(r'Hatch\w[a-zA-Z0-9_]', self.next_locations_list[element]):
                print(f'— Открыть люк: {self.next_locations_list[element]}')
        return self.next_locations_list

    def print_actions(self):
        print('Выберите действие:')
        for element in range(len(self.next_locations_list)):
            if re.search(r'Mob\w[a-zA-Z0-9_]|Boss\w[a-zA-Z0-9_]', self.next_locations_list[element]):
                print(f'{element + 1}. Атаковать монстра {self.next_locations_list[element]}')
                self.actions_dict[(element + 1)] = self.next_locations_list[element]
            elif re.search(r'Location\w[a-zA-Z0-9_]', self.next_locations_list[element]):
                print(f'{element + 1}. Перейти в локацию: {self.next_locations_list[element]}')
                self.actions_dict[(element + 1)] = self.next_locations_list[element]
            elif re.search(r'Hatch\w[a-zA-Z0-9_]', self.next_locations_list[element]):
                print(f'{element + 1}. Открыть люк: {self.next_locations_list[element]}')
                self.actions_dict[(element + 1)] = self.next_locations_list[element]
            if element == len(self.next_locations_list) - 1:
                print(f'{element + 2}. Сдаться и выйти из игры')
                self.actions_dict[(element + 2)] = 'game_over'
        return self.actions_dict

    def attack_monster(self, user_action):
        mob_boss_exp_pattern = r'(Mob_exp|Boss_exp)(\d{,4})(\w+)'
        self.game_data_dict['current_experience'] += int(re.match(mob_boss_exp_pattern,
                                                                  self.actions_dict[user_action])[2])
        mob_boss_time_pattern = r'(Mob_exp|Boss_exp)(\d{2,3})(_tm)(\d{1,}\.\d{0,}|\d{1,})'
        self.game_data_dict['current_date'] += Decimal((re.match(mob_boss_time_pattern, self.actions_dict[user_action])[4]))
        self.remaining_time -= Decimal((re.match(mob_boss_time_pattern, self.actions_dict[user_action])[4]))
        self.next_locations_list.remove(self.actions_dict[user_action])
        self.actions_dict = {}
        print(f"Полученный опыт: {self.game_data_dict['current_experience']}\n "
              f"Прошло времени: {self.game_data_dict['current_date']} секунд\n "
              f"Осталось времени: {self.remaining_time} секунд")
        self.mobs_defeated += 1

    def change_location(self, user_action):
        location_pattern = r'(Location_)(\w{0,1}\d{1,2})(_tm)(\d{1,}\.\d{0,}|\d{1,})'
        self.game_data_dict['current_date'] += Decimal((re.match(location_pattern, self.actions_dict[user_action])[4]))
        self.remaining_time -= Decimal((re.match(location_pattern, self.actions_dict[user_action])[4]))
        self.game_data_dict['current_location'] = \
            self.game_data_dict['current_location'][user_action + self.mobs_defeated - 1][
                self.actions_dict[user_action]]
        self.current_location_for_print = re.match(location_pattern, self.actions_dict[user_action]).group()
        print(f"Вы перешли в локацию: {self.current_location_for_print}")
        print(f"Прошло времени: {self.game_data_dict['current_date']} секунд")
        print(f"Осталось времени: {self.remaining_time} секунд")
        self.next_locations_list = []
        self.actions_dict = {}

    def open_trapdoor(self, user_action):
        print("Открываем люк...")
        location_pattern = r'(Hatch_tm)(\d+\.\d+|\d+)'
        self.game_data_dict['current_date'] += Decimal((re.match(location_pattern, self.actions_dict[user_action])[2]))
        self.remaining_time -= Decimal((re.match(location_pattern, self.actions_dict[user_action])[2]))

    def game_over(self):
        print(f"Игра завершена!")
        self.run = False
        return self.run

    def win_game(self):
        print(f"Поздравляем! Вы выбрались на поверхность!")
        self.run = False
        return self.run

    def action(self):
        user_action = int(input())
        if user_action not in self.actions_dict.keys():
            raise ActionError('Действие недопустимо')
        # атака монстра
        if re.search(r'Mob\w[a-zA-Z0-9_]|Boss\w[a-zA-Z0-9_]', self.actions_dict[user_action]):
            self.attack_monster(user_action)
        # переход в локацию
        elif re.search(r'Location\w[a-zA-Z0-9_]', self.actions_dict[user_action]):
            self.change_location(user_action)
        # найден люк
        elif re.search(r'Hatch\w[a-zA-Z0-9_]', self.actions_dict[user_action]):
            self.open_trapdoor(user_action)
            if self.game_data_dict['current_experience'] >= EXPERIENCE_FOR_WIN:
                self.win_game()
            else:
                print("Не хватает опыта для открытия люка")
                self.game_over()
        # сдаться и завершить игру
        elif re.search(r'game_over', self.actions_dict[user_action]):
            print(f'Вы сдались и вышли из игры')
            self.game_over()

    def write_data_to_csv_file(self):
        csv_data_write_list = []
        csv_data_write_list.append(self.current_location_for_print)
        csv_data_write_list.append(self.game_data_dict['current_experience'])
        csv_data_write_list.append(self.game_data_dict['current_date'])
        writer.writerow(csv_data_write_list)

    def run_game(self):
        self.check_time_remaining()
        self.print_information()
        self.print_actions()
        self.action()
        self.write_data_to_csv_file()
        print('.' * 100)


field_names = ['current_location', 'current_experience', 'current_date']
with open(RPG_JSON_FILE, 'r') as read_file, open(OUT_CSV_FILE, 'a', newline='') as out_csv_file:
    json_file = json.load(read_file)
    writer = csv.writer(out_csv_file)
    writer.writerow(field_names)
    game = GameRPG(remaining_time=REMAINING_TIME, file=json_file['Location_0_tm0'], writer=writer)
    while game.run is True:
        game.run_game()

# Учитывая время и опыт, не забывайте о точности вычислений!

# зачет!
