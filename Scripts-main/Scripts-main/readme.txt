- we need to scrape the data from sofascore tennis live matches, implement some filters to make sure we're getting the wanted data and dump it to the mongodb.
- sofascore live matches api: https://www.sofascore.com/tennis


- Filters:

Top aces: 

Filter 1- Highest to lowest entries
Filter 2- Only show values 4 and (higher) > than 4

Best first serve: 
Filter 1 - Highest to lowest order entries 
Filter 2- Only show values (higher) > than 60% 
Filter 3- Show only values (higher) > than 10 serves (highest number highlighted on sofascore pic below)

Best second serve: 

Filter 1 - Highest to lowest entries  
Filter 2- Only show values (higher) > then 60% 
Filter 3- Show only values (higher) > than 5 serves (highest number highlighted on sofascore pic below)

Best first serve points 

Filter 1- Highest to lowest entries 
Filter 2- Show only values > 60% 
Filter 3- Show only values (higher) > than 7 serves (highest number highlighted on sofascore pic below)

Best second serve points: 

Filter 1- Highest to lowest entries 
Filter 2- Show only values > 60%
Filter 3- Show only values (higher) > than 4 serves (highest number highlighted on sofascore pic below)
