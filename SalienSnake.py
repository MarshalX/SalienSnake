#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SalienSnake Copyright © 2018 Il'ya Semyonov
# License: https://www.gnu.org/licenses/gpl-3.0.en.html

import argparse
import requests
import time
import logging

from threading import Thread
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
            self.build_url('ITerritoryControlMinigameService', 'GetPlanet'),
            {
                'id': planet_id,
                'language': self.language
            }
        )

    def get_planets(self):
        return self.get(
            self.build_url('ITerritoryControlMinigameService', 'GetPlanets'),
            {
                'active_only': 1,
                'language': self.language
            }
        )

    def get_player_info(self):
        return self.post(
            self.build_url('ITerritoryControlMinigameService', 'GetPlayerInfo'),
            {
                'access_token': self.token
            }
        )

    def join_planet(self, planet_id):
        return self.post(
            self.build_url('ITerritoryControlMinigameService', 'JoinPlanet'),
            {
                'id': planet_id,
                'access_token': self.token
            }
        )

    def join_zone(self, zone_id):
        return self.post(
            self.build_url('ITerritoryControlMinigameService', 'JoinZone'),
            {
                'zone_position': zone_id,
                'access_token': self.token
            }
        )

    def represent_clan(self, clan_id):
        return self.post(
            self.build_url('ITerritoryControlMinigameService', 'RepresentClan'),
            {
                'access_token': self.token,
                'clanid': clan_id
            }
        )

    def report_score(self, score):
        return self.post(
            self.build_url('ITerritoryControlMinigameService', 'ReportScore'),
            {
                'access_token': self.token,
                'score': score,
                'language': self.language
            }
        )

    def leave_game_instance(self, instance_id):
        return self.post(
            self.build_url('IMiniGameService', 'LeaveGame'),
            {
                'access_token': self.token,
                'gameid': instance_id
            }
        )


class Difficulty(Enum):
    HIGH = 3
    MEDIUM = 2
    LOW = 1


class ThreadWithName(Thread):
    def __init__(self):
        Thread.__init__(self)

        self.name = ''

    def info(self, msg):
        logger.info('{}: {}'.format(self.name, msg))

    def warning(self, msg):
        logger.warning('{}: {}'.format(self.name, msg))


class Commander(ThreadWithName):
    _API = SteamApi()

    planet = None
    zone = None

    def __init__(self):
        ThreadWithName.__init__(self)

        self.name = 'Commander'

    @staticmethod
    def find_best_planet_and_zone():
        new_planets = Commander._API.get_planets()
        planets_info = []

        for planet_item in new_planets['response']['planets']:
            if not planet_item['state']['captured']:
                planets_info.append(Commander._API.get_planet(planet_item['id']))

        for difficulty in Difficulty:
            for planet_info in planets_info:
                for zone_item in planet_info['response']['planets'][0]['zones']:
                    if not zone_item['captured'] and zone_item['difficulty'] == difficulty.value:
                        return planet_info['response']['planets'][0], zone_item

            logger.info('Commander: can\'t get planets with the complexity level of zones {}'.format(difficulty))

    @staticmethod
    def check_zone(planet, zone):
        logger.info('Commander: I check the accuracy of my information on zone {}'.format(zone['zone_position']))

        updated_planet_info = Commander._API.get_planet(planet['id'])
        zone_info = {}

        for zone_item in updated_planet_info['response']['planets'][0]['zones']:
            if zone_item['zone_position'] == zone['zone_position']:
                zone_info = zone_item

        if zone_info.get('captured', True):
            logger.info('Information has become wrong! I give new data...')

            Commander.find_best_planet_and_zone()
        else:
            logger.info('Information on the zone is relevant!')

    def run(self):
        while True:
            self.info('I get the optimal planet and landing zone!')

            Commander.planet, Commander.zone = Commander.find_best_planet_and_zone()

            self.info('All attack the planet {}, zone {} ({}%)!'.format(
                Commander.planet['id'],
                Commander.zone['zone_position'],
                int(Commander.zone['capture_progress'] * 100)
            ))

            time.sleep(5 * 60)


class Salien(ThreadWithName):
    def __init__(self, token, name, language=None):
        ThreadWithName.__init__(self)

        self.name = name
        self.planet,  self.zone = {}, {}
        self.API = SteamApi(token, language)
        self.player = self.API.get_player_info()

    def info(self, msg):
        logger.info('{}: {}'.format(self.name, msg))

    def warning(self, msg):
        logger.warning('{}: {}'.format(self.name, msg))

    def leave_planet(self, planet_id):
        self.info('Trying to leave the current planet...')

        while True:
            self.API.leave_game_instance(planet_id)

            if self.API.response_headers['x-eresult'] == '1':
                self.info('Successfully left the planet!')

                break
            elif self.API.response_headers['x-eresult'] == '11':
                # The bot did not finish the zone on another planet
                time.sleep(30)

            time.sleep(1)

    def join_planet(self):
        self.leave_planet(self.planet['id'])
        self.API.join_planet(Commander.planet['id'])

        self.info('Yes, sir! Joined planet #{}'.format(Commander.planet['id']))

    def join_zone(self):
        self.API.join_zone(self.zone['zone_position'])

        if self.API.response_headers['x-eresult'] == '27':
            Commander.find_best_planet_and_zone()

        self.info('Attacking zone {}; {}'.format(
            self.zone['zone_position'],
            Difficulty(self.zone['difficulty'])
        ))

    def run(self):
        self.info('Current score = {}/{}; Current Level = {}'.format(
            self.player['response']['score'],
            self.player['response']['next_level_score'],
            self.player['response']['level']
        ))

        if 'active_planet' in self.player['response']:
            self.leave_planet(self.player['response']['active_planet'])

        while True:
            if self.planet.get('id', -1) != Commander.planet['id']:
                self.planet = Commander.planet
                self.join_planet()

            if self.zone.get('zone_position', -1) != Commander.zone['zone_position']:
                self.zone = Commander.zone

            self.join_zone()

            time.sleep(120)

            score = 120 * (5 * (2 ** (self.zone['difficulty'] - 1)))

            try:
                score_stats = self.API.report_score(score)

                self.info('Current score = {}/{}; Current level = {}'.format(
                    score_stats['response']['new_score'],
                    score_stats['response']['next_level_score'],
                    score_stats['response']['new_level']
                ))
            except KeyError:
                x_eresult = int(self.API.response_headers.get('x-eresult', -1))

                if x_eresult == 93:
                    self.warning('API. ReportScore. Request sent too early.')
                elif x_eresult == 73:
                    self.warning('API. ReportScore. Invalid \'score\' value.')
                elif x_eresult == 42:
                    self.warning(
                        'API. ReportScore. Did not have time to send the report '
                        'or did not attack the zone or zone captured...')
                elif x_eresult == 27:
                    self.warning(
                        'API. ReportScore. Zone Captured! This zone has been recaptured '
                        'from the Duldrumz by the Steam Community.')
                else:
                    self.warning('API. ReportScore. X-eresult: {}; x-error_message: {}'.format(
                        x_eresult, self.API.response_headers.get('x-error_message')))

                if self.planet.get('id', -1) == Commander.planet['id'] and \
                        self.zone.get('zone_position', -1) == Commander.zone['zone_position']:
                    Commander.check_zone(self.planet, self.zone)


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

        logger.info(
            'You learned the ID of planets, now you can use --planet <planet id> '
            'or skip this argument, then planet will be automatically selected.')
        exit(0)

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
        Salien(token, name, args.language).start()

        logger.info('Thread \'{}\' has started!'.format(name))
