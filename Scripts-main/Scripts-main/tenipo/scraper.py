from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from pymongo import MongoClient
from datetime import datetime
import time


def setup_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)


def setup_mongo():
    print('[✓] Setting up MongoDB connection...')
    
    # Replace credentials with secure env vars or config in production
    connection_string = "mongodb+srv://bilal:pLnClBIMtgJrn2jv@cluster0.gi3fv.mongodb.net/"
    
    try:
        client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        db = client["edgeAI"]
        collection = db["tenipo"]

        # Ensure unique index on match_url to prevent duplicates
        collection.create_index("match_url", unique=True)

        print('[✓] MongoDB connection established and index ensured.')
        return collection

    except Exception as e:
        print(f'[✗] Failed to connect to MongoDB: {e}')
        return None


def get_itf_links(driver):
    itf_links = set()
    itf_spans = driver.find_elements(By.XPATH, "//span[contains(text(), 'ITF')]")

    for span in itf_spans:
        try:
            parent_div = span.find_element(By.XPATH, "./ancestor::div[contains(@onclick, '/tournament/')]")
            onclick_attr = parent_div.get_attribute("onclick")
            if onclick_attr:
                link = onclick_attr.split("'")[1] if "'" in onclick_attr else onclick_attr.split('"')[1]
                full_url = "https://tenipo.com" + link
                itf_links.add(full_url)
        except Exception as e:
            print("[!] Error extracting ITF link:", e)

    return list(itf_links)


def extract_match_data(driver, match_url):
    driver.get(match_url)
    time.sleep(3)
    try:
        tournament_name = driver.find_element(By.XPATH, "//div[@style and contains(text(), 'ITF')]").text
        round_info = driver.find_element(By.XPATH, "//div[@class='offline' and contains(text(), 'Round')]").text
        players = driver.find_elements(By.XPATH, "//table[@class='detail_players name']//td")
        if len(players) < 2:
            raise ValueError("Not enough player data")

        player1 = players[0].text.replace('\n', ' ').strip()
        player2 = players[1].text.replace('\n', ' ').strip()

        match_data = {
            "scraped_at": datetime.utcnow(),
            "tournament": tournament_name,
            "round": round_info,
            "player1": player1,
            "player2": player2,
            "match_url": match_url,
            "pt_by_pt": [],
            "stats": []
        }

        # Click "Pt by Pt"
        try:
            pt_by_pt_button = driver.find_element(By.ID, "buttonhistoryall")
            driver.execute_script("arguments[0].click();", pt_by_pt_button)
            time.sleep(2)

            headers = driver.find_elements(By.CLASS_NAME, "ohlavicka1")
            histories = driver.find_elements(By.CLASS_NAME, "sethistory")

            for header, history in zip(headers, histories):
                try:
                    score_text = header.find_element(By.CLASS_NAME, "ohlavicka3").text.strip()
                    points = []

                    for point in history.find_elements(By.CLASS_NAME, "pointlogg"):
                        spans = point.find_elements(By.TAG_NAME, "span")
                        if len(spans) == 1:
                            before = point.text.split("\n")[0].strip()
                            after = spans[0].text.strip()
                        elif len(spans) == 2:
                            before = spans[0].text.strip()
                            after = spans[1].text.strip()
                        else:
                            before = after = "?"
                        points.append({"before": before, "after": after})

                    match_data["pt_by_pt"].append({
                        "score_header": score_text,
                        "points": points
                    })
                except Exception as e:
                    print(f"[!] Error parsing point-by-point block: {e}")
        except Exception as e:
            print(f"[!] Could not extract Pt by Pt data: {e}")

        # Click "Stats"
        try:
            stats_button = driver.find_element(By.ID, "buttonstatsall")
            driver.execute_script("arguments[0].click();", stats_button)
            time.sleep(2)

            stats_container = driver.find_element(By.ID, "stats")
            stat_blocks = stats_container.find_elements(By.CLASS_NAME, "stat")

            for stat in stat_blocks:
                try:
                    stat_name = stat.find_element(By.CLASS_NAME, "stat_name").text.strip()
                    player1_stat = stat.find_element(By.CLASS_NAME, "stat_col.l").text.strip().replace("\n", " ")
                    player2_stats = stat.find_elements(By.CLASS_NAME, "stat_col")
                    player2_stat = player2_stats[1].text.strip().replace("\n", " ") if len(player2_stats) > 1 else ""

                    match_data["stats"].append({
                        "name": stat_name,
                        "player1": player1_stat,
                        "player2": player2_stat
                    })
                except Exception as stat_err:
                    print(f"[!] Error reading a stat block: {stat_err}")
        except Exception as stats_err:
            print(f"[!] Could not extract match stats: {stats_err}")

        return match_data

    except Exception as e:
        print(f"[!] Failed to extract match data from {match_url}: {e}")
        return None


def main():
    collection = setup_mongo()

    while True:
        driver = setup_driver()
        driver.get("https://tenipo.com/livescore")
        time.sleep(3)

        itf_links = get_itf_links(driver)
        print(f"\nFound {len(itf_links)} ITF tournaments.")

        for url in itf_links:
            try:
                driver.get(url)
                time.sleep(3)

                # Click "Live" button
                try:
                    live_button = driver.find_element(By.XPATH, "//div[@class='button_detail2' and contains(text(), 'Live')]")
                    driver.execute_script("arguments[0].click();", live_button)
                    time.sleep(2)
                except Exception:
                    print(f"[!] No Live button for tournament: {url}")
                    continue

                match_urls = set()
                table3_elements = driver.find_elements(By.XPATH, "//table[contains(@class, 'table3') and @onclick]")
                for table in table3_elements:
                    try:
                        onclick_attr = table.get_attribute("onclick")
                        if onclick_attr:
                            url_part = onclick_attr.split('"')[1]
                            full_url = f"https://tenipo.com{url_part}"
                            match_urls.add(full_url)
                    except Exception as e:
                        print(f"[!] Error parsing table3 onclick: {e}")

                print(f"→ Found {len(match_urls)} match links")

                for match_url in match_urls:
                    data = extract_match_data(driver, match_url)
                    if data:
                        try:
                            print ('data', data)
                            collection.update_one(
                                {"match_url": data["match_url"]},
                                {"$set": data},
                                upsert=True
                            )
                            print(f"[✓] Inserted/Updated match: {data['player1']} vs {data['player2']}")
                        except Exception as mongo_err:
                            print(f"[!] Mongo insert error: {mongo_err}")

            except Exception as e:
                print(f"[!] Failed to process tournament URL: {url}, Error: {e}")

        driver.quit()
        print("✅ Completed one full scrape cycle. Waiting 5 seconds...\n")
        time.sleep(5)


if __name__ == "__main__":
    main()
