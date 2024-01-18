import streamlit as st
import pandas as pd
import numpy as np
import pbpfunctions as pbpf
import pybet

# STREAMLIT PREFS
st.set_page_config(layout='wide')

# ADD COMBOS TO DATAFRAME
def add_combos(df: pd.DataFrame):
   df['Date'] = pd.to_datetime(df['Date'])
   df['FTM'] = df['Points'] - (2 * df['FG2M']) - (3 * df['FG3M'])
   df['P+R'] = df['Points'] + df['Rebounds']
   df['P+A'] = df['Points'] + df['Assists']
   df['R+A'] = df['Rebounds'] + df['Assists']
   df['P+R+A'] = df['Points'] + df['Rebounds'] + df['Assists']
   df['Stocks'] = df['Steals'] + df['Blocks']
   return df

# GLOBAL DATA TO USE
base = pd.read_csv('./new-logs.csv').drop_duplicates()
base = add_combos(base)
ALL_PLAYERS = sorted(list(set(base.Name)))
ALL_PLAYERS.insert(0, 'Any Player')
ALL_TEAMS = sorted(list(set(base.Team)))
ALL_TEAMS.insert(0, 'Any Team')
scores = pd.read_csv('./current-scoreboard.csv')
player_stats = pd.read_csv('./player-advanced.csv').drop(columns=['Unnamed: 0'])
player_stats = player_stats[player_stats['MP'] >= 48].fillna(0)

# FILTER PLAYERS BY POSITION
def filter_players(
   positions, mpg_min, mpg_max, per_min, per_max, usg_min, usg_max, fg3r_min, fg3r_max, ftr_min, ftr_max, orb_min,
   orb_max, drb_min, drb_max, ast_min, ast_max, stl_min, stl_max, blk_min, blk_max
):
   if len(positions) > 0:
      dfs = []
      for pos in positions:
         temp = player_stats[player_stats['Pos'].str.contains(pos)].copy()
         dfs.append(temp)
      df = pd.concat(dfs)
   else:
      df = player_stats.copy()
   df['MPG'] = df['MP'] / df['G']
   for col in ['3PAr', 'FTr']:
      df[col] = df[col] * 100
   df = df[
      ((df['MPG'] >= mpg_min) & (df['MPG'] <= mpg_max)) &
      ((df['PER'] >= per_min) & (df['PER'] <= per_max)) &
      ((df['USG%'] >= usg_min) & (df['USG%'] <= usg_max)) &
      ((df['3PAr'] >= fg3r_min) & (df['3PAr'] <= fg3r_max)) &
      ((df['FTr'] >= ftr_min) & (df['FTr'] <= ftr_max)) &
      ((df['ORB%'] >= orb_min) & (df['ORB%'] <= orb_max)) &
      ((df['DRB%'] >= drb_min) & (df['DRB%'] <= drb_max)) &
      ((df['AST%'] >= ast_min) & (df['AST%'] <= ast_max)) &
      ((df['STL%'] >= stl_min) & (df['STL%'] <= stl_max)) &
      ((df['BLK%'] >= blk_min) & (df['BLK%'] <= blk_max))
   ]
   return list(df.Player)

# GET PLAYERS
def get_players(team: str):
   roster = pbpf.get_team_roster(team, 2023)
   return roster.Name

# ADJUST 'REST'
def format_rest(rest):
   if rest >= 3:
      return '3+'
   elif rest == 2:
      return '2'
   elif rest == 1:
      return '1'
   elif rest == 0:
      return '0'
   elif rest == None:
      return '3+'
   else:
      return '3+'

# Player-based filtering
def get_data(
      player="Any Player", opponents=[], min_low=0, min_high=48, home_away='Both', win_loss='Both', mov_min=0, mov_max=100, game_split='Full Season',
      rest=[], playing=[], not_playing=[]
   ):
   """
   This function filters data, much similar to `get_team_data`
   """
   # Take care of log-based data
   df = pd.read_csv('./new-logs.csv').drop(columns=['Unnamed: 0']).drop_duplicates()
   df = add_combos(df)
   has = scores[['GameId', 'Team', 'TeamScore', 'OppScore', 'Home']].copy()
   has['Win'] = has['TeamScore'] > has['OppScore']
   has['MOV'] = np.abs(has['TeamScore'] - has['OppScore'])
   df = df.merge(has, on=['GameId', 'Team'])
   df = df.sort_values(by=['Date', 'Minutes'], ascending=[True, False])
   # Filter to include teammates
   if len(playing) > 0:
      game_counts = base[base['Name'].isin(playing)].groupby('GameId')['Name'].nunique()
      ids_to_include = game_counts[game_counts == len(playing)].index.tolist()
      df = df[df['GameId'].isin(ids_to_include)]
   # Filter to exclude teammates
   if len(not_playing) > 0:
      ids = base[base['Name'].isin(not_playing)].GameId
      df = df[~df['GameId'].isin(ids)]
   # Filter for specific player
   if player != "Any Player":
      df = df[df['Name'] == player]
   # Filter for rest
   df['Rest'] = df['Date'].diff().dt.days - 1
   if len(rest) > 0:
      df['Rest'] = df['Rest'].apply(lambda x: format_rest(x))
      df = df[df['Rest'].isin(rest)]
   # Filter for opponents
   if len(opponents) > 0:
      df = df[df['Opponent'].isin(opponents)]
   # Filter for home/away
   if home_away == 'Home':
      df = df[df['Home'] == True]
   elif home_away == 'Away':
      df = df[df['Home'] == False]
   # Filter for win/loss
   if win_loss == 'Win':
      df = df[df['Win'] == True]
   elif win_loss == 'Loss':
      df = df[df['Win'] == False]
   # Adjust for minutes played, margin of victory
   df = df[
      (df['Minutes'] >= min_low) & (df['Minutes'] <= min_high) & (df['MOV'] >= mov_min) & (df['MOV'] <= mov_max)
   ].drop(columns=['GameId', 'MOV']).sort_values(by='Date', ascending=False)
   # Filter for games split
   if game_split == 'Last 5':
      return df.head(5)
   elif game_split == 'Last 10':
      return df.head(10)
   elif game_split == 'Last 30':
      return df.head(30)
   else:
      return df
   
# Team-based filtering
def get_team_data(
   team='Any Team', players=[], min_low=0, min_high=48, home_away=[], win_loss=[], mov_min=0, mov_max=48, game_split=[], rest=[],
   positions=[], per_min=0, per_max=100, usg_min=0, usg_max=100, fg3r_min=0, fg3r_max=100, ftr_min=0, ftr_max=100, orb_min=0,
   orb_max=100, drb_min=0, drb_max=100, ast_min=0, ast_max=100, stl_min=0, stl_max=100, blk_min=0, blk_max=100, missing_players=[],
   mpg_min=0, mpg_max=48
):
   """
   This function is intended to filter the data based on how players are performing against a specific team. It's very similar to 
   `get_data`, except that focuses on how a specific player is performing with given criteria.
   """
   # Take care of log-based data
   df = pd.read_csv('./new-logs.csv').drop(columns=['Unnamed: 0']).drop_duplicates()
   df = add_combos(df)
   has = scores[['GameId', 'Team', 'TeamScore', 'OppScore', 'Home']].copy()
   has['Win'] = has['TeamScore'] > has['OppScore']
   has['MOV'] = np.abs(has['TeamScore'] - has['OppScore'])
   df = df.merge(has, on=['GameId', 'Team'])
   df = df.sort_values(by=['Date', 'Minutes'], ascending=[True, False])
   # Filter for missing players
   if len(missing_players) > 0:
      invalidids = []
      for player in missing_players:
         invalidids = invalidids + list(base[base['Name'] == player].GameId)
      df = df[~df['GameId'].isin(invalidids)].copy()
   # Filter given player stat criteria
   players_to_include = filter_players(
      positions, mpg_min, mpg_max, per_min, per_max, usg_min, usg_max, fg3r_min, fg3r_max, ftr_min, ftr_max, orb_min,
      orb_max, drb_min, drb_max, ast_min, ast_max, stl_min, stl_max, blk_min, blk_max
   )
   df = df[df['Name'].isin(players_to_include)]
   # Filter for a specific team
   if team != "Any Team":
      df = df[df['Opponent'] == team]
   # Filter for rest
   df['Rest'] = df['Date'].diff().dt.days - 1
   if len(rest) > 0:
      df['Rest'] = df['Rest'].apply(lambda x: format_rest(x))
      df = df[df['Rest'].isin(rest)]
   # Filter for home/away
   if home_away == 'Home':
      df = df[df['Home'] == False]
   elif home_away == 'Away':
      df = df[df['Home'] == True]
   # Filter for win/loss
   if win_loss == 'Win':
      df = df[df['Win'] == False]
   elif win_loss == 'Loss':
      df = df[df['Win'] == True]
   # Adjust for minutes played, margin of victory
   df = df[
      (df['Minutes'] >= min_low) & (df['Minutes'] <= min_high) & (df['MOV'] >= mov_min) & (df['MOV'] <= mov_max)
   ].drop(columns=['GameId', 'MOV'])
   # Filter for games split
   if game_split == 'Last 5':
      return df.head(5)
   elif game_split == 'Last 10':
      return df.head(10)
   elif game_split == 'Last 30':
      return df.head(30)
   else:
      return df

player_based, team_based = st.tabs(['Player-Based Research', 'Opponent-Based Research'])

with player_based:
   # PAGE HEADER
   st.header("Player-Based NBA Prop Research")
   st.markdown('''
               Below are all player counting statistics this season. Utilize the filters to parse down
               the data. For example, you can answer the question *how many points per game does Damian Lillard average
               when playing 25 minutes or less?*
               ''')

   # FILTERS
   with st.container(border=True):
      st.markdown('''
                  All player positions and advanced statistics come from [Cleaning the Glass](https://cleaningtheglass.com). Note that positions are estimated and may not reflect your best ideas of player positions. If you need help with getting started with research, you can see some examples [here](https://x.com).
                  ''')
      # Form Row 1
      row1 = st.columns([1, 1, 1, 1])
      players = row1[0].selectbox('Player', ALL_PLAYERS, placeholder='Choose player') # Filter the player(s)
      opponents = row1[1].multiselect('Opponent', ALL_TEAMS, placeholder='Choose opponents') # Filter the opponent(s)
      min_low = row1[2].number_input('Min. Minutes Played', value=0, step=1)
      min_high = row1[3].number_input('Max. Minutes Played', value=48, step=1)
      # Form Row 2
      row2 = st.columns([1, 1, 1, 1])
      mov_min = row2[0].number_input('Min. Margin of Victory', value=0, step=1)
      mov_max = row2[1].number_input('Max. Margin of Victory', value=100, step=1)
      rest = row2[2].multiselect('Days Rest', ["0", "1", "2", "3+"], placeholder='Days between Games')
      game_split = row2[3].selectbox('Games Split', ['Full Season', 'Last 5', 'Last 10', 'Last 30'], placeholder='Choose a games split')
      # Form Row 3 (Splits)
      row3 = st.columns([1, 1, 1, 1])
      hab = row3[0].radio('Home/Away', ['Both', 'Home', 'Away'])
      wls = row3[1].radio('Win/Loss', ['Both', 'Win', 'Loss'])
      if players is not None and players != 'Any Player':
         team = base[base['Name'] == players].Team.iloc[0]
         roster = get_players(team)
         in_game = row3[2].multiselect('Played In Game', roster, placeholder='Select teammates in game')
      else:
         in_game = []
      if players is not None and players != 'Any Player':
         team = base[base['Name'] == players].Team.iloc[0]
         roster = get_players(team)
         out_game = row3[3].multiselect('Did Not Play', roster, placeholder='Select teammates out of the game')
      else:
         out_game = []
      
   # DISPLAY DF
   st.dataframe(
      get_data(
         players, opponents, min_low, min_high, hab, wls, mov_min, mov_max,
         game_split, rest, in_game, out_game
      ),
      use_container_width=True
   )
   
   # Assemble prop research data
   prop_data = get_data(
      players, opponents, min_low, min_high, hab, wls, mov_min, mov_max, game_split, rest, in_game, out_game
   )
   base['Game'] = base['Name'] + ' ' + base['Opponent'] + ' ' + base['Date'].astype(str)
   prop_data['Game'] = prop_data['Name'] + ' ' + prop_data['Opponent'] + ' ' + prop_data['Date'].astype(str)
   
   # Table with splits
   splits_table = pd.DataFrame(columns=['Split', 'Name', 'Minutes', 'Points', 'Rebounds', 'Assists', 'FG3M', 'Steals', 'Blocks'])
   # Calculate averages from prop_data and create a DataFrame for the first row
   prop_averages = prop_data[['Minutes', 'Points', 'Rebounds', 'Assists', 'FG3M', 'Steals', 'Blocks']].mean()
   prop_averages['Name'] = prop_data['Name'].iloc[0]  # Using 'Name' column
   prop_averages['Split'] = 'Your Choosen Splits'
   prop_row = pd.DataFrame([prop_averages])
   # Calculate averages from the base dataset for the same player and create a DataFrame for the second row
   player_name = prop_data['Name'].iloc[0]
   base_player_data = base[base['Name'] == player_name].copy()
   base_player_data = base_player_data[~base_player_data['Game'].isin(prop_data['Game'])]
   base_averages = base_player_data[['Minutes', 'Points', 'Rebounds', 'Assists', 'FG3M', 'Steals', 'Blocks']].mean().to_frame().T
   base_averages['Name'] = player_name
   base_averages['Split'] = 'All Other Games'
   # Concatenate the two DataFrames to form the splits table
   splits_table = pd.concat([prop_row, base_averages], ignore_index=True)
   splits_table['Games'] = [len(prop_data), len(base_player_data)]
   split_cols = ['Games', 'Minutes', 'Points', 'Rebounds', 'Assists', 'FG3M', 'Steals', 'Blocks']
   splits_table = splits_table[['Split', 'Name'] + split_cols]
   for col in split_cols:
      splits_table[col] = splits_table[col].round(2)
   # Display the table with splits
   st.markdown('''
      Here are the player's averages with the given splits you've provided.
   ''')
   st.dataframe(splits_table, use_container_width=True)

   st.markdown('''
      ## Prop Report
      If you'd like to do research on particular prop with the given filters above, set the information here. It will provide hit rates, expected value, and more based off your selected splits
      from above.
   ''')
   
   # PROP INPUT
   with st.container(border=True):
      row = st.columns([2, 2, 1, 1])
      prop_type = row[0].selectbox(
         'Prop Type',
         ['Points', 'Rebounds', 'Assists', 'Steals', 'Blocks', 'FG3M', 'P+R', 'P+A', 'R+A', 'P+R+A', 'Stocks', 'Turnovers']
      )
      prop_line = row[1].number_input('Line', value=10.5, step=0.5)
      over_odds = row[2].number_input('Over Odds', value=-110, step=10)
      under_odds = row[3].number_input('Under Odds', value=-110, step=10)
   
   hit_rate = np.mean(prop_data[prop_type] > prop_line)
   wins = np.sum(prop_data[prop_type] > prop_line)
   losses = len(prop_data) - wins
   print('new iter')
   ev_over = round(pybet.expected_value(over_odds, hit_rate), 2)
   if ev_over < 0:
      ev_over = f'{ev_over}u'
   else:
      ev_over = f'+{ev_over}u'
   ev_under = round(pybet.expected_value(under_odds, 1 - hit_rate), 2)
   if ev_under < 0:
      ev_under = f'{ev_under}u'
   else:
      ev_under = f'+{ev_under}u'
   
   # Display prop research data
   st.markdown('### Prop Results')
   st.markdown('### ')
   prop_information = st.columns([2, 1])
   prop_information[0].bar_chart(prop_data, x='Game', y=prop_type)
   prop_information[1].markdown(
      f'''
      In the **{len(prop_data)} game sample size** with the given splits, this prop has an average of {round(np.mean(prop_data[prop_type]), 1)}.\n
      The over has a record of {wins}-{losses} and a hit rate of {round(hit_rate * 100, 1)}% and an implied probability of {round(pybet.implied_probability(over_odds) * 100, 1)}%. This gives an expected profit of {ev_over} on a 1u bet.\n
      The under has a hit rate of {round((1 - hit_rate) * 100, 1)}% and an implied probability of {round(pybet.implied_probability(under_odds) * 100, 1)}%. This gives an expected profit of {ev_under} on a 1u bet.
      ''')
   
with team_based:
   # PAGE HEADER
   st.header("Team-Based NBA Prop Research")
   st.markdown('''
               Below are all player counting statistics this season. Utilize the filters to parse down
               the data. For example, you can answer the question *how have point guards shooting at least 40% from three
               been averaging against the Milwaukee Bucks in the last 10 games?*
               ''')

   # FILTERS
   with st.container(border=True):
      st.markdown('''
                  All player positions and advanced statistics come from [Basketball Reference](https://www.basketball-reference.com/leagues/NBA_2024_advanced.html). If you need help with getting started with research, you can see some examples [here](https://x.com).
                  ''')
      # Form Row 1
      row1 = st.columns([1, 1, 1, 1, 1])
      team = row1[0].selectbox('Team', ALL_TEAMS, placeholder='Choose team', index=1)
      positions = row1[1].multiselect('Positions', ['PG', 'SG', 'SF', 'PF', 'C'], placeholder='Choose positions')
      minutes_min = row1[2].number_input('Min. Minutes Played', value=0)
      minutes_max = row1[3].number_input('Max. Minutes Played', value=48)
      if team not in ['Any Team', None]:
         missing_players = row1[4].multiselect('Missing Players', get_players(team))
      else:
         missing_players = []
      # Form Row 2
      row2 = st.columns([1, 1, 1, 1, 1])
      hab = row2[0].selectbox('Location', ['Both', 'Home', 'Road'])
      wls = row2[1].selectbox('Outcome', ['Both', 'Win', 'Loss'])
      mov_min = row2[2].number_input('Min. Margin of Victory', value=0)
      mov_max = row2[3].number_input('Max. Margin of Victory', value=100)
      game_split = row2[4].selectbox('Split', ['Last 5', 'Last 10', 'Full Season'], index=2)
      # First row of player filters
      rowone = st.columns([1, 1, 1, 1, 1])
      rowone_mpg = rowone[0].columns([2, 2]) # Minutes per game
      mpg_min = rowone_mpg[0].number_input('MPG Min.', value=0, step=1)
      mpg_max = rowone_mpg[1].number_input('MPG Max.', value=48, step=1)
      rowone_per = rowone[1].columns([2, 2]) # PER
      per_min = rowone_per[0].number_input('PER Min.', value=0, step=1)
      per_max = rowone_per[1].number_input('PER Max.', value=50, step=1)
      rowone_usg = rowone[2].columns([1, 1]) # Usage Rate
      usg_min = rowone_usg[0].number_input('USG% Min.', value=0, step=1)
      usg_max = rowone_usg[1].number_input('USG% Max.', value=100, step=1)
      rowone_fg3r = rowone[3].columns([1, 1]) # Three Point Rate
      fg3r_min = rowone_fg3r[0].number_input('3P Rate Min.', value=0, step=1)
      fg3r_max = rowone_fg3r[1].number_input('3P Rate Max.', value=100, step=1)
      rowone_ftr = rowone[4].columns([1, 1]) # Free Throw Rate
      ftr_min = rowone_ftr[0].number_input('FT Rate Min.', value=0, step=1)
      ftr_max = rowone_ftr[1].number_input('FT Rate Max.', value=100, step=1)
      # Second row of player filters
      rowtwo = st.columns([1, 1, 1, 1, 1])
      rowtwo_orb = rowtwo[0].columns([1, 1]) # OREB Rate
      orb_min = rowtwo_orb[0].number_input('OREB% Min.', value=0, step=1)
      orb_max = rowtwo_orb[1].number_input('OREB% Max.', value=100, step=1)
      rowtwo_drb = rowtwo[1].columns([1, 1]) # DREB Rate
      drb_min = rowtwo_drb[0].number_input('DREB% Min.', value=0, step=1)
      drb_max = rowtwo_drb[1].number_input('DREB% Max.', value=100, step=1)
      rowtwo_ast = rowtwo[2].columns([1, 1]) # AST Rate
      ast_min = rowtwo_ast[0].number_input('AST% Min.', value=0, step=1)
      ast_max = rowtwo_ast[1].number_input('AST% Max.', value=100, step=1)
      rowtwo_stl = rowtwo[3].columns([1, 1]) # STL Rate
      stl_min = rowtwo_stl[0].number_input('STL% Min.', value=0, step=1)
      stl_max = rowtwo_stl[1].number_input('STL% Max.', value=100, step=1)
      rowtwo_blk = rowtwo[4].columns([1, 1]) # BLK Rate
      blk_min = rowtwo_blk[0].number_input('BLK% Min.', value=0, step=1)
      blk_max = rowtwo_blk[1].number_input('BLK% Max.', value=100, step=1)
         
   rest = [] 
   # DISPLAY DF
   matchup_data = get_team_data(
      team, players, minutes_min, minutes_max, hab, wls, mov_min, mov_max, game_split, rest, positions, per_min, per_max,
      usg_min, usg_max, fg3r_min, fg3r_max, ftr_min, ftr_max, orb_min, orb_max, drb_min, drb_max, ast_min, ast_max,
      stl_min, stl_max, blk_min, blk_max, missing_players, mpg_min, mpg_max
   )
   st.dataframe(matchup_data, use_container_width=True)
   
   # Summarize the Data
   proj_mins = st.columns([3, 1])
   proj_mins[0].markdown('''
      The matchups you choose have the following rates per minute of play. You can set a projected number of minutes to
      get the corresponding projections for the player, based off of the opponent's allowed production.
   ''')
   proj_min = proj_mins[1].number_input('Projected Minutes', value=36)
   sum_df = pd.DataFrame()
   sum_df['Rate'] = ['Per Minute', f'Per {proj_min} Minutes']
   sum_df['Games'] = [len(matchup_data)] * 2
   sum_df['Points per Minute'] = [
      np.sum(matchup_data.Points) / np.sum(matchup_data.Minutes),
      round(np.sum(matchup_data.Points) / np.sum(matchup_data.Minutes) * proj_min, 2)
   ]
   sum_df['Rebounds per Minute'] = [
      np.sum(matchup_data.Rebounds) / np.sum(matchup_data.Minutes),
      round(np.sum(matchup_data.Rebounds) / np.sum(matchup_data.Minutes) * proj_min, 2)
   ]
   sum_df['Assists per Minute'] = [
      np.sum(matchup_data.Assists) / np.sum(matchup_data.Minutes),
      round(np.sum(matchup_data.Assists) / np.sum(matchup_data.Minutes) * proj_min, 2)
   ]
   sum_df['3PM per Minute'] = [
      np.sum(matchup_data.FG3M) / np.sum(matchup_data.Minutes),
      round(np.sum(matchup_data.FG3M) / np.sum(matchup_data.Minutes) * proj_min, 2)
   ]
   sum_df['Tov per Minute'] = [
      np.sum(matchup_data.Turnovers) / np.sum(matchup_data.Minutes),
      round(np.sum(matchup_data.Turnovers) / np.sum(matchup_data.Minutes) * proj_min, 2)
   ]
   sum_df['FTM per Minute'] = [
      np.sum(matchup_data.FTM) / np.sum(matchup_data.Minutes),
      round(np.sum(matchup_data.FTM) / np.sum(matchup_data.Minutes) * proj_min, 2)
   ]
   st.dataframe(sum_df, use_container_width=True)