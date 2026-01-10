from build.core import OxtanDB

def run_workspace_test():
    print("🚀 Initializing Oxtan Workspace...")
    
    try:
        # If credentials aren't passed, Oxtan will prompt you in the terminal
        with OxtanDB(database="exam") as db:
            
            print("\n🛠️  Setting up table...")
            db.raw("CREATE TABLE IF NOT EXISTS oxtan_demo (id INT PRIMARY KEY, name VARCHAR(50), role VARCHAR(50))")
            
            print("📝 Inserting data...")
            db.insert("oxtan_demo", {"id": 101, "name": "Jack", "role": "Developer"})
            db.insert("oxtan_demo", {"id": 102, "name": "Sarah", "role": "Designer"})

            print("🔍 Querying data...")
            developers = db.select("oxtan_demo", where={"role": "Developer"})
            
            print("\n📊 Results found:")
            for dev in developers:
                print(f" -> User: {dev['name']} | ID: {dev['id']}")

            print("\n🔄 Updating record...")
            db.update("oxtan_demo", data={"role": "Lead"}, where={"id": 101})

            tables = db.get_tables()
            print(f"📂 Current Database Tables: {tables}")

    except Exception as e:
        print(f"\n❌ Workspace Flow Interrupted: {e}")

if __name__ == "__main__":
    run_workspace_test()