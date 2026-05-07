CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    event_date TIMESTAMP NOT NULL,
    description TEXT,
    location TEXT,
    image_url VARCHAR(512),
    notification_enabled BOOLEAN DEFAULT 0,  
    notification_time TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE holidays (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    date DATE NOT NULL,   
    description TEXT
);