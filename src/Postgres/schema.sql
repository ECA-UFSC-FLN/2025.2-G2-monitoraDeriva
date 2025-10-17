CREATE TABLE public.deriva_points (
	id serial4 NOT NULL,
	sender_id varchar(255) NOT NULL,
	"timestamp" timestamp NOT NULL,
	latitude float8 NOT NULL,
	longitude float8 NOT NULL,
	gps_module_id varchar(255) NOT NULL,
	CONSTRAINT deriva_points_pkey PRIMARY KEY (id)
);

CREATE TABLE public.users (
	id serial4 NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    is_approved boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT users_pkey PRIMARY KEY (id),
    CONSTRAINT users_email_key UNIQUE (email)
);