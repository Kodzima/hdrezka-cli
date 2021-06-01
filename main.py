import requests
from bs4 import BeautifulSoup as bs4
import time
import os
import json
import re

def watchMovie(url,subtitle):
    if subtitle == "":
        os.system(f'mpv {url}')
    else:
        os.system(f'mpv {url} --sub-file={subtitle}')


def chooseQuality(urls,subtitle):
    allQuality = re.findall(r'\[(\w*)\]', urls)
    for quality in allQuality:
        print(f'>> {allQuality.index(quality)}) {quality}')
    try:
        choose = int(input('Выберите качество фильма/серии: '))
    except:
        pass
    url = re.findall(r'\[\w*\](\S*):hls', urls)[choose]
    print(url)
    watchMovie(url,subtitle)

def getSubtitles(subtitles):
    languages = re.findall(r"\[(\w*)\]",subtitles)
    for language in languages:
        print(f'>> {languages.index(language)}) {language}')
    try:
        choose = int(input('Выберите язык субтитров: '))
    except:
        getSubtitles(subtitles)
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
        for season in allSeasons:
            print(f'>> {allSeasons.index(season)}) {season.text}')
        try:
            season = int(input('Выберите сезон: '))
        except:
            getEpisodes(filmId, translatorId)
        parse = bs4(data['episodes'], 'lxml')
        allEpisodes = parse.findAll('li', {'data-season_id' : str(season+1)})
        for episode in allEpisodes:
            print(f'>> {allEpisodes.index(episode)}) {episode.text}')
        try:
            episode = int(input('Выберите эпизод: '))
        except:
            getEpisodes(filmId, translatorId)
        getEpisodeUrls(season, episode, translatorId, filmId)


def chooseTranslators(url):
    filmId = re.findall(r'/(\w*)-', url)[0]
    response = requests.get(url)
    html = bs4(response.content, 'lxml')
    allTranslators = html.findAll('li', class_='b-translator__item')
    if allTranslators != []:
        allId = []
        for translator in allTranslators:
            allId.append(translator['data-translator_id'])
            name = translator.text
            language = ""
            try:
                language = '(' + translator.find('img')['title'] + ')'
            except:
                pass
            print(f">> {allTranslators.index(translator)}) {name} {language}")
        try:
            choose = int(input('Выберите озвучку: '))
            getEpisodes(filmId, allId[choose])
        except Exception as E:
            print(E)
            print('Что-то не так...')
            chooseTranslators(url)
    else:
        try:
            translatorId = re.findall(r'SeriesEvents\(\d*,(\d*)', response.text)[0]
        except:
            translatorId = re.findall(r'MoviesEvents\(\d*, (\d*)', response.text)[0]
        getEpisodes(filmId, translatorId)


def choose(allFilms):
    urls = []
    types = []
    for film in allFilms:
        name = film.find('div', class_='b-content__inline_item-link').text
        url = film.find('a', href=True)['href']
        type = film.find('i', class_='entity').text
        urls.append(url)
        types.append(type)
        print(f'>> {allFilms.index(film)}) {name} {" "*(50-len(name))} {type} ')
    try:
        userInput = int(input('Введите номер нужного вам фильма/сериала: '))
        chooseTranslators(urls[userInput])
    except Exception as E:
        print(E)
        print('Повторите попытку')
        choose(allFilms)

def search(query):
    response = requests.get('https://rezka.ag/search/?do=search&subaction=search&q=' + query)
    html = bs4(response.content, 'lxml')
    allFilms = html.findAll('div', class_='b-content__inline_item')
    choose(allFilms)

if __name__ == '__main__':
    query = input('Введите название фильма/сериала, который будете смотреть: ').replace(' ', '+')
    search(query)
