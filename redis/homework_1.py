import json
import urllib.request 

url="https://api.nasa.gov/planetary/apod?date=2017-01-26&api_key=dhluCFyP1IcpgrZqhUK27IALEzkJPFc8lpHNO8Wk"

content = urllib.request.urlopen(url).read()

encoding = urllib.request.urlopen(url).info().get_content_charset('utf-8')

contentjs = json.loads(content.decode(encoding))

print(contentjs['url'])
