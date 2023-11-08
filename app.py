import redis
import getpass
import subprocess
from dotenv import load_dotenv
import os

load_dotenv()


# Define the Redis connection parameters
redis_host = os.getenv("REDIS_HOST")
redis_port = os.getenv("REDIS_PORT")
redis_password = os.getenv("REDIS_PASSWORD")

# Initialize the Redis connection
redis_client = redis.StrictRedis(
    host=redis_host,
    port=redis_port,
    password=redis_password,
    db=0,
    decode_responses=True
)

def login():
    while True:
        username = input("Enter your username: ")
        password = getpass.getpass("Enter your password: ")
        stored_password = redis_client.hget('users', username)
        
        if stored_password == password:
            return username
        else:
            print("Invalid username or password. Try again.")

def signup():
    while True:
        username = input("Enter a new username: ")
        password = getpass.getpass("Enter a password: ")
        
        if not redis_client.hexists('users', username):
            redis_client.hset('users', username, password)
            print("Signup successful. You can now log in.")
            return

        print("Username already exists. Try a different one.")

def get_local_pip_list():
    try:
        # Use subprocess to run the 'pip3 list' command
        pip_list = subprocess.check_output(['pip3', 'list']).decode('utf-8')
        return pip_list
    except subprocess.CalledProcessError:
        print("Failed to get local pip3 list. Make sure 'pip3' is installed.")
        return None

def upload_pip(username):
    pip_list = get_local_pip_list()
    if pip_list is not None:
        redis_client.set(username, pip_list)
        print("Pip3 list uploaded successfully.")

def download_all_packages(username):
    pip_list = redis_client.get(username)
    
    if pip_list:
        for line in pip_list.split('\n'):
            if line:
                package_info = line.strip().split()
                if len(package_info) >= 1:
                    package_name = package_info[0]
                    print(f"Downloading and installing {package_name}...")
                    subprocess.call(['pip3', 'install', package_name])
                    print(f"{package_name} has been downloaded and installed.")
    else:
        print("No pip data found for the user.")

def main():
    username = None  # Initialize username as None
    while True:
        if username is None:
            print("\n1. Login\n2. Signup\n5. Quit")
        else:
            print(f"\nLogged in as: {username}\n3. Upload Pip List\n4. Download All Packages\n5. Sign Out")
        choice = input("Enter your choice: ")

        if choice == '1':
            username = login()
        elif choice == '2':
            signup()
        elif choice == '3':
            if username is not None:
                upload_pip(username)
            else:
                print("Please log in first.")
        elif choice == '4':
            if username is not None:
                download_all_packages(username)
        elif choice == '5':
            if username is not None:
                username = None  # Sign out by resetting the username
                print("Signed out.")
            else:
                break
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main()
