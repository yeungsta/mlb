from datetime import datetime, timedelta

from langchain.tools import tool

from pybaseball import  playerid_lookup
from pybaseball import  statcast_pitcher
from pybaseball import  statcast_batter, statcast_batter_exitvelo_barrels
from pybaseball import cache

cache.enable()

@tool
def retrieve_historical_player_id(firstName: str, lastName: str) -> dict:
    """Tool to look up historical and retired player IDs from the Savant dataset given a player's first and last name"""
    # Find player id
    data = playerid_lookup(lastName, firstName, True)

    if data.empty:
        print(f"Player {firstName} {lastName} not found in historical player lookup!\n")
        return {}
    else:    
        if data.key_mlbam.values.size == 1: # pyright: ignore[reportAttributeAccessIssue]
            key_mlbam = data.key_mlbam.values[0]
            starting_year = f"{(str(data.mlb_played_first.values[0].item())).split('.')[0]}"
            ending_year = f"{(str(data.mlb_played_last.values[0].item())).split('.')[0]}"

            #print player's first name, last name, first year, last year, and mlbam id            
            print(f"Historical player found: {firstName} {lastName}, {starting_year} - {ending_year}, MLBAM ID: {key_mlbam}\n")
            return { "mlbam_id": key_mlbam.item(), "first_name": firstName, "last_name": lastName, "first_year": starting_year, "last_year": ending_year }  # Convert numpy int to native Python int for better compatibility with LLMs          
        else:
            #not found
            print(f"Player {firstName} {lastName} not found in historical player lookup!\n")
            return {}
        
            # #print all matches if there are multiple
            # print("Multiple players found. Possible matches:")
            # #cache the key_mlbam values in a set to avoid duplicates
            # mlbam_set = set()
            # for index, row in data.iterrows():
            #     #print player's first name, last name, first year, last year, and mlbam id
            #     if row['key_mlbam'] not in mlbam_set:
            #         print(f"{row['name_first']} {row['name_last']}, {row['mlb_played_first']}-{row['mlb_played_last']}, MLBAM ID: {row['key_mlbam']}")
            #         mlbam_set.add(row['key_mlbam'])
            
            # # just return the first mlbam id for now (could be improved by allowing the user to select which player they meant in the case of multiple matches)
            # key_mlbam = data.key_mlbam.values[0]
            # firstName = data.name_first.values[0]
            # lastName = data.name_last.values[0]
            # starting_year = f"{(str(data.mlb_played_first.values[0].item())).split('.')[0]}"
            # ending_year = f"{(str(data.mlb_played_last.values[0].item())).split('.')[0]}"
            # print(f'Auto-selecting first option: {firstName} {lastName}, MLBAM ID: {key_mlbam}')
            # return { "mlbam_id": key_mlbam.item(), "first_name": firstName, "last_name": lastName, "first_year": starting_year, "last_year": ending_year }  # Convert numpy int to native Python int for better compatibility with LLMs

@tool
def retrieve_pitcher_pitch_type_stats(start_dt: str, end_dt: str, mlbam_id: int) -> dict:
    """Tool to retrieve a pitcher's pitch-type stats given a player's MLBAM ID and a date range (start_dt and end_dt in format YYYY-MM-DD). Use the past year if no date range is provided."""
    print(f"Retrieving pitcher stats for pitcher id {mlbam_id} for range {start_dt} to {end_dt}:\n")

    pitcher_stats = statcast_pitcher(start_dt, end_dt, mlbam_id)
    pitch_type_stats = pitcher_stats.groupby("pitch_type").release_speed.agg("mean")

    # print(pitch_type_stats.to_dict())
    return pitch_type_stats.to_dict()

@tool
def retrieve_pitcher_pitch_type_stats_past_year(todays_dt: str, mlbam_id: int) -> dict:
    """Tool to retrieve a pitcher's pitch-type stats given a player's MLBAM ID for the past year given today's date."""

    #calculate date one year ago from today's date
    start_dt, end_dt = calculate_date_one_year_ago(todays_dt)

    print(f"Retrieving pitcher stats for pitcher id {mlbam_id} for range {start_dt} to {end_dt}:\n")

    pitcher_stats = statcast_pitcher(start_dt, end_dt, mlbam_id)
    pitch_type_stats = pitcher_stats.groupby("pitch_type").release_speed.agg("mean")

    # print(pitch_type_stats.to_dict())
    return pitch_type_stats.to_dict()

@tool
def retrieve_batter_exit_velo_stats(start_dt: str, end_dt: str, mlbam_id: int) -> dict:
    """Tool to retrieve a batter's exit velocity by pitch-type stats given a player's MLBAM ID and a date range (start_dt and end_dt in format YYYY-MM-DD). Use the past year if no date range is provided."""
    print(f"Retrieving batter stats for batter id {mlbam_id} for range {start_dt} to {end_dt}:\n")

    batter_stats = statcast_batter(start_dt, end_dt, mlbam_id)
    exit_velo_by_pitch_type_stats = batter_stats.groupby("pitch_type").release_speed.agg("mean")

    # get data for batters with a minimum of 100 batted ball events in 2019
    # exit_velo_stats = statcast_batter_exitvelo_barrels(2025, 100)

    # print(exit_velo_by_pitch_type_stats.to_dict())
    return exit_velo_by_pitch_type_stats.to_dict()

@tool
def retrieve_batter_exit_velo_stats_past_year(todays_dt: str, mlbam_id: int) -> dict:
    """Tool to retrieve a batter's exit velocity by pitch-type stats given a player's MLBAM ID for the past year given today's date."""

    #calculate date one year ago from today's date
    start_dt, end_dt = calculate_date_one_year_ago(todays_dt)

    print(f"Retrieving batter stats for batter id {mlbam_id} for range {start_dt} to {end_dt}:\n")

    batter_stats = statcast_batter(start_dt, end_dt, mlbam_id)
    exit_velo_by_pitch_type_stats = batter_stats.groupby("pitch_type").release_speed.agg("mean")

    # get data for batters with a minimum of 100 batted ball events in 2019
    # exit_velo_stats = statcast_batter_exitvelo_barrels(2025, 100)

    # print(exit_velo_by_pitch_type_stats.to_dict())
    return exit_velo_by_pitch_type_stats.to_dict()

@tool
def head_to_head_stats(pitcher_mlbam_id: int, batter_mlbam_id: int, start_year: str, end_year: str) -> dict:
    """Tool to retrieve complete, historical head-to-head stats for a pitcher vs. batter matchup, starting with the earliest possible date of their matchup history."""
    print(f"Retrieving historical head-to-head stats for pitcher id {pitcher_mlbam_id} and batter id {batter_mlbam_id} from {start_year} to {end_year}:\n")

    # Fetch all pitches thrown by the pitcher (e.g., since the start of Statcast in 2008)
    # Note: Queries for long date ranges may take a moment to process.

    pitcher_data = statcast_pitcher(start_year + "-01-01", end_year + "-01-01", player_id=pitcher_mlbam_id)

    # Filter for the specific batter
    matchup_data = pitcher_data[pitcher_data['batter'] == batter_mlbam_id]

    # View the results of every completed plate appearance
    outcomes = matchup_data.dropna(subset=['events'])
    # print(outcomes[['game_date', 'events', 'description', 'launch_speed']])

    return {"total_pitches": len(matchup_data), "outcomes": matchup_data['events'].value_counts().to_dict(), 
            "avg_exit_velo": matchup_data['launch_speed'].mean(), "pitch_mix": matchup_data['pitch_type'].value_counts(normalize=True).to_dict(),
            "detailed_outcomes": outcomes[['game_date', 'events', 'description', 'launch_speed']].to_dict(orient='records')}

def calculate_date_one_year_ago(todays_dt: str) -> tuple[str, str]:
    """Helper function to calculate the date one year ago from today's date."""
    end_dt = datetime.strptime(todays_dt, "%Y-%m-%d")
    start_dt = end_dt - timedelta(days=365)
    return start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d")