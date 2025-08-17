import statsapi
import datetime
from pybaseball import playerid_lookup, batting_stats, pitching_stats
from fuzzywuzzy import process

# --- Manual Input Section ---
giants_pitcher_name = 'Justin Verlander'
opp_pitcher_name = 'Adrian Houser'
giants_team_name = 'San Francisco Giants'
opp_team_name = 'Tampa Bay Rays'
is_home_game = True
sf_line = [
    'Heliot Ramos', 
    'Rafael Devers', 
    'Willy Adames', 
    'Dominic Smith', 
    'Jung Hoo Lee', 
    'Christian Koss',
    'Tyler Fitzgerald', 
    'Grant McCray',
    'Andrew Knizner'
    ]

opp_line = [
    'Chandler Simpson', 
    'Yandy Diaz',
    'Brandon Lowe', 
    'Junior Caminero',
    'Jake Mangum',
    'Josh Lowe', 
    'Ha-Seong Kim',     
    'Bob Seymour', 
    'Nick Fortes'
    ]

# --- Functions ---
def validate_roster(lineup, team_name):
    try:
        team_lookup = statsapi.lookup_team(team_name)
        if not team_lookup:
            print(f"No team found for {team_name}. Skipping roster validation.")
            return lineup
        team_id = team_lookup[0]['id']
        roster = statsapi.roster(team_id, season=2025)
        roster_names = [line.split()[-1] for line in roster.split('\n') if line.strip()]
        valid_lineup = []
        for player in lineup:
            last_name = player.split()[-1]
            match = process.extractOne(last_name, roster_names)
            if match and match[1] > 80:
                valid_lineup.append(player)
            else:
                print(f"Warning: {player} may not be on {team_name} roster")
        return valid_lineup if valid_lineup else lineup
    except Exception as e:
        print(f"Error validating roster for {team_name}: {e}")
        return lineup

def get_player_ids(lineups):
    player_ids = []
    for name in lineups:
        try:
            player = statsapi.lookup_player(name)
            if player:
                player_ids.append({'name': name, 'id': player[0]['id']})
            else:
                print(f"Could not find ID for {name}. Attempting fuzzy match...")
                name_parts = name.split()
                if len(name_parts) >= 2:
                    last_name, first_name = name_parts[-1], name_parts[0]
                    player_data = playerid_lookup(last_name, first_name, fuzzy=True)
                    if not player_data.empty:
                        player_ids.append({'name': name, 'id': player_data['key_mlbam'].iloc[0]})
                    else:
                        print(f"No match found for {name}")
                else:
                    print(f"Invalid name format for {name}")
        except Exception as e:
            print(f"Error looking up {name}: {e}")
    return player_ids

def get_player_stats(player_ids, stats_type='hitting'):
    league_avg_ops = 0.700
    park_factors = {'San Francisco Giants': 0.95, 'Tampa Bay Rays': 1.00}
    player_stats = {}
    
    for player in player_ids:
        player_name = player['name']
        player_id = player['id']
        try:
            # Try statsapi without season parameter
            stats_data = statsapi.player_stat_data(player_id, group=stats_type, type="season")
            print(f"API response for {player_name} ({stats_type}): {stats_data}")  # Debug
            if stats_data.get('stats') and stats_data['stats'][0].get('stats'):
                stats = stats_data['stats'][0]['stats']
                if stats_type == 'hitting':
                    ops = float(stats.get('ops', 0.0))
                    team = giants_team_name if player_name in sf_line else opp_team_name
                    park_factor = park_factors.get(team, 1.0)
                    ops_plus = (ops / league_avg_ops) * 100 * park_factor
                    player_stats[player_name] = ops_plus
                else:
                    stat_value = float(stats.get('fip', stats.get('era', 4.00)))
                    player_stats[player_name] = stat_value
            else:
                print(f"No {stats_type} stats for {player_name}. Using pybaseball fallback...")
                name_parts = player_name.split()
                if len(name_parts) >= 2:
                    last_name, first_name = name_parts[-1], name_parts[0]
                    player_data = playerid_lookup(last_name, first_name, fuzzy=True)
                    if not player_data.empty:
                        fg_id = player_data['key_fangraphs'].iloc[0]
                        if stats_type == 'hitting':
                            stats = batting_stats(2025, qual=0)
                            player_stats_row = stats[stats['IDfg'] == fg_id]
                            if not player_stats_row.empty:
                                ops = player_stats_row['OPS'].iloc[0]
                                team = giants_team_name if player_name in sf_line else opp_team_name
                                park_factor = park_factors.get(team, 1.0)
                                ops_plus = (ops / league_avg_ops) * 100 * park_factor
                                player_stats[player_name] = ops_plus
                            else:
                                player_stats[player_name] = 100.0
                        else:
                            stats = pitching_stats(2025, qual=0)
                            player_stats_row = stats[stats['IDfg'] == fg_id]
                            if not player_stats_row.empty:
                                player_stats[player_name] = player_stats_row['era'].iloc[0]
                            else:
                                player_stats[player_name] = 4.00
                    else:
                        player_stats[player_name] = 100.0 if stats_type == 'hitting' else 4.00
                else:
                    player_stats[player_name] = 100.0 if stats_type == 'hitting' else 4.00
        except Exception as e:
            print(f"Error retrieving {stats_type} stats for {player_name}: {e}")
            player_stats[player_name] = 100.0 if stats_type == 'hitting' else 4.00
    return player_stats

def get_team_bullpen_stats(team_name):
    try:
        team_lookup = statsapi.lookup_team(team_name)
        if not team_lookup:
            print(f"No team found for {team_name}. Using default bullpen ERA.")
            return 4.00
        team_id = team_lookup[0]['id']
        stats = statsapi.team_stats(team_id, 'pitching', 'season')['stats'][0]['stats']
        return float(stats.get('era', 4.00))
    except Exception as e:
        print(f"Error retrieving bullpen stats for {team_name}: {e}")
        return 4.00

def calculate_win_probability(giants_stats, opp_stats, giants_pitcher_fip, opp_pitcher_fip, is_home):
    
    # Calculate Team Offensive Score (based on OPS+)
    giants_off_score = sum(ops / 100 for ops in giants_stats.values()) / len(giants_stats)
    opp_off_score = sum(ops / 100 for ops in opp_stats.values()) / len(opp_stats)
    
    # A simplified model for runs scored based on offense vs. opposing pitcher
    # A team with an OPS+ of 100 (league average) will score about 4.5 runs per game against a 4.00 ERA pitcher.
    
    giants_runs = (giants_off_score * 4.5) * (4.00 / opp_pitcher_fip)
    opp_runs = (opp_off_score * 4.5) * (4.00 / giants_pitcher_fip)
    
    # Adjust for home field advantage
    if is_home:
        giants_runs *= 1.05
        
    print(f"\nEstimated Runs: Giants {giants_runs:.2f}, Opponent {opp_runs:.2f}")
    print(f"Giants Pitcher ERA: {giants_pitcher_fip:.2f}, Opponent Pitcher ERA: {opp_pitcher_fip:.2f}")
    
    exponent = 1.83
    
    # Use Pythagorean Expectation formula to calculate win probability
    win_prob = (giants_runs**exponent) / (giants_runs**exponent + opp_runs**exponent)
    
    return win_prob * 100

# --- Main Execution ---
if __name__ == "__main__":
    sf_line = validate_roster(sf_line, giants_team_name)
    opp_line = validate_roster(opp_line, opp_team_name)
    
    giants_players_ids = get_player_ids(sf_line)
    opp_players_ids = get_player_ids(opp_line)
    
    giants_hitting_stats = get_player_stats(giants_players_ids, 'hitting')
    opp_hitting_stats = get_player_stats(opp_players_ids, 'hitting')
    
    print(f"\n--- {giants_team_name} OPS+ ---")
    for name, ops in giants_hitting_stats.items():
        print(f"{name}: {ops:.1f}")
    
    print(f"\n--- {opp_team_name} OPS+ ---")
    for name, ops in opp_hitting_stats.items():
        print(f"{name}: {ops:.1f}")
    
    giants_pitcher_ids = get_player_ids([giants_pitcher_name])
    opp_pitcher_ids = get_player_ids([opp_pitcher_name])
    
    giants_pitcher_stats = get_player_stats(giants_pitcher_ids, 'pitching')
    opp_pitcher_stats = get_player_stats(opp_pitcher_ids, 'pitching')
    
    giants_pitcher_fip = giants_pitcher_stats.get(giants_pitcher_name, 4.00)
    opp_pitcher_fip = opp_pitcher_stats.get(opp_pitcher_name, 4.00)
    
    win_prob = calculate_win_probability(giants_hitting_stats, opp_hitting_stats, giants_pitcher_fip, opp_pitcher_fip, is_home_game)
    
    print("\n" + "="*50)
    print(f" The Giants have a {win_prob:.2f}% chance to win today.")
    print("="*50)
