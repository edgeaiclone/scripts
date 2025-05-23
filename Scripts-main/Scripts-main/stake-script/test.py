import requests
import json

url = "https://stake.com/_api/graphql"

payload = "{\"query\":\"query BetsBoard_HighrollerSportBets($limit: Int!) {\\n  highrollerSportBets(limit: $limit) {\\n    id\\n    iid\\n    bet {\\n      ...BetsBoardSport_BetBet\\n    }\\n  }\\n}\\n\\nfragment BetsBoardSport_BetBet on BetBet {\\n  __typename\\n  ... on SwishBet {\\n    __typename\\n    id\\n    updatedAt\\n    createdAt\\n    potentialMultiplier\\n    amount\\n    currency\\n    user {\\n      id\\n      name\\n      preferenceHideBets\\n    }\\n    outcomes {\\n      __typename\\n      id\\n      odds\\n      outcome {\\n        __typename\\n        id\\n        market {\\n          id\\n          competitor {\\n            name\\n          }\\n          game {\\n            id\\n            fixture {\\n              id\\n              tournament {\\n                id\\n                category {\\n                  id\\n                  sport {\\n                    id\\n                    slug\\n                  }\\n                }\\n              }\\n            }\\n          }\\n        }\\n      }\\n    }\\n  }\\n  ... on SportBet {\\n    __typename\\n    id\\n    updatedAt\\n    createdAt\\n    potentialMultiplier\\n    amount\\n    currency\\n    user {\\n      name\\n      preferenceHideBets\\n    }\\n    outcomes {\\n      id\\n      odds\\n      fixtureAbreviation\\n      fixtureName\\n      fixture {\\n        id\\n        tournament {\\n          id\\n          category {\\n            id\\n            sport {\\n              id\\n              slug\\n            }\\n          }\\n        }\\n      }\\n    }\\n  }\\n  ... on RacingBet {\\n    __typename\\n    id\\n    active\\n    payout\\n    updatedAt\\n    createdAt\\n    betPotentialMultiplier: potentialMultiplier\\n    amount\\n    currency\\n    betStatus: status\\n    payoutMultiplier\\n    adjustments {\\n      payoutMultiplier\\n    }\\n    user {\\n      id\\n      name\\n      preferenceHideBets\\n    }\\n    outcomes {\\n      id\\n      type\\n      derivativeType\\n      prices {\\n        marketName\\n        odds\\n      }\\n      event {\\n        meeting {\\n          racing {\\n            slug\\n          }\\n        }\\n      }\\n      selectionSlots {\\n        runners {\\n          name\\n        }\\n      }\\n      result {\\n        resultedPrices\\n      }\\n    }\\n  }\\n}\\n\",\"variables\":{\"limit\":10}}"
headers = {
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
  'Sec-Fetch-Dest': 'empty',
  'Sec-Fetch-Mode': 'cors',
  'Sec-Fetch-Site': 'same-origin',
  'Sec-GPC': '1',
  'Priority': 'u=0',
  'TE': 'trailers',
  'Cookie': '__cf_bm=nHTrA2ufDX1jzZG2NUF0Wtr3KDXOKgIDjqd.Y3ud8vQ-1741742102-1.0.1.1-d2WK.yXS7nqAbtHaTgeiz_RwkohBTWeVkrl2C4Y18gVq9WLvxVt85lyTq1CUzUMbYrUKpcbVai0NwcB_g5ISVoQ3m_xejssFAlP0wkbdVk0; _cfuvid=.cJoSd7nVcf4jRRPKC87u8N2xAFxXq0rBcj7nt.QIq0-1741742102989-0.0.1.1-604800000'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
