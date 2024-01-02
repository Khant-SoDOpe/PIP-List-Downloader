import redis
import getpass
import subprocess
import pkg_resources
import os

# Define Redis connection parameters
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

class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def check_password(self, password):
        return self.password == password

class UserManager:
    def login(self):
        while True:
            username = input("Enter your username: ")
            password = getpass.getpass("Enter your password: ")
            stored_password = redis_client.hget('users', username)  

            if stored_password and stored_password == password:
                return User(username, password)
            else:
                print("Invalid username or password. Try again.")

    def signup(self):
        while True:
            username = input("Enter a new username: ")
            password = getpass.getpass("Enter a password: ")

            if not redis_client.hexists('users', username):
                redis_client.hset('users', username, password)
                print("Signup successful. You can now log in.")
                return User(username, password)
            else:
                print("Username already exists. Try a different one.")

class PackageManager:
    @staticmethod
    def get_local_pip_list():
        try:
            installed_packages = pkg_resources.working_set
            installed_packages_list = sorted(["%s==%s" % (i.key, i.version) for i in installed_packages])
            return '\n'.join(installed_packages_list)
        except Exception as e:
            print(f"Failed to get local pip list: {e}")
            return None
        
    @staticmethod
    def upload_pip(user):
        pip_list = PackageManager.get_local_pip_list()
        if pip_list is not None:
            redis_client.set(user.username, pip_list)
            print("Pip3 list uploaded successfully.")

    @staticmethod
    def download_all_packages(user):
        pip_list = redis_client.get(user.username)

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
                package_manager.upload_pip(user)
            else:
                print("Please log in first.")
        elif choice == '4':
            if user is not None:
                package_manager.download_all_packages(user)
        elif choice == '5':
            if user is not None:
                user = None  # Sign out by resetting the user
                print("Signed out.")
            else:
                break
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main()