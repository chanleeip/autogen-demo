import os
import requests
from dotenv import load_dotenv
import subprocess
import json
import tempfile
load_dotenv()

def search_code(query:str)->list[str]:
    '''
    Search for code in a github repository using the github api
    Args:
        query: str - The query to search for (e.g. "Org name AND api_key= OR apikey= OR access_token= OR secret= OR password=") . It must be in syntax of github search api.
    Returns:
        list[str] - List of repository urls
    '''
    url = "https://api.github.com/search/code"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"
    }
    params = {
        "q": query,
        "per_page": 10,  # Get more results
        "page": 1
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            urls=[]
            for item in data['items']:
                # Extract repository URL from file URL
                # Convert from: https://github.com/owner/repo/blob/branch/path/to/file
                # To: https://github.com/owner/repo
                file_url = item['html_url']
                if '/blob/' in file_url:
                    repo_url = file_url.split('/blob/')[0]
                    if repo_url not in urls:  # Avoid duplicates
                        urls.append(repo_url)
                else:
                    urls.append(file_url)
            return urls
        else:
            print(f"Error {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"Exception occurred: {e}")
        return None


def run_trufflehog(url:str)->list[dict]:
    '''
    Run trufflehog on a github repository
    Args:
        url: str - The url of the github repository
    Returns:
        list[dict] - List of dictionaries containing the results of the trufflehog scan
    '''
    output=[]
    print("RUNNING TOOLS---TRUFFLEHOG")
    try:
        result = subprocess.run(["trufflehog", "git", url, "--archive-max-depth=5", "--results=verified,unverified,unknown","-j","--log-level=1"], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"TruffleHog failed: {result.stderr}")
            return []
            
        for line in result.stdout.split("\n"):
            if line.strip() and "SourceMetadata" in line:
                try:
                    output.append(json.loads(line))
                except json.JSONDecodeError:
                    print(f"Failed to parse TruffleHog output line: {line}")
                    continue
        return output
    except Exception as e:
        print(f"Error running TruffleHog: {e}")
        return []


def run_gitleaks(url:str)->list[dict]:
    '''
    Run gitleaks on a github repository
    Args:
        url: str - The url of the github repository
    Returns:
        list[dict] - List of dictionaries containing the results of the gitleaks scan
    '''
    print("RUNNING TOOLS---GITLEAKS")
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Clone the repository
            clone_result = subprocess.run(["git", "clone", url, temp_dir], capture_output=True, text=True)
            if clone_result.returncode != 0:
                print(f"Failed to clone repository: {clone_result.stderr}")
                return []
            
            # Run gitleaks
            gitleaks_result = subprocess.run(["gitleaks", "git", temp_dir, "--report-format", "json","--report-path", "gitleaks_report.json"], capture_output=True, text=True)
            
            # Check if report file exists and read it
            if os.path.exists("gitleaks_report.json"):
                with open("gitleaks_report.json", "r") as f:
                    output = json.load(f)
                    return output
            else:
                print("No gitleaks report generated")
                return []
    except Exception as e:
        print(f"Error running gitleaks: {e}")
        return []





if __name__ == "__main__":
    # print(json.dumps(run_trufflehog("https://github.com/RolandCroft/Language-Security-Challenges"), indent=4))
    # print(json.dumps(run_gitleaks("https://github.com/RolandCroft/Language-Security-Challenges"), indent=4))
    1