CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    jersey_number INT,
    team TEXT,
    position TEXT
);

CREATE TABLE games (
    id SERIAL PRIMARY KEY,
    date DATE DEFAULT CURRENT_DATE,
    location TEXT,
    team_a TEXT,
    team_b TEXT
);

CREATE TABLE game_players (
    id SERIAL PRIMARY KEY,
    game_id INT REFERENCES games(id) ON DELETE CASCADE,
    player_id INT REFERENCES players(id) ON DELETE CASCADE,
    track_id INT NOT NULL,
    team TEXT
);

CREATE TABLE frames (
    id SERIAL PRIMARY KEY,
    game_id INT REFERENCES games(id) ON DELETE CASCADE,
    frame_num INT NOT NULL,
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_detections JSONB NOT NULL
);

CREATE TABLE actions (
    id SERIAL PRIMARY KEY,
    game_id INT REFERENCES games(id) ON DELETE CASCADE,
    frame_id INT REFERENCES frames(id) ON DELETE CASCADE,
    action_type TEXT NOT NULL,
    player_id INT REFERENCES game_players(id),
    target_player_id INT REFERENCES game_players(id),
    team TEXT,
    game_time TIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE game_scores (
    id SERIAL PRIMARY KEY,
    game_id INT REFERENCES games(id) ON DELETE CASCADE,
    team TEXT NOT NULL,
    current_score INT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);