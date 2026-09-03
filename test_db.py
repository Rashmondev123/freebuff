import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv("DATABASE_URL"))

cur = conn.cursor()

create_users_table = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    balance NUMERIC DEFAULT 1000000,
    created_at TIMESTAMP DEFAULT NOW(),
    display_name TEXT
);
"""

create_bet_slips_table = """
CREATE TABLE IF NOT EXISTS bet_slips (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    stake NUMERIC NOT NULL,
    total_odds NUMERIC NOT NULL,
    potential_payout NUMERIC NOT NULL,
    status TEXT DEFAULT 'pending',
    date_placed TIMESTAMP DEFAULT NOW(),
    date_settled TIMESTAMP,
    share_code TEXT UNIQUE
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

cur.execute(create_users_table)
cur.execute(create_bet_slips_table)
cur.execute(create_selections_table)

conn.commit()

print("All tables created successfully on Neon!")

cur.close()
conn.close()