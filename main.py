import os
from flask import Flask, flash, render_template, send_file, redirect, request, send_from_directory, jsonify
import paramiko
from io import StringIO

from file_operations import *

app = Flask(__name__)

directory = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/connect', methods=['POST'])
def connect():
    global directory

    server_address = request.form['server_address']
    username = request.form['username']
    password = request.form['password']

    try:
        # Connect to the remote server using SSH
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(server_address, username=username, password=password)

        # Create a SFTP client
        sftp_client = ssh_client.open_sftp()

        # List files in the desired directory
        directory = get_user_home_directory(ssh_client) 
        files_list = sftp_client.listdir(directory)

        # Store file list in a buffer
       # Store file list in a buffer
       
        # Close connections
        sftp_client.close()
        ssh_client.close()

        # Render the files list page with retrieved data
        return render_template('files.html', files=files_list)
    
    except Exception as error:
        # Handle connection errors
        return render_template('error.html', error=str(error))

@app.route('/create-directory')
def create_directory_page():
    return render_template('create_directory.html', directory=directory)

@app.route('/create-directory', methods=['POST'])
def create_directory():
    global directory

    try:
        # Get the directory name from the request
        directory_name = request.json.get('directoryName')

        # Check if the directory already exists
        target_directory = os.path.join(directory, directory_name)
        if os.path.exists(target_directory):
            return jsonify(success=False, error="Directory already exists")

        # Create the directory in the user's home directory
        os.makedirs(target_directory)

        # Return success response to the client
        return jsonify(success=True)

    except Exception as error:
        # Print the full traceback to the console for debugging
        import traceback
        print(f"Error creating directory: {error}")
        traceback.print_exc()

        # Return a generic error response to the client
        return jsonify(success=False, error="Failed to create the directory. Please try again.")

if __name__ == '__main__':
    app.run(debug=True)