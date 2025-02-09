create table if not exists activities
(
	activity_id bigint not null
		primary key,
	athlete_id bigint not null,
	name varchar(255) null,
	distance decimal(8,1) null,
	total_elevation_gain bigint null,
	type varchar(50) null,
	sport_type varchar(50) null,
	moving_time bigint null,
	start_date mediumtext null
)
collate=utf8mb4_unicode_ci;

create table if not exists athletes
(
	athlete_id int unsigned auto_increment
		primary key,
	created_at timestamp default CURRENT_TIMESTAMP not null,
	email varchar(255) null,
	firstname varchar(255) null,
	lastname varchar(100) null
)
collate=utf8mb4_unicode_ci;

create table if not exists goals_plans
(
	goals_plans_id bigint auto_increment comment 'primary key'
		primary key,
	athlete_id bigint not null,
	goal_name varchar(25) not null comment 'Name of the goal, such as "yord"',
	plan decimal(10,2) not null comment 'Planned goal',
	constraint goals_plans_key
		unique (athlete_id, goal_name)
)
comment 'Tracks goal plans' collate=utf8mb4_unicode_ci;

create table if not exists goals_stats
(
	goal_id bigint auto_increment comment 'primary key'
		primary key,
	athlete_id bigint not null,
	goal_name varchar(25) not null comment 'Name of the goal, such as "Yearly Ride goal"',
	stat decimal(10,2) null comment 'Current value',
	constraint goals_key
		unique (athlete_id, goal_name)
)
comment 'Tracks stats per each goal' collate=utf8mb4_unicode_ci;

create table if not exists token_cache
(
	athlete_id int not null
		primary key,
	access_token char(255) null,
	refresh_token char(255) null,
	expires_at varchar(20) not null
);

