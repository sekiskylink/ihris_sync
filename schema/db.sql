-- intrahealth Tables, Samuel Sekiwere, 2016-10-23
-- remeber to add indexes
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION "uuid-ossp";
CREATE EXTENSION plpythonu;
CREATE EXTENSION hstore;

-- webpy sessions
CREATE TABLE sessions (
    session_id CHAR(128) UNIQUE NOT NULL,
    atime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data TEXT
);

CREATE TABLE user_roles (
    id SERIAL NOT NULL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    descr text DEFAULT '',
    cdate TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX user_roles_idx1 ON user_roles(name);

CREATE TABLE user_role_permissions (
    id SERIAL NOT NULL PRIMARY KEY,
    user_role INTEGER NOT NULL REFERENCES user_roles ON DELETE CASCADE ON UPDATE CASCADE,
    Sys_module TEXT NOT NULL, -- the name of the module - defined above this level
    sys_perms VARCHAR(16) NOT NULL,
    unique(sys_module,user_role)
);

CREATE TABLE users (
    id bigserial NOT NULL PRIMARY KEY,
    user_role  INTEGER NOT NULL REFERENCES user_roles ON DELETE RESTRICT ON UPDATE CASCADE, --(call agents, admin, service providers)
    firstname TEXT NOT NULL DEFAULT '',
    lastname TEXT NOT NULL DEFAULT '',
    username TEXT NOT NULL UNIQUE,
    telephone TEXT NOT NULL UNIQUE, -- acts as the username
    password TEXT NOT NULL, -- blowfish hash of password
    email TEXT NOT NULL DEFAULT '',
    allowed_ips TEXT NOT NULL DEFAULT '127.0.0.1;::1', -- semi-colon separated list of allowed ip masks
    denied_ips TEXT NOT NULL DEFAULT '', -- semi-colon separated list of denied ip masks
    failed_attempts TEXT DEFAULT '0/'||to_char(now(),'yyyymmdd'),
    transaction_limit TEXT DEFAULT '0/'||to_char(now(),'yyyymmdd'),
    is_active BOOLEAN NOT NULL DEFAULT 't',
    is_system_user BOOLEAN NOT NULL DEFAULT 'f',
    last_login TIMESTAMPTZ,
    last_passwd_update TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX users_idx1 ON users(telephone);
CREATE INDEX users_idx2 ON users(username);

CREATE OR REPLACE FUNCTION public.get_user_name(userid bigint)
 RETURNS text
 LANGUAGE plpgsql
AS $function$
    DECLARE
        xname TEXT;
    BEGIN
        SELECT INTO xname username FROM users WHERE id = userid;
        IF xname IS NULL THEN
            RETURN '';
        END IF;
        RETURN xname;
    END;
$function$;

CREATE TABLE audit_log (
        id BIGSERIAL NOT NULL PRIMARY KEY,
        logtype VARCHAR(32) NOT NULL DEFAULT '',
        actor TEXT NOT NULL,
        action text NOT NULL DEFAULT '',
        remote_ip INET,
        detail TEXT NOT NULL,
        created_by INTEGER REFERENCES users(id), -- like actor id
        created TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX au_idx1 ON audit_log(created);
CREATE INDEX au_idx2 ON audit_log(logtype);
CREATE INDEX au_idx4 ON audit_log(action);


-- used for scheduling messages
CREATE TABLE schedules(
    id SERIAL PRIMARY KEY NOT NULL,
    type TEXT NOT NULL DEFAULT 'sms', -- also 'push_contact'
    params JSON NOT NULL DEFAULT '{}'::json,
    run_time TIMESTAMP NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL DEFAULT 'ready',
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    created TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX schedules_idx ON schedules(run_time);
CREATE INDEX schedules_idx1 ON schedules(type);
CREATE INDEX schedules_idx2 ON schedules(status);

INSERT INTO user_roles(name, descr)
VALUES('Administrator','For the Administrators'), ('Basic', 'For the basic users'), ('Warehouse Manager', 'The warehouse manager');

INSERT INTO user_role_permissions(user_role, sys_module,sys_perms)
VALUES
        ((SELECT id FROM user_roles WHERE name ='Administrator'),'Users','rw');

INSERT INTO users(firstname,lastname,username,telephone,password,email,user_role,is_system_user)
VALUES
        ('Samuel','Sekiwere','admin', '+256782820208', crypt('admin',gen_salt('bf')),'sekiskylink@gmail.com',
        (SELECT id FROM user_roles WHERE name ='Administrator'),'t'),
        ('Guest','User','guest', '+256753475676', crypt('guest',gen_salt('bf')),'sekiskylink@gmail.com',
        (SELECT id FROM user_roles WHERE name ='Basic'),'t'),
        ('Ivan','Muguya','ivan', '+256756253430', crypt('ivan',gen_salt('bf')),'sekiskylink@gmail.com',
        (SELECT id FROM user_roles WHERE name ='Warehouse Manager'),'f');


CREATE TABLE healthprovider_types(
    id SERIAL PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,
    created TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE healthproviders(
    id SERIAL PRIMARY KEY NOT NULL,
    ihrisid TEXT NOT NULL,
    firstname TEXT NOT NULL DEFAULT '',
    lastname TEXT NOT NULL DEFAULT '',
    commonname TEXT NOT NULL DEFAULT '',
    telephone TEXT NOT NULL DEFAULT '',
    alt_tel TEXT NOT NULL DEFAULT '',
    other_tel TEXT NOT NULL DEFAULT '',
    gender VARCHAR(2) NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    alt_email TEXT NOT NULL DEFAULT '',
    facilityid TEXT NOT NULL DEFAULT '',
    role INTEGER REFERENCES healthprovider_types(id),
    registration_number TEXT DEFAULT '',
    registration_date DATE,
    license_number TEXT DEFAULT '',
    license_date DATE,
    license_renewal DATE,
    created TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX healthproviders_idx1 ON healthproviders(ihrisid);
CREATE INDEX healthproviders_idx2 ON healthproviders(firstname);
CREATE INDEX healthproviders_idx3 ON healthproviders(lastname);
CREATE INDEX healthproviders_idx4 ON healthproviders(commonname);
CREATE INDEX healthproviders_idx5 ON healthproviders(telephone);
CREATE INDEX healthproviders_idx6 ON healthproviders(gender);
CREATE INDEX healthproviders_idx7 ON healthproviders(role);

DROP VIEW IF EXISTS healthproviders_view;
CREATE VIEW healthproviders_view AS
    SELECT a.firstname || ' ' || a.lastname as name,
        a.commonname, a.telephone, a.alt_tel, a.other_tel, a.email,
        a.alt_email, a.gender, a.facilityid, a.registration_number,
        a.registration_date, a.license_number, a.license_date, a.license_renewal,
        b.name as cadre
    FROM healthproviders a, healthprovider_types b
    WHERE a.role = b.id;
