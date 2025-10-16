ALTER DATABASE "liip-abnahme-new" OWNER TO "liip-abnahme";
  

\c liip-abnahme-new

CREATE EXTENSION postgis;

CREATE EXTENSION postgis_topology;

GRANT USAGE ON SCHEMA topology TO "liip-abnahme";

GRANT SELECT ON ALL TABLES IN SCHEMA topology TO "liip-abnahme";

GRANT USAGE ON SCHEMA tiger TO "liip-abnahme";

GRANT SELECT ON ALL TABLES IN SCHEMA tiger TO "liip-abnahme";

GRANT USAGE ON SCHEMA tiger_data TO "liip-abnahme

GRANT SELECT ON ALL TABLES IN SCHEMA tiger_data TO "liip-abnahme";