"""
The use case imitates Instagram and aims to construct a schema for users, photos and their connections. MongoDB is
chosen since it has the advantage of schema less and deep-query ability. It scales well on large database and supports fast access to the data. Since we aim to have a large amount of users and the response rate of system should be really fast, MongoDB is a good fit.

Explain what will happen if coffee is spilled on one of the servers in your cluster, causing it to go down.


What data is it not ok to lose in your app? What can you do in your commands to mitigate the risk of lost data?

"""

import pymongo
import datetime
from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client.mongogram
users = db['users']
photos = db['photos']
comments = db['comments']
follows = db['follows']
likes = db['likes']

# Action 1: add new user to the users collection
def register(username, password, birthday, description=""):
	return users.insert_one({"username": username,"password": password,  "birthday": birthday, "description": description, "follower_count": 0, "following_count":0}).inserted_id

# Action 2: add a relationship between two users if one follows the other
def follow(from_id, to_id):
	follows.insert_one({"follower": from_id, "following": to_id})
	users.update({'_id': from_id}, {'$set':{'following_count': users.find_one({"_id":from_id})['following_count']+1 }})
	users.update({'_id': to_id}, {'$set': {'follower_count': users.find_one({"_id": to_id})['follower_count']+1 }})

# Action 3: remove a relationship between two users if one unfollows the other
def unfollow(from_id, to_id):
	follows.remove({"follower": from_id, "following": to_id})
	users.update({'_id': from_id}, {'$set': {'following_count': users.find_one({'_id':from_id})['following_count']-1}})
	users.update({'_id': to_id}, {'$set': {'follower_count': users.find_one({'_id': from_id})['follower_count']-1}})

# Action 4: post a photo
def photo(user, url):
	photos.insert_one({'user_id': id, 'url': url, 'time': datetime.datetime.utcnow(), "likes": 0, 'comments': 0})

# Action 5: like a photo, record the user who likes and the photo
def like(user, photo):
	likes.insert_one({'photo_id': photo['_id'], 'user_id': user['_id']})
	photos.update({'_id': photo['_id']}, {'$set':{ 'likes': photo['likes']+1 }})

# Action 6: unlike a photo
def unlike(user, photo):
	likes.remove( {'photo_id': photo['_id'], 'user_id': user['_id']} )
	photos.update({'_id': photo['_id']}, {'$set': { 'likes': photo['likes']-1 }})

# Action 7: post a comment
def comment(user, photo, cmt):
	comments.insert_one({ 'photo_id': photo['_id'], 'user_id': user['_id'], 'comment': cmt, 'time': datetime.datetime.utcnow()})
	photos.update({'_id': photo['_id']}, {'$set': {'comments': photo['comments']+1}})

# Action 8: remove an existing user and all its related models, except for its comments and likes
def unregister(user):
	# update the following/followed status
	for doc in follows.find({'follower': user['_id']}):
		unfollow(user['_id'], doc['following'])
		follows.remove({'_id': doc['_id']})
	for doc in follows.find({'following': user['_id']}):
		follow_id = doc['follower']
		users.update({'_id': follow_id}, {'$set': {'following_count': users.find_one({'_id': follow_id})['following_count']-1}})
		follows.remove({'_id': doc['_id']})
	# clear all its photos
	for pho in photos.find({'user_id': user['_id']}):
		likes.remove({'photo_id': pho['_id']})
		comments.remove({'photo_id': pho['_id']})
		photos.remove({'_id': pho['_id']})
	users.remove({'_id': user['_id'], 'username': user['username']})

# helper to return the document from the collections:
def find_user(user_id):
	return users.find_one({'_id': user_id})



def main():
	# add a bunch of users
	down_id = register("Robert Downey Jr", "downey1965", "04-04-1965", "Ironman: genius, billionaire, playboy philanthropist")
	holl_id = register("Tom Holland", "holland1996", "06-01-1996", "A dancer, an actor, the Spiderman")
	hems_id = register("Christopher Hemsworth", "hemsworth1983", "08-11-1983", "Once the Sexiest Man in the world")

	# each user can post photos
	downey = find_user(down_id)
	holland = find_user(holl_id)
	hemsworth = find_user(hems_id)

	photo(,)

if __name__ == "__main__":
	main()
