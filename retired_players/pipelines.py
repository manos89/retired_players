# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html


import logging
import pymongo

class MongoPipeline(object):

    collection_name ="players"

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        ## pull in information from settings.py
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE'),

        )

    def open_spider(self, spider):
        ## initializing spider
        ## opening db connection
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        ## clean up when spider is closed
        self.client.close()

    def process_item(self, item, spider):
        ## how to handle each post
        self.season = dict(item)['Stats'].keys()[0]
        try:
            results=self.db[self.collection_name].find({'BasicInfo.playerID':dict(item)['BasicInfo']['playerID']})
            resultscount= results.limit(1).count()
        except:
            resultscount=0
        if resultscount>0:
            # self.db[self.collection_name].remove(results[0])
            # self.db[self.collection_name].insert(dict(item))
            season_exists=self.db[self.collection_name].find({"Stats."+self.season: { "$exists": True, "$ne": "null"}})
            self.db[self.collection_name].update({'BasicInfo.playerID': dict(item)['BasicInfo']['playerID']},
                                                 {"$set": {"BasicInfo": item['BasicInfo']}})

            HasStats=len(item['Stats'][self.season]['fullStats'])
            if HasStats>0:
                self.db[self.collection_name].update({'BasicInfo.playerID':dict(item)['BasicInfo']['playerID']}, {"$set": {"Stats."+self.season: item['Stats'][self.season]}})
        else:
            self.db[self.collection_name].insert({'BasicInfo':dict(item)['BasicInfo']})
            HasStats=len(item['Stats'][self.season]['fullStats'])
            if HasStats>0:
                self.db[self.collection_name].update({'BasicInfo.playerID': dict(item)['BasicInfo']['playerID']},
                                                     {"$set": {"Stats." + self.season: item['Stats'][self.season]}})
        logging.debug("Post added to MongoDB")
        return item