import os
import psycopg2
import log
import requests
from datetime import datetime, timedelta


DB_HOST = os.getenv("DB_HOST", "localhost")
#DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "currency_converter")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")




def request_rate():
    money = ["USD", "VND", "JPY"]
    base = ["VND", "USD", "JPY"]
    rate = {}
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://google.com",
    }
    for item in money:
        for baseitem in base:
            if item == baseitem:
                continue
            url = f"https://hexarate.paikama.co/api/rates/latest/{baseitem}?target={item}"
            response = requests.get(url, headers=header, timeout=10 )
            if response.status_code == 200:
                data = response.json()
                cc_data = data["data"]
                cc_data.pop("base")
                rate.setdefault(baseitem, []).append(cc_data)
                log.logger.info(f"Rate for {baseitem} to {item}: {cc_data}")
            else:
                log.logger.error(f"Failed to get rate for {baseitem} to {item}: {response.status_code}")
    return rate


def get_db_connection():
    try:
        conn = psycopg2.connect(
            host = DB_HOST,
            #port = DB_PORT,
            database = DB_NAME,
            user = DB_USER,
            password = DB_PASSWORD
        )
        return conn
    except Exception as e:
        log.logger.error(f"Error connecting to the database: {str(e)}")
        return None

def create_tables():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Create currency_usd table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS currency_usd (
                id SERIAL PRIMARY KEY,
                time TIMESTAMP NOT NULL,
                currency_usd NUMERIC NOT NULL,
                rate_vnd NUMERIC NOT NULL,
                rate_jpy NUMERIC NOT NULL
            );
        ''')

        # Create currency_vnd table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS currency_vnd (
                id SERIAL PRIMARY KEY,
                time TIMESTAMP NOT NULL,
                currency_vnd NUMERIC NOT NULL,
                rate_usd NUMERIC NOT NULL,
                rate_jpy NUMERIC NOT NULL
            );
        ''')

        # Create currency_jpy table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS currency_jpy (
                id SERIAL PRIMARY KEY,
                time TIMESTAMP NOT NULL,
                currency_jpy NUMERIC NOT NULL,
                rate_usd NUMERIC NOT NULL,
                rate_vnd NUMERIC NOT NULL
            );
        ''')
        
        conn.commit()
        cur.close()
        conn.close()
        log.logger.info("Tables created successfully")
    except Exception as e:
        log.logger.error(f"Error creating tables: {str(e)}")

def update_db():
    try:
        db = request_rate()
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Process USD
        if "USD" in db:
            rates = db["USD"]
            rate_vnd = next((item['mid'] for item in rates if item['target'] == 'VND'), None)
            rate_jpy = next((item['mid'] for item in rates if item['target'] == 'JPY'), None)
            timestamp = next((item['timestamp'] for item in rates), None)
            
            if rate_vnd and rate_jpy and timestamp:
                cur.execute(
                    '''
                    INSERT INTO currency_usd (time, currency_usd, rate_vnd, rate_jpy)
                    VALUES (%s, 1, %s, %s)
                    ''',
                    (timestamp, rate_vnd, rate_jpy)
                )

        # Process VND
        if "VND" in db:
            rates = db["VND"]
            rate_usd = next((item['mid'] for item in rates if item['target'] == 'USD'), None)
            rate_jpy = next((item['mid'] for item in rates if item['target'] == 'JPY'), None)
            timestamp = next((item['timestamp'] for item in rates), None)
            
            if rate_usd and rate_jpy and timestamp:
                cur.execute(
                    '''
                    INSERT INTO currency_vnd (time, currency_vnd, rate_usd, rate_jpy)
                    VALUES (%s, 1, %s, %s)
                    ''',
                    (timestamp, rate_usd, rate_jpy)
                )

        # Process JPY
        if "JPY" in db:
            rates = db["JPY"]
            rate_usd = next((item['mid'] for item in rates if item['target'] == 'USD'), None)
            rate_vnd = next((item['mid'] for item in rates if item['target'] == 'VND'), None)
            timestamp = next((item['timestamp'] for item in rates), None)
            
            if rate_usd and rate_vnd and timestamp:
                cur.execute(
                    '''
                    INSERT INTO currency_jpy (time, currency_jpy, rate_usd, rate_vnd)
                    VALUES (%s, 1, %s, %s)
                    ''',
                    (timestamp, rate_usd, rate_vnd)
                )

        conn.commit()
        cur.close()
        conn.close()
        log.logger.info("Database updated successfully")
    except Exception as e:
        log.logger.error(f"Error updating database: {str(e)}")

def get_db_data(a):
    labels = []
    values = []

    table_map = {
        "USD": "currency_usd",
        "VND": "currency_vnd",
        "JPY": "currency_jpy"
    }

    table_name = table_map.get(a)
    if not table_name:
        return [],[]
    conn = get_db_connection()
    if not conn:
        return [],[]

    try:
        cur.execute("SELECT to_regclass(%s)", (table_name,))
        if cur.fetchone()[0] is None:
            log.logger.error(f"Table {table_name} does not exist")
            return [],[]
        
        query = f"""
            SELECT to_char(time, 'DD/MM HH24:MI'), rate 
            FROM {table_name} 
            WHERE time >= NOW() - INTERVAL '7 days' 
            ORDER BY time ASC
        """
        cur.execute(query)
        rows = cur.fetchall()
        for row in rows:
            labels.append(row[0])
            values.append(float(row[1]))
        log.logger.info(f"Data retrieved successfully: {labels}, {values}")
    except Exception as e:
        log.logger.error(f"Error retrieving data: {str(e)}")

    finally:
        if conn:
            conn.close()
    return labels, values
        

        
    


    
def process_db():
    try:
        conn = get_db_connection()
        if not conn:
            return
        
        try:
            cur = conn.cursor()
            cur.execute("SELECT MAX(time) FROM currency_usd")
            row = cur.fetchall()
            if row and row[0] and row[0][0] :
                last_time = row[0][0]
            else:
                last_time = None
            now = datetime.now()

            should_update = False

            if not last_time:
                log.logger.info("No data in database, updating...")
                should_update = True
            elif (now -last_time) > timedelta(days=1):
                log.logger.info("Data is older than 1 day, updating...")
                should_update = True
            else:
                log.logger.info("Data is up to date, no update needed")
                
            if should_update:
                update_db()
                conn.commit()
                log.logger.info("Database updated successfully")
            else:
                log.logger.info("Database is up to date, no update needed")
        except Exception as e:
            log.logger.error(f"Error processing database: {str(e)}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
    except Exception as e:
        log.logger.error(f"Error processing database: {str(e)}")