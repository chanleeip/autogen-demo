import subprocess

def run_nmap_scan(arguments: str) -> str:
    '''
    This function runs nmap scan with the given arguments string.
    It returns the output of the nmap scan.
    '''
    try:
        print(arguments,"HEHEHEH")
        # Split the string into a list of arguments
        args_list = arguments.split()
        result = subprocess.run(["nmap"] + args_list, capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return f"Error: {str(e)}"


def run_whois_lookup(domain: str) -> str:
    '''
    This function runs whois lookup for the given domain.
    It returns the output of the whois lookup.
    '''
    try:
        result = subprocess.run(["whois", domain], capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    # Test with string arguments
    print(run_nmap_scan("-sT -Pn 192.168.0.1"))