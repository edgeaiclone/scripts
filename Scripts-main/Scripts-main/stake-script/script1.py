import requests
import json
import logging
import pymongo
from pymongo import MongoClient
import schedule
import time
from datetime import datetime, timedelta, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MONGO_URI = "mongodb+srv://bilal:pLnClBIMtgJrn2jv@cluster0.gi3fv.mongodb.net"
DATABASE_NAME = "edgeAI"
COLLECTION_NAME = "bets"

# Connect to MongoDBpay
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

initial_url = "https://stake.com/_api/graphql"
initial_payload = {
    "query": """
    query BetsBoard_HighrollerSportBets($limit: Int!) {
      highrollerSportBets(limit: $limit) {
        id
        iid
        bet {
          ...BetsBoardSport_BetBet
        }
      }
    }
    fragment BetsBoardSport_BetBet on BetBet {
      __typename
      ... on SwishBet {
        __typename
        id
        updatedAt
        createdAt
        potentialMultiplier
        amount
        currency
        user {
          id
          name
          preferenceHideBets
        }
        outcomes {
          __typename
          id
          odds
          outcome {
            __typename
            id
            market {
              id
              competitor {
                name
              }
              game {
                id
                fixture {
                  id
                  tournament {
                    id
                    category {
                      id
                      sport {
                        id
                        slug
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
      ... on SportBet {
        __typename
        id
        updatedAt
        createdAt
        potentialMultiplier
        amount
        currency
        user {
          name
          preferenceHideBets
        }
        outcomes {
          id
          odds
          fixtureAbreviation
          fixtureName
          fixture {
            id
            tournament {
              id
              category {
                id
                sport {
                  id
                  slug
                }
              }
            }
          }
        }
      }
      ... on RacingBet {
        __typename
        id
        active
        payout
        updatedAt
        createdAt
        betPotentialMultiplier: potentialMultiplier
        amount
        currency
        betStatus: status
        payoutMultiplier
        adjustments {
          payoutMultiplier
        }
        user {
          id
          name
          preferenceHideBets
        }
        outcomes {
          id
          type
          derivativeType
          prices {
            marketName
            odds
          }
          event {
            meeting {
              racing {
                slug
              }
            }
          }
          selectionSlots {
            runners {
              name
            }
          }
          result {
            resultedPrices
          }
        }
      }
    }
    """,
    "variables": {"limit": 10}
}

initial_headers = {
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0',
  'Accept': '*/*',
  'Accept-Language': 'en-US,en;q=0.5',
  'Accept-Encoding': 'gzip, deflate, br, zstd',
  'Referer': 'https://stake.com/sports/home',
  'access-control-allow-origin': '*',
  'content-type': 'application/json',
  'x-language': 'en',
  'x-operation-name': 'BetsBoard_HighrollerSportBets',
  'x-operation-type': 'query',
  'Origin': 'https://stake.com',
  'DNT': '1',
  'Connection': 'keep-alive',
  'Cookie': 'currency_currency=btc; currency_hideZeroBalances=false; currency_currencyView=crypto; session_info=undefined; fiat_number_format=en; cookie_consent=false; leftSidebarView_v2=expanded; sidebarView=hidden; casinoSearch=["Monopoly","Crazy Time","Sweet Bonanza","Money Train","Reactoonz"]; sportsSearch=["Liverpool FC","Kansas City Chiefs","Los Angeles Lakers","FC Barcelona","FC Bayern Munich"]; sportMarketGroupMap={}; oddsFormat=decimal; cookie_last_vip_tab=progress; quick_bet_popup=false; locale=en; intercom-id-cx1ywgf2=41356840-ce7f-4d80-9107-8843eaf057f0; intercom-device-id-cx1ywgf2=ecf41563-11f5-40ba-b5ed-18f5f3f8d002; g_state={"i_p":1745681141005,"i_l":4}; fullscreen_preference=false; _cfuvid=OvFM_AUkQ5tOSLlF0nJQgNXhw6726t9FZdxpJDqTGAs-1743438855035-0.0.1.1-604800000; intercom-session-cx1ywgf2=; __cf_bm=3b.yYP8QZ8CnlX8R1eHin19SrdtcdkoNctb88PSY7pE-1743438855-1.0.1.1-UuJTS03IUmBneFZTUze.K6y3cMofSxxR11gdNU5.1MjKZ9Dn4WYJuFIKjzqpDnjmFxiswqpirlAi9_5vpugzH_kvZqiK0RS9WduwVZMP8MI; cf_clearance=ttwScvU49XKNEzRRN3VqZXm0CmODzcluQVFTIPNzsjY-1743438856-1.2.1.1-19VINKc7_hhQObvA0GGga30ynmf8RyrIsPalxSoAMHlhxKSuthPUyCZdlAU.ijYK0.kNpCPR7xRltIwFg02Jt9mWqXMrWyfNELxaKWweNqhxd5.00RTFuMHKlKrXIRWfMRUTeHbQfuMn_ImvfqjpqfO9mrwvtEiskdPf.8MrvlCej8VH3gpjVQk_c70vE0yoHq96v0Oa3t.Abu5ypdXdjqcOLCoTIdaKVzWRjxA8lEW_h.Pmokv0aeEmHFKT6mJuNj7BRgcLU3rTV4_vE0mQNFZ71n4qeoqddgqICYqo97Yu5sngLUWF10NUtbfOb51r6rEvZXttgM9XLZQa3oACbu65YFHFYRBw0Xz0TnA0YVJadcLioPk3NXz8wgmuJqXJjELwUmfG02TrG1TUg9K_yIS802fe0Wqu06.fssinG3w; __cf_bm=8CXU5KCRMuxXIKRxjmLQMWKzByT9jzBJfZ8IR.TCWjA-1743438806-1.0.1.1-5WTQjh6n_4DNgDmTtcP.h3RipyyC5vFJYnsKRGq2jieZSBpiIhIyFf1NSHNgPEf8nm9v3rtlXYQzDhaVpOygtiU1ssgzMPh2Kn7MqKRQLBg',
  'Sec-Fetch-Dest': 'empty',
  'Sec-Fetch-Mode': 'cors',
  'Sec-Fetch-Site': 'same-origin',
  'Sec-GPC': '1',
  'Priority': 'u=0',
  'TE': 'trailers'
}

detail_headers = {
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0',
  'Accept': 'application/graphql+json, application/json',
  'Accept-Language': 'en-US,en;q=0.5',
  'Accept-Encoding': 'gzip, deflate, br, zstd',
  'Referer': 'https://stake.com/sports/home?iid=sport%3A319918809&modal=bet',
  'content-type': 'application/json',
  'x-language': 'en',
  'Origin': 'https://stake.com',
  'DNT': '1',
  'Connection': 'keep-alive',
  'Cookie': 'currency_currency=btc; currency_hideZeroBalances=false; currency_currencyView=crypto; session_info=undefined; fiat_number_format=en; cookie_consent=false; leftSidebarView_v2=expanded; sidebarView=hidden; casinoSearch=["Monopoly","Crazy Time","Sweet Bonanza","Money Train","Reactoonz"]; sportsSearch=["Liverpool FC","Kansas City Chiefs","Los Angeles Lakers","FC Barcelona","FC Bayern Munich"]; sportMarketGroupMap={}; oddsFormat=decimal; cookie_last_vip_tab=progress; quick_bet_popup=false; locale=en; intercom-id-cx1ywgf2=41356840-ce7f-4d80-9107-8843eaf057f0; intercom-device-id-cx1ywgf2=ecf41563-11f5-40ba-b5ed-18f5f3f8d002; g_state={"i_p":1745681141005,"i_l":4}; fullscreen_preference=false; _cfuvid=OvFM_AUkQ5tOSLlF0nJQgNXhw6726t9FZdxpJDqTGAs-1743438855035-0.0.1.1-604800000; intercom-session-cx1ywgf2=; __cf_bm=3b.yYP8QZ8CnlX8R1eHin19SrdtcdkoNctb88PSY7pE-1743438855-1.0.1.1-UuJTS03IUmBneFZTUze.K6y3cMofSxxR11gdNU5.1MjKZ9Dn4WYJuFIKjzqpDnjmFxiswqpirlAi9_5vpugzH_kvZqiK0RS9WduwVZMP8MI; cf_clearance=ttwScvU49XKNEzRRN3VqZXm0CmODzcluQVFTIPNzsjY-1743438856-1.2.1.1-19VINKc7_hhQObvA0GGga30ynmf8RyrIsPalxSoAMHlhxKSuthPUyCZdlAU.ijYK0.kNpCPR7xRltIwFg02Jt9mWqXMrWyfNELxaKWweNqhxd5.00RTFuMHKlKrXIRWfMRUTeHbQfuMn_ImvfqjpqfO9mrwvtEiskdPf.8MrvlCej8VH3gpjVQk_c70vE0yoHq96v0Oa3t.Abu5ypdXdjqcOLCoTIdaKVzWRjxA8lEW_h.Pmokv0aeEmHFKT6mJuNj7BRgcLU3rTV4_vE0mQNFZ71n4qeoqddgqICYqo97Yu5sngLUWF10NUtbfOb51r6rEvZXttgM9XLZQa3oACbu65YFHFYRBw0Xz0TnA0YVJadcLioPk3NXz8wgmuJqXJjELwUmfG02TrG1TUg9K_yIS802fe0Wqu06.fssinG3w; __cf_bm=8CXU5KCRMuxXIKRxjmLQMWKzByT9jzBJfZ8IR.TCWjA-1743438806-1.0.1.1-5WTQjh6n_4DNgDmTtcP.h3RipyyC5vFJYnsKRGq2jieZSBpiIhIyFf1NSHNgPEf8nm9v3rtlXYQzDhaVpOygtiU1ssgzMPh2Kn7MqKRQLBg',
  'Sec-Fetch-Dest': 'empty',
  'Sec-Fetch-Mode': 'cors',
  'Sec-Fetch-Site': 'same-origin',
  'Sec-GPC': '1',
  'Priority': 'u=4',
  'TE': 'trailers'
}

def insert_to_mongodb(data):
    try:
        # Insert data into MongoDB collection
        if data:
            existing_doc = collection.find_one({"iid": data["iid"]})

        if not existing_doc:
                print ('data', data)
                # Insert data into MongoDB collection if it doesn't exist
                collection.insert_one(data)
                logging.info(f"Data inserted into MongoDB")
        else:
            logging.warning("No data to insert into MongoDB.")
    except Exception as e:
        logging.error(f"Error inserting data into MongoDB: {e}")

def get_exchange_rate(currency):
    try:
        if currency.upper() == "USDT":
            return 1  # No conversion needed

        url = f"https://api.coingate.com/v2/rates/merchant/{currency.upper()}/USDT"
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse the response, which is just a number as a string
        exchange_rate = float(response.text)
        
        # logging.info(f"Exchange rate for {currency.upper()} to USDT: {exchange_rate}")
        return exchange_rate  # Return exchange rate as float
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed for {currency.upper()}: {e}")
        return None
    except ValueError as e:
        logging.error(f"Failed to decode JSON for {currency.upper()}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error in get_exchange_rate for {currency.upper()}: {e}")
        return None

def fetch_initial_bets():
    try:
        # logging.info(f"Fetching initial bets from {initial_url}")
        response = requests.post(initial_url, headers=initial_headers, json=initial_payload)
        response.raise_for_status()  # Raise an exception for HTTP errors

        data = response.json()
        tennis_iids = []  # Initialize list to store tennis iids
       
        if "data" in data and "highrollerSportBets" in data["data"]:
            # Iterate over the bets and find the slug
            for bet in data["data"]["highrollerSportBets"]:

                #remove duplicates
                if (len(bet['bet']['outcomes']) >= 2):
                    # print (len(bet['bet']['outcomes']))
                    # print ('found multi, continue', bet)
                    continue

                # Ensure bet['bet']['outcomes'] exists and is not empty
                if 'outcomes' in bet.get('bet', {}):
                    for outcome in bet['bet']['outcomes']:
                        if 'fixture' in outcome and 'tournament' in outcome['fixture']:
                            if 'category' in outcome['fixture']['tournament'] and 'sport' in outcome['fixture']['tournament']['category']:
                                sport_slug = outcome['fixture']['tournament']['category']['sport'].get('slug', '')
                                if sport_slug == "tennis":
                                    tennis_iids.append(bet["iid"])

            if tennis_iids:
                # logging.info(f"Found {len(tennis_iids)} tennis bets.")
                return tennis_iids  # Return list of iids if matches are found
            else:
                logging.info("No tennis bets found.")
                return None
        else:
            logging.warning("Response structure is missing required keys.")
            return None
    except requests.exceptions.RequestException as e:
        # Handle request exceptions
        logging.error(f"Request failed: {e}")
        return None
    except ValueError as e:
        # Handle JSON decoding errors
        logging.error(f"Failed to decode JSON: {e}")
        return None
    except KeyError as e:
        # Handle missing keys in the response
        logging.error(f"KeyError: Missing key {e} in response data.")
        return None
    except Exception as e:
        # General error handling
        logging.error(f"An error occurred: {e}")
        return None

# Function to fetch detailed data for each iid
def fetch_bet_details(iid):
    url = "https://stake.com/_api/graphql"

    payload = "{\"query\":\"query BetLookup($iid: String, $betId: String) {\\n  bet(iid: $iid, betId: $betId) {\\n    ...BetFragment\\n    __typename\\n  }\\n}\\n\\nfragment CasinoBet on CasinoBet {\\n  id\\n  active\\n  payoutMultiplier\\n  amountMultiplier\\n  amount\\n  payout\\n  updatedAt\\n  currency\\n  game\\n  user {\\n    id\\n    name\\n    __typename\\n  }\\n}\\n\\nfragment EvolutionBet on EvolutionBet {\\n  id\\n  amount\\n  currency\\n  createdAt\\n  payout\\n  payoutMultiplier\\n  user {\\n    id\\n    name\\n    __typename\\n  }\\n  softswissGame: game {\\n    id\\n    name\\n    edge\\n    __typename\\n  }\\n}\\n\\nfragment MultiplayerCrashBet on MultiplayerCrashBet {\\n  id\\n  user {\\n    id\\n    name\\n    preferenceHideBets\\n    __typename\\n  }\\n  payoutMultiplier\\n  gameId\\n  amount\\n  payout\\n  currency\\n  result\\n  updatedAt\\n  cashoutAt\\n  btcAmount: amount(currency: btc)\\n}\\n\\nfragment MultiplayerSlideBet on MultiplayerSlideBet {\\n  id\\n  user {\\n    id\\n    name\\n    preferenceHideBets\\n    __typename\\n  }\\n  payoutMultiplier\\n  gameId\\n  amount\\n  payout\\n  currency\\n  slideResult: result\\n  updatedAt\\n  cashoutAt\\n  btcAmount: amount(currency: btc)\\n  active\\n  createdAt\\n}\\n\\nfragment SoftswissBet on SoftswissBet {\\n  id\\n  amount\\n  currency\\n  updatedAt\\n  payout\\n  payoutMultiplier\\n  user {\\n    id\\n    name\\n    __typename\\n  }\\n  softswissGame: game {\\n    id\\n    name\\n    edge\\n    extId\\n    provider {\\n      id\\n      name\\n      __typename\\n    }\\n    __typename\\n  }\\n}\\n\\nfragment ThirdPartyBet on ThirdPartyBet {\\n  id\\n  amount\\n  currency\\n  updatedAt\\n  payout\\n  payoutMultiplier\\n  betReplay\\n  user {\\n    id\\n    name\\n    __typename\\n  }\\n  thirdPartyGame: game {\\n    id\\n    name\\n    edge\\n    extId\\n    provider {\\n      id\\n      name\\n      __typename\\n    }\\n    __typename\\n  }\\n}\\n\\nfragment SportMarketOutcome on SportMarketOutcome {\\n  __typename\\n  id\\n  active\\n  odds\\n  name\\n  customBetAvailable\\n}\\n\\nfragment SportMarket on SportMarket {\\n  id\\n  name\\n  status\\n  extId\\n  specifiers\\n  customBetAvailable\\n  provider\\n}\\n\\nfragment SportFixtureCompetitor on SportFixtureCompetitor {\\n  name\\n  extId\\n  countryCode\\n  abbreviation\\n  iconPath\\n}\\n\\nfragment SportFixtureDataMatch on SportFixtureDataMatch {\\n  startTime\\n  competitors {\\n    ...SportFixtureCompetitor\\n    __typename\\n  }\\n  teams {\\n    name\\n    qualifier\\n    __typename\\n  }\\n  tvChannels {\\n    language\\n    name\\n    streamUrl\\n    __typename\\n  }\\n  __typename\\n}\\n\\nfragment SportFixtureDataOutright on SportFixtureDataOutright {\\n  name\\n  startTime\\n  endTime\\n  __typename\\n}\\n\\nfragment CategoryTreeNested on SportCategory {\\n  id\\n  name\\n  slug\\n  sport {\\n    id\\n    name\\n    slug\\n    __typename\\n  }\\n}\\n\\nfragment TournamentTreeNested on SportTournament {\\n  id\\n  name\\n  slug\\n  category {\\n    ...CategoryTreeNested\\n    cashoutEnabled\\n    __typename\\n  }\\n}\\n\\nfragment SportOutcomeFixtureEventStatus on SportFixtureEventStatusData {\\n  homeScore\\n  awayScore\\n  matchStatus\\n  clock {\\n    matchTime\\n    remainingTime\\n    __typename\\n  }\\n  periodScores {\\n    homeScore\\n    awayScore\\n    matchStatus\\n    __typename\\n  }\\n  currentTeamServing\\n  homeGameScore\\n  awayGameScore\\n  statistic {\\n    yellowCards {\\n      away\\n      home\\n      __typename\\n    }\\n    redCards {\\n      away\\n      home\\n      __typename\\n    }\\n    corners {\\n      home\\n      away\\n      __typename\\n    }\\n    __typename\\n  }\\n}\\n\\nfragment EsportOutcomeFixtureEventStatus on EsportFixtureEventStatus {\\n  matchStatus\\n  homeScore\\n  awayScore\\n  scoreboard {\\n    homeGold\\n    awayGold\\n    homeGoals\\n    awayGoals\\n    homeKills\\n    awayKills\\n    gameTime\\n    homeDestroyedTowers\\n    awayDestroyedTurrets\\n    currentRound\\n    currentCtTeam\\n    currentDefTeam\\n    time\\n    awayWonRounds\\n    homeWonRounds\\n    remainingGameTime\\n    __typename\\n  }\\n  periodScores {\\n    type\\n    number\\n    awayGoals\\n    awayKills\\n    awayScore\\n    homeGoals\\n    homeKills\\n    homeScore\\n    awayWonRounds\\n    homeWonRounds\\n    matchStatus\\n    __typename\\n  }\\n  __typename\\n}\\n\\nfragment SportFixtureLiveStreamExists on SportFixture {\\n  id\\n  betradarStream {\\n    exists\\n    __typename\\n  }\\n  imgArenaStream {\\n    exists\\n    __typename\\n  }\\n  abiosStream {\\n    exists\\n    stream {\\n      startTime\\n      id\\n      __typename\\n    }\\n    __typename\\n  }\\n  geniussportsStream(deliveryType: hls) {\\n    exists\\n    __typename\\n  }\\n  statsPerformStream(getData: false) {\\n    isAvailable\\n    geoBlocked\\n    __typename\\n  }\\n}\\n\\nfragment SportBet on SportBet {\\n  __typename\\n  id\\n  customBet\\n  amount\\n  active\\n  currency\\n  status\\n  payoutMultiplier\\n  cashoutMultiplier\\n  cashoutDisabled\\n  updatedAt\\n  payout\\n  createdAt\\n  potentialMultiplier\\n  adjustments {\\n    id\\n    payoutMultiplier\\n    updatedAt\\n    createdAt\\n    __typename\\n  }\\n  promotionBet {\\n    settleType\\n    status\\n    payout\\n    currency\\n    promotion {\\n      name\\n      __typename\\n    }\\n    __typename\\n  }\\n  user {\\n    id\\n    name\\n    __typename\\n  }\\n  bet {\\n    iid\\n    __typename\\n  }\\n  outcomes {\\n    __typename\\n    odds\\n    totalOdds\\n    status\\n    outcome {\\n      __typename\\n      ...SportMarketOutcome\\n      probabilities\\n      voidFactor\\n      payout\\n    }\\n    sport {\\n      cashoutEnabled\\n      __typename\\n    }\\n    market {\\n      ...SportMarket\\n      __typename\\n    }\\n    fixture {\\n      id\\n      status\\n      slug\\n      provider\\n      marketCount(status: [active, suspended])\\n      extId\\n      cashoutEnabled\\n      data {\\n        ...SportFixtureDataMatch\\n        ...SportFixtureDataOutright\\n        __typename\\n      }\\n      tournament {\\n        ...TournamentTreeNested\\n        cashoutEnabled\\n        __typename\\n      }\\n      eventStatus {\\n        ...SportOutcomeFixtureEventStatus\\n        ...EsportOutcomeFixtureEventStatus\\n        __typename\\n      }\\n      ...SportFixtureLiveStreamExists\\n      __typename\\n    }\\n  }\\n}\\n\\nfragment SportFixtureEventStatus on SportFixtureEventStatusData {\\n  __typename\\n  homeScore\\n  awayScore\\n  matchStatus\\n  clock {\\n    matchTime\\n    remainingTime\\n    __typename\\n  }\\n  periodScores {\\n    homeScore\\n    awayScore\\n    matchStatus\\n    __typename\\n  }\\n  currentTeamServing\\n  homeGameScore\\n  awayGameScore\\n  statistic {\\n    yellowCards {\\n      away\\n      home\\n      __typename\\n    }\\n    redCards {\\n      away\\n      home\\n      __typename\\n    }\\n    corners {\\n      home\\n      away\\n      __typename\\n    }\\n    __typename\\n  }\\n}\\n\\nfragment EsportFixtureEventStatus on EsportFixtureEventStatus {\\n  matchStatus\\n  homeScore\\n  awayScore\\n  scoreboard {\\n    homeGold\\n    awayGold\\n    homeGoals\\n    awayGoals\\n    homeKills\\n    awayKills\\n    gameTime\\n    homeDestroyedTowers\\n    awayDestroyedTurrets\\n    currentRound\\n    currentCtTeam\\n    currentDefTeam\\n    time\\n    awayWonRounds\\n    homeWonRounds\\n    remainingGameTime\\n    __typename\\n  }\\n  periodScores {\\n    type\\n    number\\n    awayGoals\\n    awayKills\\n    awayScore\\n    homeGoals\\n    homeKills\\n    homeScore\\n    awayWonRounds\\n    homeWonRounds\\n    matchStatus\\n    __typename\\n  }\\n  __typename\\n}\\n\\nfragment SwishMarketOutcomeFragment on SwishMarketOutcome {\\n  __typename\\n  id\\n  line\\n  over\\n  under\\n  gradeOver\\n  gradeUnder\\n  suspended\\n  balanced\\n  name\\n  competitor {\\n    id\\n    name\\n    stats {\\n      name\\n      dataConfirmed\\n      played\\n      __typename\\n    }\\n    __typename\\n  }\\n  market {\\n    id\\n    game {\\n      disabled\\n      status\\n      __typename\\n    }\\n    inPlay\\n    stat {\\n      swishStatId\\n      name\\n      value\\n      type\\n      __typename\\n    }\\n    game {\\n      id\\n      fixture {\\n        id\\n        extId\\n        name\\n        slug\\n        status\\n        provider\\n        swishGame {\\n          swishSportId\\n          status\\n          __typename\\n        }\\n        eventStatus {\\n          ...SportFixtureEventStatus\\n          ...EsportFixtureEventStatus\\n          __typename\\n        }\\n        data {\\n          ... on SportFixtureDataMatch {\\n            __typename\\n            startTime\\n            teams {\\n              name\\n              qualifier\\n              __typename\\n            }\\n            competitors {\\n              name\\n              extId\\n              countryCode\\n              abbreviation\\n              __typename\\n            }\\n          }\\n          ... on SportFixtureDataOutright {\\n            __typename\\n            startTime\\n            name\\n          }\\n          __typename\\n        }\\n        tournament {\\n          id\\n          slug\\n          name\\n          category {\\n            id\\n            slug\\n            name\\n            sport {\\n              id\\n              name\\n              slug\\n              __typename\\n            }\\n            __typename\\n          }\\n          __typename\\n        }\\n        __typename\\n      }\\n      __typename\\n    }\\n    __typename\\n  }\\n}\\n\\nfragment SwishBetFragment on SwishBet {\\n  __typename\\n  active\\n  amount\\n  cashoutDisabled\\n  potentialMultiplier\\n  createdAt\\n  currency\\n  customBet\\n  id\\n  odds\\n  payout\\n  payoutMultiplier\\n  adjustments {\\n    id\\n    payoutMultiplier\\n    updatedAt\\n    createdAt\\n    __typename\\n  }\\n  updatedAt\\n  status\\n  user {\\n    id\\n    name\\n    preferenceHideBets\\n    __typename\\n  }\\n  outcomes {\\n    __typename\\n    id\\n    odds\\n    lineType\\n    outcome {\\n      ...SwishMarketOutcomeFragment\\n      market {\\n        data {\\n          atBat {\\n            marketDurationStart\\n            __typename\\n          }\\n          __typename\\n        }\\n        __typename\\n      }\\n      __typename\\n    }\\n  }\\n}\\n\\nfragment RunnerOutcomeButton_RacingOutcome on RacingOutcome {\\n  id\\n  active\\n  odds\\n  market {\\n    name\\n    status\\n    __typename\\n  }\\n}\\n\\nfragment RunnerOutcomeButton_RacingRunner on RacingRunner {\\n  id\\n  name\\n  scratched\\n  runnerNumber\\n  barrierPosition\\n  hcpDraw\\n  attributes {\\n    weight\\n    __typename\\n  }\\n  careerStats {\\n    last6Runs\\n    __typename\\n  }\\n  jockey {\\n    name\\n    __typename\\n  }\\n  trainer {\\n    name\\n    __typename\\n  }\\n  prices {\\n    id\\n    active\\n    odds\\n    market {\\n      name\\n      status\\n      __typename\\n    }\\n    ...RunnerOutcomeButton_RacingOutcome\\n    __typename\\n  }\\n}\\n\\nfragment RacingBet on RacingBet {\\n  __typename\\n  id\\n  active\\n  amount\\n  createdAt\\n  updatedAt\\n  currency\\n  resultType\\n  user {\\n    id\\n    name\\n    __typename\\n  }\\n  outcomes {\\n    id\\n    updatedAt\\n    prices {\\n      odds\\n      marketName\\n      __typename\\n    }\\n    result {\\n      resultedPrices\\n      status\\n      deadheatMultiplier\\n      __typename\\n    }\\n    deductions {\\n      key\\n      name\\n      percentage\\n      __typename\\n    }\\n    type\\n    derivativeType\\n    event {\\n      id\\n      eventNumber\\n      slug\\n      startTime\\n      status\\n      stream {\\n        url\\n        exists\\n        geoBlocked\\n        __typename\\n      }\\n      runners {\\n        scratched\\n        __typename\\n      }\\n      meeting {\\n        slug\\n        racing {\\n          slug\\n          name\\n          __typename\\n        }\\n        racingGroup {\\n          slug\\n          name\\n          __typename\\n        }\\n        venue {\\n          name\\n          geoBlocked\\n          __typename\\n        }\\n        category {\\n          name\\n          slug\\n          __typename\\n        }\\n        __typename\\n      }\\n      topRunnerList(limit: 4) {\\n        finalPosition\\n        runnerNumber\\n        __typename\\n      }\\n      __typename\\n    }\\n    selectionSlots {\\n      runners {\\n        ...RunnerOutcomeButton_RacingRunner\\n        __typename\\n      }\\n      selections\\n      type\\n      __typename\\n    }\\n    __typename\\n  }\\n  payout\\n  payoutMultiplier\\n  adjustments {\\n    id\\n    payoutMultiplier\\n    updatedAt\\n    createdAt\\n    __typename\\n  }\\n  betStatus: status\\n  betPotentialMultiplier: potentialMultiplier\\n}\\n\\nfragment BetFragment on Bet {\\n  id\\n  iid\\n  type\\n  scope\\n  game {\\n    name\\n    icon\\n    slug\\n    __typename\\n  }\\n  bet {\\n    ... on CasinoBet {\\n      ...CasinoBet\\n      user {\\n        id\\n        name\\n        preferenceHideBets\\n        __typename\\n      }\\n      __typename\\n    }\\n    ... on EvolutionBet {\\n      ...EvolutionBet\\n      user {\\n        id\\n        name\\n        preferenceHideBets\\n        __typename\\n      }\\n      __typename\\n    }\\n    ... on MultiplayerCrashBet {\\n      ...MultiplayerCrashBet\\n      user {\\n        id\\n        name\\n        preferenceHideBets\\n        __typename\\n      }\\n      __typename\\n    }\\n    ... on MultiplayerSlideBet {\\n      ...MultiplayerSlideBet\\n      user {\\n        id\\n        name\\n        preferenceHideBets\\n        __typename\\n      }\\n      __typename\\n    }\\n    ... on SoftswissBet {\\n      ...SoftswissBet\\n      user {\\n        id\\n        name\\n        preferenceHideBets\\n        __typename\\n      }\\n      __typename\\n    }\\n    ... on ThirdPartyBet {\\n      ...ThirdPartyBet\\n      __typename\\n    }\\n    ... on SportBet {\\n      ...SportBet\\n      promotionBet {\\n        payout\\n        status\\n        currency\\n        payoutValue\\n        promotion {\\n          name\\n          __typename\\n        }\\n        __typename\\n      }\\n      user {\\n        id\\n        name\\n        preferenceHideBets\\n        __typename\\n      }\\n      __typename\\n    }\\n    ... on SwishBet {\\n      ...SwishBetFragment\\n      user {\\n        id\\n        name\\n        preferenceHideBets\\n        __typename\\n      }\\n      __typename\\n    }\\n    ... on RacingBet {\\n      ...RacingBet\\n      __typename\\n    }\\n    __typename\\n  }\\n}\\n\",\"variables\":{\"iid\":\"" + iid + "\"}}"

    try:
        # Making the POST request and parsing the response
        logging.info(f"Fetching bet details for IID: {iid}")
        response = requests.request("POST", url, headers=detail_headers, data=payload).json()

        # Check if the response contains the expected structure
        bet_data = response.get('data', {}).get('bet', {}).get('bet', {})
        if not bet_data:
            logging.warning(f"Bet data not found in the response for IID: {iid}")
            return None

        # Safe extraction of bet details
        createdAt = bet_data.get('createdAt')
        createdAt = datetime.strptime(createdAt, "%a, %d %b %Y %H:%M:%S GMT").isoformat()
        updatedAt = bet_data.get('updatedAt')
        updatedAt = datetime.strptime(updatedAt, "%a, %d %b %Y %H:%M:%S GMT").isoformat()
        bettingAmount = bet_data.get('amount')
        bettingCurrency = bet_data.get('currency', '').upper()
        outcomes = bet_data.get('outcomes', [])

        if not outcomes:
            logging.warning(f"No outcomes found for IID: {iid}")
            return None

        odds = outcomes[0].get('odds')
        if odds is None:
            logging.warning(f"Odds not found for IID: {iid}")
            return None

        payout = bettingAmount * odds if bettingAmount and odds else 0

        # Fetch exchange rate for the betting currency
        exchange_rate = get_exchange_rate(bettingCurrency)
        # print ('exchange_rate', exchange_rate)
        converted_stake, converted_payout = 0, 0
        if exchange_rate:
            converted_stake = bettingAmount * exchange_rate
            converted_payout = payout * exchange_rate
        else:
            logging.warning(f"Could not convert currency for IID {iid} due to missing exchange rate.")
            return None

        # Extract match details
        matchName = outcomes[0].get('market', {}).get('name', 'Unknown')
        fixtureName = outcomes[0].get('fixture', {}).get('data', {}).get("competitors", [])

        if not fixtureName:
            logging.warning(f"Competitors not found for IID: {iid}")
            return None

        competitor_names = " - ".join([competitor.get('name', 'Unknown') for competitor in fixtureName])

        # Prepare data dictionary
        data = {
            "iid": iid,
            "fixtureName": competitor_names,
            "odds": odds,
            "bettingAmount": bettingAmount,
            # "bettingCurrency": bettingCurrency + "-USDT",
            "bettingCurrency": "USDT",
            "actualPayout": payout,
            "convertedPayout": converted_payout,
            "convertedStake": converted_stake,
            "matchName": matchName,
            "createdAt": createdAt,
            "updatedAt": updatedAt,
            "sports": "Tennis",
        }

        return data

    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed for IID {iid}: {e}")
        return None
    except KeyError as e:
        logging.error(f"Missing expected data for IID {iid}, key error: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error processing bet details for IID {iid}: {e}")
        return Nones

# Main function to fetch initial bets and then detailed data for each iid
def main():
    try:
        initial_data = fetch_initial_bets()

        twenty_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=20)

        twenty_minutes_ago_str = twenty_minutes_ago.strftime("%a, %d %b %Y %H:%M:%S GMT")

        recent_data = collection.find({"createdAt": {"$gte": twenty_minutes_ago_str}})

        # Convert cursor to list and check if empty
        recent_data_list = list(recent_data)

        #check if initial data is in recent data list. If found, remove the string from initial data
        #initial data has is list of strings with uuid, we need to check if any of these uuids are present in the recent data list, if present, remove pirticular uuid from initial data list
        for data in recent_data_list:
            if data["iid"] in initial_data:
                initial_data.remove(data["iid"])

        # remove the duplications
        if initial_data:
            # print ('initialdata: ', initial_data)
            for bet in initial_data:  # Directly iterate over the list
                try:
                    logging.info(f"Processing bet: {bet}")
                    if bet:
                        bet_details = fetch_bet_details(bet)
                        # Append the bet details into MongoDB
                        insert_to_mongodb(bet_details)

                    else:
                        logging.warning(f"Skipping empty bet: {bet}")
                except Exception as e:
                    logging.error(f"Error processing bet {bet}: {e}")
        else:
            logging.warning("No initial data found, cannot proceed with fetching bet details.")

    except Exception as e:
        logging.error(f"An error occurred in the main function: {e}")

if __name__ == "__main__":
  main()
    # while True:
    #     # schedule.run_pending()
    #     # time.sleep(60)
    #     main()