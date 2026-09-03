import os
import secrets
import requests
import psycopg2
from flask import Flask, request, session
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
CORS(app, supports_credentials=True, origins=["http://127.0.0.1:5500", "https://freebuff-black.vercel.app"])

ODDS_API_KEY = os.getenv("ODDS_API_KEY")


def get_db_connection():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return psycopg2.connect(database_url)

    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

@app.route("/")
def hello():
    return {"message": "FreeBuff backend is alive"}


@app.route("/games")
def games():
    url = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "uk",
        "markets": "h2h"
    }
    response = requests.get(url, params=params)
    real_games = response.json()

    clean_games = []

    for game in real_games:
        if not game.get("bookmakers"):
            continue

        first_bookmaker = game["bookmakers"][0]
        outcomes = first_bookmaker["markets"][0]["outcomes"]

        odds_by_outcome = {}
        for outcome in outcomes:
            odds_by_outcome[outcome["name"]] = outcome["price"]

        clean_game = {
            "id": game["id"],
            "home_team": game["home_team"],
            "away_team": game["away_team"],
            "commence_time": game["commence_time"],
            "odds": {
                "home": odds_by_outcome.get(game["home_team"]),
                "draw": odds_by_outcome.get("Draw"),
                "away": odds_by_outcome.get(game["away_team"])
            }
        }
        clean_games.append(clean_game)

    return {"games": clean_games}


@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return {"error": "Email and password are required"}, 400

    password_hash = generate_password_hash(password)

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id",
            (email, password_hash)
        )
        new_user_id = cur.fetchone()[0]

        display_name = f"Player{new_user_id}"
        cur.execute(
            "UPDATE users SET display_name = %s WHERE id = %s",
            (display_name, new_user_id)
        )

        conn.commit()
        return {"message": "Account created", "user_id": new_user_id}, 201

    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return {"error": "An account with that email already exists"}, 409

    finally:
        cur.close()
        conn.close()


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return {"error": "Email and password are required"}, 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, password_hash FROM users WHERE email = %s", (email,))
    user = cur.fetchone()

    cur.close()
    conn.close()

    if user is None:
        return {"error": "Invalid email or password"}, 401

    user_id, stored_hash = user

    if not check_password_hash(stored_hash, password):
        return {"error": "Invalid email or password"}, 401

    session["user_id"] = user_id

    return {"message": "Login successful", "user_id": user_id}, 200


@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    return {"message": "Logged out"}, 200


@app.route("/me")
def me():
    user_id = session.get("user_id")

    if user_id is None:
        return {"error": "Not logged in"}, 401

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT balance, display_name FROM users WHERE id = %s", (user_id,))
    balance, display_name = cur.fetchone()
    cur.close()
    conn.close()

    return {
        "message": "You are logged in",
        "user_id": user_id,
        "balance": float(balance),
        "display_name": display_name
    }, 200


@app.route("/update-display-name", methods=["POST"])
def update_display_name():
    user_id = session.get("user_id")

    if user_id is None:
        return {"error": "You must be logged in"}, 401

    data = request.get_json()
    new_name = data.get("display_name", "").strip()

    if not new_name or len(new_name) > 20:
        return {"error": "Display name must be 1-20 characters"}, 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET display_name = %s WHERE id = %s", (new_name, user_id))
    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Display name updated", "display_name": new_name}, 200


@app.route("/place-bet", methods=["POST"])
def place_bet():
    user_id = session.get("user_id")

    if user_id is None:
        return {"error": "You must be logged in to place a bet"}, 401

    data = request.get_json()
    stake = data.get("stake")
    selections = data.get("selections")

    if not stake or not selections or len(selections) == 0:
        return {"error": "Stake and at least one selection are required"}, 400

    total_odds = 1
    for selection in selections:
        total_odds *= selection["odds"]

    potential_payout = round(stake * total_odds, 2)

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        share_code = secrets.token_urlsafe(6)

        cur.execute(
            """INSERT INTO bet_slips (user_id, stake, total_odds, potential_payout, share_code)
               VALUES (%s, %s, %s, %s, %s) RETURNING id""",
            (user_id, stake, total_odds, potential_payout, share_code)
        )
        slip_id = cur.fetchone()[0]

        for selection in selections:
            cur.execute(
                """INSERT INTO selections (slip_id, league, home_team, away_team, pick, odds)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (
                    slip_id,
                    selection.get("league"),
                    selection.get("home_team"),
                    selection.get("away_team"),
                    selection["pick"],
                    selection["odds"]
                )
            )

        conn.commit()
        return {
            "message": "Bet placed",
            "slip_id": slip_id,
            "total_odds": total_odds,
            "potential_payout": potential_payout,
            "share_code": share_code
        }, 201

    except Exception as e:
        conn.rollback()
        return {"error": "Something went wrong placing the bet"}, 500

    finally:
        cur.close()
        conn.close()


def fetch_bets_by_status(user_id, status_filter):
    conn = get_db_connection()
    cur = conn.cursor()

    if status_filter == "pending":
        cur.execute(
            """SELECT id, stake, total_odds, potential_payout, status, date_placed, date_settled, share_code
               FROM bet_slips
               WHERE user_id = %s AND status = 'pending'
               ORDER BY date_placed DESC""",
            (user_id,)
        )
    else:
        cur.execute(
            """SELECT id, stake, total_odds, potential_payout, status, date_placed, date_settled, share_code
               FROM bet_slips
               WHERE user_id = %s AND status != 'pending'
               ORDER BY date_settled DESC""",
            (user_id,)
        )

    slips = cur.fetchall()
    result = []

    for slip in slips:
        slip_id, stake, total_odds, potential_payout, status, date_placed, date_settled, share_code = slip

        cur.execute(
            """SELECT id, home_team, away_team, pick, odds, result
               FROM selections
               WHERE slip_id = %s""",
            (slip_id,)
        )
        selections = cur.fetchall()

        selections_list = []
        for sel in selections:
            sel_id, home_team, away_team, pick, odds, result_status = sel
            selections_list.append({
                "selection_id": sel_id,
                "home_team": home_team,
                "away_team": away_team,
                "pick": pick,
                "odds": float(odds),
                "result": result_status
            })

        result.append({
            "slip_id": slip_id,
            "stake": float(stake),
            "total_odds": float(total_odds),
            "potential_payout": float(potential_payout),
            "status": status,
            "date_placed": date_placed.isoformat(),
            "date_settled": date_settled.isoformat() if date_settled else None,
            "share_code": share_code,
            "selections": selections_list
        })

    cur.close()
    conn.close()

    return result


@app.route("/my-bets")
def my_bets():
    user_id = session.get("user_id")

    if user_id is None:
        return {"error": "You must be logged in"}, 401

    bets = fetch_bets_by_status(user_id, "pending")
    return {"bets": bets}


@app.route("/bet-history")
def bet_history():
    user_id = session.get("user_id")

    if user_id is None:
        return {"error": "You must be logged in"}, 401

    bets = fetch_bets_by_status(user_id, "settled")
    return {"bets": bets}


@app.route("/settle-selection", methods=["POST"])
def settle_selection():
    user_id = session.get("user_id")

    if user_id is None:
        return {"error": "You must be logged in"}, 401

    data = request.get_json()
    selection_id = data.get("selection_id")
    outcome = data.get("result")

    if outcome not in ("won", "lost"):
        return {"error": "result must be 'won' or 'lost'"}, 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """SELECT bet_slips.id
               FROM selections
               JOIN bet_slips ON selections.slip_id = bet_slips.id
               WHERE selections.id = %s AND bet_slips.user_id = %s""",
            (selection_id, user_id)
        )
        row = cur.fetchone()

        if row is None:
            return {"error": "Selection not found"}, 404

        slip_id = row[0]

        cur.execute(
            "UPDATE selections SET result = %s WHERE id = %s",
            (outcome, selection_id)
        )

        cur.execute(
            "SELECT result FROM selections WHERE slip_id = %s",
            (slip_id,)
        )
        all_results = [r[0] for r in cur.fetchall()]

        if "lost" in all_results:
            new_slip_status = "lost"
        elif all(r == "won" for r in all_results):
            new_slip_status = "won"
        else:
            new_slip_status = "pending"

        if new_slip_status != "pending":
            cur.execute(
                "UPDATE bet_slips SET status = %s, date_settled = NOW() WHERE id = %s",
                (new_slip_status, slip_id)
            )

        conn.commit()

        return {
            "message": "Selection updated",
            "slip_id": slip_id,
            "slip_status": new_slip_status
        }, 200

    except Exception as e:
        conn.rollback()
        return {"error": "Something went wrong settling the selection"}, 500

    finally:
        cur.close()
        conn.close()


@app.route("/insights")
def insights():
    user_id = session.get("user_id")

    if user_id is None:
        return {"error": "You must be logged in"}, 401

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """SELECT id, stake, potential_payout, status, date_settled
           FROM bet_slips
           WHERE user_id = %s
             AND status IN ('won', 'lost')
             AND date_settled >= NOW() - INTERVAL '7 days'""",
        (user_id,)
    )
    slips = cur.fetchall()

    if len(slips) == 0:
        cur.close()
        conn.close()
        return {
            "has_data": False,
            "message": "No settled bets in the last 7 days yet."
        }

    total_slips = len(slips)
    won_slips = sum(1 for s in slips if s[3] == "won")
    overall_win_rate = round((won_slips / total_slips) * 100, 1)

    average_stake = round(sum(float(s[1]) for s in slips) / total_slips, 2)

    won_payouts = [float(s[2]) for s in slips if s[3] == "won"]
    average_payout = round(sum(won_payouts) / len(won_payouts), 2) if won_payouts else 0

    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_stats = {day: {"won": 0, "total": 0} for day in day_names}

    for slip in slips:
        date_settled = slip[4]
        status = slip[3]
        day_name = day_names[date_settled.weekday()]
        day_stats[day_name]["total"] += 1
        if status == "won":
            day_stats[day_name]["won"] += 1

    day_win_rates = {}
    for day, stats in day_stats.items():
        if stats["total"] > 0:
            day_win_rates[day] = round((stats["won"] / stats["total"]) * 100, 1)

    best_day = max(day_win_rates, key=day_win_rates.get) if day_win_rates else None
    worst_day = min(day_win_rates, key=day_win_rates.get) if day_win_rates else None

    slip_ids = [s[0] for s in slips]
    cur.execute(
        """SELECT league, result FROM selections
           WHERE slip_id = ANY(%s) AND result IN ('won', 'lost')""",
        (slip_ids,)
    )
    selection_rows = cur.fetchall()

    league_stats = {}
    for league, result in selection_rows:
        if league not in league_stats:
            league_stats[league] = {"won": 0, "total": 0}
        league_stats[league]["total"] += 1
        if result == "won":
            league_stats[league]["won"] += 1

    league_win_rates = {}
    for league, stats in league_stats.items():
        league_win_rates[league] = round((stats["won"] / stats["total"]) * 100, 1)

    cur.close()
    conn.close()

    return {
        "has_data": True,
        "total_bets": total_slips,
        "overall_win_rate": overall_win_rate,
        "average_stake": average_stake,
        "average_payout": average_payout,
        "best_day": best_day,
        "worst_day": worst_day,
        "win_rate_by_league": league_win_rates
    }


@app.route("/slip/<share_code>")
def view_shared_slip(share_code):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """SELECT id, stake, total_odds, potential_payout, status, date_placed
           FROM bet_slips
           WHERE share_code = %s""",
        (share_code,)
    )
    slip = cur.fetchone()

    if slip is None:
        cur.close()
        conn.close()
        return {"error": "Slip not found"}, 404

    slip_id, stake, total_odds, potential_payout, status, date_placed = slip

    cur.execute(
        """SELECT home_team, away_team, pick, odds, result
           FROM selections
           WHERE slip_id = %s""",
        (slip_id,)
    )
    selections = cur.fetchall()

    selections_list = [
        {
            "home_team": s[0],
            "away_team": s[1],
            "pick": s[2],
            "odds": float(s[3]),
            "result": s[4]
        }
        for s in selections
    ]

    cur.close()
    conn.close()

    return {
        "stake": float(stake),
        "total_odds": float(total_odds),
        "potential_payout": float(potential_payout),
        "status": status,
        "date_placed": date_placed.isoformat(),
        "selections": selections_list
    }


@app.route("/leaderboard")
def leaderboard():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """SELECT users.display_name,
                  COUNT(bet_slips.id) AS total_bets,
                  SUM(CASE WHEN bet_slips.status = 'won' THEN 1 ELSE 0 END) AS won_bets,
                  SUM(CASE WHEN bet_slips.status = 'won'
                           THEN bet_slips.potential_payout - bet_slips.stake
                           ELSE -bet_slips.stake END) AS net_profit
           FROM bet_slips
           JOIN users ON bet_slips.user_id = users.id
           WHERE bet_slips.status IN ('won', 'lost')
           GROUP BY users.id, users.display_name
           HAVING COUNT(bet_slips.id) >= 3"""
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    leaderboard_data = []
    for display_name, total_bets, won_bets, net_profit in rows:
        win_rate = round((won_bets / total_bets) * 100, 1)
        leaderboard_data.append({
            "display_name": display_name,
            "total_bets": total_bets,
            "win_rate": win_rate,
            "net_profit": float(net_profit)
        })

    leaderboard_data.sort(key=lambda x: x["win_rate"], reverse=True)

    return {"leaderboard": leaderboard_data[:20]}


if __name__ == "__main__":
    app.run(debug=True, port=5000)