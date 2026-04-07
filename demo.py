# Use this for local testing. 
# Once published, users will do: from oxtan import OxtanDB
from build.core import OxtanDB 

def run_workspace_test():
    print("🚀 Initializing Oxtan Workspace...")
    
    try:
        # We use from_cli() for the demo so it interactively prompts the user.
        # In automated CI/CD or production, users will just use: with OxtanDB() as db:
        with OxtanDB.from_cli() as db:
            
            print("\n🛠️  Setting up table...")
            # Drop table first so the demo is idempotent (can be run multiple times without PK errors)
            db.raw("DROP TABLE IF EXISTS oxtan_demo")
            db.raw("CREATE TABLE oxtan_demo (id INT PRIMARY KEY, name VARCHAR(50), role VARCHAR(50))")
            
            print("📝 Inserting data...")
            db.insert("oxtan_demo", {"id": 101, "name": "Jack", "role": "Developer"})
            db.insert("oxtan_demo", {"id": 102, "name": "Sarah", "role": "Designer"})

            print("🔍 Querying data (Returns a Pandas DataFrame!)...")
            # Showcasing the new string-based WHERE clause we just fixed
            developers_df = db.select("oxtan_demo", where="role = 'Developer'") 
            
            print("\n📊 Results found:")
            print(developers_df) # Prints a beautifully formatted DataFrame table

            print("\n🔄 Updating record...")
            # Showcasing that dictionary-based WHERE clauses still work perfectly
            db.update("oxtan_demo", data={"role": "Lead"}, where={"id": 101})

            tables = db.get_tables()
            print(f"\n📂 Current Database Tables: {tables}")

    except Exception as e:
        print(f"\n❌ Workspace Flow Interrupted: {e}")

if __name__ == "__main__":
    run_workspace_test()