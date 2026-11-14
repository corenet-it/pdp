-- Upgrade a PostgreSQL volume created before P09.
-- This intentionally fails while overlapping Confirmed rows exist: those rows
-- need a business decision (usually cancelling one booking) before the rule can
-- be enforced.
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE SEQUENCE IF NOT EXISTS reservation_ids START 101;

SELECT setval(
    'reservation_ids',
    GREATEST(
        101,
        COALESCE((SELECT max(substring(id FROM 2)::bigint)
                  FROM reservations WHERE id ~ '^R[0-9]+$'), 100) + 1,
        (SELECT last_value + CASE WHEN is_called THEN 1 ELSE 0 END
         FROM reservation_ids)
    ),
    false
);

DO $migration$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'reservations_no_overlap'
    ) THEN
        ALTER TABLE reservations
            ADD CONSTRAINT reservations_no_overlap
            EXCLUDE USING gist (
                room_number WITH =,
                daterange(check_in, check_out, '[)') WITH &&
            ) WHERE (status = 'Confirmed');
    END IF;
END
$migration$;
