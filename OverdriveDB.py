from pymongo import MongoClient
import pymongo
from InstagramAPI import InstagramAPI
import pickle
import utils
import time
import datetime
import debug
import json 
import credentials
import threading
import numpy

#### Performs all actions for the database ####

static_lock = threading.Lock()

class Mongoloid(object):

    def __init__(self):
        
            # connect to MongoServer
        self.client = MongoClient(credentials.mongo_url)

        # -------   COLLECTIONS  ------- #

        # contains all users interacted with
        self.userlist  = self.client['Instagram'].user_profiles
        # blacklist prevents me from following someone twice
        self.blacklist = self.client['Instagram'].blacklist
        self.profile_activity    = self.client['Instagram'].profile_activity

        # my followers
        self.followers = self.client['Instagram'].followers
        # my following
        self.following = self.client['Instagram'].following


    # ---- USERLIST FUNCTIONS ---- #
    def write_api_pk(self, scraper_api, pk, the_time = datetime.datetime.now()):
        search_item = self.userlist.find_one({'pk': pk})    
        if(search_item == None):
            scraper_api.getUsernameInfo(pk)
            try:
                response = scraper_api.LastJson['user']
            except:
                print(scraper_api.LastJson)
            response['follow_time'] = the_time
            self.userlist.replace_one({'pk':response['pk']}, response, True)
            time.sleep(numpy.random.normal(60, 20))

    def write_user_item(self, user_item, time = datetime.datetime.now()):
        del user_item["_id"]
        self.userlist.replace_one({'pk':user_item['pk']}, user_item, True)

    def find_pk(self, pk):
        result = self.userlist.find_one({'pk': pk})
        return result

    def userlist_count(self):
        return self.userlist.count_documents({})

    def get_user_by_metric(self, metric):
        with static_lock:
            target = self.userlist.find_one(metric)
            if not target == None:
                self.mark_user_scraped(target['pk'])
            return target

    def mark_user_scraped(self, pk):
        self.userlist.update({"pk":pk}, {"$set": {"scraped": datetime.datetime.now()}})

    # ---- BLACKLIST FUNCTIONS ---- #
    def blacklist_member(self, pk):
        user = self.blacklist.find_one({'pk': pk})
        if(user == None):
            return False
        else:
            return True

    def blacklist_add(self, pk):
        self.blacklist.replace_one({'pk': pk}, {'pk': pk}, True)

    def blacklist_count(self):
        return self.blacklist.count_documents({})

    # ---- TELEMETRY FUNCTIONS --- #
    def get_followers(self):
        result = []
        for item in self.followers.find({}):
            result.append(item['pk'])
        return result

    def set_followers(self, followers_list):
        self.followers.delete_many({})
        self.followers.insert_many(followers_list)

    def followers_count(self):
        return self.followers.count_documents({})


    def get_following(self):
        result = []
        for item in self.following.find({}):
            result.append(item['pk'])
        return result

    def set_following(self, following_list):
        self.following.delete_many({})
        self.following.insert_many(following_list)

    def following_count(self):
        return self.following.count_documents({})


    ################################MAINTENENCE

    def removeScraped(self):
        self.userlist.update({}, {'$unset': {'scraped': None}}, multi=True)
        self.userlist.update({}, {'$unset': {'blacklisted': None}}, multi=True)
        self.userlist.update({}, {'$unset': {'followed': None}}, multi=True)
