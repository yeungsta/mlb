# Find Clayton Kershaw's player id
from pybaseball import playerid_lookup, statcast_pitcher, statcast_batter

# data = playerid_lookup('kershaw', 'clayton')
# print(data)
# pitcher_stats = statcast_pitcher('2025-06-01', '2025-07-01', data.key_mlbam.values[0])
# pitch_type_stats = pitcher_stats.groupby("pitch_type").release_speed.agg("mean")
# print(pitch_type_stats)

# data = playerid_lookup('judge', 'aaron')
# print(data)
# batter_stats = statcast_batter('2025-06-01', '2025-07-01', data.key_mlbam.values[0])
# print(batter_stats)

#lookup player not found
# data = playerid_lookup('tatis', 'fernando', True)
# if data.empty:
#     print("Player not found in player lookup!")
# else:    
#     if data.key_mlbam.values.size == 1:
#         key_mlbam = data.key_mlbam.values[0]
#         print(f'Found MLBAM for Fernando Tatis: {key_mlbam}')
#     else:
#         #print all matches if there are multiple
#         print("Multiple players found. Possible matches:")
#         #cache the key_mlbam values in a set to avoid duplicates
#         mlbam_set = set()
#         for index, row in data.iterrows():
#             #print player's first name, last name, first year, last year, and mlbam id
#             if row['key_mlbam'] not in mlbam_set:
#                 print(f"{row['name_first']} {row['name_last']}, {row['mlb_played_first']}-{row['mlb_played_last']}, MLBAM ID: {row['key_mlbam']}")
#                 mlbam_set.add(row['key_mlbam'])

# lookup historical matchup between Garrett Crochet and Aaron Judge
pitcher = playerid_lookup('crochet', 'garrett')
crochet_id = pitcher.key_mlbam.values[0]
crochet_first_year = pitcher.mlb_played_first.values[0]

batter = playerid_lookup('judge', 'aaron')
judge_id = batter.key_mlbam.values[0]  # Aaron Judge's MLBAM ID
judge_first_year = batter.mlb_played_first.values[0]

starting_year = max(crochet_first_year, judge_first_year)

# Fetch all pitches thrown by the pitcher (e.g., since the start of Statcast in 2008)
# Note: Queries for long date ranges may take a moment to process.
#convert starting_year to YYYY-MM-DD format
start_date = f"{(str(starting_year)).split('.')[0]}-01-01"

pitcher_data = statcast_pitcher(start_date, '2026-03-20', player_id=crochet_id)

# Filter for the specific batter
matchup_data = pitcher_data[pitcher_data['batter'] == judge_id]

print(f"Total Pitches: {len(matchup_data)}\n")
print(f"Outcomes:\n{matchup_data['events'].value_counts()}\n")
print(f"Avg Exit Velo: {matchup_data['launch_speed'].mean()}\n")
print(f"Pitch Mix:\n{matchup_data['pitch_type'].value_counts(normalize=True)}\n")

# View the results of every completed plate appearance
outcomes = matchup_data.dropna(subset=['events'])
print(outcomes[['game_date', 'events', 'description', 'launch_speed']])