from agents_ import run_secret_scan

if __name__ == "__main__":
    import asyncio
    query = input("Enter your search query or repository URL: ")
    asyncio.run(run_secret_scan(query))