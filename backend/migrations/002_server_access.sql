-- Ejecutar con administración después de provisionar expensa_server fuera del repositorio.
-- No se incluye contraseña. El rol debe ser LOGIN, NOSUPERUSER, NOCREATEDB, NOCREATEROLE.
GRANT CONNECT ON DATABASE postgres TO expensa_server;
GRANT USAGE ON SCHEMA expensa TO expensa_server;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA expensa TO expensa_server;
DO $$
DECLARE t record;
BEGIN
  FOR t IN SELECT tablename FROM pg_tables WHERE schemaname='expensa' LOOP
    IF NOT EXISTS (SELECT FROM pg_policies WHERE schemaname='expensa'
                   AND tablename=t.tablename AND policyname='server_access') THEN
      EXECUTE format('CREATE POLICY server_access ON expensa.%I TO expensa_server USING (true) WITH CHECK (true)',t.tablename);
    END IF;
  END LOOP;
END $$;
