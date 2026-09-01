import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)

cur = conn.cursor()

create_bet_slips_table = """
CREATE TABLE IF NOT EXISTS bet_slips (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    stake NUMERIC NOT NULL,
    total_odds NUMERIC NOT NULL,
    potential_payout NUMERIC NOT NULL,
    status TEXT DEFAULT 'pending',
    date_placed TIMESTAMP DEFAULT NOW(),
    date_settled TIMESTAMP
);
"""

create_selections_table = """
CREATE TABLE IF NOT EXISTS selections (
    id SERIAL PRIMARY KEY,
    slip_id INTEGER REFERENCES bet_slips(id),
    league TEXT,
    home_team TEXT,
    away_team TEXT,
    pick TEXT NOT NULL,
    odds NUMERIC NOT NULL,
    result TEXT DEFAULT 'pending'
);
"""

cur.execute(create_bet_slips_table)
cur.execute(create_selections_table)

conn.commit()

print("bet_slips and selections tables created successfully!")

cur.close()
conn.close()