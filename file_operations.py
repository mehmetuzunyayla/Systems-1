from contextlib import contextmanager
import paramiko

# Thanks to this helper function our system is dynamic to the all users.

def get_user_home_directory(ssh_client):
    # Get the home directory of the connected user
    stdin, stdout, stderr = ssh_client.exec_command("echo $HOME")
    home_directory = stdout.read().decode().strip()
    return home_directory


@contextmanager
def get_ssh_sftp_client(server_address, username, password):
    """Establish an SSH connection and yield both SSH and SFTP clients."""
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(server_address, username=username, password=password)
    sftp_client = ssh_client.open_sftp()
    try:
        yield ssh_client, sftp_client  # Yielding both clients
    finally:
        sftp_client.close()
        ssh_client.close()
