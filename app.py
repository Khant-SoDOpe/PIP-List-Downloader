import redis
import getpass
import subprocess
import pkg_resources
import os
import sys
from dotenv import load_dotenv
import bcrypt  # Added bcrypt for password hashing

load_dotenv()
# Define Redis connection parameters
redis_host = os.getenv("REDIS_HOST")
redis_port = os.getenv("REDIS_PORT")
redis_password = os.getenv("REDIS_PASSWORD")

# Validate environment variables
if not redis_host or not redis_port:
    raise ValueError("REDIS_HOST and REDIS_PORT must be set.")

redis_port = int(redis_port)

# Initialize the Redis connection
redis_client = redis.StrictRedis(
    host=redis_host,
    port=redis_port,
    password=redis_password,
    db=0,
    decode_responses=True
)

class User:
    def __init__(self, username):
        self.username = username

    def check_password(self, password):
        stored_password = redis_client.hget('users', self.username)
        return stored_password and bcrypt.checkpw(password.encode(), stored_password.encode())

    def set_password(self, password):
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        redis_client.hset('users', self.username, hashed_password)

class UserManager:
    def login(self):
        while True:
            username = input("Enter your username: ")
            password = getpass.getpass("Enter your password: ")
            user = User(username)
            if user.check_password(password):
                return user
            else:
                print("Invalid username or password. Try again.")

    def signup(self):
        while True:
            username = input("Enter a new username: ")
            password = getpass.getpass("Enter a password: ")

            if not redis_client.hexists('users', username):
                user = User(username)
                user.set_password(password)
                print("Signup successful. You can now log in.")
                return user
            else:
                print("Username already exists. Try a different one.")

class PackageManager:
    @staticmethod
    def get_local_pip_list():
        """
        Retrieve the list of installed packages using pkg_resources.
        """
        try:
            installed_packages = pkg_resources.working_set
            installed_packages_list = sorted(["%s==%s" % (i.key, i.version) for i in installed_packages])
            return '\n'.join(installed_packages_list)
        except Exception as e:
            print(f"Failed to get local pip list: {e}")
            return None

    @staticmethod
    def get_local_pip_list_using_pip():
        """
        Retrieve the list of installed packages using pip module.
        """
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format=freeze'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"Failed to run pip list: {result.stderr}")
                return None
        except Exception as e:
            print(f"Failed to get local pip list using pip: {e}")
            return None

    @staticmethod
    def upload_pip(user, use_pip_module=False):
        """
        Upload the list of installed packages to Redis.
        """
        if use_pip_module:
            pip_list = PackageManager.get_local_pip_list_using_pip()
        else:
            pip_list = PackageManager.get_local_pip_list()

        if pip_list is not None:
            redis_client.set(user.username, pip_list)
            print("Pip list uploaded successfully.")
        else:
            print("Failed to retrieve pip list.")

    @staticmethod
    def download_all_packages(user):
        """
        Download and install all packages from the stored pip list in Redis.
        """
        pip_list = redis_client.get(user.username)

        if pip_list:
            for line in pip_list.split('\n'):
                if line:
                    package_info = line.strip().split('==')
                    if len(package_info) >= 1:
                        package_name = package_info[0]
                        print(f"Downloading and installing {package_name}...")
                        subprocess.call([sys.executable, '-m', 'pip', 'install', package_name])
                        print(f"{package_name} has been downloaded and installed.")
        else:
            print("No pip data found for the user.")

def main():
    user_manager = UserManager()
    package_manager = PackageManager()
    user = None

    while True:
        if user is None:
            print("\n1. Login\n2. Signup\n5. Quit")
        else:
            print(f"\nLogged in as: {user.username}\n3. Upload Pip List\n4. Download All Packages\n5. Sign Out")
        choice = input("Enter your choice: ")

        if choice == '1':
            user = user_manager.login()
        elif choice == '2':
            user = user_manager.signup()
        elif choice == '3':
            if user is not None:
                use_pip_module = input("Use pip module to get pip list? (yes/no): ").strip().lower() == 'yes'
                package_manager.upload_pip(user, use_pip_module)
            else:
                print("Please log in first.")
        elif choice == '4':
            if user is not None:
                package_manager.download_all_packages(user)
            else:
                print("Please log in first.")
        elif choice == '5':
            if user is not None:
                user = None
                print("Signed out.")
            else:
                break
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main()
