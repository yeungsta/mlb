from langchain.tools import tool
import statsapi

@tool
def retrieve_game_id(date: str, team_name: str) -> str:
    """Tool to retrieve the game ID for a specified date for a specified team. Date should be in format YYYY-MM-DD."""
    lookup_team_id = statsapi.lookup_team(team_name)[0]['id']

    game_schedule = statsapi.schedule(start_date=date, end_date=date, team=lookup_team_id)
    if game_schedule is None or len(game_schedule) == 0:
        return f"Couldn't find a game for {team_name} on {date}."
    else:
        game_pack_id = game_schedule[0]['game_id']
        
        if game_pack_id is None:    
            return f"Couldn't find game ID for {team_name} on {date}."
        else:
            return str(game_pack_id)
    
@tool
def game_info(game_pack_id: str) -> dict:
    """Tool to retrieve game info for a given game pack ID, including the scheduled start time of the game and the starting pitchers for both teams."""
    game_info = statsapi.get("game", {"gamePk": game_pack_id})

    start_date = game_info['gameData']['datetime']['officialDate'] # pyright: ignore[reportOptionalSubscript]
    start_time = game_info['gameData']['datetime']['time'] + game_info['gameData']['datetime']['ampm'] # pyright: ignore[reportOptionalSubscript]
    game_status = game_info['gameData']['status']['detailedState'] # pyright: ignore[reportOptionalSubscript]
    home_team = game_info['gameData']['teams']['home']['name'] # pyright: ignore[reportOptionalSubscript]
    away_team = game_info['gameData']['teams']['away']['name'] # pyright: ignore[reportOptionalSubscript]
    home_probable_pitcher = game_info['gameData']['probablePitchers']['home'] if 'probablePitchers' in game_info['gameData'] and 'home' in game_info['gameData']['probablePitchers'] else None # pyright: ignore[reportOptionalSubscript]
    away_probable_pitcher = game_info['gameData']['probablePitchers']['away'] if 'probablePitchers' in game_info['gameData'] and 'away' in game_info['gameData']['probablePitchers'] else None # pyright: ignore[reportOptionalSubscript]

    return {"game_pack_id": game_pack_id, "start_date": start_date, "start_time": start_time, "game_status": game_status, "home_team": home_team, "away_team": away_team, "home_probable_pitcher": home_probable_pitcher, "away_probable_pitcher": away_probable_pitcher}

@tool
def starting_lineups(game_pack_id: str) -> dict:
    """Tool to retrieve the starting lineups for a given game pack ID."""

    # Get the boxscore data
    box_data = statsapi.boxscore_data(game_pack_id)

    # print("Away Starting Lineup:")
    # for p in get_starters(box_data['away']):
    #     print(f"{p['order']}. {p['name']} ({p['position']})")

    # print("\nHome Lineup:")
    # for p in get_starters(box_data['home']):
    #     print(f"{p['order']}. {p['name']} ({p['position']})")

    #return the starting lineups in a structured format
    home_lineup = [{"order": p['order'], "name": p['name'], "position": p['position']} for p in get_starters(box_data['home'])]
    away_lineup = [{"order": p['order'], "name": p['name'], "position": p['position']} for p in get_starters(box_data['away'])]

    return {"home_lineup": home_lineup, "away_lineup": away_lineup}

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