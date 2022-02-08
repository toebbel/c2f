DROP TABLE IF EXISTS recordings;
DROP TABLE IF EXISTS call_events;

CREATE TABLE call_events(
    call_id STRING NOT NULL,
    owner_number STRING NOT NULL,
    observed_at TIMESTAMP NOT  NULL DEFAULT CURRENT_TIMESTAMP,
    event_type STRING NOT NULL,
    payload STRING
);

CREATE TABLE recordings(
    call_id STRING PRIMARY KEY,
    owner_number STRING NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    storage_blob_id STRING NOT NULL,
    scheduled_for TIMESTAMP -- null as long as customer has not scheduled it
);