import pymongo
from pymongo import MongoClient

# set up connection to import the database
collection = MongoClient().test.movies

# Part A: update documents with specified variable values in-place and atomically
target_docs = collection.find({"genres": "Drama", "rated": "NOT RATED"})
for d in target_docs:
    collection.update({"_id": d["_id"]}, {'$set':{"rated": "Pending rating"}})

# Part B: insert a Drama movie into the database
collection.insert_one({"title":"A Quiet Place", "year":2018, "countries":["United States"], "genres":["Drama", "Sci-Fi", "Horror"], "directors":["John Krasinski"], "imdb":{"id":6644200, "rating":8.1, "votes":53102}})
# testing 
# print(collection.find({"title":"A Quiet Place"})[0]["genres"])

# Part C: aggregate to get the sum of documents whose genre includes Drama
cursor_c = collection.aggregate([{"$match":{"genres": "Drama"}}, {"$group": {"_id": "Drama", "count": {"$sum": 1}}}])
# testing
# for d in cursor_c:
#     print(d)

# Part D: count the movies made in the country I was borned
cursor_d = collection.aggregate([{"$match": {"countries": "China", "rated": "Pending rating"}}, {"$group": {"_id": {"country": "China", "rating": "Pending rating"}, "count": {"$sum": 1}}}])
# testing
#print(list(cursor_d))

# Part E:
# insert new docs to two new collections
MongoClient().test.teams.insert({"team": "Golden State Warriors", "champ": 5})
MongoClient().test.teams.insert({"team": "Los Angeles Lakers", "champ": 16})

MongoClient().test.players.insert({"team": "Golden State Warriors", "player": "Steph Curry"})
MongoClient().test.players.insert({"team": "Los Angeles Lakers", "player": "Kobe Bryant"})

combined = MongoClient().test.teams.aggregate([{"$lookup": {"from": "players", "localField": "team", "foreignField": "team", "as": "members"}}])
#print(list(combined))


