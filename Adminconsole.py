from flask import Flask, render_template, request, g
import psycopg2

app = Flask(__name__)

def get_db():
    if 'db' not in g:
        g.db = psycopg2.connect(
            dbname="jeu_loup",
            user="postgres",
            password="mysecretpassword",
            host="10.1.4.227",
            port="5434"
        )
    return g.db

def insert_data(nbr_ligne, nbr_col, wait_time, nbr_tour, nbr_obstacle, nbr_player):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO settings_parties (nbr_ligne, nbr_col, wait_time, nbr_tour, nbr_obstacle, nbr_player) VALUES ({nbr_ligne}, {nbr_col}, {wait_time}, {nbr_tour}, {nbr_obstacle}, {nbr_player})")
    conn.commit()
    cursor.close()

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

@app.route('/', methods=['GET', 'POST'])
def new_game():
    nbr_ligne = request.form.get("nbr_ligne")
    nbr_col = request.form.get("nbr_column")
    wait_time = request.form.get("tps_wait_for_turn")
    nbr_tour = request.form.get("nbr_tour")
    nbr_obstacle = request.form.get("nbr_obstacle")
    nbr_player = request.form.get("nbr_player")
    if nbr_ligne != None and nbr_col != None and wait_time != None and nbr_tour != None and nbr_obstacle != None and nbr_player != None:
        insert_data(nbr_ligne, nbr_col, wait_time, nbr_tour, nbr_obstacle, nbr_player)
        return render_template("new_game.html")
    else:
        return render_template("new_game.html")


app.run(debug=True)