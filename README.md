# San Francisco Giants Win Probability Predictor

This Python script calculates the win probability for a Major League Baseball game based on a statistical analysis of the starting lineups and pitchers. By pulling real-time data from the MLB Stats API and PyBaseball, it provides an estimated win percentage for a specified team. It's meant to be run when the starting lineups are announced for any given day's game. In this configuration it can also be run to back-test older games. To change seasons, just find and replace the season year. It's currently set to 2025.

# Features

  Real-Time Stats: Fetches up-to-date player and team statistics.
  
  Intelligent Lookups: Uses fuzzy matching to handle player name variations and ensure accurate data retrieval.
  
  Customizable: Easily update lineups, teams, and pitchers for any game.
  
  Home-Field Advantage: Adjusts the final probability to account for home-field advantage.

# How to Use

Make sure you have Python installed on your system. This script requires several libraries, which you can install using pip.
Bash

    pip install statsapi pybaseball fuzzywuzzy python-levenshtein

Note: python-levenshtein is a dependency of fuzzywuzzy that improves performance.



Open the main.py (or whatever you've named the file) in a code editor. Navigate to the Manual Input Section at the top of the file and edit the variables with the information for the game you want to analyze. This is a v1 where it's manual input and a basic win probability model. Additional versions with automation and more complex predicitions will be created.

# --- Manual Input Section ---
    giants_pitcher_name = 'Landen Roupp'
    opp_pitcher_name = 'Joe Boyle'
    giants_team_name = 'San Francisco Giants'
    opp_team_name = 'Tampa Bay Rays'
    is_home_game = True

    sf_line = [
    'Heliot Ramos', 
    'Rafael Devers', 
    'Willy Adames', 
    'Dominic Smith', 
    # ...and so on
    ]

    opp_line = [
    'Chandler Simpson', 
    'Brandon Lowe', 
    # ...and so on
    ]

   

The script will print the OPS+ for each player and the FIP for the starting pitchers, then display the final win probability calculation.

# How It Works

The script calculates win probability based on a statistical model that considers offensive and pitching performance.

OPS+ (On-base Plus Slugging Plus): For hitters, the script pulls OPS and converts it to OPS+. This is a normalized stat where 100 is league average. Values above 100 are better than average, and values below 100 are worse.

FIP (Fielding Independent Pitching): For pitchers, the script uses FIP, which measures a pitcher's effectiveness based on outcomes they can control (strikeouts, walks, hit-by-pitches, and home runs). A lower FIP is better.

The script then uses these stats to estimate the expected runs scored and allowed by each team, applying a formula similar to Pythagorean Expectation to arrive at the final win probability. A slight boost is also given to the home team.
