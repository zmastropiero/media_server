from typing import Any, Generator
import paramiko
from contextlib import contextmanager
import xmlrpc.client
from urllib.parse import quote
import os
import subprocess
from dotenv import load_dotenv
import sys

load_dotenv()

seedBoxUserName = "krandlehandle"
seedBoxAddress = "ant.seedhost.eu"
seedBoxsshKey = os.path.expanduser("~/.ssh/id_rsa")


@contextmanager
def create_ssh_tunnel(
    taget: str,
    remoteHost: str,
    port: int,
) -> Generator[None, Any, None]:

    # Create an SSH tunnel using paramiko and bind it to a local port.

    if taget == "seedbox":
        sshHost = seedBoxAddress
        sshUsername = seedBoxUserName
        sshKey = seedBoxsshKey

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        # Connect to the SSH server
        ssh.connect(
            sshHost,
            22,
            username=sshUsername,
            key_filename=sshKey)

        # log errors
        paramiko.util.log_to_file("paramiko.log")

        # Create the tunnel
        transport = ssh.get_transport()
        local_tunnel = transport.open_channel(
            "direct-tcpip", (remoteHost, port), (remoteHost, port)
        )
        print(f"SSH tunnel established: localhost:{port} -> {port}:{port}")
        yield
    finally:
        # Close the tunnel and SSH connection
        local_tunnel.close()
        ssh.close()
        print("SSH tunnel closed.")


def connect_to_rtorrent(
        rtorrentUsername: str,
        rtorrentAddress: str
):
    """
    Connect to the rTorrent XML-RPC interface via the SSH tunnel.
    """
    # Credentials

    rtorrentPassword = os.getenv("RTORRENT_PASSWORD")
    if not rtorrentPassword:
        raise ValueError("rTorrent password not in environment variables.")

    # Encode credentials to handle special characters
    encoded_credentials = (f"{quote(rtorrentUsername)}"
                           f":{quote(rtorrentPassword)}")

    # Define the ruTorrent XML-RPC URL with authentication
    rpc_url = (f"http://{encoded_credentials}@"
               f"{rtorrentUsername}.{rtorrentAddress}/{rtorrentUsername}/RPC1")

    try:
        client = xmlrpc.client.ServerProxy(rpc_url, allow_none=True)
        return client
    except Exception as e:
        print(f"Error connecting to rTorrent XML-RPC: {e}")


def execute_command_over_ssh(
    target: str,
    command: str
) -> str:
    if target == "seedbox":
        sshHost = seedBoxAddress
        sshUsername = seedBoxUserName
        sshKey = seedBoxsshKey
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        # Connect to the SSH server
        ssh.connect(
            sshHost,
            22,
            username=sshUsername,
            key_filename=sshKey
        )
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode('utf-8').strip()
        error = stderr.read().decode('utf-8').strip()

        if error:
            print(f"Error executing command: {error}")
        # else:
        #     print(f"Command executed successfully: {command}")
        return output
    finally:
        ssh.close()
        print("SSH connection closed.")


def run_lftp(
    target: str,
    path_type:  str,
    remote_path: str,
) -> None:
    if target == "seedbox":
        lftpAddress = seedBoxAddress
        lftUserName = seedBoxUserName
        lftPassword = os.getenv("RTORRENT_PASSWORD")
        local_path = "/Volumes/krandle_handle/dropbox/"
        remote_path_simple = remote_path.replace("/home22/krandlehandle/", "/")
    if path_type == "directory":
        command_type = "mirror"
        options = "--c --parallel=10 --use-pget-n=10"
    else:
        command_type = "pget"
        options = "-n 4"

    lftp_script = f"""
                set net:timeout 5;
                set net:max-retries 3;
                set net:reconnect-interval-multiplier 1;
                set net:reconnect-interval-base 5;
                set ftp:ssl-allow no;
                set dns:cache-expire 1h;
                set ftp:passive-mode off;
                open -u {lftUserName},{lftPassword} {lftpAddress}
                lcd {local_path}
                {command_type} {options or ""} {remote_path_simple}
                bye
                """
    try:
        # Use subprocess.Popen to capture real-time output
        process = subprocess.Popen(
            ["lftp", "-d", "-c", lftp_script],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Stream stdout and stderr to console in real-time
        for line in process.stdout:
            print(line, end='')

        for line in process.stderr:
            print(line, end='', file=sys.stderr)

        process.wait()  # Wait for process to complete
        if process.returncode == 0:
            print("LFTP command executed successfully.")
        else:
            print(f"LFTP command failed with return code {process.returncode}.")
    except Exception as e:
        print(f"An error occurred: {e}")
