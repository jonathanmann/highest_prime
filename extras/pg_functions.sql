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
