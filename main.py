import base64
import logging
from stat import S_ISDIR
logging.basicConfig(level=logging.DEBUG)
import os
from flask import Flask, flash, render_template, send_file, redirect, request, send_from_directory, jsonify, session
from io import StringIO

from file_operations import *

app = Flask(__name__)

app.secret_key = 'rick'

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

    # Store SSH details in session for later use
    session['ssh_details'] = {
        'server_address': server_address,
        'username': username,
        'password': password,
    }

    try:
        with get_ssh_sftp_client(server_address, username, password) as (ssh_client, sftp_client):
            # List files in the desired directory, excluding hidden files
            directory = get_user_home_directory(ssh_client)  # Use ssh_client here
            files_list = [f for f in sftp_client.listdir(directory) if not f.startswith('.')]

            # Update session with the current path
            session['ssh_details']['current_path'] = directory

            # Render the files list page with retrieved data
            return render_template('files.html', files=files_list)
    
    except Exception as error:
        # Handle connection errors
        return render_template('error.html', error=str(error))

@app.route('/open', methods=['GET'])
def open():
    ssh_details = session.get('ssh_details')
    if not ssh_details:
        return jsonify({'error': 'SSH details not found in session'}), 401

    try:
        with get_ssh_sftp_client(ssh_details['server_address'], ssh_details['username'], ssh_details['password']) as (ssh_client, sftp_client):
            base_path = ssh_details['current_path']
            if not base_path:
                return jsonify({'error': 'Base path not found'}), 400

            relative_path = request.args.get('path', '').lstrip('/')
            if not relative_path:
                return jsonify({'error': 'No file path provided'}), 400

            full_path = os.path.join(base_path, relative_path)
            full_path = full_path.replace('\\', '/')

            file_attr = sftp_client.stat(full_path)
            if S_ISDIR(file_attr.st_mode):
                files = sftp_client.listdir(full_path)
                return jsonify({'type': 'directory', 'contents': files})
            else:
                with sftp_client.open(full_path, 'rb') as file:
                    content = file.read()
                    try:
                        content = content.decode('utf-8')
                    except UnicodeDecodeError:
                        content = base64.b64encode(content).decode('utf-8')
                return jsonify({'type': 'file', 'contents': content})

    except IOError as e:
        app.logger.error(f'Error accessing path: {e}')
        return jsonify({'error': 'Error accessing path: {}'.format(e)}), 404
    except Exception as e:
        app.logger.error(f'An error occurred: {e}')
        return jsonify({'error': 'An error occurred while trying to open the file or directory'}), 500

@app.route('/home')
def home():
    ssh_details = session.get('ssh_details')
    if not ssh_details:
        return render_template('error.html', error='SSH details not found in session')

    try:
        with get_ssh_sftp_client(ssh_details['server_address'], ssh_details['username'], ssh_details['password']) as (ssh_client, sftp_client):
            base_path = ssh_details['current_path']
            files_list = [f for f in sftp_client.listdir(base_path) if not f.startswith('.')]
            return render_template('files.html', files=files_list)

    except Exception as e:
        return render_template('error.html', error=str(e))
    
@app.route('/create_directory', methods=['GET', 'POST'])
def create_directory():
    ssh_details = session.get('ssh_details')
    if not ssh_details:
        return render_template('error.html', error='SSH details not found in session')

    if request.method == 'POST':
        try:
            directory_name = request.json.get('directory_name')
            if not directory_name:
                return jsonify({'error': 'Directory name is required'}), 400

            with get_ssh_sftp_client(ssh_details['server_address'], ssh_details['username'], ssh_details['password']) as (ssh_client, sftp_client):
                current_path = ssh_details['current_path']
                # Ensure directory name does not contain any path separator
                safe_directory_name = os.path.basename(directory_name)
                new_directory_path = os.path.join(current_path, safe_directory_name).replace('\\', '/')
                print("New directory path:", new_directory_path)

                try:
                    sftp_client.chdir(new_directory_path)  # Try to change to the directory
                    return jsonify({'error': 'Directory already exists'}), 400
                except IOError:
                    # Directory does not exist, create it
                    sftp_client.mkdir(new_directory_path)
                    return jsonify({'success': 'Directory created successfully'})

        except Exception as e:
            app.logger.error(f'An error occurred: {e}')
            return jsonify({'error': f'An error occurred while trying to create the directory: {str(e)}'}), 500
    else:
        return render_template('create_directory.html')

@app.route('/delete_item', methods=['POST'])
def delete_item():
    ssh_details = session.get('ssh_details')
    if not ssh_details:
        return jsonify({'error': 'SSH details not found in session'}), 401

    try:
        item_path = request.json.get('item_path')
        app.logger.debug(f"Received delete request for path: {item_path}")

        if not item_path:
            return jsonify({'error': 'Item path is required'}), 400

        with get_ssh_sftp_client(ssh_details['server_address'], ssh_details['username'], ssh_details['password']) as (ssh_client, sftp_client):
            # Check if it's a file or directory and delete accordingly
            try:
                if S_ISDIR(sftp_client.stat(item_path).st_mode):
                    sftp_client.rmdir(item_path)  # Delete directory (ensure it's empty)
                else:
                    sftp_client.remove(item_path)  # Delete file
                return jsonify({'success': 'Item deleted successfully'})
            except IOError as e:
                # Handle specific IO errors (e.g., directory not empty)
                return jsonify({'error': str(e)}), 400

    except Exception as e:
        app.logger.error(f'An error occurred: {e}')
        return jsonify({'error': 'An error occurred while trying to delete the item'}), 500

@app.route('/create_file', methods=['GET'])
def display_create_file():
    ssh_details = session.get('ssh_details')
    if not ssh_details:
        return render_template('error.html', error='SSH details not found in session')

    current_path = request.args.get('path', ssh_details.get('current_path', ''))
    return render_template('create_file.html', current_path=current_path)


@app.route('/create_file', methods=['POST'])
def create_file():
    ssh_details = session.get('ssh_details')
    if not ssh_details:
        return jsonify({'error': 'SSH details not found in session'}), 401

    try:
        file_name = request.json.get('file_name')
        # Using the current path from the request or falling back to the session's current path
        current_path = request.json.get('current_path', ssh_details['current_path'])
        new_file_path = os.path.join(current_path, file_name).replace('\\', '/')

        app.logger.debug(f"Creating file at: {new_file_path}")

        with get_ssh_sftp_client(ssh_details['server_address'], ssh_details['username'], ssh_details['password']) as (ssh_client, sftp_client):
            if not os.path.exists(new_file_path):
                with sftp_client.open(new_file_path, 'w') as new_file:
                    new_file.write('')
                return jsonify({'success': 'File created successfully'})
            else:
                return jsonify({'error': 'File already exists'}), 400

    except Exception as e:
        app.logger.error(f'An error occurred: {e}')
        return jsonify({'error': f'An error occurred while trying to create the file: {e}'}), 500

if __name__ == '__main__':
    app.run(debug=True)