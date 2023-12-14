from flask import Flask, flash, render_template, send_file, redirect, request, send_from_directory, jsonify
import paramiko
from io import StringIO

from file_operations import *

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/connect', methods=['POST'])
def connect():
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
        directory = '/home/mehmet' 
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


@app.route('/create-directory', methods=['POST'])
def create_directory():
    directory_name = request.form['directory_name']
    parent_directory = '/home/mehmet'  # Update this as needed

    try:
        # Create the directory
        create_directory(directory_name, parent_directory)

        # Success message and redirect
        flash('Directory created successfully!', 'success')
        return redirect('/files')
    except Exception as error:
        # Handle error and display message
        flash(f'Error creating directory: {error}', 'error')
        return render_template('error.html', error=str(error))
  
if __name__ == '__main__':
    app.run(debug=True)