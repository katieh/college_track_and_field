## ------------------------------------------------------------------ ##
##  get_team_links.py                                                 ##
##                                                                    ##
##  Name: Katie Hanss                                                 ##
##  NetID: khanss                                                     ##
##                                                                    ##
##  Description: This program uses tfrrs search feature to get a set  ##
##  of all schools in the NCAA and their tfrrs page.                  ##
## ------------------------------------------------------------------ ##

## ------------------------------------------------------------------ ##
##                         Import Statements                          ##
## ------------------------------------------------------------------ ##

from bs4 import BeautifulSoup
import requests
import json

## ------------------------------------------------------------------ ##
##                              Main Method                           ##
## ------------------------------------------------------------------ ##

## declare sets and search URL
teams = set()
f_teams = set()
m_teams = set()
search = 'https://www.tfrrs.org/team_search.html?team_search='

alphabet = ['a', 'b' 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

## search for each letter in the alphabet
for letter in alphabet:

  ## request page and find results
  search_page = requests.get(search + letter).text
  soup = BeautifulSoup(search_page, 'lxml')
  table = soup.find('div', {'id': 'results_search'}).find('div', 'data')
  rows = table.find_all('tr')

  ## get results and put the team names and links into the
  ## the appropriate sets.
  for row in rows:
    if row.find('td', 'name') is not None:
      team_name = row.find('td', 'name').text.replace('\n', '')
      team_link = 'https:' + row.find('a').get('href')
      teams.add((team_name, team_link))

      if '(F)' in team_name:
        f_teams.add((team_name, team_link))

      else:
        m_teams.add((team_name, team_link))

## save files
with open('team_links.json', 'w') as fp:
  json.dump(list(teams), fp)

with open('male_team_links.json', 'w') as fp:
  json.dump(list(m_teams), fp)

with open('female_team_links.json', 'w') as fp:
  json.dump(list(f_teams), fp)