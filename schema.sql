-- 1. Voters Table: Stores voter details
CREATE TABLE Voters (
    voter_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    has_voted BOOLEAN DEFAULT 0
);

-- 2. Elections Table: Stores election details
CREATE TABLE Elections (
    election_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    status TEXT CHECK (status IN ('Scheduled', 'Ongoing', 'Completed')) NOT NULL
);

-- 3. PoliticalParties Table: Stores registered political parties
CREATE TABLE PoliticalParties (
    party_id INTEGER PRIMARY KEY AUTOINCREMENT,
    party_name TEXT UNIQUE NOT NULL
);

-- 4. Positions Table: Stores different positions available in elections
CREATE TABLE Positions (
    position_id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_name TEXT NOT NULL,
    allocated_seats INTEGER DEFAULT 1
);

-- 5. Candidates Table: Stores candidate details
CREATE TABLE Candidates (
    candidate_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    party_id INTEGER NOT NULL,
    position_id INTEGER NOT NULL,
    election_id INTEGER NOT NULL,
    FOREIGN KEY (party_id) REFERENCES PoliticalParties(party_id),
    FOREIGN KEY (position_id) REFERENCES Positions(position_id),
    FOREIGN KEY (election_id) REFERENCES Elections(election_id)
);

-- 6. Votes Table: Stores votes linked to blockchain
CREATE TABLE Votes (
    vote_id INTEGER PRIMARY KEY AUTOINCREMENT,
    voter_id INTEGER NOT NULL,
    candidate_id INTEGER NOT NULL,
    election_id INTEGER NOT NULL,
    blockchain_hash TEXT NOT NULL,
    FOREIGN KEY (voter_id) REFERENCES Voters(voter_id),
    FOREIGN KEY (candidate_id) REFERENCES Candidates(candidate_id),
    FOREIGN KEY (election_id) REFERENCES Elections(election_id)
);


