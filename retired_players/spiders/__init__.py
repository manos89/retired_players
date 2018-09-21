import scrapy
import builtins
import requests,re,json,string
from datetime import datetime
from retired_players.items import RetiredPlayersItem
from scrapy.loader import ItemLoader
from scrapy.spidermiddlewares.httperror import HttpError

from scrapy.spidermiddlewares.httperror import HttpError

def float(number):
    try:
        return builtins.float(number)
    except:
        return number

def average_float(number):
    try:
        return builtins.float("{0:.3f}".format(builtins.float(number)*0.01))
    except:
        return number




def make_date(datestring):
    try:
        datetime_object = datetime.strptime(datestring, '%m/%d/%Y')
        return datetime_object
    except Exception as E:
        print(str(E))
        return datestring


def int(number):
    try:
        return builtins.int(number)
    except:
        return number

letters= string.ascii_lowercase
wordict={}
wordcounter=1
for l in letters:
    wordict[l]=wordcounter
    wordcounter+=1

def get_first_team(Team1,Team2):
    global wordict
    for i in range(0,100):
        if wordict[Team1[i]] < wordict[Team2[i]]:
            return Team1,Team2
        elif wordict[Team1[i]] > wordict[Team2[i]]:
            return Team2, Team1
    print('Equal teams')

def get_game_id(Date,Team1,Team2):
    global wordict
    Team1=Team1.lower()
    Team2=Team2.lower()
    Gameid=Date.strip().split('/')[-1]+Date.strip().split('/')[1]+Date.strip().split('/')[0]
    Team1,Team2=get_first_team(Team1, Team2)
    for i in range(0,3):
        try:
            Gameid+=str(wordict[Team1[i].lower()])
        except:
            Gameid+="0"
    for i in range(0,3):
        try:
            Gameid+=str(wordict[Team2[i].lower()])
        except:
            Gameid += "0"
    return Gameid


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
                                     'nationality': Nationality, 'playerName': player_name, 'position': get_proper(player_json,'Position'),
                                     'teamCountry': "", 'teamName': "", 'teamNo': "",
                                     'games': "", 'points': "", 'rebounds': "",
                                     'assists':""}}
        stats_url = "https://basketball.eurobasket.com/PlayerStatsAjax.asp?PlayerId={PID}&Season={S}"
        print(str(pid))
        for i in range(1990,2020):
            request2 = scrapy.Request(url=stats_url.replace('{PID}',str(pid)).replace('{S}',str(i)), callback=self.parse_stats, dont_filter=True)
            request2.meta['season'] = str(i)
            request2.meta['item']=JsonPlayer
            yield request2


    def parse_stats(self, response):
            # page = response.url.split("/")[-2]
            PlayerDict = response.meta['item']
            season= response.meta['season']
            PlayerDict['averageStats'] = {}
            PlayerDict['fullStats'] = {}
            l = ItemLoader(item=RetiredPlayersItem(), response=response)
            Titles=response.css("h4::text").extract()
            TableClasses=response.css("table.my_Title")
            TeamsPlayed=[]
            AllGames = []
            AllAverages=[]
            AllSummaries=[]
            Gamedict={}
            j=0
            for i in range(0,len(TableClasses)):
                start = Titles[j].find('(')
                end = Titles[j].find(')')
                League = Titles[j][start + 1:end]
                Title=str(TableClasses[i].css("::text").extract()).upper()
                if "AVERAGE" in Title:
                    AverageStatClasses=[]
                    AverageStatClasses+=TableClasses[i].css("tr.my_pStats1")
                    AverageStatClasses += TableClasses[i].css("tr.my_pStats2")
                    for AverageStatClass in AverageStatClasses:
                        Averagestats=AverageStatClass.css("td::text").extract()
                        TeamsPlayed.append(Averagestats[0])
                        if '%' in Averagestats[4]:
                            AllAverages.append({'League':League,'teamName': Averagestats[0], 'games': int(Averagestats[1]),
                                                                          'minutes':float(Averagestats[2]),
                                                                          'points': float(Averagestats[3]),
                                                                          'fg2Average': average_float(Averagestats[4].replace('%','')),
                                                                          'fg3Average': average_float(Averagestats[5].replace('%','')),
                                                                          'ftAverage': average_float(Averagestats[6].replace('%','')),
                                                                          'offRebounds': float(Averagestats[7].replace('%','')),
                                                                          'defRebounds': float(Averagestats[8]),
                                                                          'totalRebounds': float(Averagestats[9]),
                                                                          'assists': float(Averagestats[10]),
                                                                          'personalFouls': float(Averagestats[11]),
                                                                          'blocks': float(Averagestats[12]),
                                                                          'steals': float(Averagestats[13]), 'turnovers': float(Averagestats[14]),
                                                                          'ranking': float(Averagestats[15])})
                        elif '-' in Averagestats[4]:
                            AllSummaries.append({'League':League,'teamName': Averagestats[0], 'games': int(Averagestats[1]),
                                                                          'minutes':float(Averagestats[2]),
                                                                          'points': float(Averagestats[3]),
                                                                          'fg2Average': average_float(Averagestats[4]),
                                                                          'fg2s':int(Averagestats[4].split('-')[0]),
                                                                          'fg2f':int(Averagestats[4].split('-')[1]),
                                                                          'fg3Average': average_float(Averagestats[5]),
                                                                          'fg3s':int(Averagestats[5].split('-')[0]),
                                                                          'fg3f':int(Averagestats[5].split('-')[1]),
                                                                          'ftAverage': average_float(Averagestats[6]),
                                                                          'fts':int(Averagestats[6].split('-')[0]),
                                                                          'ftf':int(Averagestats[6].split('-')[1]),
                                                                          'offRebounds': float(Averagestats[7].replace('%','')),
                                                                          'defRebounds': float(Averagestats[8]),
                                                                          'totalRebounds': float(Averagestats[9]),
                                                                          'assists': float(Averagestats[10]),
                                                                          'personalFouls': float(Averagestats[11]),
                                                                          'blocks': float(Averagestats[12]),
                                                                          'steals': float(Averagestats[13]), 'turnovers': float(Averagestats[14]),
                                                                          'ranking': float(Averagestats[15])})

                    j+=1
                elif 'DETAILS' in str(TableClasses[i].css("::text").extract_first()).upper():
                    Headers=str(TableClasses[i].css("::text").extract())
                    GameStats1 = TableClasses[i].css("tr.my_pStats1")
                    GameStats2 = TableClasses[i].css("tr.my_pStats2")
                    GameStats=GameStats1+GameStats2
                    for G in GameStats:
                        Scoreclass=G.css("td")
                        ScoreLink=Scoreclass.css("a::attr(href)").extract_first()
                        HomeTeam=ScoreLink.split("_")[-2]
                        AwayTeam=ScoreLink.split("_")[-1]
                        AwayTeam=AwayTeam.split('-')[0]
                        Score=Scoreclass.css("a::text").extract_first()
                        Game=G.css("td::text").extract()
                        winner = ''
                        PlayerTeam=Game[1]
                        OpponentTeam=Game[2]

                        if 'Home Team' in Headers:
                            if PlayerTeam not in TeamsPlayed:
                                temp=PlayerTeam
                                PlayerTeam=OpponentTeam
                                OpponentTeam=temp
                        try:
                            Scorearray=Score.split('-')
                            if int(Scorearray[0])>int(Scorearray[1]):
                                winner=Game[1]
                            else:
                                winner = Game[2]
                        except:
                            pass
                        SingleGame = {'league':League,'date': Game[0],'winner':winner ,'homeTeam':HomeTeam,'awayTeam':AwayTeam,'playerTeam':PlayerTeam ,
                                      'opponentTeam':OpponentTeam , 'result': Score,
                                  'minutes': int(Game[4]), 'points': int(Game[5]), 'fg2':Game[6],'fg2s':int(Game[6].split('-')[0]),'fg2f':int(Game[6].split('-')[1]) ,
                                    'fg3': Game[7],'fg3s':int(Game[7].split('-')[0]),'fg3f':int(Game[7].split('-')[1]),
                                  'ft': Game[8],'fts':int(Game[8].split('-')[0]), 'ftf':int(Game[8].split('-')[1]) ,
                                      'offRebounds': int(Game[9]), 'defRebounds': int(Game[10]),
                                  'totalRebounds': int(Game[11]), 'assists': int(Game[12]), 'personalFouls': int(Game[13]),
                                  'blocks': int(Game[14]), 'steals': int(Game[15]), 'turnovers': int(Game[16]), 'ranking': float(Game[17])}

                        SingleGame['GameId']=get_game_id(SingleGame['date'], PlayerTeam, OpponentTeam).strip()
                        SingleGame['date']=make_date(Game[0])
                        AllGames.append(SingleGame)

                    j+=1
            Gamedict[season]={'fullStats':AllGames,'averageStats':AllAverages,'summaryStats':AllSummaries}
            l.add_value('BasicInfo',PlayerDict['basic_info'])
            l.add_value('Stats', Gamedict)
            return l.load_item()