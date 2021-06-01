#!/usr/bin/env python3
# coding=utf-8

import requests
from bs4 import BeautifulSoup as bs4
import time
import os
import json
import re
from pyfzf.pyfzf import FzfPrompt

fzf = FzfPrompt()

def watchMovie(url,subtitle):
    if subtitle == "":
        os.system(f'mpv {url}')
    else:
        os.system(f'mpv {url} --sub-file={subtitle}')


def chooseQuality(urls,subtitle):
    allQuality = re.findall(r'\[(\w*)\]', urls)
    choose = allQuality.index(fzf.prompt(allQuality)[0])
    url = re.findall(r'\[\w*\](\S*):hls', urls)[choose]
    watchMovie(url,subtitle)

def getSubtitles(subtitles):
    languages = re.findall(r"\[(\w*)\]",subtitles)
    choose = languages.index(fzf.prompt(languages))[0]
    subtitleUrls = re.findall(r"\[\w*\](\S*)", subtitles.replace(',', ' '))
    return subtitleUrls[choose]
    

def getEpisodeUrls(season, episode, translatorId, filmId):
    payload = {
            'id' : filmId,
            'translator_id' : translatorId,
            'season': str(season + 1),
            'episode' : str(episode + 1),
            'action' : 'get_stream'
            }
    response = requests.post('https://rezka.ag/ajax/get_cdn_series/?t=' + str(int(time.time()*1000)), data=payload)
    subtitle = ""
    data = json.loads(response.content)
    if data['subtitle']:
        subtitle = getSubtitles(data['subtitle'])
    chooseQuality(data['url'],subtitle)


def getEpisodes(filmId, translatorId):
    payload = {
            'id' : filmId,
            'translator_id' : translatorId,
            'action' : 'get_episodes'
            }
    response = requests.post('https://rezka.ag/ajax/get_cdn_series/?t=' + str(time.time()), data=payload)
    data = json.loads(response.content)
    if data['success'] == False:
        payload = {
                'id' : filmId,
                'translator_id' : translatorId,
                'action' : 'get_movie'
                }
        response = requests.post('https://rezka.ag/ajax/get_cdn_series/?t=' + str(time.time()), data=payload)
        data = json.loads(response.content)
        subtitleUrl = ""
        if data['subtitle']:
            subtitleUrl = getSubtitles(data['subtitle'])
        chooseQuality(data['url'], subtitleUrl)
    else:
        parse = bs4(data['seasons'], 'lxml')
        allSeasons = parse.findAll('li')
        seasons = []
        for season in allSeasons:
            seasons.append(season.text)
        season = seasons.index(fzf.prompt(seasons)[0])
        parse = bs4(data['episodes'], 'lxml')
        allEpisodes = parse.findAll('li', {'data-season_id' : str(season+1)})
        episodes = []
        for episode in allEpisodes:
            episodes.append(episode.text)
        episode = episodes.index(fzf.prompt(episodes)[0])
        getEpisodeUrls(season, episode, translatorId, filmId)


def chooseTranslators(url):
    filmId = re.findall(r'/(\w*)-', url)[0]
    response = requests.get(url)
    html = bs4(response.content, 'lxml')
    allTranslators = html.findAll('li', class_='b-translator__item')
    if allTranslators != []:
        allId = []
        names = []
        for translator in allTranslators:
            allId.append(translator['data-translator_id'])
            name = translator.text
            try:
                name += ' (' + translator.find('img')['title'] + ')'
            except:
                pass
            names.append(name)
        choose = fzf.prompt(names)[0]
        getEpisodes(filmId, allId[names.index(choose)])
    else:
        try:
            translatorId = re.findall(r'SeriesEvents\(\d*,(\d*)', response.text)[0]
        except:
            translatorId = re.findall(r'MoviesEvents\(\d*, (\d*)', response.text)[0]
        getEpisodes(filmId, translatorId)


def choose(allFilms):
    urls = []
    names = []
    for film in allFilms:
        name = film.find('div', class_='b-content__inline_item-link').text
        url = film.find('a', href=True)['href']
        type = film.find('i', class_='entity').text
        urls.append(url)
        names.append(name)
    choose = fzf.prompt(names)[0]
    chooseTranslators(urls[names.index(choose)])

def search(query):
    response = requests.get('https://rezka.ag/search/?do=search&subaction=search&q=' + query)
    html = bs4(response.content, 'lxml')
    allFilms = html.findAll('div', class_='b-content__inline_item')
    choose(allFilms)

if __name__ == '__main__':
    query = input('Введите название фильма/сериала, который будете смотреть: ').replace(' ', '+')
    search(query)
