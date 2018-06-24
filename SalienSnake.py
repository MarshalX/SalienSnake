#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SalienSnake Copyright © 2018 Il'ya Semyonov
# License: https://www.gnu.org/licenses/gpl-3.0.en.html

import random
import argparse
import requests
import time
import logging

from threading import Thread

logFormatter = logging.Formatter(
    '%(levelname)-5s [%(asctime)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('saliengame')

console_handler = logging.StreamHandler()
console_handler.setFormatter(logFormatter)

logger.addHandler(console_handler)
logger.setLevel(logging.INFO)


class Salien(Thread):
    def __init__(self, token, name, disable_boss_priority, language=None, planet=None):
        Thread.__init__(self)

        self.name = name
        self.planet = planet
        self.disable_boss_priority = disable_boss_priority
        self.API = SteamApi(token, language)
        self.player = self.API.get_player_info()

    def info(self, msg):
        logger.info('{}: {}'.format(self.name, msg))

    def warning(self, msg):
        logger.warning('{}: {}'.format(self.name, msg))

    def join_self_planet(self):
        self.API.join_planet(self.planet)
        self.info('Joined planet #{}'.format(self.planet))

    def find_new_planet(self):
        new_planets = self.API.get_planets()
        new_planet = None

        for planet_item in new_planets['response']['planets']:
            if not planet_item['state']['captured'] and \
                    (not new_planet or new_planet['state']['capture_progress'] > planet_item['state']['capture_progress']):
                new_planet = planet_item

        self.info('Planet #{} - {} ({}%) seems nice, joining there!'.format(
            new_planet['id'], new_planet['state']['name'], int(new_planet['state']['capture_progress'] * 100)
        ))
        return new_planet['id']

    def run(self):
        self.info('Current score = {}/{}; Current Level = {}'.format(
            self.player['response']['score'],
            self.player['response']['next_level_score'],
            self.player['response']['level']
        ))

        if not self.planet:
            if 'active_planet' in self.player['response']:
                self.planet = self.player['response']['active_planet']
            else:
                self.planet = self.find_new_planet()

        self.join_self_planet()

        while True:
            planet_info = self.API.get_planet(self.planet)
            zone = None

            if 'planets' in planet_info['response']:
                for zone_item in planet_info['response']['planets'][0]['zones']:
                    if not self.disable_boss_priority and zone_item['type'] == 4:
                        zone = zone_item
                        break

                    if not zone_item['captured'] and zone_item['capture_progress'] < 0.95 \
                            and (not zone or zone['difficulty'] < zone_item['difficulty']):
                        zone = zone_item

            if not zone:
                self.planet = self.find_new_planet()
                self.join_self_planet()

                continue

            self.info('Attacking zone {}; difficulty {} '
                      .format(zone['zone_position'], zone['difficulty'], ('BOSS' if zone['type'] == 4 else '')))
            self.API.join_zone(zone['zone_position'])

            time.sleep(random.randint(110, 120))

            score = 120 * (5 * (2 ** (zone['difficulty'] - 1)))

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
                    self.warning('API. ReportScore. Did not have time to send the report or did not attack the zone.')
                else:
                    self.warning('API. ReportScore. X-eresult: {}; x-error_message: {}'.format(
                        x_eresult, self.API.response_headers.get('x-error_message')))

            self.player = self.API.get_player_info()


def request_decorate(method):
    def wrapper(self, url, data):
        while True:
            try:
                request = method(self, url, data)
                response = request.json()

                self.response_headers = request.headers

                logger.debug('{}{}: {}; Response headers: {}'.format(
                    method.__name__.upper(), data, response, request.headers))

                if 'response' not in response:
                    raise Exception('Cannot get response from Steam API')

                return response
            except Exception as e:
                logger.warning('An exception has occurred in API.{}: {}'.format(method.__name__, e))

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

    def __init__(self, token=None, language=None):
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
            self.build_url('ITerritoryControlMinigameService', 'LeaveGame'),
            {
                'gameid': instance_id,
                'access_token': self.token
            }
        )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-t', '--token', help='Token value from https://steamcommunity.com/saliengame/gettoken')
    parser.add_argument('-p', '--planet', help='Planet ID')
    parser.add_argument('-f', '--file', help='File with session IDs')
    parser.add_argument(
        '--language', help='Language (example: english, russian)', default='english')
    parser.add_argument(
        '-l', '--list-planets', action='store_true', help='List all planets')
    parser.add_argument(
        '-d', '--debug', action='store_true', help='Enable debug mode', default=False)
    parser.add_argument(
        '-dbp', '--disable-boss-priority', action='store_true',
        help='Disable boss priority (if the boss is found on the planet, then he will NOT be attacked)', default=False)
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

    for name, token in tokens.items():
        Salien(token, name, args.disable_boss_priority, args.language, args.planet).start()

        logger.info('Thread \'{}\' has started!'.format(name))
