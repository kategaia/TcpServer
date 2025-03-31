from flask import Flask, render_template, request, g
import psycopg2
from random import randint
from Class_plateau import Plateau
from Class_joueur import Joueur


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

def insert_data_plateau(id_plateau, nbr_ligne, nbr_col, nbr_obstacle):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO plateaux (id_plateau, nbr_ligne, nbr_col, nbr_obstacle) VALUES ( {id_plateau}, {nbr_ligne}, {nbr_col}, {nbr_obstacle})")
    conn.commit()
    cursor.close()

def insert_data_obstacle(pos_x, pos_y, id_plat):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO obstacles (pos_x, pos_y, id_plateau) VALUES ({pos_x}, {pos_y}, {id_plat})")
    conn.commit()
    cursor.close()

def get_id_plateau():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(id_plateau) FROM plateaux")
    rows = cursor.fetchall()
    cursor.close()
    return rows[0]

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.route('/', methods=['GET', 'POST'])
def new_game():
    id_plateau = get_id_plateau()
    print(id_plateau)
    if id_plateau[0] == None:
        id_plat = 0
    else:
        id_plat = int(id_plateau[0])
        print(id_plat)
    nbr_ligne = request.form.get("nbr_ligne")
    nbr_col = request.form.get("nbr_column")
    wait_time = request.form.get("tps_wait_for_turn")
    nbr_tour = request.form.get("nbr_tour")
    nbr_obstacle = request.form.get("nbr_obstacle")
    nbr_player = request.form.get("nbr_player")
    nbr_loup = request.form.get("nbr_loup")
    if nbr_ligne != None and nbr_col != None and wait_time != None and nbr_tour != None and nbr_obstacle != None and nbr_player != None and nbr_loup != None:
        plateau = nouveau_jeu(int(nbr_ligne), int(nbr_col), int(nbr_obstacle), int(nbr_player), int(nbr_loup))
        plat = plateau[0]
        id_plat += 1
        insert_data_plateau(id_plat, int(nbr_ligne), int(nbr_col), int(nbr_obstacle))
        obstacle = Plateau.generate_random_obstacles(self=plat)
        for i in range(len(obstacle)):
            insert_data_obstacle(obstacle[i][0], obstacle[i][1], id_plat)
        return render_template("new_game.html")
    else:
        return render_template("new_game.html")

def nouveau_jeu(taille_x, taille_y, nb_obstacle, nb_joueurs, nb_loup):
    print()
    print("----nouveau jeu----")
    plateau = Plateau(taille_x, taille_y, nb_obstacle)
    print(plateau)
    joueurs = []
    for i in range(nb_joueurs):
        x = 0
        y = 0
        while((x,y) in plateau.get_pos_obstacles()):
                x = randint(0, taille_x - 1)
                y = randint(0, taille_y - 1)
        if i <= nb_loup-1:
            joueurs.append(Joueur(i, "loup", x, y, "OK", 0))
        else:
            joueurs.append(Joueur(i, "villageois", x, y, "OK", 0))
        print()
        print("---------------")
        joueurs[i].info_joueur()
    

    return plateau, joueurs

app.run(debug=True)