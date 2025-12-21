import os
import subprocess
import sys

# Configuration
BASE_DIR = "/home/tcmofashi/proj"
REPOS = [
    "MaiMBot",
    "MaimConfig",
    "MaimWeb",
    "maim_db",
    "maim_message"
]
EXCLUDE_REPOS = [
    "MaimWebBackend"  # Start by ignoring the Replier Backend
]

def run_command(command, cwd):
    """Run a shell command in the specified directory."""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command '{' '.join(command)}' in {cwd}:")
        print(e.stderr)
        return None

def sync_repo(repo_name, commit_msg):
    """Sync a single repository."""
    repo_path = os.path.join(BASE_DIR, repo_name)
    
    if not os.path.exists(repo_path):
        print(f"Skipping {repo_name}: Directory not found.")
        return

    print(f"\nProcessing {repo_name}...")

    # Git Add
    print("  - git add .")
    run_command(["git", "add", "."], repo_path)

    # Git Commit
    print(f"  - git commit -m '{commit_msg}'")
    # check status first to avoid empty commit error if we used check=True on commit
    status_output = run_command(["git", "status", "--porcelain"], repo_path)
    if status_output:
        commit_output = run_command(["git", "commit", "-m", commit_msg], repo_path)
        if commit_output:
            print("    Commit successful.")
        else:
            print("    Commit failed (or nothing to commit but status showed changes?).")
    else:
        print("    Nothing to commit.")

    # Git Push
    print("  - git push")
    push_output = run_command(["git", "push"], repo_path)
    if push_output is not None: 
         # subprocess.run returns None on error in my wrapper if exception caught, 
         # but push output goes to stderr often even on success for progress, 
         # and stdout for messages. 
         # Actually git push details often go to stderr. 
         # Let's just trust check=True in run_command or the error handling.
         print("    Push successful.")

def main():
    # Get commit message from args or default to "update"
    if len(sys.argv) > 1:
        commit_msg = sys.argv[1]
    else:
        print("Usage: python3 sync_repos.py [commit_message]")
        print("No commit message provided, using default: 'update'")
        commit_msg = "update"

    print(f"Starting Multi-Repo Sync with message: '{commit_msg}'...")
    
    for repo in REPOS:
        if repo in EXCLUDE_REPOS:
            print(f"\nSkipping {repo} (Excluded).")
            continue
            
        sync_repo(repo, commit_msg)

    print("\nAll tasks completed.")

if __name__ == "__main__":
    main()
