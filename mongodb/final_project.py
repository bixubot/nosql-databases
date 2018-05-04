"""
The use case imitates Instagram and aims to construct a schema for users, photos and their connections. MongoDB is
chosen since it has the advantage of schema less and deep-query ability. It scales well on large database and supports fast access to the data. Since we aim to have a large amount of users and the response rate of system should be really fast, MongoDB is a good fit.

There are 3 users registered and 1 unregistered later, 7 photos and 8 comments, with many follows and likes representing the relationship between users and photos.

If something bad unexpected happened and caused one of the servers go down, MongoDB cluster will run a negotiation among the rest of the functional servers to find a new primary server to hold the database replica. If somehow all the rest servers are down or no comminucation can be done between the rest, there will not be a new master until the situation is solved.

We set up an admin user that can directly read and write the database so that the passwords and other important information will not leak easily.
All documents are supposed to be securely stored, especially users' profiles. In order to protect user profiles, a user cannot unregister with a wrong password. Also, all related data will be deleted if a user successfully unregister itself. 

In order to allow authentication, remember to allow "--auth" when starting the MongoDB server. Or go to the configuration file, usually "/etc/mongod.conf" in Ubuntu, edit "authorization: enabled", and then restart the server.

"""

import pymongo
import datetime
from pymongo import MongoClient


client = MongoClient('localhost', 27017)
client.drop_database("mongogram") # clear the database for demo purpose
database = client.mongogram
database.command("dropUser", "admin")

database.command("createUser", "admin", pwd="complicated", roles = ["readWrite"])
users = database['users']
photos = database['photos']
comments = database['comments']
follows = database['follows']
likes = database['likes']

# Action 1: add new user to the users collection
def register(username, password, birthday, description=""):
	return users.insert_one({"username": username,"password": password,  "birthday": birthday, "description": description, "follower_count": 0, "following_count":0}).inserted_id

# Action 2: add a relationship between two users if one follows the other
def follow(from_id, to_id):
	follows.insert_one({"follower": from_id, "following": to_id, 'time': datetime.datetime.utcnow()})
	users.update({'_id': from_id}, {'$set':{'following_count': users.find_one({"_id":from_id})['following_count']+1 }})
	users.update({'_id': to_id}, {'$set': {'follower_count': users.find_one({"_id": to_id})['follower_count']+1 }})

# Action 3: remove a relationship between two users if one unfollows the other
def unfollow(from_id, to_id):
	follows.remove({"follower": from_id, "following": to_id})
	users.update({'_id': from_id}, {'$set': {'following_count': users.find_one({'_id':from_id})['following_count']-1}})
	users.update({'_id': to_id}, {'$set': {'follower_count': users.find_one({'_id': from_id})['follower_count']-1}})

# Action 4: post a photo
def photo(user, url):
	return photos.insert_one({'user_id': user['_id'], 'url': url, 'time': datetime.datetime.utcnow(), "likes": 0, 'comments': 0}).inserted_id

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
def unregister(user, password):
	if users.find_one({'_id': user['_id']})['password'] != password:
		print("Invalid password!")
		return

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

# Action 9: retrieve all the photos of the user that the user querying follows
def get_photos(user1, user2):
	phos = []
	if follows.find({'follower': user1['_id'], 'following': user2['_id']}):
		for i in photos.find({'user_id': user2['_id']}):
			phos.append(i['url'])
	return phos


# helper to return the document from the collections:
def find_user(user_id):
	return users.find_one({'_id': user_id})

def find_photo(photo_id):
	return photos.find_one({'_id': photo_id})

def main():
	# add a bunch of users
	down_id = register("Robert Downey Jr", "downey1965", "04-04-1965", "Ironman: genius, billionaire, playboy philanthropist")
	holl_id = register("Tom Holland", "holland1996", "06-01-1996", "A dancer, an actor, the Spiderman")
	hems_id = register("Christopher Hemsworth", "hemsworth1983", "08-11-1983", "Once the Sexiest Man in the world")
	

#	print("\n>>> Testing user registration")
#	for i in users.find({}):
#		print("    "+str(i))
	
	# find user docs using their ids
	downey = find_user(down_id)
	holland = find_user(holl_id)
	hemsworth = find_user(hems_id)
	
	# users can follow others
	follow(down_id, holl_id)
	follow(holl_id, down_id)
	follow(holl_id, hems_id)
	follow(hems_id, down_id)
	follow(down_id, hems_id)
	follow(hems_id, holl_id)

#	print("\n>>> Testing action follow")
#	count = 0
#	for i in follows.find({}):
#		count += 1
#	print("    Follow records count: "+str(count))
#	print("    Downey's following count: "+str(find_user(down_id)['following_count']))
#	print("    Holland's follower count: "+str(find_user(holl_id)['follower_count']))

	# users can also unfollow other users.	
	unfollow(down_id, holl_id)

	print("\n>>> Testing action unfollow")
	count = 0
	for i in follows.find({}):
		count += 1
	print("    Follow records count: "+str(count))
	print("    Downey's following count: "+str(find_user(down_id)['following_count']))
	print("    Holland's follower count: "+str(find_user(holl_id)['follower_count']))		

	# user can post a photo
	pho1 = photo(downey, "https://www.instagram.com/p/Bhwc28fDcyC/?hl=en&taken-by=robertdowneyjr")
	pho2 = photo(holland, "https://www.instagram.com/p/BiNdfdiFTeg/?hl=en&taken-by=tomholland2013")
	pho3 = photo(hemsworth, "https://www.instagram.com/p/BiBNtG4Fxqg/?hl=en&taken-by=chrishemsworth")
	pho4 = photo(holland, "https://www.instagram.com/p/BhkdYGJF4k0/?hl=en&taken-by=tomholland2013")	
	pho5 = photo(downey, "https://www.instagram.com/p/Bh8DjesD_lR/?hl=en&taken-by=robertdowneyjr")
	pho6 = photo(downey, "https://www.instagram.com/p/BhtDGCMDe0v/?hl=en&taken-by=robertdowneyjr")
	pho7 = photo(hemsworth, "https://www.instagram.com/p/BgQBJlRFX6C/?hl=en&taken-by=chrishemsworth")

	# user can like a photo
	like(hemsworth, find_photo(pho1))
	like(holland, find_photo(pho1))
	like(downey, find_photo(pho2))
	like(holland, find_photo(pho6))
	like(holland, find_photo(pho3))
	like(hemsworth, find_photo(pho4))

	print("\n>>> Testing photo posts and likes")
	print("    Downey's first photo has likes: "+str(find_photo(pho1)['likes']))
	print("    Holland's fisrt photo has likes: "+str(find_photo(pho2)['likes']))

	# user can unlike a photo
	unlike(hemsworth, find_photo(pho1))
	
	print("\n>>> Testing unliking a photo")
	print("    Downey's first photo has likes: "+str(find_photo(pho1)['likes']))

	# user can comment on a photo
	comment(hemsworth, find_photo(pho1), "Why am I not in the photo?")
	comment(downey, find_photo(pho1), "Oops!")
	comment(holland, find_photo(pho1), "I look great!")
	comment(downey, find_photo(pho4), "It's so good to be young!")
	comment(downey, find_photo(pho6), "I really like this vase. It's trully a masterpiece")
	comment(hemsworth, find_photo(pho6), "You see my hammer by any chance?")
	comment(holland, find_photo(pho6), "I really should stay away from these.. just in case")
	comment(holland, find_photo(pho6), "Oh, I like the hat btw")	
	comment(hemsworth, find_photo(pho7), "Which hair style looks better: long or short?")

	for c in comments.find({'photo_id': pho1}):
		print("    "+ str(users.find_one({'_id':c['user_id']})['username']) + " says: "+ c['comment']+ " at "+ str(c['time']))
	
	# a user can retrieve all the photos of the other user that it follows
	phos = get_photos(holland, downey)
	print("\n>>> Testing user retrieving all photos from who it follows")
	print(phos)

	# a user can also unregister from the application
	print("\n>>> Testing unregister with wrong password")
	unregister(holland, "just kidding!")
	print("\n>>> Testing successful unregister")

	unregister(holland, "holland1996")
	print("    Currently registered users:")
	for i in users.find({}):
		print("      "+str(i["username"]))

if __name__ == "__main__":
	main()
