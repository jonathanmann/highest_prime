create or replace procedure reduce_max_cap(x int)
language plpgsql    
as $$
begin 
    delete from primes where num > x;
    commit;
end; $$

create or replace procedure add_valid_prime(x int)
language plpgsql    
as $$
begin 
    insert into primes values (x);
    commit;
end; 
$$


