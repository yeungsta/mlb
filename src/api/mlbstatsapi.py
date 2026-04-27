import statsapi

def next_game_id(team_name: str) -> str:
    """Tool to retrieve the next game's game ID for a given team."""
    lookup_team_id = statsapi.lookup_team(team_name)[0]['id']

    game_pack_id = statsapi.next_game(lookup_team_id)

    if game_pack_id is None:    
        return f"Couldn't find game ID for {team_name}."
    else:
        return str(game_pack_id)

def last_game_id(team_name: str) -> str:
    """Tool to retrieve the last game's game ID for a given team."""
    lookup_team_id = statsapi.lookup_team(team_name)[0]['id']

    game_pack_id = statsapi.last_game(lookup_team_id)

    if game_pack_id is None:    
        return f"Couldn't find game ID for {team_name}."
    else:
        return str(game_pack_id)
    
def get_starters(team_data):
    starters = []
    # Players are stored in a dictionary keyed by 'ID' (e.g., 'ID605141')
    for player_id in team_data['players']:
        player = team_data['players'][player_id]
        # Starters have a battingOrder value (substitutes often have it as None or different formats)
        if player.get('battingOrder') and int(player['battingOrder']) % 100 == 0:
            starters.append({
                'order': int(player['battingOrder']) // 100,
                'name': player['person']['fullName'],
                'position': player['position']['abbreviation']
            })
    return sorted(starters, key=lambda x: x['order'])

team_name = "Los Angeles Dodgers"
# team_name = "yankees"

lookup_team_id = statsapi.lookup_team(team_name)[0]['id']

# historical game: last game of 2025 season for the team
# game_schedule = statsapi.schedule(start_date="2025-11-01", end_date="2025-12-01", team=lookup_team_id)
game_schedule = statsapi.schedule(start_date="2026-03-26", end_date="2026-03-26", team=lookup_team_id)
game_pack_id = game_schedule[0]['game_id']
# game_date = game_schedule[0]['game_date']
# game_status = game_schedule[0]['status']
# home_probable_pitcher = game_schedule[0]['home_probable_pitcher']
# away_probable_pitcher = game_schedule[0]['away_probable_pitcher']
# print(game_pack_id, game_date, game_status, home_probable_pitcher, away_probable_pitcher)

# upcoming game
# game_pack_id = statsapi.next_game(lookup_team_id)
# game_pack_id = statsapi.last_game(lookup_team_id)

if game_pack_id is None:
    print(f"Couldn't find game ID for {team_name}.")
else:
    # get game info
    game_info = statsapi.get("game", {"gamePk": game_pack_id})

    #print the starting lineup for both teams and the scheduled start time of the game
    print(f"Next game for {team_name}:")
    print(f"Scheduled start time: {game_info['gameData']['datetime']['dateTime']}") # pyright: ignore[reportOptionalSubscript]
    print(f"Game status: {game_info['gameData']['status']['detailedState']}") # pyright: ignore[reportOptionalSubscript]
    
    # print("Scheduled Starting Lineup:")
    # for team in game_info['gameData']['teams'].values(): # pyright: ignore[reportOptionalSubscript]
    #     print(f"{team['name']}:")
    #     if 'players' in team:
    #         for player in team['players'].values():
    #             if player['position']['code'] == '1': #starting pitcher
    #                 print(f"  {player['fullName']} (SP)")
    #             else:
    #                 print(f"  {player['fullName']} ({player['position']['abbreviation']})")

    # Get the boxscore data
    box_data = statsapi.boxscore_data(game_pack_id)

    print("Away Starting Lineup:")
    for p in get_starters(box_data['away']):
        print(f"{p['order']}. {p['name']} ({p['position']})")

    print("\nHome Lineup:")
    for p in get_starters(box_data['home']):
        print(f"{p['order']}. {p['name']} ({p['position']})")



