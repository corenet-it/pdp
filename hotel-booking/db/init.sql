-- P09: GiST can compare the room text with equality and the stay as a range.
CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TABLE IF NOT EXISTS rooms (
    number text PRIMARY KEY,
    type text NOT NULL
);

CREATE TABLE IF NOT EXISTS reservations (
    id text PRIMARY KEY,
    guest_name text NOT NULL,
    guest_email text NOT NULL,
    room_number text NOT NULL REFERENCES rooms(number),
    check_in date NOT NULL,
    check_out date NOT NULL,
    status text NOT NULL CHECK (status IN ('Confirmed', 'Cancelled')),
    CHECK (check_out > check_in),
    CONSTRAINT reservations_no_overlap EXCLUDE USING gist (
        room_number WITH =,
        daterange(check_in, check_out, '[)') WITH &&
    ) WHERE (status = 'Confirmed')
);

-- Sequence ids remain unique even when two requests allocate them together.
CREATE SEQUENCE IF NOT EXISTS reservation_ids START 101;

-- Keep an existing database's sequence above all R<number> ids. On a new
-- database this leaves the first value at R101.
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

INSERT INTO rooms (number, type) VALUES ('R7', 'Standard'), ('R8', 'Deluxe')
ON CONFLICT (number) DO NOTHING;
