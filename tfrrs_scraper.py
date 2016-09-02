## ------------------------------------------------------------------ ##
##  Name: Katie Hanss                                                 ##
##  NetID: khanss                                                     ##
##                                                                    ##
##  Description: This program crawles through team pages of the links ##
##  pervided in the args[1] file. It saves the result of the crawl    ##
##  in a file named args[2].                                          ##
##                                                                    ##
##  Commandline Arguments:                                            ##
##                                                                    ##
##  args[1] - name of file with links. File must be formated as:      ##
##  [[team_name 1, team_link 1], [team_name 2, team_link 2], ...]     ##
##                                                                    ##
##  args[2] - name of the file that you want to save the results to   ##
## ------------------------------------------------------------------ ##

## ------------------------------------------------------------------ ##
##                         Import Statements                          ##
## ------------------------------------------------------------------ ##
from bs4 import BeautifulSoup
import requests
import json
import sys
import time
import os

## ------------------------------------------------------------------ ##
##                       Get All Seasons Function                     ##
## ------------------------------------------------------------------ ##
def get_all_seasons(team_link):

  tl = []
  tl.append(team_link)

  ## get links to all years on the roster
  seasons = None
  i = 0

  while seasons is None and i < 10:
    start_page = requests.get(team_link).text
    soup = BeautifulSoup(start_page, 'lxml')
    seasons = soup.find('div', {'id':'seasons_block'})
    i = i + 1

  seasons = seasons.findAll('option')
  for season in seasons:
    season_link = team_link + '?config_hnd=' + season.get('value')
    tl.append(season_link)

  return tl

## ------------------------------------------------------------------ ##
##                      Get Athlete Links Function                    ##
## ------------------------------------------------------------------ ##

def get_athlete_links(season_links):

  ## athlete list
  al = set()

  ## get links to all athletes on the roster from all years
  ## NOTE: ONLY TAKE SENIORS!
  for season_link in season_links:

    table = None
    i = 0

    while table is None and i < 10:
      time.sleep(0.5 + i)
      season_page = requests.get(season_link).text
      soup = BeautifulSoup(season_page, 'lxml')
      table = soup.find('div', 'data scroll')
      i = i + 1

    table = table.find('table')
    rows = table.find_all('tr')
    for row in rows:
      if 'SR' in row.find('td', 'year').text:
        al.add('https:' + row.find('a').get('href').replace('\t',''))

  return al

## ------------------------------------------------------------------ ##
##                       Process Team Function                        ##
## ------------------------------------------------------------------ ##

def process_team(team_link):

  ## get links to all seasons
  season_links = get_all_seasons(team_link)
  ##season_links = [team_link]

  ## get athlete links and return them
  return get_athlete_links(season_links)

## ------------------------------------------------------------------ ##
##                       Process Athlete Function                     ##
## ------------------------------------------------------------------ ##

def process_athlete(team_name, athlete_link, team_tree, meets_tree, events_tree):

  ## get the athlete data
  athlete_data = None
  i = 0

  while athlete_data is None and i < 10:
    time.sleep(0.5 + i)
    athlete_page = requests.get(athlete_link).text
    soup = BeautifulSoup(athlete_page, 'lxml')
    athlete_data = soup.find('div', id='athlete')
    i = i + 1

  ## get athlete name
  name = athlete_data.find('div', 'title').find('h2').text
  print '\t' + athlete_link

  ## get athlete tree (create new if not already there)
  if name not in team_tree.keys():
    team_tree[name] = {}
  athlete_tree = team_tree[name]

  ## put times and events into the athlete tree
  meet_results = athlete_data.find('div', 'meetresults')
  rows = meet_results.find_all('tr')
  del rows[0]
  for row in rows:
    cells = row.findAll('td')
    race = {}

    ## save time info
    mark = cells[5].find('a')

    ## early on in the cite, markes may not be linked and are
    ## instead in a <span title = "Submitted by coach.">mark</span>
    if mark is None:
      mark = cells[5].find('span')

    ## remove weird characters that are sometimes in the mark
    mark = mark.text.replace('\n', '')

    ## if it's a jump / throw / etc. recorded in meters
    if 'm' in mark:
      if mark.replace('m', '').replace('.', '').isdigit():
        race['unit'] = 'meters'
        race['mark'] = float(mark.replace('m', ''))
      else:
        not_processed.add(mark)
        race['unit'] = None
        race['mark'] = None

    elif '\'' in mark:
      marks = mark.split('\'')
      if marks[0].replace('.', '').isdigit() and marks[1].replace('\'', '').replace('"', '').replace('.', '').isdigit:
        race['unit'] = 'meters'
        race['mark'] = float(marks[0]) * 0.3048 + float(marks[1].replace('\'', '').replace('"', '')) * 0.0254
      else:
        not_processed.add(mark)
        race['unit'] = None
        race['mark'] = None

    elif ':' in mark:
      if mark[:mark.find(':')].replace('.', '').isdigit() and mark[mark.find(':') + 1:].replace('.', '').isdigit():
        race['unit'] = 'seconds'
        race['mark'] = float(mark[:mark.find(':')]) * 60 + float(mark[mark.find(':') + 1:])
      else:
        print name, mark
        sys.exit("Found an example")
        not_processed.add(mark)
        race['unit'] = None
        race['mark'] = None

    elif mark.replace('.', '').isdigit():
      race['unit'] = 'seconds'
      race['mark'] = float(mark)

    else:
      not_processed.add(mark)
      race['unit'] = None
      race['mark'] = None

    ## only add the event if we have a mark
    if race['mark'] != None:

      ## get race date in correct format
      date = cells[0].text.replace('\n', '')

      if '/' in date and '-' in date:
        date = date[date.find('-') + 1:].replace('/', '-')

      elif '/' in date:
        date = date.replace('/', '-')

      race['date'] = date.replace(' ', '')

      ## get the meet information
      meet = cells[1].find('a')
      if meet is None:
        meet = cells[1]
      race['meet'] = meet.text.replace('\n', '')

      ## extract other race information
      race['athlete'] = name
      race['team'] = team_name
      race['mark_string'] = mark
      race['sport'] = cells[2].text.replace('\n', '')
      race['event'] = cells[3].text.replace('\t', '').replace('\n', '')
      race['rnd'] = cells[4].text.replace('\n', '')
      race['place'] = cells[7].text.replace('\n', '')

      ## if the event is NOT a relay, put into athlete event tree
      if 'x' not in race['event'] and 'R' not in race['event']:

        ## --------------------- PUT EVENT IN TEAM TREE --------------- ##

        ## create athlete event tree if not already there.
        if race['event'] not in athlete_tree.keys():
          athlete_tree[race['event']] = []

        athlete_tree[race['event']].append(race)

        ## --------------------- PUT EVENT IN MEET TREE --------------- ##

        ## create meet node if nessesary
        if race['meet'] not in meets_tree.keys():
          meets_tree[race['meet']] = {}

        ## create meet-event node if nessesary
        if race['event'] not in meets_tree[race['meet']].keys():
          meets_tree[race['meet']][race['event']] = []

        ## put race in the meet-event
        meets_tree[race['meet']][race['event']].append(race)

  ## ---------------------- PUT EVENT IN EVENTS TREE ---------------- ##

  for event in athlete_tree:

    ## sort the list of events
    athlete_tree[event].sort(key=lambda x: x['mark'])

    ## create event node in NCAA tree if nessesary
    if event not in events_tree.keys():
      events_tree[event] = []

    ## events where larger mark is better
    if event is ('HJ' or 'PV' or 'LJ' or 'TJ' or 'SP' or 'WT' or 'DT' or 'HT' or 'JT' or 'Hep' or 'Pent' or 'Dec'):
      events_tree[event].append(athlete_tree[event][len(athlete_tree[event]) - 1])

    ## events where smaller mark is better
    else:
      events_tree[event].append(athlete_tree[event][0])

## ------------------------------------------------------------------ ##
##                              Main Method                           ##
## ------------------------------------------------------------------ ##

## throw error if there aren't enough command-line arguments
if len(sys.argv) < 3:
  raise Exception('Please provide input and output json file names')

## store list of marks that the scraper couldn't handle
not_processed = set()

if os.path.isfile(sys.argv[2]):
  with open(sys.argv[2]) as data_file:
    NCAA_Tree = json.load(data_file)

else:
  ## NCAA TREE
  NCAA_Tree = {}

  ## female branch
  NCAA_Tree['f'] = {}
  NCAA_Tree['f']['teams'] = {}
  NCAA_Tree['f']['events'] = {}
  NCAA_Tree['f']['meets'] = {}

  ## male branch
  NCAA_Tree['m'] = {}
  NCAA_Tree['m']['teams'] = {}
  NCAA_Tree['m']['events'] = {}
  NCAA_Tree['m']['meets'] = {}

## Open datafile. Modified from
## http://stackoverflow.com/questions/20199126/reading-a-json-file-using-python
with open(sys.argv[1]) as json_data:
  data = json.load(json_data)
  json_data.close()

## process all team links in the data file
for team_entry in data:
  team_name = team_entry[0]
  team_link = team_entry[1]

  print team_name, team_link

  ## figure out the gender of the team and modify name
  gender = 'f'
  if '(M)' in team_name:
    gender = 'm'

  ## create the team branch if it doesn't already exhist.
  if team_name not in NCAA_Tree[gender]['teams'].keys():
    NCAA_Tree[gender]['teams'][team_name] = {}

  ## pointers to places in the tree (for convenience)
  team_tree = NCAA_Tree[gender]['teams'][team_name]
  meets_tree = NCAA_Tree[gender]['meets']
  events_tree = NCAA_Tree[gender]['events']

  ## get the athlete links and team tree
  athlete_links = process_team(team_link)

  ## add each athlete to the team tree
  for athlete_link in athlete_links:
    process_athlete(team_name, athlete_link, team_tree, meets_tree, events_tree)

  ## sort the NCAA female event lists
  for event in NCAA_Tree['f']['events']:
    NCAA_Tree['f']['events'][event].sort(key=lambda x: x['mark'])

  ## sort the NCAA male event lists
  for event in NCAA_Tree['m']['events']:
    NCAA_Tree['m']['events'][event].sort(key=lambda x: x['mark'])

  with open(sys.argv[2], 'w') as fp:
    json.dump(NCAA_Tree, fp)

print "I didn't know how to handle:"
for mark in not_processed:
  print "   " + mark

