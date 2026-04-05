import sqlite3
from pathlib import Path


class Database:
    def __init__(self, db_path: str = "leads.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.init_db()

    def init_db(self):
        cur = self.conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                address TEXT,
                city TEXT,
                state TEXT,
                zip_code TEXT,
                industry TEXT,
                building_sqft INTEGER,
                building_year_built INTEGER,
                estimated_energy_spend REAL,
                source TEXT NOT NULL DEFAULT 'manual',
                score REAL DEFAULT 0.0,
                status TEXT DEFAULT 'new',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                title TEXT,
                email TEXT,
                phone TEXT,
                is_primary INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
                contact_id INTEGER REFERENCES contacts(id),
                type TEXT NOT NULL,
                subject TEXT,
                body TEXT,
                occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                google_id TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                picture_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
            CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(score DESC);
            CREATE INDEX IF NOT EXISTS idx_contacts_lead_id ON contacts(lead_id);
            CREATE INDEX IF NOT EXISTS idx_interactions_lead_id ON interactions(lead_id);
        """)
        self.conn.commit()

    def add_lead(self, **kwargs) -> int:
        cols = [k for k in kwargs if k in (
            "company_name", "address", "city", "state", "zip_code",
            "industry", "building_sqft", "building_year_built",
            "estimated_energy_spend", "source", "score", "status", "notes",
        )]
        placeholders = ", ".join("?" for _ in cols)
        col_names = ", ".join(cols)
        values = [kwargs[c] for c in cols]
        cur = self.conn.execute(
            f"INSERT INTO leads ({col_names}) VALUES ({placeholders})", values
        )
        self.conn.commit()
        return cur.lastrowid

    def get_lead(self, lead_id: int) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM leads WHERE id = ?", (lead_id,)
        ).fetchone()
        return dict(row) if row else None

    def update_lead(self, lead_id: int, **kwargs):
        allowed = {
            "company_name", "address", "city", "state", "zip_code",
            "industry", "building_sqft", "building_year_built",
            "estimated_energy_spend", "source", "score", "status", "notes",
        }
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [lead_id]
        self.conn.execute(
            f"UPDATE leads SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values,
        )
        self.conn.commit()

    def list_leads(self, status: str = None, min_score: float = None,
                   limit: int = 50) -> list[dict]:
        query = "SELECT * FROM leads WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if min_score is not None:
            query += " AND score >= ?"
            params.append(min_score)
        query += " ORDER BY score DESC LIMIT ?"
        params.append(limit)
        rows = self.conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def lead_exists(self, company_name: str, address: str = None) -> bool:
        if address:
            row = self.conn.execute(
                "SELECT 1 FROM leads WHERE company_name = ? AND address = ?",
                (company_name, address),
            ).fetchone()
        else:
            row = self.conn.execute(
                "SELECT 1 FROM leads WHERE company_name = ?",
                (company_name,),
            ).fetchone()
        return row is not None

    def search_leads(self, query: str) -> list[dict]:
        pattern = f"%{query}%"
        rows = self.conn.execute(
            "SELECT * FROM leads WHERE company_name LIKE ? OR city LIKE ? OR industry LIKE ? ORDER BY score DESC",
            (pattern, pattern, pattern),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_all_leads(self) -> list[dict]:
        rows = self.conn.execute("SELECT * FROM leads ORDER BY id").fetchall()
        return [dict(r) for r in rows]

    # --- Contacts ---

    def add_contact(self, lead_id: int, **kwargs) -> int:
        cols = [k for k in kwargs if k in ("name", "title", "email", "phone", "is_primary")]
        placeholders = ", ".join("?" for _ in cols)
        col_names = ", ".join(["lead_id"] + cols)
        values = [lead_id] + [kwargs[c] for c in cols]
        cur = self.conn.execute(
            f"INSERT INTO contacts ({col_names}) VALUES (?, {placeholders})", values
        )
        self.conn.commit()
        return cur.lastrowid

    def get_contacts(self, lead_id: int) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM contacts WHERE lead_id = ? ORDER BY is_primary DESC", (lead_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    # --- Interactions ---

    def add_interaction(self, lead_id: int, **kwargs) -> int:
        cols = [k for k in kwargs if k in ("contact_id", "type", "subject", "body")]
        placeholders = ", ".join("?" for _ in cols)
        col_names = ", ".join(["lead_id"] + cols)
        values = [lead_id] + [kwargs[c] for c in cols]
        cur = self.conn.execute(
            f"INSERT INTO interactions ({col_names}) VALUES (?, {placeholders})", values
        )
        self.conn.commit()
        return cur.lastrowid

    def get_interactions(self, lead_id: int) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM interactions WHERE lead_id = ? ORDER BY occurred_at DESC",
            (lead_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # --- Users ---

    def upsert_user(self, google_id: str, email: str, name: str = None,
                    picture_url: str = None) -> dict:
        self.conn.execute(
            """INSERT INTO users (google_id, email, name, picture_url)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(google_id) DO UPDATE SET
                   email = excluded.email,
                   name = excluded.name,
                   picture_url = excluded.picture_url,
                   last_login = CURRENT_TIMESTAMP""",
            (google_id, email, name, picture_url),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT * FROM users WHERE google_id = ?", (google_id,)
        ).fetchone()
        return dict(row)

    def get_user(self, user_id: int) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None

    def close(self):
        self.conn.close()
