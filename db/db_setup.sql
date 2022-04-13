
-- folksonomy main table, with public/private partitionning
CREATE TABLE folksonomy (
    product     varchar(24)   NOT NULL,
    k           varchar       NOT NULL,
    v           varchar       NOT NULL,
    owner       varchar       NOT NULL,
    version     integer       NOT NULL,
    editor      varchar       NOT NULL,
    last_edit   timestamp,
    comment     varchar(200)
) PARTITION BY LIST (owner);

-- public partition
CREATE TABLE folksonomy_public PARTITION OF folksonomy 
    FOR VALUES IN ('');

-- private partition
CREATE TABLE folksonomy_private PARTITION OF folksonomy 
    DEFAULT;

-- automatic timestamp + version check
CREATE OR REPLACE FUNCTION folksonomy_timestamp() RETURNS trigger AS $folksonomy_timestamp$
    BEGIN
        -- check version number validity
        IF (TG_OP = 'INSERT') AND (NEW.version != 1)
        THEN
            RAISE EXCEPTION '@@ first version must be equal to 1, was % @@', NEW.version;
        END IF;
        IF (TG_OP = 'UPDATE')
            AND (NEW.version != OLD.version+1)
            AND (NEW.version != 0)
        THEN
            RAISE EXCEPTION '@@ next version must be equal to %, was % @@', OLD.version+1, NEW.version;
        END IF;
        -- set last_edit timestamp ourself
        NEW.last_edit := current_timestamp AT TIME ZONE 'GMT';
        RETURN NEW;
    END;
$folksonomy_timestamp$ LANGUAGE plpgsql;
CREATE TRIGGER folksonomy_autotimestamp BEFORE INSERT OR UPDATE on folksonomy
    FOR EACH ROW EXECUTE FUNCTION folksonomy_timestamp();

-- index for unicity + search by product[owner[key]]
CREATE UNIQUE INDEX ON folksonomy  (product,owner,k);
-- index to search by owner[key[value]]
CREATE INDEX ON folksonomy_public  (k,v);
CREATE INDEX ON folksonomy_private (owner,k,v);



-- folksonomy versionned table
CREATE TABLE folksonomy_versions (
    product     varchar(24)   NOT NULL,
    k           varchar       NOT NULL,
    v           varchar       NOT NULL,
    owner       varchar       NOT NULL,
    version     integer       NOT NULL,
    editor      varchar       NOT NULL,
    last_edit   timestamp,
    comment     varchar(200)
);

CREATE INDEX ON folksonomy_versions (product,owner,k);

-- trigger based versionning
CREATE OR REPLACE FUNCTION folksonomy_archive() RETURNS trigger AS $folksonomy_archive$
    BEGIN
        INSERT INTO folksonomy_versions SELECT NEW.*;
        RETURN NULL;
    END;
$folksonomy_archive$ LANGUAGE plpgsql;
CREATE TRIGGER folksonomy_versionning AFTER INSERT OR UPDATE on folksonomy
    FOR EACH ROW EXECUTE FUNCTION folksonomy_archive();


-- authentication table
CREATE TABLE auth (token varchar, user_id varchar, last_use timestamp);
CREATE INDEX ON auth (token);
