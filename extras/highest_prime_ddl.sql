BEGIN TRANSACTION;

--SQLITE TABLES (9)
CREATE TABLE game_type(name varchar(255) PRIMARY KEY,description varchar(255),time_limit int);
CREATE TABLE game(name varchar(255) PRIMARY KEY,players int, cap int,game_type_name varchar(255), FOREIGN KEY(game_type_name) REFERENCES game_type(name));
CREATE TABLE game_queue(game_name varchar(255),player_name varchar(255),FOREIGN KEY(game_name) REFERENCES game(name),FOREIGN KEY(player_name) REFERENCES player(name));
CREATE TABLE guess(game_name varchar(255), player_name varchar(255),prime_guess int,is_prime int,FOREIGN KEY(game_name) REFERENCES game(name),FOREIGN KEY(player_name) REFERENCES player(name));
CREATE TABLE rank(name varchar(255) PRIMARY KEY, min_wins int);
CREATE TABLE tournament(name varchar(255) PRIMARY KEY, description varchar(255), team_limit int);
CREATE TABLE team(name varchar(255) PRIMARY KEY, description varchar(255), members int,tournament_name varchar(255), FOREIGN KEY (tournament_name) REFERENCES tournament(name));
CREATE TABLE player(name varchar(255) PRIMARY KEY,profile_image varchar(255),rank_name varchar(255),wins int,team_name varchar(255), FOREIGN KEY (rank_name) REFERENCES rank(name), FOREIGN KEY (team_name) REFERENCES team(name));
CREATE TABLE primes(num int);

--SQLITE VIEWS (2)
CREATE VIEW game_detail_v as select g.name as game_name, gt.name as game_type, p.name as player, u.prime_guess as guess, u.is_prime, gt.time_limit
    from game g inner join game_queue q on g.name = q.game_name
    inner join player p on q.player_name = p.name
    inner join game_type gt on gt.name = g.game_type_name
    inner join guess u on u.game_name = g.name;
CREATE VIEW tournament_detail_v as
    select tr.name tournament,t.name team, rank_name  from tournament tr
    inner join team t on t.tournament_name = tr.name
    inner join player p on p.team_name = t.name;

--SQLITE TRIGGERS (2)
CREATE TRIGGER update_player_rank
   AFTER UPDATE ON player
   WHEN old.wins < new.wins
   BEGIN
   	UPDATE player set rank_name = (select name from rank where min_wins <= new.wins order by min_wins desc limit 1) where new.name = old.name;
   END;
CREATE TRIGGER update_team_count
   AFTER INSERT ON player
   BEGIN
   	UPDATE team set members = (select members from team where name = new.team_name) + 1 where name = new.team_name;
   END;
COMMIT;

--POSTGRES PROCEDURES (2)
CREATE OR REPLACE PROCEDURE reduce_max_cap(x int)
language plpgsql    
as $$
begin 
    delete from primes where num > x;
    commit;
end; $$

CREATE OR REPLACE PROCEDURE add_valid_prime(x int)
language plpgsql    
as $$
begin 
    insert into primes values (x);
    commit;
end; 
$$

--POSTGRES FUNCTIONS (2)
CREATE FUNCTION valid_prime(val integer) RETURNS bool AS $$
BEGIN
RETURN (select count(num) from primes where num = val) > 0;
END; $$
LANGUAGE PLPGSQL;

CREATE FUNCTION valid_cap(val integer) RETURNS bool AS $$
BEGIN
RETURN val < 5001;
END; $$
LANGUAGE PLPGSQL;
