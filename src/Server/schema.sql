CREATE TABLE public.deriva_points (
	id serial4 NOT NULL,
	sender_id varchar(255) NOT NULL,
	"timestamp" timestamp NOT NULL,
	latitude float8 NOT NULL,
	longitude float8 NOT NULL,
	gps_module_id varchar(255) NOT NULL,
	CONSTRAINT deriva_points_pkey PRIMARY KEY (id)
);