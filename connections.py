from typing import Any, Generator
import paramiko
from contextlib import contextmanager
import xmlrpc.client
from urllib.parse import quote
import os
import subprocess
import yaml


def load_config(config_path="config.yaml"):
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)

    # Get the active environment
    env = os.getenv("ENVIRONMENT", config.get("environment", "dev"))

    env_config = {**config.get("base", {}), **config[env]}

    # Resolve environment variable
    env_config["rtorrent_password"] = os.getenv("RTORRENT_PASSWORD")

    return env_config


config = load_config()

seedBoxUserName = config["seedbox_username"]
seedBoxAddress = config["seedbox_address"]
seedBoxsshKey = config["home"] + config["ssh_key"]
seedBoxPassword = config["rtorrent_password"]
seedboxRootPath = config["seedbox_root_path"]

remoteHost = config["rtorrent_remote_host"]
rtorrentXMLPort = config["rtorrent_xml_port"]
rtorrentUsername = config["rtorrent_username"]
rtorrentAddress = seedBoxAddress
rtorrentPassword = seedBoxPassword

mediaServerRootPath = config["file_server"]
mediaServerDropZone = mediaServerRootPath + config["dropzone"]


@contextmanager
def create_ssh_tunnel() -> Generator[None, Any, None]:

    # Create an SSH tunnel using paramiko and bind it to a local port.
    sshHost = seedBoxAddress
    sshUsername = seedBoxUserName
    sshKey = seedBoxsshKey
    port = rtorrentXMLPort

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


def connect_to_rtorrent():
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
        lftPassword = seedBoxPassword
        local_path = mediaServerDropZone
        remote_path_simple = remote_path.replace(seedboxRootPath, "")
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
        result = subprocess.run(
            ["lftp", "-c", lftp_script],
            text=True,
            capture_output=True,
            check=True,
        )
        print("LFTP command executed successfully.")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error executing lftp command.")
        print(e.stderr)
        raise
