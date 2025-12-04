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

def upsert_data(cur, table_name, timestamp, base_col, base_valm, r1_col, r1_val, r2_col, r2_val):
    check_query = f"SELECT id FROM {table_name} WHERE time::date = %s::date"
    cur.execute(check_query, (timestamp,))
    row = cur.fetchone()
    if row:
        row_id = row[0]
        update_query = f"""
            UPDATE{table_name}
            SET time = %s, {base_col} = %s, {r1_col} = %s, {r2_col} = %s
            WHERE id = %s
            """
    else:
        insert_query = f"""
            INSERT INTO {table_name} (time, {base_col}, {r1_col}, {r2_col})
            VALUES (%s, %s, %s, %s)
            """
        cur.execute(insert_query, (timestamp, base_valm, r1_val, r2_val))
    
    

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
                upsert_data(cur, "currency_usd", timestamp, "currency_usd", 1, "rate_vnd", rate_vnd, "rate_jpy", rate_jpy)

        # Process VND
        if "VND" in db:
            rates = db["VND"]
            rate_usd = next((item['mid'] for item in rates if item['target'] == 'USD'), None)
            rate_jpy = next((item['mid'] for item in rates if item['target'] == 'JPY'), None)
            timestamp = next((item['timestamp'] for item in rates), None)
            
            if rate_usd and rate_jpy and timestamp:
                upsert_data(cur, "currency_vnd", timestamp, "currency_vnd", 1, "rate_usd", rate_usd, "rate_jpy", rate_jpy)

        # Process JPY
        if "JPY" in db:
            rates = db["JPY"]
            rate_usd = next((item['mid'] for item in rates if item['target'] == 'USD'), None)
            rate_vnd = next((item['mid'] for item in rates if item['target'] == 'VND'), None)
            timestamp = next((item['timestamp'] for item in rates), None)
            
            if rate_usd and rate_vnd and timestamp:
                upsert_data(cur, "currency_jpy", timestamp, "currency_jpy", 1, "rate_usd", rate_usd, "rate_vnd", rate_vnd)

        conn.commit()
        log.logger.info("Database updated successfully")
    except Exception as e:
        if conn:
            conn.rollback()
            log.logger.error(f"Error updating database: {str(e)}")
    finally:
        if conn:
            cur.close()
            conn.close()
def get_db_data(a,b):
    labels = []
    values = []

    table_map = {
        "USD": "currency_usd",
        "VND": "currency_vnd",
        "JPY": "currency_jpy"
    }

    table_name = table_map.get(a)
    column_name = f"rate_{b.lower()}"
    if not table_name:
        return [],[]
    conn = get_db_connection()
    if not conn:
        return [],[]
    cur = conn.cursor()
    try:
        cur.execute("SELECT to_regclass(%s)", (table_name,))
        if cur.fetchone()[0] is None:
            log.logger.error(f"Table {table_name} does not exist")
            return [],[]
        
        cur.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = %s AND column_name = %s",
            (table_name, column_name)
        )
        if not cur.fetchone():
            log.logger.error(f"Column {column_name} does not exist in table {table_name}")
            return [],[]

        query = f"""
            SELECT to_char(time, 'DD/MM HH24:MI'), {column_name} 
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
        

