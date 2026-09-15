import subprocess
import sys

def automate_git_push(commit_message):
    try:
        # Stage all changes
        subprocess.run(["git", "add", "."], check=True)
        
        # Commit changes with the provided message
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        
        # Push to the remote repository (main branch)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        
        print(f"Successfully committed and pushed changes: {commit_message}")
    except subprocess.CalledProcessError as e:
        print(f"Error during Git operations: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: Please provide a commit message.")
    else:
        commit_message = sys.argv[1]
        automate_git_push(commit_message)
