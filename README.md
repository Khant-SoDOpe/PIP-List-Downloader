# Prizama's Package Manager

## Overview

This project includes a package manager with two versions:
1. **GUI Version** - A graphical user interface (GUI) for managing packages.
2. **Command-Line Version** - A command-line interface (CLI) for managing packages without a GUI.

## Prerequisites

Before running either version, ensure you have the following installed:
- Python 3.x
- Redis server

## Installation

1. Clone the repository or download the code files.

2. Install the required Python packages. You can do this by running:

    ```bash
    pip install -r requirements.txt
    ```

3. Set up your environment variables:

    - Copy the `.env.example` file to `.env`:

      ```bash
      cp .env.example .env
      ```

    - Edit the `.env` file to include your Redis connection parameters:

      ```
      REDIS_HOST=your_redis_host
      REDIS_PORT=your_redis_port
      REDIS_PASSWORD=your_redis_password
      ```

## GUI Version

### Overview

The GUI version uses Tkinter to provide a user-friendly interface for managing packages.

### Running the GUI Version

1. **Start the Application**

    Run the following command to start the GUI application:

    ```bash
    python app-gui.py
    ```

2. **Usage**

    - **Login**: Click "Login" and enter your username and password.
    - **Signup**: Click "Signup" to create a new account.
    - **Upload Selected Packages**: Select packages from the table and click "Upload Selected Packages" to upload them to Redis.
    - **Download All Packages**: Click "Download All Packages" to download and install all packages associated with the logged-in user.
    - **Download Selected Packages**: Select packages from the table and click "Download Selected Packages" to download and install them.
    - **Logout**: Click "Logout" to sign out of your account.

## Command-Line Version

### Overview

The command-line version provides a terminal-based interface for managing packages.

### Running the Command-Line Version

1. **Start the Application**

    Run the following command to start the CLI application:

    ```bash
    python app.py
    ```

2. **Usage**

    - **Login**: Enter your username and password when prompted.
    - **Signup**: Create a new account by entering a new username and password when prompted.
    - **Upload Pip List**: Choose whether to use the pip module or pkg_resources to upload the pip list.
    - **Download All Packages**: Download and install all packages associated with the logged-in user.
    - **Sign Out**: Sign out of your account.

## Notes

- Ensure Redis is running before using either version of the package manager.
- Customize the `.env` file with your Redis server details.

For more information or help, feel free to reach out to me.
