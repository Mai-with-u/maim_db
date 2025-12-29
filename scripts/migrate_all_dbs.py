import sqlite3
import os
import glob
import subprocess

PROJECT_ROOT = "/home/tcmofashi/proj/maim_db"

def run_command(command):
    try:
        subprocess.run(command, shell=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {command} Error: {e}")
        return False

def fix_permissions(db_path):
    print(f"Fixing permissions for {db_path} and its parent directory...")
    parent_dir = os.path.dirname(db_path)
    # Recursively chmod parent dir and file to 777 to avoid readonly errors
    run_command(f"sudo chmod 777 {parent_dir}")
    run_command(f"sudo chmod 666 {db_path}")

def migrate_db(db_path):
    print(f"\nProcessing database: {db_path}")
    
    if not os.access(db_path, os.W_OK):
        fix_permissions(db_path)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check for person_info table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='person_info'")
        if not cursor.fetchone():
            print("  Skipping: Table 'person_info' not found.")
            conn.close()
            return

        # Check for agent_id column
        cursor.execute("PRAGMA table_info(person_info)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "agent_id" in columns:
            print("  Skipping: Column 'agent_id' already exists.")
        else:
            print("  Migrating: Adding 'agent_id' column...")
            try:
                cursor.execute("ALTER TABLE person_info ADD COLUMN agent_id TEXT")
                cursor.execute("CREATE INDEX IF NOT EXISTS person_info_agent_id ON person_info(agent_id)")
                conn.commit()
                print("  Success: Migration completed.")
            except sqlite3.OperationalError as e:
                if "readonly" in str(e):
                    print("  Error: Database is read-only. Attempting permission fix...")
                    conn.close()
                    fix_permissions(db_path)
                    # Retry
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("ALTER TABLE person_info ADD COLUMN agent_id TEXT")
                    cursor.execute("CREATE INDEX IF NOT EXISTS person_info_agent_id ON person_info(agent_id)")
                    conn.commit()
                    print("  Success: Migration completed after permission fix.")
                else:
                    raise e
                    
    except Exception as e:
        print(f"  Failed: {e}")
    finally:
        if conn:
            conn.close()

def main():
    print(f"Scanning for databases in {PROJECT_ROOT}...")
    # Find all .db files recursively
    db_files = glob.glob(os.path.join(PROJECT_ROOT, "**", "*.db"), recursive=True)
    
    if not db_files:
        print("No database files found.")
        return

    for db_file in db_files:
        migrate_db(db_file)

if __name__ == "__main__":
    main()
