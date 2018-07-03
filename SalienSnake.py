#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SalienSnake Copyright © 2018 Il'ya Semyonov
# License: https://www.gnu.org/licenses/gpl-3.0.en.html

import argparse
import requests
import time
import logging

from threading import Thread, Lock
from enum import Enum

logFormatter = logging.Formatter(
    '%(levelname)-5s [%(asctime)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('saliengame')

console_handler = logging.StreamHandler()
console_handler.setFormatter(logFormatter)

logger.addHandler(console_handler)
logger.setLevel(logging.INFO)


def request_decorate(method):
    def wrapper(self, url, data):
        while True:
            try:
                request = method(self, url, data)
                self.response_headers = request.headers
                self.response_headers['code'] = request.status_code

                logger.debug('Method: {}; Data: {}; Response headers: {}'.format(
                    method.__name__.upper(), data, request.headers))

                response = request.json()

                logger.debug('Response: {}'.format(response))

                return response
            except ValueError:
                logger.warning("Cannot get json response from Steam API. Status code: {}"
                               .format(self.response_headers['code']))
            except Exception as e:
                logger.warning('An exception has occurred in API.{}: {}'.format(method.__name__, repr(e)))

            time.sleep(1)

    return wrapper


class SteamApi:
    headers = {
        'Accept': '*/*',
        'Origin': 'https://steamcommunity.com',
        'Referer': 'https://steamcommunity.com/saliengame/play',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
    }

    api_host = 'https://community.steam-api.com/'
    api_version = 'v0001'

    def __init__(self, token=None, language='english'):
        self.language = language
        self.token = token
        self.response_headers = {}

    def build_url(self, interface, method):
        return '{}{}/{}/{}/'.format(self.api_host, interface, method, self.api_version)

    @request_decorate
    def get(self, url, data):
        return requests.get(url, params=data, headers=self.headers)

    @request_decorate
    def post(self, url, data):
        return requests.post(url, headers=self.headers, data=data)

    def get_planet(self, planet_id):
        return self.get(
            self.build_url('ITerritoryControlMinigameService', 'GetPlanet'), {
                'id': planet_id,
                'language': self.language
            }
        )

    def get_planets(self):
        return self.get(
            self.build_url('ITerritoryControlMinigameService', 'GetPlanets'), {
                'active_only': 1,
                'language': self.language
            }
        )

    def get_player_info(self):
        return self.post(
            self.build_url('ITerritoryControlMinigameService', 'GetPlayerInfo'), {
                'access_token': self.token
            }
        )

    def join_planet(self, planet_id):
        return self.post(
            self.build_url('ITerritoryControlMinigameService', 'JoinPlanet'), {
                'id': planet_id,
                'access_token': self.token
            }
        )

    def join_zone(self, zone_id):
        return self.post(
            self.build_url('ITerritoryControlMinigameService', 'JoinZone'), {
                'zone_position': zone_id,
                'access_token': self.token
            }
        )

    def join_boss_zone(self, zone_id):
        return self.post(
            self.build_url('ITerritoryControlMinigameService', 'JoinBossZone'), {
                'zone_position': zone_id,
                'access_token': self.token
            }
        )

    def represent_clan(self, clan_id):
        return self.post(
            self.build_url('ITerritoryControlMinigameService', 'RepresentClan'), {
                'access_token': self.token,
                'clanid': clan_id
            }
        )

    def report_score(self, score):
        return self.post(
            self.build_url('ITerritoryControlMinigameService', 'ReportScore'), {
                'access_token': self.token,
                'score': score,
                'language': self.language
            }
        )

    def report_boss_damage(self, damage_done, damage_taken, used_healing):
        return self.post(
            self.build_url('ITerritoryControlMinigameService', 'ReportBossDamage'), {
                'access_token': self.token,
                'use_heal_ability': used_healing,
                'damage_to_boss': damage_done,
                'damage_taken': damage_taken
            }
        )

    def leave_game_instance(self, instance_id):
        return self.post(
            self.build_url('IMiniGameService', 'LeaveGame'), {
                'access_token': self.token,
                'gameid': instance_id
            }
        )


class Difficulty(Enum):
    HIGH = 3
    MEDIUM = 2
    LOW = 1


class Instance(Enum):
    zone = 'ZONE'
    planet = 'PLANET'


class Type(Enum):
    boss = 4
    default = 3


class NamedThread(Thread):
    def __init__(self):
        Thread.__init__(self)

        self.name = ''

    def info(self, msg):
        logger.info('{}: {}'.format(self.name, msg))

    def warning(self, msg):
        logger.warning('{}: {}'.format(self.name, msg))


class Commander(NamedThread):
    API = SteamApi()

    type = None
    planet = None
    zone = None

    lock = Lock()

    def __init__(self):
        NamedThread.__init__(self)

        self.name = 'Commander'

    @staticmethod
    def find_best_planet_and_zone():
        new_planets = Commander.API.get_planets()
        planets_info = []

        for planet_item in new_planets['response']['planets']:
            if not planet_item['state']['captured']:
                planets_info.append(Commander.API.get_planet(planet_item['id']))

        for planet_info in planets_info:
            for zone_item in planet_info['response']['planets'][0]['zones']:
                    if zone_item.get('boss_active', False):
                        return Type.boss, planet_info['response']['planets'][0], zone_item

        logger.info('Commander: can\'t get planets with the type of zones {}'.format(Type.boss))

        for difficulty in Difficulty:
            for planet_info in planets_info:
                for zone_item in planet_info['response']['planets'][0]['zones']:
                    if not zone_item['captured'] and zone_item['difficulty'] == difficulty.value \
                            and zone_item.get('capture_progress', 0) and zone_item.get('capture_progress', 0) < 0.9:
                        return Type.default, planet_info['response']['planets'][0], zone_item

            logger.info('Commander: can\'t get planets with the complexity level of zones {}'.format(difficulty))

    @staticmethod
    def check_current_information():
        acquire = Commander.lock.acquire(blocking=False)

        if not acquire:
            return

        logger.info('Commander: Locked thread!')

        try:
            planet_id = Commander.planet.get('id')
            zone_id = Commander.zone.get('zone_position')

            logger.info('Commander: I check the accuracy of my information on zone {}'.format(zone_id))

            updated_planet_info = Commander.API.get_planet(planet_id)
            zone_info = {}

            for zone_item in updated_planet_info['response']['planets'][0]['zones']:
                if zone_item['zone_position'] == zone_id:
                    zone_info = zone_item

            if (Commander.type == Type.default and zone_info.get('captured', True)) \
                    or (Commander.type == Type.boss and not zone_info.get('boss_active', False)):
                logger.info('Commander: Information has become wrong! I give new data...')

                Commander.type, Commander.planet, Commander.zone = Commander.find_best_planet_and_zone()

                logger.info('Commander: New information arrived! Planet {}, zone {} ({}%)!'.format(
                    Commander.planet['id'],
                    Commander.zone['zone_position'],
                    int(Commander.zone['capture_progress'] * 100)
                ))
            else:
                logger.info('Commander: Information on the zone is relevant! ({}%)'
                            .format(int(Commander.zone['capture_progress'] * 100)))

            logger.info('Commander: Unlocked thread!')
        finally:
            Commander.lock.release()

    def run(self):
        while True:
            self.info('I get the optimal planet and landing zone!')

            Commander.type, Commander.planet, Commander.zone = Commander.find_best_planet_and_zone()

            self.info('All attack the planet {}, zone {} ({}%)!'.format(
                Commander.planet['id'],
                Commander.zone['zone_position'],
                int(Commander.zone['capture_progress'] * 100)
            ))

            time.sleep(60)


class Player(NamedThread):
    def __init__(self, token, name, language=None):
        NamedThread.__init__(self)

        self.name = name
        self.API = SteamApi(token, language)
        self.player = self.API.get_player_info()

    def get_active_planet(self):
        return self.player['response'].get('active_planet')

    def get_active_zone(self):
        return self.player['response'].get('active_zone_game')

    def get_active_zone_position(self):
        return self.player['response'].get('active_zone_position')

    def leave_game(self, instance, instance_id):
        if not instance_id:
            return

        self.info('Trying to leave the current {} (#{})...'.format(instance, instance_id))

        self.API.leave_game_instance(instance_id)

        x_eresult = int(self.API.response_headers.get('x-eresult', -1))
        if x_eresult == 1:
            self.info('Successfully left the {} (#{})!'.format(instance, instance_id))
        elif x_eresult == 11:
            raise AttributeError()
        else:
            self.warning('API. LeaveGame. X-eresult: {}; x-error_message: {}'.format(
                x_eresult, self.API.response_headers.get('x-error_message')))

    def leave_current_zone(self):
        zone_id = self.get_active_zone()

        try:
            self.leave_game(Instance.zone, zone_id)
        except AttributeError:
            self.info('I\'m not in this zone!')

    def leave_current_planet(self):
        planet_id = self.get_active_planet()

        try:
            self.leave_game(Instance.planet, planet_id)
        except AttributeError:
            self.info('I can not leave the planet, I am in the zone.')

            self.leave_current_zone()
            self.leave_current_planet()

    def join_planet(self, planet):
        current_planet = self.get_active_planet()
        if current_planet != planet['id']:
            self.leave_current_planet()

            self.API.join_planet(planet['id'])

            self.info('Yes, sir! Joined planet #{}'.format(planet['id']))

    def join_zone(self, zone):
        self.API.join_zone(zone['zone_position'])

        if self.API.response_headers['x-eresult'] == '27':
            raise AttributeError()

        self.info('Attacking zone {}; {}'.format(
            zone['zone_position'],
            Difficulty(zone['difficulty'])
        ))

    def join_boss_zone(self, zone):
        self.API.join_boss_zone(zone['zone_position'])

        x_eresult = int(self.API.response_headers.get('x-eresult', -1))
        if x_eresult == 1:
            self.info('Attacking BOSS zone {}'.format(zone['zone_position']))
        elif x_eresult == 8:
            self.info('Can\'t join to the boss zone because it\'s not a boos zone')

            raise AttributeError()
        elif x_eresult == 11:
            self.info('Already in the boss zone #{}'.format(zone['zone_position']))
        elif x_eresult != 1:
            self.warning('API. JoinBossZone. X-eresult: {}; x-error_message: {}'
                         .format(x_eresult, self.API.response_headers.get('x-error_message')))

    def report_score(self, score):
        response = self.API.report_score(score)

        x_eresult = int(self.API.response_headers.get('x-eresult', -1))

        if x_eresult == 1:
            return response['response']

        if x_eresult == 93:
            self.warning('API. ReportScore. Request sent too early.')
        elif x_eresult == 73:
            self.warning('API. ReportScore. Invalid \'score\' value.')
        elif x_eresult == 42:
            self.warning(
                'API. ReportScore. Did not have time to send the report '
                'or did not attack the zone or zone captured...')

            Commander.check_current_information()
        elif x_eresult == 27:
            self.warning(
                'API. ReportScore. Zone Captured! This zone has been recaptured '
                'from the Duldrumz by the Steam Community.')

            Commander.check_current_information()
        else:
            self.warning('API. ReportScore. X-eresult: {}; x-error_message: {}'.format(
                x_eresult, self.API.response_headers.get('x-error_message')))

    def report_boss_damage(self, damage_done, damage_taken, used_healing):
        response = self.API.report_boss_damage(damage_done, damage_taken, used_healing)

        x_eresult = int(self.API.response_headers.get('x-eresult', -1))
        if x_eresult == 11:
            self.info('The boss killed you! Restarting...')

            raise AttributeError()
        elif x_eresult != 1:
            self.warning('API. ReportBossDamage. X-eresult: {}; x-error_message: {}'
                         .format(x_eresult, self.API.response_headers.get('x-error_message')))
            raise AttributeError()

        return response['response']

    def run(self):
        self.leave_current_zone()

        self.info('Current score = {}/{}; Current Level = {}'.format(
            self.player['response']['score'],
            self.player['response'].get('next_level_score', 'MAX LVL(25)'),
            self.player['response']['level']
        ))

        while True:
            self.player = self.API.get_player_info()
            self.join_planet(Commander.planet)

            Game(self).play()


class Game:
    def __init__(self, player):
        self.player = player

    def play(self):
        if Commander.type == Type.default:
            self.start_default_game()
        elif Commander.type == Type.boss:
            self.start_boss_game()

    def start_default_game(self):
        try:
            self.player.join_zone(Commander.zone)
        except AttributeError:
            self.player.warning('I can\'t attack this zone. It\'s captured!')

            Commander.check_current_information()
            return

        for _ in range(110):
            current_zone = self.player.get_active_zone_position()
            if current_zone and str(Commander.zone['zone_position']) != current_zone:
                self.player.info('The current zone is captured. I see no reason to be there. Change of zone...')

                self.player.leave_current_zone()
                return

            time.sleep(1)

        score = 120 * (5 * (2 ** (Commander.zone['difficulty'] - 1)))

        report_score = self.player.report_score(score)
        if report_score:
            self.player.info('Current score = {}/{}; Current level = {}'.format(
                report_score['new_score'],
                report_score.get('next_level_score', 'MAX LVL(25)'),
                report_score['new_level']
            ))

    def start_boss_game(self):
        try:
            self.player.join_boss_zone(Commander.zone)

            time.sleep(5)
        except AttributeError:
            Commander.check_current_information()

            return

        damage_done = 1
        damage_taken = 0

        seconds = -1
        while True:
            seconds += 1
            time.sleep(1)

            used_healing = 0
            if not seconds % 120:
                self.player.info('Used the restoration of health!')
                used_healing = 1

            if not seconds % 5:
                try:
                    response = self.player.report_boss_damage(damage_done, damage_taken, used_healing)
                except AttributeError:
                    return
                else:
                    if not response.get('boss_status'):
                        self.player.info('Waiting for the boss to attack...')
                    elif response.get('game_over'):
                        self.player.info('Fight with the boss is over!')

                        Commander.check_current_information()
                        return
                    elif response.get('waiting_for_players'):
                        self.player.info('Waiting for the players!')
                    else:
                        self.player.info('BOSS health {}/{}'.format(
                            response['boss_status']['boss_hp'], response['boss_status']['boss_max_hp']
                        ))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-t', '--token', help='Token value from https://steamcommunity.com/saliengame/gettoken')
    parser.add_argument('-f', '--file', help='File with session IDs')
    parser.add_argument(
        '--language', help='Language (example: english, russian)', default='english')
    parser.add_argument(
        '-l', '--list-planets', action='store_true', help='List all planets')
    parser.add_argument(
        '-d', '--debug', action='store_true', help='Enable debug mode', default=False)
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    if args.list_planets:
        API = SteamApi(language=args.language)

        planets = API.get_planets()
        for planet in planets['response']['planets']:
            logger.info('{}: {} ({}%)'.format(
                planet['id'], planet['state']['name'],
                int(planet['state']['capture_progress'] * 100)
            ))

    tokens = {}

    if args.file:
        with open(args.file, 'r', encoding='UTF-8') as f:
            for number, token in enumerate(f.readlines()):
                token = token.strip()
                name = 'Account #{}'.format(number)

                if len(token) != 32:
                    logger.warning(
                        'Token on {} line is invalid, it should be '
                        '32 characters long!'.format(number + 1))
                    continue

                tokens[name] = token
    else:
        if not args.token:
            logger.warning(
                'https://steamcommunity.com/saliengame/gettoken, '
                'please copy and paste the value of \'token\'\n'
                'It will look like \'00112233445566778899aabbccddeeff\''
            )
            args.token = input('Token: ')

        if len(args.token) != 32:
            logger.warning(
                'Token is invalid, it should be 32 characters long!')
        else:
            tokens['Account #0'] = args.token

    Commander().start()
    while not Commander.planet or not Commander.zone:
        time.sleep(1)
    for name, token in tokens.items():
        Player(token, name, args.language).start()

        logger.info('Thread \'{}\' has started!'.format(name))
