CREATE TABLE IF NOT EXISTS shows (
    id UUID PRIMARY KEY,
    date DATE NOT NULL,
    year INT NOT NULL,
    venue_name VARCHAR(255) NOT NULL,
    venue_city VARCHAR(100),
    venue_state VARCHAR(100),
    venue_country VARCHAR(100),
    tour_name VARCHAR(255),
    total_songs INT,
    num_sets INT,
    setlist_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_data JSONB NOT NULL,
    UNIQUE(date, venue_name)
);

CREATE TABLE IF NOT EXISTS songs (
    id SERIAL PRIMARY KEY,
    show_id UUID NOT NULL,
    set_number VARCHAR(50),
    position INT,
    title VARCHAR(255) NOT NULL,
    transition VARCHAR(50),
    notes TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (show_id) REFERENCES shows(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notes (
    id SERIAL PRIMARY KEY,
    show_id UUID NOT NULL,
    note_type VARCHAR(50),
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (show_id) REFERENCES shows(id) ON DELETE CASCADE
);

-- Create indexes for faster queries
CREATE INDEX idx_shows_date ON shows(date DESC);
CREATE INDEX idx_shows_year ON shows(year);
CREATE INDEX idx_shows_venue ON shows(venue_name);
CREATE INDEX idx_shows_city ON shows(venue_city);
CREATE INDEX idx_songs_show_id ON songs(show_id);
CREATE INDEX idx_songs_title ON songs(title);
CREATE INDEX idx_notes_show_id ON notes(show_id);
