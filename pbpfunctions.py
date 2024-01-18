import pandas as pd
import requests
import json
import numpy as np

ALL_TEAMS = [
   'Hawks', 'Celtics', 'Nets', 'Hornets', 'Bulls', 'Cavaliers',
   'Mavericks', 'Nuggets', 'Pistons', 'Warriors', 'Rockets', 'Pacers',
   'Clippers', 'Lakers', 'Grizzlies', 'Heat', 'Bucks', 'Timberwolves',
   'Pelicans', 'Knicks', 'Thunder', 'Magic', '76ers', 'Suns',
   'Trail Blazers', 'Kings', 'Spurs', 'Raptors', 'Jazz', 'Wizards'
]

def get_team_id(team: str):
  if team in ['ATL', 'Hawks', 'Atlanta Hawks']:
      return(1610612737)
  elif team in ['BOS', 'Celtics', 'Boston Celtics']:
      return 1610612738
  elif team in ['BKN', 'Nets', 'Brooklyn Nets']:
      return 1610612751
  elif team in ['CHA', 'Hornets', 'Charlotte Hornets']:
      return 1610612766
  elif team in ['CHI', 'Bulls', 'Chicago Bulls']:
      return 1610612741
  elif team in ['CLE', 'Cavaliers', 'Cleveland Cavaliers']:
      return 1610612739
  elif team in ['DAL', 'Mavericks', 'Dallas Mavericks']:
      return 1610612742
  elif team in ['DEN', 'Nuggets', 'Denver Nuggets']:
      return 1610612743
  elif team in ['DET', 'Pistons', 'Detroit Pistons']:
      return 1610612765
  elif team in ['GSW', 'Warriors', 'Golden State Warriors']:
      return 1610612744
  elif team in ['HOU', 'Rockets', 'Houston Rockets']:
      return 1610612745
  elif team in ['IND', 'Pacers', 'Indiana Pacers']:
      return 1610612754
  elif team in ['LAC', 'Clippers', 'Los Angeles Clippers']:
      return 1610612746
  elif team in ['LAL', 'Lakers', 'Los Angeles Lakers']:
      return 1610612747
  elif team in ['MEM', 'Grizzlies', 'Memphis Grizzlies']:
      return 1610612763
  elif team in ['MIA', 'Heat', 'Miami Heat']:
      return 1610612748
  elif team in ['MIL', 'Bucks', 'Milwaukee Bucks']:
      return 1610612749
  elif team in ['MIN', 'Timberwolves', 'Minnesota Timberwolves']:
      return 1610612750
  elif team in ['NOP', 'Pelicans', 'New Orleans Pelicans']:
      return 1610612740
  elif team in ['NYK', 'Knicks', 'New York Knicks']:
      return 1610612752
  elif team in ['OKC', 'Thunder', 'Oklahoma City Thunder']:
      return 1610612760
  elif team in ['ORL', 'Magic', 'Orlando Magic']:
      return 1610612753
  elif team in ['PHI', '76ers', 'Philadelphia 76ers']:
      return 1610612755
  elif team in ['PHX', 'Suns', 'Phoenix Suns']:
      return 1610612756
  elif team in ['POR', 'Trail Blazers', 'Portland Trail Blazers']:
      return 1610612757
  elif team in ['SAC', 'Kings', 'Sacramento Kings']:
      return 1610612758
  elif team in ['SAS', 'Spurs', 'San Antonio Spurs']:
      return 1610612759
  elif team in ['TOR', 'Raptors', 'Toronto Raptors']:
      return 1610612761
  elif team in ['UTA', 'Jazz', 'Utah Jazz']:
      return 1610612762
  elif team in ['WAS', 'Wizards', 'Washington Wizards']:
      return 1610612764
  else:
    return 0
 
def adjust_minutes(df: pd.DataFrame):
  try:
    df['Min'] = df['Minutes'].str.split(':').str[0].astype(float)
    df['Sec'] = df['Minutes'].str.split(':').str[1].astype(float) / 60
    df['Minutes'] = df['Min'] + df['Sec'].round(2)
    df = df.drop(columns=['Min', 'Sec'])
  except:
    pass
  return df

def get_player_id(player: str):
  r = requests.get('https://api.pbpstats.com/get-all-players-for-league/nba')
  data = json.loads(r.content).get('players')
  ids = list(data.keys())
  names = list(data.values())
  return ids[names.index(player)]

def get_team_logs(team: str, season: int):
  team_id = get_team_id(team)
  url = f'https://api.pbpstats.com/get-game-logs/nba?Season={season}-{season + 1 - 2000}&SeasonType=Regular%2BSeason&EntityId={team_id}&EntityType=Team'
  response = requests.get(url)
  data = json.loads(response.content)
  df = pd.DataFrame(data.get('multi_row_table_data')).fillna(0)
  df['Team'] = team
  df['Season'] = season
  return adjust_minutes(df)

def get_player_logs(player: str, season: int):
  pid = get_player_id(player)
  url = f'https://api.pbpstats.com/get-game-logs/nba?Season={season}-{season + 1 - 2000}&SeasonType=Regular%2BSeason&EntityId={pid}&EntityType=Player'
  r = requests.get(url)
  data = json.loads(r.content).get('multi_row_table_data')
  df = pd.DataFrame(data).fillna(0)
  df['Name'] = player
  df['Season'] = season
  df = adjust_minutes(df)
  return df

def get_scoreboard(season: int):
  url = f'https://api.pbpstats.com/get-games/nba?Season={season}-{season + 1 - 2000}&SeasonType=Regular%2BSeason'
  r = requests.get(url)
  data = json.loads(r.content).get('results')
  df = pd.DataFrame(data)
  home = df.rename(
      columns={'HomeTeamId': 'TeamId', 'AwayTeamId': 'OppId', 'HomePoints': 'TeamScore', 'AwayPoints': 'OppScore', 'HomePossessions': 'TeamPoss', 'AwayPossessions': 'OppPoss', 'HomeTeamAbbreviation': 'Team', 'AwayTeamAbbreviation': 'Opp'}
  )
  home['Home'] = True
  home['Date'] = pd.to_datetime(home['Date'], format='%Y-%m-%d')
  away = df.rename(
      columns={'HomeTeamId': 'OppId', 'AwayTeamId': 'TeamId', 'HomePoints': 'OppScore', 'AwayPoints': 'TeamScore', 'HomePossessions': 'OppPoss', 'AwayPossessions': 'TeamPoss', 'HomeTeamAbbreviation': 'Opp', 'AwayTeamAbbreviation': 'Team'}
  )
  away['Home'] = False
  away['Date'] = pd.to_datetime(away['Date'], format='%Y-%m-%d')
  df = pd.concat([home, away])
  return df.sort_values(by='Date')

def get_game_stats(ids: list, seasons: list, dates: list, teams: list, opps: list):
  stats = []
  for i in range(0, len(ids)):
    url = f'https://api.pbpstats.com/get-game-stats?Type=Player&GameId={ids[i]}'
    r = requests.get(url)
    data = json.loads(r.content)
    home = pd.DataFrame(data.get('stats').get('Home').get('FullGame'))
    home = home[home['Name'] != 'Team']
    home = home.drop(columns=['ShortName'])
    home['Team'] = teams[i]
    home['Season'] = seasons[i]
    home['Date'] = dates[i]
    home['Opp'] = opps[i]
    away = pd.DataFrame(data.get('stats').get('Away').get('FullGame'))
    away = away[away['Name'] != 'Team']
    away = away.drop(columns=['ShortName'])
    away['Team'] = opps[i]
    away['Season'] = seasons[i]
    away['Date'] = dates[i]
    away['Opp'] = teams[i]
    stats.append(pd.concat([home, away]))
  df = pd.concat(stats)
  df = df.fillna(0)
  df = adjust_minutes(df)
  return df

def get_team_roster(team: str, season: int):
  url = f'https://api.pbpstats.com/get-team-players-for-season?Season={season}-{season+1-2000}&SeasonType=Regular%20Season&TeamId={get_team_id(team)}'
  r = requests.get(url)
  data = json.loads(r.content)
  data = data.get('players')
  df = pd.DataFrame({
      'Season': season,
      'Team': team,
      'Name': list(data.values()),
      'PlayerId': list(data.keys())
  })
  return df

def get_team_counting(team: str, season: int):
  stats = []
  roster = get_team_roster(team, season)
  for player in roster['Name']:
    try:
      logs = get_player_logs(player, season)
      new = pd.DataFrame()
      hopeful_cols = ['GameId', 'Date', 'Team', 'Opponent', 'Minutes', 'Points', 'Assists', 'DefRebounds', 'Rebounds', 'Steals', 'Blocks', 'Turnovers', 'FG2M', 'FG2A', 'FG3M', 'FG3A']
      for col in hopeful_cols:
        try:
          new[col] = logs[col]
        except:
          new[col] = 0
      new['Name'] = player
      new['Season'] = season
      stats.append(new)
    except:
      print(f'No Stats for {player}')
  team_logs = pd.concat(stats)
  team_logs = team_logs.fillna(0)
  team_logs['OffRebounds'] = team_logs['Rebounds'] - team_logs['DefRebounds']
  return team_logs[['GameId', 'Date', 'Season', 'Team', 'Opponent', 'Name', 'Minutes', 'Points', 'Assists', 'DefRebounds', 'OffRebounds', 'Rebounds', 'Steals', 'Blocks', 'Turnovers', 'FG2M', 'FG2A', 'FG3M', 'FG3A']]

def get_season_logs(season: int):
   counting_stats = []
   for team in ALL_TEAMS:
      print(f'{team}: {season}')
      try:
         team_stats = get_team_counting(team, season)
         counting_stats.append(team_stats)
      except:
         print(f'Missing data for {team}')
   season_logs = pd.concat(counting_stats)
   return season_logs

def get_ctg_stats(folder_path: str):
   # Rebounding
   defreb = pd.read_csv(f'{folder_path}/defense-rebounding.csv')
   defreb = defreb[['Player', 'Team', 'Pos', 'fgDR% Rank', 'fgOR% Rank']].copy().rename(columns={'fgDR% Rank': 'DREBRank', 'fgOR% Rank': 'OREBRank'})
   foul = pd.read_csv(f'{folder_path}/foul-drawing.csv')
   foul = foul[['Player', 'Team', 'SFLD% Rank']].copy().rename(columns={'SFLD% Rank': 'FoulRateRank'})
   offense = pd.read_csv(f'{folder_path}/offensive-overview.csv')
   offense = offense[['Player', 'Team', 'Usage Rank', 'PSA Rank', 'AST% Rank']].copy()
   shootfreq = pd.read_csv(f'{folder_path}/shooting-frequency.csv')
   shootfreq = shootfreq[['Player', 'Team', 'Rim Rank', 'All Mid Rank', 'All Three Rank']].copy()
   shootover = pd.read_csv(f'{folder_path}/shooting-overall.csv')
   shootover = shootover[['Player', 'Team', '2P%', '3P%']].copy()
   player_stats = pd.merge(defreb, foul, on=['Player', 'Team']).merge(offense, on=['Player', 'Team']).merge(shootfreq, on=['Player', 'Team']).merge(shootover, on=['Player', 'Team'])
   player_stats['2P%'] = player_stats['2P%'].str.rstrip('%')
   player_stats['3P%'] = player_stats['3P%'].str.rstrip('%')
   player_stats['2P%'] = player_stats['2P%'].astype(float)
   player_stats['3P%'] = player_stats['3P%'].astype(float)
   return player_stats

def update_player_adv_stats(season: int, path: str):
    url = f'https://www.basketball-reference.com/leagues/NBA_{season + 1}_advanced.html'
    response = requests.get(url)
    tables = pd.read_html(response.content)
    padv = tables[0]
    padv = padv[padv['Player'] != 'Player']
    padv = padv.drop(columns=['Unnamed: 19', 'Unnamed: 24'])
    padv.to_csv(path)
    print('Updated Player Advanced Stats')