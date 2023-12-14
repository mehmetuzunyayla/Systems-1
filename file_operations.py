# Implement the create_directory function
from paramiko import SFTPClient

parent_directory = "/home/mehmet"
def create_directory(directory_name, parent_directory):
    # Use the SFTP client to create the directory
    SFTPClient.mkdir(f'{parent_directory}/{directory_name}')