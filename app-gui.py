import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import redis
import subprocess
import pkg_resources
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define Redis connection parameters from environment variables
redis_host = os.getenv("REDIS_HOST")
redis_port = int(os.getenv("REDIS_PORT"))
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
    def login(self, username, password):
        stored_password = redis_client.hget('users', username)
        if stored_password and stored_password == password:
            return User(username, password)
        return None

    def signup(self, username, password):
        if not redis_client.hexists('users', username):
            redis_client.hset('users', username, password)
            return User(username, password)
        return None

class PackageManager:
    @staticmethod
    def get_local_pip_list():
        try:
            installed_packages = pkg_resources.working_set
            installed_packages_list = sorted(["%s==%s" % (i.key, i.version) for i in installed_packages])
            return installed_packages_list
        except Exception as e:
            print(f"Failed to get local pip list: {e}")
            return []

    @staticmethod
    def get_local_pip_list_using_pip():
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format=freeze'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
            else:
                print(f"Failed to run pip list: {result.stderr}")
                return []
        except Exception as e:
            print(f"Failed to get local pip list using pip: {e}")
            return []

    @staticmethod
    def upload_pip(user, packages):
        if not packages:
            print("No packages selected for upload.")
            return False

        pip_list = '\n'.join(packages)
        redis_client.set(user.username, pip_list)
        print("Pip list uploaded successfully.")
        return True

    @staticmethod
    def upload_all_pip(user):
        pip_list = PackageManager.get_local_pip_list_using_pip()
        success = PackageManager.upload_pip(user, pip_list)
        return success

    @staticmethod
    def download_pip(user, packages, progress_callback):
        if not packages:
            print("No packages selected for download.")
            return False

        for package in packages:
            package_info = package.strip().split('==')
            if len(package_info) >= 1:
                package_name = package_info[0]
                progress_callback(f"Downloading and installing {package_name}...")
                subprocess.call(['pip3', 'install', package_name])
                progress_callback(f"{package_name} has been downloaded and installed.")
        return True

    @staticmethod
    def download_all_packages(user, progress_callback):
        pip_list = redis_client.get(user.username)

        if pip_list:
            packages = pip_list.split('\n')
            for line in packages:
                package_info = line.strip().split('==')
                if len(package_info) >= 1:
                    package_name = package_info[0]
                    progress_callback(f"Downloading and installing {package_name}...")
                    subprocess.call(['pip3', 'install', package_name])
                    progress_callback(f"{package_name} has been downloaded and installed.")
            return True
        else:
            print("No pip data found for the user.")
            return False

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Package Manager")
        self.user_manager = UserManager()
        self.package_manager = PackageManager()
        self.user = None

        self.setup_gui()

    def setup_gui(self):
        # Set up the main frame
        self.frame = tk.Frame(self.root)
        self.frame.pack(pady=10, padx=10, fill='both', expand=True)

        # Title label
        self.label = tk.Label(self.frame, text="Prizama's Package Manager", font=("Arial", 16))
        self.label.pack(pady=10)

        # Button layout
        button_frame = tk.Frame(self.frame)
        button_frame.pack(pady=5)

        self.login_button = tk.Button(button_frame, text="Login", command=self.login)
        self.login_button.grid(row=0, column=0, padx=5, pady=5)

        self.signup_button = tk.Button(button_frame, text="Signup", command=self.signup)
        self.signup_button.grid(row=0, column=1, padx=5, pady=5)

        self.upload_all_button = tk.Button(button_frame, text="Upload All Packages", command=self.upload_all_pip, state='disabled')
        self.upload_all_button.grid(row=0, column=2, padx=5, pady=5)

        self.upload_selected_button = tk.Button(button_frame, text="Upload Selected Packages", command=self.upload_pip, state='disabled')
        self.upload_selected_button.grid(row=0, column=3, padx=5, pady=5)

        self.download_all_button = tk.Button(button_frame, text="Download All Packages", command=self.download_all_pip, state='disabled')
        self.download_all_button.grid(row=0, column=4, padx=5, pady=5)

        self.download_selected_button = tk.Button(button_frame, text="Download Selected Packages", command=self.download_selected_pip, state='disabled')
        self.download_selected_button.grid(row=0, column=5, padx=5, pady=5)

        self.logout_button = tk.Button(button_frame, text="Logout", command=self.logout, state='disabled')
        self.logout_button.grid(row=0, column=6, padx=5, pady=5)

        # Treeview setup
        self.package_tree = ttk.Treeview(self.frame, columns=('Select', 'Package', 'Version'), show='headings', selectmode='extended')
        self.package_tree.heading('Select', text='Select')
        self.package_tree.heading('Package', text='Package Name')
        self.package_tree.heading('Version', text='Version')

        # Center-align text
        self.package_tree.column('Select', anchor='center', width=60)
        self.package_tree.column('Package', anchor='center', width=150)
        self.package_tree.column('Version', anchor='center', width=100)

        self.package_tree.pack(expand=True, fill=tk.BOTH, pady=10)

        # Scrollbar
        self.vsb = ttk.Scrollbar(self.frame, orient="vertical", command=self.package_tree.yview)
        self.vsb.pack(side='right', fill='y')
        self.package_tree.configure(yscrollcommand=self.vsb.set)

        # Bind click event to toggle checkboxes
        self.package_tree.bind('<Button-1>', self.toggle_checkbox)

    def toggle_checkbox(self, event):
        region = self.package_tree.identify("region", event.x, event.y)
        if region == "heading":
            return

        row_id = self.package_tree.identify_row(event.y)
        column_id = self.package_tree.identify_column(event.x)

        if column_id == '#1':  # Select column
            current_value = self.package_tree.set(row_id, "Select")
            new_value = 'True' if current_value == 'False' else 'False'
            self.package_tree.set(row_id, "Select", new_value)

    def login(self):
        username = simpledialog.askstring("Login", "Enter username:")
        password = simpledialog.askstring("Login", "Enter password:", show='*')
        user = self.user_manager.login(username, password)

        if user:
            self.user = user
            messagebox.showinfo("Login", "Login successful!")
            self.toggle_buttons(True)
            self.populate_package_tree()
        else:
            messagebox.showerror("Login", "Invalid username or password.")

    def signup(self):
        username = simpledialog.askstring("Signup", "Enter new username:")
        password = simpledialog.askstring("Signup", "Enter new password:", show='*')
        user = self.user_manager.signup(username, password)

        if user:
            self.user = user
            messagebox.showinfo("Signup", "Signup successful! You are now logged in.")
            self.toggle_buttons(True)
            self.populate_package_tree()
        else:
            messagebox.showerror("Signup", "Username already exists.")

    def populate_package_tree(self):
        self.package_tree.delete(*self.package_tree.get_children())
        packages = self.package_manager.get_local_pip_list_using_pip()
        for package in packages:
            package_name, version = package.split('==')
            self.package_tree.insert('', tk.END, values=('False', package_name, version))

    def upload_all_pip(self):
        if not self.user:
            messagebox.showwarning("Upload", "Please log in first.")
            return

        success = self.package_manager.upload_all_pip(self.user)

        if success:
            messagebox.showinfo("Upload", "All packages uploaded successfully.")
        else:
            messagebox.showerror("Upload", "Failed to upload packages.")

    def upload_pip(self):
        selected_items = [self.package_tree.item(item, 'values') for item in self.package_tree.get_children() if self.package_tree.set(item, 'Select') == 'True']
        if not selected_items:
            messagebox.showwarning("Upload", "No packages selected for upload.")
            return

        selected_packages = [f"{package[1]}=={package[2]}" for package in selected_items]
        success = self.package_manager.upload_pip(self.user, selected_packages)

        if success:
            messagebox.showinfo("Upload", "Selected packages uploaded successfully.")
        else:
            messagebox.showerror("Upload", "Failed to upload selected packages.")

    def download_all_pip(self):
        if not self.user:
            messagebox.showwarning("Download", "Please log in first.")
            return

        # Create and show the progress window
        self.progress_window = tk.Toplevel(self.root)
        self.progress_window.title("Progress")
        self.progress_window.geometry("300x100")

        self.progress_label = tk.Label(self.progress_window, text="Downloading and installing packages...", padx=10, pady=10)
        self.progress_label.pack()

        self.root.update_idletasks()  # Update the GUI to show the progress window

        def update_progress(message):
            self.progress_label.config(text=message)
            self.root.update_idletasks()

        success = self.package_manager.download_all_packages(self.user, update_progress)

        if success:
            messagebox.showinfo("Download", "All packages downloaded and installed.")
        else:
            messagebox.showerror("Download", "No pip data found for the user.")

        # Close the progress window
        self.progress_window.destroy()

    def download_selected_pip(self):
        if not self.user:
            messagebox.showwarning("Download", "Please log in first.")
            return

        selected_items = [self.package_tree.item(item, 'values') for item in self.package_tree.get_children() if self.package_tree.set(item, 'Select') == 'True']
        if not selected_items:
            messagebox.showwarning("Download", "No packages selected for download.")
            return

        selected_packages = [f"{package[1]}=={package[2]}" for package in selected_items]

        # Create and show the progress window
        self.progress_window = tk.Toplevel(self.root)
        self.progress_window.title("Progress")
        self.progress_window.geometry("300x100")

        self.progress_label = tk.Label(self.progress_window, text="Downloading and installing selected packages...", padx=10, pady=10)
        self.progress_label.pack()

        self.root.update_idletasks()  # Update the GUI to show the progress window

        def update_progress(message):
            self.progress_label.config(text=message)
            self.root.update_idletasks()

        success = self.package_manager.download_pip(self.user, selected_packages, update_progress)

        if success:
            messagebox.showinfo("Download", "Selected packages downloaded and installed.")
        else:
            messagebox.showerror("Download", "Failed to download selected packages.")

        # Close the progress window
        self.progress_window.destroy()

    def logout(self):
        self.user = None
        messagebox.showinfo("Logout", "Logged out successfully.")
        self.toggle_buttons(False)

    def toggle_buttons(self, logged_in):
        if logged_in:
            self.upload_all_button.config(state='normal')
            self.upload_selected_button.config(state='normal')
            self.download_all_button.config(state='normal')
            self.download_selected_button.config(state='normal')
            self.logout_button.config(state='normal')
            self.login_button.config(state='disabled')
            self.signup_button.config(state='disabled')
        else:
            self.upload_all_button.config(state='disabled')
            self.upload_selected_button.config(state='disabled')
            self.download_all_button.config(state='disabled')
            self.download_selected_button.config(state='disabled')
            self.logout_button.config(state='disabled')
            self.login_button.config(state='normal')
            self.signup_button.config(state='normal')
            self.package_tree.delete(*self.package_tree.get_children())

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
