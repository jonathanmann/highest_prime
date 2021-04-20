#!/usr/bin/env python
import sqlite3
from flask import Flask,g,jsonify,render_template
from flask_cors import CORS
from static import *
import random

app = Flask(__name__)
CORS(app)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def exec_stmt(sql,args={}):
    try:
        db = get_db()
        cur = db.cursor()
        cur.execute(sql,args)
        db.commit()
        cur.close()
        return '{"success":"true"}'
    except:
        return '{"success":"false"}'

def run_query(sql,args={}):
    db = get_db()
    cur = db.cursor()
    cur.execute(sql,args)
    r = cur.fetchall()
    cur.close()
    return r

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/',strict_slashes=False)
def index():
    return render_template('index.html') 

@app.route('/reset',strict_slashes=False)
def reset_db():

    exec_stmt("drop table game_type;")
    exec_stmt("create table game_type(name varchar(255) PRIMARY KEY,description varchar(255),time_limit int);")
    exec_stmt("insert into game_type values('standard','guess before time runs out', 45);")

    exec_stmt("drop table game;")
    exec_stmt("create table game(name varchar(255) PRIMARY KEY,players int, cap int,game_type_name varchar(255), FOREIGN KEY(game_type_name) REFERENCES game_type(name));")

    exec_stmt("drop table game_queue;")
    exec_stmt("create table game_queue(game_name varchar(255),player_name varchar(255),FOREIGN KEY(game_name) REFERENCES game(name),FOREIGN KEY(player_name) REFERENCES player(name));")

    exec_stmt("drop table guess;")
    exec_stmt("create table guess(game_name varchar(255), player_name varchar(255),prime_guess int,is_prime int,FOREIGN KEY(game_name) REFERENCES game(name),FOREIGN KEY(player_name) REFERENCES player(name));")


    exec_stmt("drop table rank;")
    exec_stmt("create table rank(name varchar(255) PRIMARY KEY, min_wins int);")
    exec_stmt("insert into rank values('n00b',0);")
    exec_stmt("insert into rank values('0k',10);")
    exec_stmt("insert into rank values('1337',25);")

    exec_stmt("drop table tournament;")
    exec_stmt("create table tournament(name varchar(255) PRIMARY KEY, description varchar(255), team_limit int);")
    exec_stmt("insert into tournament values('T1','simple tournament',5);")

    exec_stmt("drop table team;")
    exec_stmt("create table team(name varchar(255) PRIMARY KEY, description varchar(255), members int,tournament_name varchar(255), FOREIGN KEY (tournament_name) REFERENCES tournament(name));")
    exec_stmt("insert into team values('NYU','only team playing',0,'T1');")
    #exec_stmt("create table team(name varchar(255) PRIMARY KEY, description varchar(255), members int,tournament_name varchar(255));")
    #exec_stmt("insert into team values('NYU','only team playing',0);")


    exec_stmt("drop table player;")
    exec_stmt("create table player(name varchar(255) PRIMARY KEY,profile_image varchar(255),rank_name varchar(255),wins int,team_name varchar(255), FOREIGN KEY (rank_name) REFERENCES rank(name), FOREIGN KEY (team_name) REFERENCES team(name));")

    #exec_stmt("drop table score;")
    #exec_stmt("create table score(player_name varchar(255), wins int,FOREIGN KEY(player_name) REFERENCES player(name));")

    exec_stmt("drop table primes;")
    exec_stmt("create table primes(num int);")
    for n in primes:
        exec_stmt("insert into primes values(:num);",{"num":n})
    
    exec_stmt("drop view game_detail_v;")

    game_view_create_script = """
    create view game_detail_v as select g.name as game_name, gt.name as game_type, p.name as player, u.prime_guess as guess, u.is_prime, gt.time_limit
    from game g inner join game_queue q on g.name = q.game_name
    inner join player p on q.player_name = p.name
    inner join game_type gt on gt.name = g.game_type_name
    inner join guess u on u.game_name = g.name;
    """
    exec_stmt(game_view_create_script)

    exec_stmt("drop view tournament_detail_v;")
    tournament_view_create_script = """
    create view tournament_detail_v as
    select tr.name tournament,t.name team, rank_name  from tournament tr
    inner join team t on t.tournament_name = tr.name
    inner join player p on p.team_name = t.name;
    """
    exec_stmt(tournament_view_create_script)

    
    exec_stmt("drop TRIGGER update_player_rank;")
    rank_trigger_create_script = """
    CREATE TRIGGER update_player_rank
   AFTER UPDATE ON player
   WHEN old.wins < new.wins
   BEGIN
   	UPDATE player set rank_name = (select name from rank where min_wins <= new.wins order by min_wins desc limit 1) where new.name = old.name;
   END;
    """
    exec_stmt(rank_trigger_create_script)

    exec_stmt("drop TRIGGER update_team_count;")
    teams_trigger_create_script = """
    CREATE TRIGGER update_team_count
   AFTER UPDATE ON player
   WHEN new.team_name <> old.team_name
   BEGIN
   	UPDATE team set members = (select members from team where name = new.team_name) + 1 where name = new.team_name;
   	UPDATE team set members = (select members from team where name = new.team_name) - 1 where name = old.team_name;
   END;
    """
    teams_trigger_create_script = """
    CREATE TRIGGER update_team_count
   AFTER INSERT ON player
   BEGIN
   	UPDATE team set members = (select members from team where name = new.team_name) + 1 where name = new.team_name;
   END;
    """
    exec_stmt(teams_trigger_create_script)


    """
    exec_stmt("insert into game values('game1',2,500);")
    exec_stmt("insert into game_queue values('game1','dude7');")
    exec_stmt("insert into game values('game2',3,1500);")
    exec_stmt("insert into game_queue values('game2','dude4');")
    exec_stmt("insert into game_queue values('game2','dude5');")
    exec_stmt("insert into game_queue values('game2','dude6');")
    """
    return '{"success":"true"}'

@app.route('/list_games',strict_slashes=False)
def list_games():
    r = run_query("select name from game;")
    d = {x[0]:'x' for x in r}
    return jsonify(d)

@app.route('/list_players/<string:game_name>',strict_slashes=False)
def list_players(game_name):
    r = run_query("select player_name from game_queue where game_name = :game_name;",{"game_name":game_name})
    d = {x[0]:'x' for x in r}
    return jsonify(d)

@app.route('/play/<string:game_name>/<string:player>',strict_slashes=False)
def play(game_name,player):
    d = run_query("select cap,players from game where name = :game_name;",{"game_name":game_name})[0]
    cap = d[0]
    player_min = d[1]
    exec_stmt("insert into game_queue (game_name,player_name) values(:game_name,:player);",{"game_name":game_name,"player":player})
    return render_template('play.html',nm=game_name,pl=player,cp=cap,pm=player_min) 

@app.route('/generic_update/<string:table_name>/<string:search_column_name>/<string:search_column_val>/<string:update_column_name>/<string:update_column_val>',strict_slashes=False)
def generic_update(table_name,search_column_name,search_column_val,update_column_name,update_column_val):
    #UNSAFE REMOVE AFTER ASSINGMENT
    return exec_stmt("update " + table_name + " set " + update_column_name + " = :update_column_val where " + search_column_name + " = :search_column_val;",{"update_column_val":update_column_val,"search_column_val":search_column_val})

@app.route('/generic_delete/<string:table_name>/<string:search_column_name>/<string:search_column_val>',strict_slashes=False)
def generic_delete(table_name,search_column_name,search_column_val):
    #UNSAFE REMOVE AFTER ASSINGMENT
    return exec_stmt("delete from " + table_name + " where " + search_column_name + " = :search_column_val;",{"search_column_val":search_column_val})

@app.route('/start/<string:game_name>',strict_slashes=False)
def start(game_name):
    r = run_query("select (select count(distinct player_name) from game_queue where game_name = :game_name) >= (select players from game where name = :game_name);",{"game_name":game_name})
    d = {"start":x[0] for x in r}
    return jsonify(d)

@app.route('/create/<string:game_name>/<int:players>',strict_slashes=False)
def create(game_name,players):
    cap = random.randint(100,5001)
    return exec_stmt("insert into game values(:game_name,:players,:cap,'standard');",{"game_name":game_name,"players":players,"cap":cap})

@app.route('/guess/<string:game_name>/<string:player>/<int:prime_guess>',strict_slashes=False)
def guess(game_name,player,prime_guess):
    is_prime = 0
    if prime_guess in primes:
        is_prime = 1
    return exec_stmt("insert into guess values(:game_name,:player,:prime_guess,:is_prime);",{"game_name":game_name,"player":player,"prime_guess":prime_guess,"is_prime":is_prime})

@app.route('/results/<string:game_name>',strict_slashes=False)
def results(game_name):
    p = run_query("select players from game where name = :game_name;",{"game_name":game_name})[0][0]
    return render_template('results.html',nm=game_name,pm=p) 

@app.route('/scores/<string:game_name>',strict_slashes=False)
def scores(game_name):
    r = run_query("select player_name,prime_guess,is_prime from guess where game_name = :game_name;",{"game_name":game_name})
    d = {x[0]:{'guess':x[1],'prime':x[2]} for x in r}
    return jsonify(d)

@app.route('/clear/<string:game_name>',strict_slashes=False)
def clear(game_name):
    exec_stmt("delete from game where name= :game_name;",{"game_name":game_name})
    return exec_stmt("delete from guess where game_name= :game_name;",{"game_name":game_name})

@app.route('/register/<string:username>',strict_slashes=False)
def register(username):
    r = exec_stmt("insert into player (name,profile_image,rank_name,wins,team_name) values(:username,'img/default.png','n00b',0,'NYU');",{"username":username})
    return r

@app.route('/cap',strict_slashes=False)
def cap():
    cap = random.randint(100,5001)
    return '{"cap": ' + str(cap) + '}'

@app.route('/player_check',strict_slashes=False)
def player_check():
    r = run_query("select name,rank_name from player;")
    d = {str(x[0]):x[1] for x in r}
    return jsonify(d)

@app.route('/tournament_team_rank_count_report',strict_slashes=False)
def tournament_team_rank_count_report():
    r = run_query("select tournament, team, rank_name, count(rank_name) from tournament_detail_v  group by tournament, team, rank_name;")
    d = {'-'.join([x[0],x[1],x[2]]):x[3] for x in r}
    return jsonify(d)

@app.route('/tournament_rank_count_report',strict_slashes=False)
def tournament_rank_count_report():
    r = run_query("select tournament, rank_name, count(rank_name) from tournament_detail_v  group by tournament, rank_name;")
    d = {'-'.join([x[0],x[1]]):x[2] for x in r}
    return jsonify(d)

@app.route('/max_guess_by_player_report',strict_slashes=False)
def max_guess_by_player_report():
    r = run_query("select player, max(guess) from game_detail_v gdv where is_prime = 1 group by player;")
    d = {str(x[0]):x[1] for x in r}
    return jsonify(d)

