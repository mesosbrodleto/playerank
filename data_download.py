"""

Downloading script for soccer logs public open dataset:
https://figshare.com/collections/Soccer_match_event_dataset/4415000/2

Data description available here:

Please cite the source as:


"""

import requests, zipfile, json, io


dataset_links = {

'matches' : 'https://ndownloader.figshare.com/files/14464622',
'events' : 'https://ndownloader.figshare.com/files/14464685',
'players' : 'https://ndownloader.figshare.com/files/15073721',
'teams': 'https://ndownloader.figshare.com/files/15073697',
}


r = requests.get(dataset_links['matches'], stream=True)
z = zipfile.ZipFile(io.BytesIO(r.content))
z.extractall("data/matches")

r = requests.get(dataset_links['events'], stream=True)
z = zipfile.ZipFile(io.BytesIO(r.content))
z.extractall("data/events")
#
r = requests.get(dataset_links['teams'], stream=True)
print (r.content, file=open('data/teams.json','w'))


r = requests.get(dataset_links['players'], stream=True)
print (r.content, file=open('data/players.json','w'))
