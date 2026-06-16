-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.django_migrations (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  app character varying NOT NULL,
  name character varying NOT NULL,
  applied timestamp with time zone NOT NULL,
  CONSTRAINT django_migrations_pkey PRIMARY KEY (id)
);
CREATE TABLE public.django_content_type (
  id integer GENERATED ALWAYS AS IDENTITY NOT NULL,
  app_label character varying NOT NULL,
  model character varying NOT NULL,
  CONSTRAINT django_content_type_pkey PRIMARY KEY (id)
);
CREATE TABLE public.auth_permission (
  id integer GENERATED ALWAYS AS IDENTITY NOT NULL,
  name character varying NOT NULL,
  content_type_id integer NOT NULL,
  codename character varying NOT NULL,
  CONSTRAINT auth_permission_pkey PRIMARY KEY (id),
  CONSTRAINT auth_permission_content_type_id_2f476e4b_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id)
);
CREATE TABLE public.auth_group (
  id integer GENERATED ALWAYS AS IDENTITY NOT NULL,
  name character varying NOT NULL UNIQUE,
  CONSTRAINT auth_group_pkey PRIMARY KEY (id)
);
CREATE TABLE public.auth_group_permissions (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  group_id integer NOT NULL,
  permission_id integer NOT NULL,
  CONSTRAINT auth_group_permissions_pkey PRIMARY KEY (id),
  CONSTRAINT auth_group_permissions_group_id_b120cbf9_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id),
  CONSTRAINT auth_group_permissio_permission_id_84c5c92e_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id)
);
CREATE TABLE public.authentication_usuariopersonalizado (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  password character varying NOT NULL,
  last_login timestamp with time zone,
  is_superuser boolean NOT NULL,
  username character varying NOT NULL UNIQUE,
  first_name character varying NOT NULL,
  last_name character varying NOT NULL,
  email character varying NOT NULL,
  is_staff boolean NOT NULL,
  is_active boolean NOT NULL,
  date_joined timestamp with time zone NOT NULL,
  role character varying NOT NULL,
  especialidad character varying,
  CONSTRAINT authentication_usuariopersonalizado_pkey PRIMARY KEY (id)
);
CREATE TABLE public.authentication_usuariopersonalizado_groups (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  usuariopersonalizado_id bigint NOT NULL,
  group_id integer NOT NULL,
  CONSTRAINT authentication_usuariopersonalizado_groups_pkey PRIMARY KEY (id),
  CONSTRAINT authentication_usuar_usuariopersonalizado_44125d24_fk_authentic FOREIGN KEY (usuariopersonalizado_id) REFERENCES public.authentication_usuariopersonalizado(id),
  CONSTRAINT authentication_usuar_group_id_a6169034_fk_auth_grou FOREIGN KEY (group_id) REFERENCES public.auth_group(id)
);
CREATE TABLE public.authentication_usuariopersonalizado_user_permissions (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  usuariopersonalizado_id bigint NOT NULL,
  permission_id integer NOT NULL,
  CONSTRAINT authentication_usuariopersonalizado_user_permissions_pkey PRIMARY KEY (id),
  CONSTRAINT authentication_usuar_usuariopersonalizado_d1c63696_fk_authentic FOREIGN KEY (usuariopersonalizado_id) REFERENCES public.authentication_usuariopersonalizado(id),
  CONSTRAINT authentication_usuar_permission_id_53746474_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id)
);
CREATE TABLE public.django_admin_log (
  id integer GENERATED ALWAYS AS IDENTITY NOT NULL,
  action_time timestamp with time zone NOT NULL,
  object_id text,
  object_repr character varying NOT NULL,
  action_flag smallint NOT NULL CHECK (action_flag >= 0),
  change_message text NOT NULL,
  content_type_id integer,
  user_id bigint NOT NULL,
  CONSTRAINT django_admin_log_pkey PRIMARY KEY (id),
  CONSTRAINT django_admin_log_content_type_id_c4bce8eb_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id),
  CONSTRAINT django_admin_log_user_id_c564eba6_fk_authentic FOREIGN KEY (user_id) REFERENCES public.authentication_usuariopersonalizado(id)
);
CREATE TABLE public.etl_paciente (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  identificacion character varying NOT NULL UNIQUE,
  nombres character varying NOT NULL,
  apellidos character varying NOT NULL,
  edad integer NOT NULL,
  sexo character varying NOT NULL,
  CONSTRAINT etl_paciente_pkey PRIMARY KEY (id)
);
CREATE TABLE public.etl_registroclinico (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  peso double precision NOT NULL,
  altura double precision NOT NULL,
  imc double precision NOT NULL,
  presion_sistolica integer NOT NULL,
  presion_diastolica integer NOT NULL,
  frecuencia_cardiaca integer NOT NULL,
  glucosa double precision NOT NULL,
  colesterol integer NOT NULL,
  saturacion_oxigeno double precision NOT NULL,
  temperatura double precision NOT NULL,
  antecedentes_familiares text NOT NULL,
  fumador boolean NOT NULL,
  consumo_alcohol boolean NOT NULL,
  actividad_fisica character varying NOT NULL,
  diagnostico_preliminar text NOT NULL,
  riesgo_enfermedad character varying NOT NULL,
  fecha_consulta date NOT NULL,
  paciente_id bigint NOT NULL,
  CONSTRAINT etl_registroclinico_pkey PRIMARY KEY (id),
  CONSTRAINT etl_registroclinico_paciente_id_e671c355_fk_etl_paciente_id FOREIGN KEY (paciente_id) REFERENCES public.etl_paciente(id)
);
CREATE TABLE public.django_session (
  session_key character varying NOT NULL,
  session_data text NOT NULL,
  expire_date timestamp with time zone NOT NULL,
  CONSTRAINT django_session_pkey PRIMARY KEY (session_key)
);
CREATE TABLE public.ml_modeloml (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  fecha_entrenamiento timestamp with time zone NOT NULL,
  algoritmo character varying NOT NULL,
  accuracy double precision NOT NULL,
  precision double precision NOT NULL,
  recall double precision NOT NULL,
  f1_score double precision NOT NULL,
  total_registros integer NOT NULL,
  activo boolean NOT NULL,
  CONSTRAINT ml_modeloml_pkey PRIMARY KEY (id)
);
CREATE TABLE public.etl_etllog (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  fecha_ejecucion timestamp with time zone NOT NULL,
  registros_procesados integer NOT NULL,
  registros_fallidos integer NOT NULL,
  tiempo_ejecucion double precision NOT NULL,
  estado character varying NOT NULL,
  archivo_fuente character varying NOT NULL,
  mensaje_error text NOT NULL,
  log_detalle text NOT NULL,
  usuario_id bigint,
  CONSTRAINT etl_etllog_pkey PRIMARY KEY (id),
  CONSTRAINT etl_etllog_usuario_id_0912ca71_fk_authentic FOREIGN KEY (usuario_id) REFERENCES public.authentication_usuariopersonalizado(id)
);
CREATE TABLE public.token_blacklist_blacklistedtoken (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  blacklisted_at timestamp with time zone NOT NULL,
  token_id bigint NOT NULL UNIQUE,
  CONSTRAINT token_blacklist_blacklistedtoken_pkey PRIMARY KEY (id),
  CONSTRAINT token_blacklist_blacklistedtoken_token_id_3cc7fe56_fk FOREIGN KEY (token_id) REFERENCES public.token_blacklist_outstandingtoken(id)
);
CREATE TABLE public.token_blacklist_outstandingtoken (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  token text NOT NULL,
  created_at timestamp with time zone,
  expires_at timestamp with time zone NOT NULL,
  user_id bigint,
  jti character varying NOT NULL UNIQUE,
  CONSTRAINT token_blacklist_outstandingtoken_pkey PRIMARY KEY (id),
  CONSTRAINT token_blacklist_outs_user_id_83bc629a_fk_authentic FOREIGN KEY (user_id) REFERENCES public.authentication_usuariopersonalizado(id)
);