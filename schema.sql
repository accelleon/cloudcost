create table if not exists iaas(
    id serial primary key,
    name text unique
);

create table if not exists accounts(
    id serial primary key,
    iaas_id int,
    name text,
    cred json,
    orderi int,
    constraint iaas_unique unique(iaas_id, name),
    constraint iaas_fk foreign key(iaas_id) references iaas(id)
);

create or replace function create_iaas(
    iaas_var text
) returns void as $$
begin
    insert into iaas (name) values (iaas_var);
end;
$$ language plpgsql;

create or replace function get_iaas() returns text[] as $$
begin
    return array(
        select name from iaas
    );
end;
$$ language plpgsql;

create or replace function create_account(
    iaas_var text,
    name_var text,
    cred_var json,
    protect_var bool default false
) returns void as $$
declare
    iaas_id_var integer;
begin
    select get_iaas_id(iaas_var) into iaas_id_var;
    if iaas_id_var is null then
        raise exception 'Provider %s does not exist', iaas_var;
    end if;

    if (select count(*) = 0 from accounts where iaas_id = iaas_id_var and name = name_var)
        and not protect_var then
            raise exception 'Account % does not exist in provider %', name_var, iaas_var;
    end if;

    begin
        insert into accounts (iaas_id, name, cred) values (
            get_iaas_id(iaas_var),
            name_var,
            cred_var
        );
    exception when unique_violation then
        if protect_var then
            raise exception 'Account % already exists in provider %', name_var, iaas_var;
        end if;
        update accounts set cred = cred_var where iaas_id = get_iaas_id(iaas_var) and name = name_var;
    end;
end;
$$ language plpgsql;

create or replace function delete_account(
    iaas_var text,
    name_var text
) returns void as $$
begin
    if (select count(*)=0 from accounts where iaas_id=get_iaas_id(iaas_var) and name=name_var) then
        raise exception 'Account does not exist';
    end if;
    delete from accounts where iaas_id=get_iaas_id(iaas_var) and name=name_var;
end;
$$ language plpgsql;

create or replace function get_iaas_id(name_var text) returns int as $$ 
begin
    return (
        select id from iaas where name=name_var
    );
end;
$$ language plpgsql;

create or replace function get_iaas_name(id_var int) returns text as $$
begin
    return (
        select name from iaas where id=id_var
    );
end;
$$ language plpgsql;

create or replace function get_accounts(iaas_var text[] default null) returns table(
    iaas text,
    name text,
    cred json
) as $$
declare i text;
begin
    if iaas_var is not null then
        foreach i in array iaas_var loop
            if get_iaas_id(i) is null then
                raise exception 'Invalid provider given %', i;
            end if;
        end loop;
    end if;

    return query (
        select
            i.name,
            a.name,
            a.cred
        from accounts as a
        left join iaas as i
        on a.iaas_id = i.id
        where (iaas_var is null or i.name = any(iaas_var))
        order by a.orderi ASC
    );
end;
$$ language plpgsql;

create or replace function set_order(
    iaas_var text,
    name_var text,
    order_var integer
) returns void as $$
declare
iaas_id_var integer;
begin
    select get_iaas_id(iaas_var) into iaas_id_var;
    if iaas_id_var is null then
        raise exception '% is not a valid provider', iaas_var;
    end if;

    if (select count(*) = 0 from accounts where iaas_id = iaas_id_var and name = name_var) then
        raise exception '% is not a valid account in provider %', name_var, iaas_var;
    end if;

    update accounts set orderi = (orderi+1) where orderi >= order_var;

    update accounts set orderi = order_var where iaas_id = iaas_id_var and name = name_var;
end;
$$ language plpgsql;