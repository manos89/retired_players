import scrapy
import builtins
import requests,re,json,string
from datetime import datetime
from retired_players.items import RetiredPlayersItem
from scrapy.loader import ItemLoader
from scrapy.spidermiddlewares.httperror import HttpError

def get_active_players():
    text=open('ids.txt','r')
    ids=[line.strip() for line in text]
    text.close()
    return ids

def get_inactive_players(active_ids):
    return [str(i) for i in range(1,4425) if str(i) not in active_ids]

def get_proper(jsonobj,jsonkey):
    try:
        return jsonobj[jsonkey]
    except:
        return ''

def get_height_cm(jsonobj,jsonkey):
    try:
        return int(jsonobj[jsonkey].split('/')[0].replace('cm',''))
    except Exception as E:
        print(str(E))
        return ''

def get_height_in(jsonobj,jsonkey):
    try:
        return int(jsonobj[jsonkey].split('/')[1].replace('cm',''))
    except:
        return ''

class QuotesSpider(scrapy.Spider):
    name = "retired_players"


    def start_requests(self):
        active_ids=get_active_players()
        inactive_ids=get_inactive_players(active_ids)
        for i in inactive_ids:
            request = scrapy.Request(url="https://basketball.eurobasket.com/player/"+str(i), callback=self.profile_scrpr, dont_filter=True)
            request.meta['id'] = str(i)
            yield request



    def profile_scrpr(self, response):
        pid = response.meta['id']
        whole_text=response.xpath('//body//text()').extract()
        whole_text=",".join(whole_text)
        info_class=response.css("td#teamlogo")[0]
        infonames=info_class.css("b::text").extract()
        infos=info_class.css("div::text").extract()
        nationinfo = info_class.css("div")
        player_json={}
        player_name=response.css("input#btnSubmit::attr(onclick)").extract_first().replace('SubmitAgent','').replace('(','').replace(')','').split(',')[-1].replace("'","")
        Nationality = nationinfo[0].css('img::attr(alt)').extract()
        Nationality=[N for N in Nationality if not N.isupper()]
        Nationality=','.join(Nationality)
        for i in range(0,len(infonames)):
            player_json[infonames[i].replace(':','').strip()]=infos[i]
        JsonPlayer = {'basic_info': {'imageUrl': '', 'playerID': pid,
                                     'playerUrl':response.request.url,
                                     'age': '',
                                     'birthday': get_proper(player_json,'Born'), 'gender': 'male', 'heightcm': get_height_cm(player_json,'Height'),
                                     'heightin': get_height_in(player_json,'Height'),
                                     'leagueName':"",
                                     'nationality': Nationality, 'playerName': player_name, 'position': get_proper(player_json,'Position:'),
                                     'teamCountry': "", 'teamName': "", 'teamNo': "",
                                     'games': "", 'points': "", 'rebounds': "",
                                     'assists':""}}
        print(JsonPlayer)

