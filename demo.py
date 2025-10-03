from build.core import OxtanDB

with OxtanDB() as db:
    print(db.run("CREATE TABLE IF NOT EXISTS oxtan (id INT PRIMARY KEY, name VARCHAR(50))"))
    print(db.run("INSERT INTO oxtan (id, name) VALUES (%s, %s)", (1, "Jack")))
    rows = db.run("SELECT * FROM oxtan")
    print("📊 Students:", rows)