import redis
import datetime


ONE_WEEK_IN_SECONDS = 7 * 86400
VOTE_SCORE = 432

def article_vote(redis, user, article):
    cutoff = datetime.datetime.now() - datetime.timedelta(seconds=ONE_WEEK_IN_SECONDS)

    if not datetime.datetime.fromtimestamp(redis.zscore('time:', article)) < cutoff:
        article_id = article.split(':')[-1]
        if redis.sadd('voted:' + article_id, user):
            redis.zincrby(name='score:', amount = VOTE_SCORE, value = article)
            redis.hincrby(name=article, key='votes', amount=1)

def article_switch_vote(redis, user, from_article, to_article):
    from_article_id = from_article.split(':')[-1]
    to_article_id = to_article.split(':')[-1]
    
    # remove up vote from article
    redis.zincrby(name='score:', amount=-VOTE_SCORE, value=from_article)
    redis.hincrby(name=from_article, key='votes', amount=-1)
    redis.srem('voted:' + from_article_id, user)
    # up vote for the article
    redis.zincrby(name='score:', amount=VOTE_SCORE, value=to_article)
    redis.hincrby(name=to_article, key='votes', amount=1)
    redis.sadd('voted:' + to_article_id, user)


redis = redis.StrictRedis(host='localhost', port=6379, db=0)

# user up votes and switch votes
article_vote(redis, "user:3", "article:1")
article_vote(redis, "user:3", "article:3")
article_switch_vote(redis, "user:2", "article:8", "article:1")

# zrange command to find "Easter egg" article
easter_egg = redis.zrangebyscore(name="score:", min=10, max=20)
easter_egg_id = easter_egg[0].split(':')[-1]
print(redis.hget("article:" + easter_egg_id, "link"))
