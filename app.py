from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = "change_this_secret"

DB = {
    "host": "localhost",
    "database": "cricketdb",
    "user": "postgres",
    "password": "SIVA@13NOV2005",
    "port": 5432
}

BATTING_STYLES = ["Right-hand bat", "Left-hand bat"]
BOWLING_STYLES = [
    "Right-arm fast", "Right-arm medium-fast", "Right-arm offbreak",
    "Left-arm fast", "Left-arm medium-fast", "Left-arm orthodox",
    "Legbreak googly", "None"
]

def get_db_connection():
    return psycopg2.connect(**DB)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

@app.context_processor
def inject_user():
    return dict(logged_in=("user_id" in session), username=session.get("username"))

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]

        if not username or not email or not password:
            flash("All fields are required", "danger")
            return redirect(url_for("register"))

        hashed = generate_password_hash(password)
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO app_user (username, email, password_hash)
                VALUES (%s, %s, %s) RETURNING id, username
            """, (username, email, hashed))
            user = cur.fetchone()
            conn.commit()
            session["user_id"] = user[0]
            session["username"] = user[1]
            flash("Registered successfully!", "success")
            return redirect(url_for("players_list"))
        except Exception as e:
            if conn:
                conn.rollback()
            flash(f"Error: {e}", "danger")
        finally:
            if conn:
                conn.close()
    return render_template("auth/register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        input_id = request.form["username_or_email"].strip()
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT id, username, password_hash
            FROM app_user
            WHERE username=%s OR email=%s
        """, (input_id, input_id))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("Login successful", "success")
            return redirect(url_for("players_list"))
        else:
            flash("Invalid login", "danger")
    return render_template("auth/login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for("login"))

@app.route("/players")
@login_required
def players_list():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM team ORDER BY team_id")
    teams = cur.fetchall()
    cur.execute("""
        SELECT p.*, t.name AS team_name
        FROM player p
        JOIN team t ON t.team_id = p.team_id
        ORDER BY p.cap_number
    """)
    players = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("players/list.html", players=players, teams=teams)

@app.route("/players/create", methods=["GET", "POST"])
@login_required
def players_create():
    if request.method == "POST":
        data = request.form
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO player (cap_number, first_name, middle_name, last_name,
                                    batting_style, bowling_style, dob, team_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data["cap_number"], data["first_name"], data.get("middle_name"),
                data["last_name"], data["batting_style"],
                None if data["bowling_style"] == "None" else data["bowling_style"],
                data["dob"], data["team_id"]
            ))
            conn.commit()
            flash("Player created", "success")
            return redirect(url_for("players_list"))
        except Exception as e:
            if conn:
                conn.rollback()
            flash(f"Error: {e}", "danger")
        finally:
            if conn:
                conn.close()

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT team_id, name FROM team ORDER BY name")
    teams = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("players/create.html",
                           teams=teams,
                           batting_styles=BATTING_STYLES,
                           bowling_styles=BOWLING_STYLES)

@app.route("/players/<int:player_id>")
@login_required
def players_detail(player_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""
        SELECT p.*, t.name AS team_name
        FROM player p
        JOIN team t ON t.team_id = p.team_id
        WHERE p.player_id = %s
    """, (player_id,))
    player = cur.fetchone()
    if player is None:
        cur.close()
        conn.close()
        return "Player not found", 404

    cur.execute("""
        SELECT 
            COUNT(DISTINCT matchid) AS total_matches,
            COALESCE(SUM(runs), 0) AS total_runs,
            COALESCE(SUM(wickets), 0) AS total_wickets,
            ROUND(AVG(avg)::numeric, 2) AS average,
            ROUND(AVG(strike_rate)::numeric, 2) AS strike_rate
        FROM records
        WHERE player_id = %s
    """, (player_id,))
    r = cur.fetchone()
    stats = {
        "total_matches": r["total_matches"] or 0,
        "total_runs": r["total_runs"] or 0,
        "total_wickets": r["total_wickets"] or 0,
        "avg_bat": float(r["average"]) if r["average"] is not None else 0.0,
        "avg_sr": float(r["strike_rate"]) if r["strike_rate"] is not None else 0.0,
        "strike_rate": float(r["strike_rate"]) if r["strike_rate"] is not None else 0.0
    }

    cur.execute("""
       SELECT
        COALESCE(SUM(no_of_mom), 0) AS mom,
        COALESCE(SUM(no_of_pos), 0) AS pos,
        COALESCE(SUM(worldcups_won), 0) AS wc
        FROM awards
        WHERE player_id = %s
    """, (player_id,))
    a = cur.fetchone()
    awards = dict(mom=a["mom"], pos=a["pos"], wc=a["wc"])

    cur.execute("""
        SELECT id, matchid, team_id, runs, avg, strike_rate, wickets
        FROM records
        WHERE player_id = %s
        ORDER BY matchid DESC
    """, (player_id,))
    match_records = cur.fetchall()

    cur.execute("""
        SELECT injury_id, injurydate, injurymatch, injurytype, recovery_time
        FROM record_of_injuries
        WHERE player_id = %s
        ORDER BY injurydate DESC
    """, (player_id,))
    injuries = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("players/detail.html",
                           player=player,
                           stats=stats,
                           awards=awards,
                           match_records=match_records,
                           injuries=injuries)

@app.route("/players/<int:player_id>/delete", methods=["POST"])
@login_required
def players_delete(player_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM player WHERE player_id = %s", (player_id,))
    conn.commit()
    cur.close()
    conn.close()
    flash("Player deleted successfully.")
    return redirect(url_for("players_list"))

@app.route("/records/create", methods=["GET", "POST"])
@login_required
def records_create():
    if request.method == "POST":
        d = request.form
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO records (player_id, matchid, team_id, runs, avg, strike_rate, wickets)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (player_id, matchid)
                DO UPDATE SET
                    team_id = EXCLUDED.team_id,
                    runs = EXCLUDED.runs,
                    avg = EXCLUDED.avg,
                    strike_rate = EXCLUDED.strike_rate,
                    wickets = EXCLUDED.wickets
            """, (
                d["player_id"], d["matchid"], d["team_id"],
                d.get("runs") or 0,
                d.get("avg") or 0.0,
                d.get("strike_rate") or 0.0,
                d.get("wickets") or 0
            ))
            conn.commit()
            flash("Record saved/updated!", "success")
            return redirect(url_for("players_detail", player_id=d["player_id"]))
        except Exception as e:
            if conn:
                conn.rollback()
            flash(f"Error: {e}", "danger")
        finally:
            if conn:
                conn.close()

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT player_id, cap_number, first_name, last_name FROM player ORDER BY cap_number;")
    players = cur.fetchall()
    cur.execute("SELECT team_id, name FROM team ORDER BY name;")
    teams = cur.fetchall()
    cur.close()
    conn.close()

    preselect = request.args.get("player_id", type=int)
    return render_template("records/create.html", players=players, teams=teams, preselect=preselect)

@app.route("/awards/create", methods=["GET", "POST"])
@login_required
def awards_create():
    if request.method == "POST":
        d = request.form
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO awards (player_id, no_of_mom, no_of_pos, worldcups_won)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (player_id)
                DO UPDATE SET
                    no_of_mom = EXCLUDED.no_of_mom,
                    no_of_pos = EXCLUDED.no_of_pos,
                    worldcups_won = EXCLUDED.worldcups_won
            """, (
                d["player_id"], d.get("no_of_mom") or 0,
                d.get("no_of_pos") or 0, d.get("worldcups_won") or 0
            ))
            conn.commit()
            flash("Awards updated!", "success")
            return redirect(url_for("players_detail", player_id=d["player_id"]))
        except Exception as e:
            if conn:
                conn.rollback()
            flash(f"Error: {e}", "danger")
        finally:
            if conn:
                conn.close()

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT player_id, cap_number, first_name, last_name FROM player ORDER BY cap_number;")
    players = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("awards/create.html", players=players)


@app.route("/injuries/create", methods=["GET", "POST"])
@login_required
def injuries_create():
    if request.method == "POST":
        d = request.form
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO record_of_injuries (player_id, injurydate, injurymatch, injurytype, recovery_time)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                d["player_id"], d["injurydate"],
                d.get("injurymatch"), d.get("injurytype"), d.get("recovery_time")
            ))
            conn.commit()
            flash("Injury record saved!", "success")
            return redirect(url_for("players_detail", player_id=d["player_id"]))
        except Exception as e:
            if conn:
                conn.rollback()
            flash(f"Error: {e}", "danger")
        finally:
            if conn:
                conn.close()

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT player_id, cap_number, first_name, last_name FROM player ORDER BY cap_number;")
    players = cur.fetchall()
    cur.close()
    conn.close()

    preselect = request.args.get("player_id", type=int)
    return render_template("injuries/create.html", players=players, preselect=preselect)

@app.route("/teams")
@login_required
def teams_list():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM team ORDER BY team_id")
    teams = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("teams/list.html", teams=teams)

@app.route("/teams/create", methods=["GET", "POST"])
@login_required
def teams_create():
    if request.method == "POST":
        name = request.form.get("name")
        sponsor_id = request.form.get("sponsor_id")
        captain = request.form.get("captain")
        coach_id = request.form.get("coach_id")
        odi_ranking = request.form.get("odi_ranking") or None
        t20i_ranking = request.form.get("t20i_ranking") or None
        test_ranking = request.form.get("test_ranking") or None

        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO team
                    (name, sponsor_id, captain, coach_id, odi_ranking, t20i_ranking, test_ranking)
                VALUES
                    (%s,   %s,         %s,      %s,       %s,          %s,            %s)
            """, (name, sponsor_id, captain, coach_id, odi_ranking, t20i_ranking, test_ranking))
            conn.commit()
            flash("Team created successfully", "success")
            return redirect(url_for("teams_list"))
        except Exception as e:
            if conn:
                conn.rollback()
            flash(f"Error: {e}", "danger")
            return redirect(url_for("teams_create"))
        finally:
            if conn:
                conn.close()

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT coach_id, name FROM coach ORDER BY name;")
    coaches = cur.fetchall()
    cur.execute("SELECT sponsor_id, name FROM sponsor ORDER BY name;")
    sponsors = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("teams/create.html", coaches=coaches, sponsors=sponsors)

@app.route("/api/players")
def api_players():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT p.*, t.name AS team_name
        FROM player p
        JOIN team t ON t.team_id = p.team_id
    """)
    players = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([dict(p) for p in players])

if __name__ == "__main__":
    app.run(debug=True)
