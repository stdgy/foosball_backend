# JSON Foosball API

## Description
Attempting to adhere to the pseudo-spec at: http://jsonapi.org/

This project is meant to be a learning experience. Just an excuse to investigate
constructing a JSON API using Python and Flask. It's part of a larger exercise which
I guess I'll call *My 12 Months of Code*. This year's New Year's Resolution was to start
a new coding project at the begininng of each month, and complete it by
the end of the month. I thought I'd spend the first few months with projects oriented
around Foosball, since we tend to play a lot of Foosball at work... 

First month is the back-end. Next month is a JS Client. Next month after that will be
either a desktop or mobile client. And that's as far as I've planned so far!

## Resources

### User
- id
- name
- first_name
- last_name
- birthday
- email

### Game
- id
- start 
- end 

### Team
- id 
- game_id
- name 

### Player
- id
- user_id 
- game_id 
- team_id 
- position 

### Score
- id 
- user_id 
- game_id 
- team_id 
- player_id 
- time 
- own_goal