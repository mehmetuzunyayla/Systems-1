# Implement the create_directory function
from paramiko import SFTPClient

def get_user_home_directory(ssh_client):
    # Get the home directory of the connected user
    stdin, stdout, stderr = ssh_client.exec_command("echo $HOME")
    home_directory = stdout.read().decode().strip()
    return home_directory