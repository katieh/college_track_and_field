## ------------------------------------------------------------------ ##
##                         Import Statements                          ##
## ------------------------------------------------------------------ ##
from bs4 import BeautifulSoup
import requests
import pandas as pd
import json
import sys
import time
import os

## ------------------------------------------------------------------ ##
##                              Main Method                           ##
## ------------------------------------------------------------------ ##

## Open datafile. Modified from
## http://stackoverflow.com/questions/20199126/reading-a-json-file-using-python
with open(sys.argv[1]) as json_data:
  data = json.load(json_data)
  json_data.close()

team_look_up = {}
team_look_up['team_name'] = []
team_look_up['division'] = []

for team_entry in data:
  team_name = team_entry[0]
  team_link = team_entry[1]
  team_division = None

  print team_name, team_link

  ## geat team page
  request = requests.get(team_link)

  ## keep requesting until you get a + responce
  i = 0
  while not request.status_code == requests.codes.ok and i < 5:
    time.sleep(1)
    request = requests.get(team_link)
    i = i + 1

  if request.status_code == requests.codes.ok:

    ## get beautifulsoup object
    team_page = request.text
    soup = BeautifulSoup(team_page, 'lxml')

    ## get all leagues
    leagues = soup.find('ul', { "class" : "headleague" }).findAll('a')

    ## see if any of the leagues are DI, DII, DIII
    for entry in leagues:
      league = entry.text

      if 'DIII' in league:
        team_division = 'DIII'

      elif 'DII' in league:
        team_division = 'DII'

      elif 'DI' in league:
        team_division = 'DI'

    if team_division is None:
      print team_name, "has no division"

    else:
      print team_name, team_division

    ## append entry
    team_look_up['team_name'].append(team_name)
    team_look_up['division'].append(team_division)

## save as CSV file
dataframe = pd.DataFrame(team_look_up)
dataframe.to_csv('team_divisions.csv', encoding="utf-8", index=False)

