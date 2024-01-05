import base64
from stat import S_ISDIR
import os
from flask import Flask, render_template, redirect, request, jsonify, session, url_for

from file_operations import *

app = Flask(__name__)

app.secret_key = 'rick'

directory = None

# This routes returns the index page.

@app.route('/')
def index():
    return render_template('index.html')

# This route is for connect and list the items in home.

@app.route('/connect', methods=['POST'])
def connect():
    global directory
    # Taking data from website
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
        # Connecting server using a helper function and listing the files.
        # Defined in file_operations.py
        with get_ssh_sftp_client(server_address, username, password) as (ssh_client, sftp_client):
            # List files in the desired directory, excluding hidden files
            directory = get_user_home_directory(
                ssh_client)  # Use ssh_client here
            files_list = [f for f in sftp_client.listdir(
                directory) if not f.startswith('.')]

            # Update session with the current path
            session['ssh_details']['current_path'] = directory

            # Render the files list page with retrieved data
            return render_template('files.html', files=files_list)

    except Exception as error:
        # Handle connection errors
        return render_template('error.html', error=str(error))

# This route is for open files and folders.

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

            # Correcting the path
            full_path = os.path.join(base_path, relative_path)
            full_path = full_path.replace('\\', '/')
            full_path = full_path.replace('//', '/')

            file_attr = sftp_client.stat(full_path)

            # Check the item if its a directory
            if S_ISDIR(file_attr.st_mode):
                files = sftp_client.listdir(full_path)
                ssh_details['current_path'] = full_path
                session.modified = True
                # Return a JSON response with directory contents
                return jsonify({'type': 'directory', 'contents': files, 'current_path': full_path})
            else:
                # Doing the file reading process
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

# This route is for return to the home directory.

@app.route('/home')
def home():
    ssh_details = session.get('ssh_details')
    if not ssh_details:
        return render_template('error.html', error='SSH details not found in session')

    try:

        with get_ssh_sftp_client(ssh_details['server_address'], ssh_details['username'], ssh_details['password']) as (ssh_client, sftp_client):
            base_path = ssh_details['current_path']
            files_list = [f for f in sftp_client.listdir(
                base_path) if not f.startswith('.')]
            return render_template('files.html', files=files_list)

    except Exception as e:
        return render_template('error.html', error=str(e))

# This route is returning create directory page.

@app.route('/create_directory', methods=['GET'])
def display_create_directory():
    ssh_details = session.get('ssh_details')
    if not ssh_details:
        return render_template('error.html', error='SSH details not found in session')

    return render_template('create_directory.html')

# This route creates directory for user.

@app.route('/create_directory', methods=['POST'])
def create_directory():
    ssh_details = session.get('ssh_details')
    if not ssh_details:
        return jsonify({'error': 'SSH details not found in session'}), 401

    try:
        directory_name = request.json.get('directory_name')
        if not directory_name:
            return jsonify({'error': 'Directory name is required'}), 400

        # Doing connection with helper function and starting the directory create process
        with get_ssh_sftp_client(ssh_details['server_address'], ssh_details['username'], ssh_details['password']) as (ssh_client, sftp_client):
            current_path = ssh_details['current_path']
            safe_directory_name = os.path.basename(directory_name)
            new_directory_path = os.path.join(
                current_path, safe_directory_name).replace('\\', '/')
            print("New directory path:", new_directory_path)

            try:
                sftp_client.chdir(new_directory_path)
                return jsonify({'error': 'Directory already exists'}), 400
            except IOError:
                sftp_client.mkdir(new_directory_path)
                return jsonify({'success': 'Directory created successfully'})

    except Exception as e:
        app.logger.error(f'An error occurred: {e}')
        return jsonify({'error': f'An error occurred while trying to create the directory: {str(e)}'}), 500

# This route deletes items for user.

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
                    # Delete directory (ensure it's empty)
                    sftp_client.rmdir(item_path)
                else:
                    sftp_client.remove(item_path)  # Delete file
                return jsonify({'success': 'Item deleted successfully'})
            except IOError as e:
                # Handle specific IO errors (e.g., directory not empty)
                return jsonify({'error': str(e)}), 400

    except Exception as e:
        app.logger.error(f'An error occurred: {e}')
        return jsonify({'error': 'An error occurred while trying to delete the item'}), 500

# This route is returning create file page.

@app.route('/create_file', methods=['GET'])
def display_create_file():
    ssh_details = session.get('ssh_details')
    if not ssh_details:
        return render_template('error.html', error='SSH details not found in session')

    current_path = request.args.get(
        'path', ssh_details.get('current_path', ''))
    return render_template('create_file.html', current_path=current_path)

# This route creates file for user.

@app.route('/create_file', methods=['POST'])
def create_file():
    ssh_details = session.get('ssh_details')
    if not ssh_details:
        return jsonify({'error': 'SSH details not found in session'}), 401

    try:
        file_name = request.json.get('file_name')
        # Using the current path from the request or falling back to the session's current path
        current_path = request.json.get(
            'current_path', ssh_details['current_path'])
        new_file_path = os.path.join(
            current_path, file_name).replace('\\', '/')

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

# This route copies items.

@app.route('/copy_item', methods=['POST'])
def copy_item():
    ssh_details = session.get('ssh_details')
    if not ssh_details:
        return jsonify({'error': 'SSH details not found in session'}), 401

    try:
        source_path = request.json.get('source')
        destination_path = request.json.get('destination')

        if not source_path or not destination_path:
            return jsonify({'error': 'Source and destination paths are required'}), 400

        with get_ssh_sftp_client(ssh_details['server_address'], ssh_details['username'], ssh_details['password']) as (ssh_client, sftp_client):
            # Forming the command to copy files on the remote server
            # Note: This assumes a Linux environment on the remote server
            copy_command = f'cp -r {source_path} {destination_path}'
            stdin, stdout, stderr = ssh_client.exec_command(copy_command)
            exit_status = stdout.channel.recv_exit_status()  # Blocking call

            if exit_status == 0:
                return jsonify({'success': 'Item copied successfully', 'destination_path': destination_path})
            else:
                error_message = stderr.read().decode()
                app.logger.error(
                    f'Copy command failed on remote server: {error_message}')
                return jsonify({'error': 'Copy command failed on remote server', 'details': error_message})

    except Exception as e:
        app.logger.error(f'An error occurred during the copy operation: {e}')
        return jsonify({'error': f'An error occurred: {e}'}), 500

# This route moves items.

@app.route('/move_item', methods=['POST'])
def move_item():
    ssh_details = session.get('ssh_details')
    if not ssh_details:
        return jsonify({'error': 'SSH details not found in session'}), 401

    try:
        source_path = request.json.get('source')
        destination_path = request.json.get('destination')

        if not source_path or not destination_path:
            return jsonify({'error': 'Source and destination paths are required'}), 400

        with get_ssh_sftp_client(ssh_details['server_address'], ssh_details['username'], ssh_details['password']) as (ssh_client, sftp_client):
            move_command = f'mv {source_path} {destination_path}'
            stdin, stdout, stderr = ssh_client.exec_command(move_command)
            exit_status = stdout.channel.recv_exit_status()

            if exit_status == 0:
                return jsonify({'success': 'Item moved successfully', 'destination_path': destination_path})
            else:
                error_message = stderr.read().decode()
                return jsonify({'error': 'Move command failed on remote server', 'details': error_message})

    except Exception as e:
        return jsonify({'error': f'An error occurred: {e}'}), 500

# This route is returning edit file page.

@app.route('/edit_file', methods=['GET'])
def edit_file():
    file_path = request.args.get('file_path')
    ssh_details = session.get('ssh_details')

    if not ssh_details:
        return render_template('error.html', error='SSH details not found in session')

    try:
        with get_ssh_sftp_client(ssh_details['server_address'], ssh_details['username'], ssh_details['password']) as (ssh_client, sftp_client):
            with sftp_client.open(file_path, 'r') as file:
                contents = file.read().decode('utf-8')  # Ensure text mode reading and decoding
            return render_template('edit_file.html', file_path=file_path, contents=contents)
    except Exception as e:
        return render_template('error.html', error=str(e))

# This route saves file to the server.

@app.route('/save_edited_file', methods=['POST'])
def save_edited_file():
    ssh_details = session.get('ssh_details')
    if not ssh_details:
        return jsonify({'error': 'SSH details not found in session'}), 401

    data = request.get_json()
    if data is None:
        return jsonify({'error': 'No data received'}), 400
    print('Received data:', data)  # Debugging line

    file_path = data.get('file_path')
    content = data.get('content')

    try:
        with get_ssh_sftp_client(ssh_details['server_address'], ssh_details['username'], ssh_details['password']) as (ssh_client, sftp_client):
            with sftp_client.open(file_path, 'w') as file:
                file.write(content)  # Ensure content is a string
            return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': f'An error occurred: {e}'}), 500
    # This route is returning edit file page.

# This route is returning change permissions page.

@app.route('/change_permissions', methods=['GET'])
def change_permissions():
    file_path = request.args.get('file_path')
    ssh_details = session.get('ssh_details')

    if not ssh_details:
        return render_template('error.html', error='SSH details not found in session')

    try:
        with get_ssh_sftp_client(ssh_details['server_address'], ssh_details['username'], ssh_details['password']) as (ssh_client, sftp_client):
            # Fetch the current permissions
            file_attr = sftp_client.stat(file_path)
            # Get the last three digits, which represent the file permissions
            current_permissions = oct(file_attr.st_mode)[-3:]
            return render_template('change_permissions.html', file_path=file_path, current_permissions=current_permissions)
    except Exception as e:
        return render_template('error.html', error=str(e))

# This route change permissions for items.

@app.route('/set_permissions', methods=['POST'])
def set_permissions():
    ssh_details = session.get('ssh_details')
    if not ssh_details:
        return jsonify({'error': 'SSH details not found in session'}), 401

    data = request.get_json()
    file_path = data.get('file_path')
    permissions = data.get('permissions')

    try:
        # Convert permissions to an octal number
        numeric_permissions = int(permissions, 8)
        with get_ssh_sftp_client(ssh_details['server_address'], ssh_details['username'], ssh_details['password']) as (ssh_client, sftp_client):
            sftp_client.chmod(file_path, numeric_permissions)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': f'An error occurred: {e}'}), 500

# This routes for resetting path and returning home route.

@app.route('/reset_path')
def reset_path():
    ssh_details = session.get('ssh_details')
    if not ssh_details:
        return redirect(url_for('index'))

    ssh_details['current_path'] = '/home/' + ssh_details['username']
    session.modified = True
    return redirect(url_for('home'))

# This route resetting the path for open route

@app.route('/reset_session_path', methods=['POST'])
def reset_session_path():
    ssh_details = session.get('ssh_details')
    if not ssh_details:
        return jsonify({'error': 'SSH details not found in session'}), 401

    # Reset the path to a default value, like the user's home directory
    default_path = '/'  # Modify as needed
    ssh_details['current_path'] = default_path
    session.modified = True
    return jsonify({'success': 'Session path reset to default', 'default_path': default_path})


if __name__ == '__main__':
    app.run(debug=True)
