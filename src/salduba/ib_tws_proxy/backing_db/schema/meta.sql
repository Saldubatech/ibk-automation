create table if not exists db_info (
  version integer primary key,
  version_time bigint,
  at integer not NULL,
  current BOOLEAN not NULL
);
