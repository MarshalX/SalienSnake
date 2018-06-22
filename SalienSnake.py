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
    '%(filename)12s[LINE:%(lineno)3d]# %(levelname)-8s [%(asctime)s]  %(message)s'
)
logger = logging.getLogger('saliengame')

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)

logger.addHandler(consoleHandler)
logger.setLevel(logging.INFO)


class Salien(Thread):
    def __init__(self, token, name='', language=None, planet=None):
        Thread.__init__(self)

        self.name = name
        self.planet = planet
        self.API = Steam_API(token, language)
        self.player = self.API.get_player_info()

    def info(self, msg):
        logger.info('{} {}'.format(self.name, msg))

    def warning(self, msg):
        logger.warning('{} {}'.format(self.name, msg))

    def run(self):
        self.info('Current score = {}/{}; Current Level = {}'.format(
            self.player['response']['score'],
            self.player['response']['next_level_score'],
            self.player['response']['level']
        ))

        if not self.planet:
            self.planet = self.player['response']['active_planet']

        self.API.join_planet(self.planet)
        self.info('Joined planet #{}'.format(self.planet))

        while True:
            planet_info = self.API.get_planet(self.planet)
            zone = None

            for zone in planet_info['response']['planets'][0]['zones']:
                if not zone['captured']:
                    zone = zone
                    break

            if zone is None:
                self.info(self.name + ' There are no free zones. Finding a new planet!')

                planets = self.API.get_planets()
                for planet in planets['response']['planets']:
                    if planet['state']['captureprogress'] < 1:
                        self.info('Planet #{} - {} ({}%) seems nice, joining there!'.format(
                            planet['id'],
                            planet['state']['name'],
                            int(planet['state']['capture_progress'] * 100)
                        ))

                        planet = planet['id']
                        break

            time.sleep(random.randint(5, 10))

            self.info('Attacking zone {}'.format(zone['zone_position']))
            self.API.join_zone(zone['zone_position'])

            time.sleep(125)

            difficulty_scores = {
                '1': '595',
                '2': '1190',
                '3': '2380'
            }
            score = difficulty_scores.get(zone['difficulty'], 120)

            try:
                score_stats = self.API.report_score(score)

                self.info('Current score = {}/{}; Current Level = {}'.format(
                    score_stats['response']['new_score'],
                    score_stats['response']['next_level_score'],
                    score_stats['response']['new_level']
                ))
            except KeyError:
                self.warning('API. ReportScore. Request sent too early.')


class Steam_API:
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
        self.language = 'english' if not language else language
        self.token = token

    def build_url(self, interface, method):
        return '{}{}/{}/{}/'.format(self.api_host, interface, method, self.api_version)

    def get(self, url, data):
        while True:
            try:
                url += '?' + '&'.join(['{}={}'.format(k, v) for k, v in data.items()])
                response = requests.get(url, headers=self.headers)

                return response.json()
            except Exception:
                logger.warning('Exception has been occurred in API.get')

            time.sleep(1)

    def post(self, url, data):
        while True:
            try:
                response = requests.post(url, headers=self.headers, data=data)

                return response.json()
            except Exception:
                logger.warning('Exception has been occurred in API.post')

            time.sleep(1)

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
                'score': score,
                'access_token': self.token,
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
    parser.add_argument('-t', '--token', help='Token value from https://steamcommunity.com/saliengame/gettoken')
    parser.add_argument('-p', '--planet', help='Planet ID')
    parser.add_argument('-f', '--file', help='File with sessions IDs')
    parser.add_argument('--language', help='Language (example: english, russian)')
    parser.add_argument('-l', '--list-planets', action='store_true', help='List planets')
    args = parser.parse_args()

    if not args.language:
        args.language = 'english'

    if args.file:
        with open(args.file, 'r', encoding='UTF-8') as f:
            for number, token in enumerate(f.readlines()):
                token = token.replace('\n', '')
                name = 'Account #{}'.format(number)

                temp_thread = Salien(token, name)
                temp_thread.start()

                logger.info('Thread \'{}\' has been started!'.format(name))
    else:
        if args.list_planets:
            API = Steam_API(language=args.language)

            planets = API.get_planets()
            for planet in planets['response']['planets']:
                logger.info(
                    '{}: {} ({}%)'.format(
                        planet['id'],
                        planet['state']['name'],
                        int(planet['state']['capture_progress'] * 100)
                    )
                )

        if not args.token:
            logger.warning(
                'https://steamcommunity.com/saliengame/gettoken, please copy and paste the value of \'token\'\n'
                'This will look like: 00112233445566778899aabbccddeeff'
            )
            args.token = input('Token: ')

        if len(args.token) != 32:
            logger.warning('Token is invalid, it should be 32 characters long!')
            exit()

        temp_thread = Salien(args.token)
        temp_thread.start()
