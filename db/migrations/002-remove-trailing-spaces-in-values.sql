-- Remove trailing spaces in values
-- depends: 000-init-db

UPDATE folksonomy SET v = TRIM(v), version=version+1 WHERE v LIKE '% ' OR v LIKE ' %';
