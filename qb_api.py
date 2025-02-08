
import qbittorrentapi
import os
from contextlib import contextmanager
import yaml
import time 
import re
import file_system
import logging
from env_resolver import qbitorrent_config
from env_resolver import log_config


# Load logging configuration
log_settings = log_config()

# Configure logging dynamically
logging.basicConfig(
    filename=log_settings["log"],  # Dynamically set log file path
    level=getattr(logging, log_settings["log_level"].upper(), logging.INFO),  # Convert log level to uppercase
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Example log message
logging.info("Logging initialized with level: %s and log file: %s",
             log_settings["log_level"], log_settings["log"])


class QBittorrentManager:
    def __init__(self, config):
        self.host = config["qbitorrentHost"]
        self.port = config["qbitorrentPort"]
        self.username = config["qbitorrentUsername"]
        self.password = config["qbitorrentPassword"]
        self.client = None

    def __enter__(self):
        self.client = qbittorrentapi.Client(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password
        )
        try:
            self.client.auth_log_in()
            logging.debug("Successfully connected to qBittorrent!")
            return self
        except qbittorrentapi.LoginFailed as e:
            logging.error(f"Login failed: {e}")
            return None

    def __exit__(self, exc_type, exc_value, traceback):
        if self.client:
            try:
                self.client.auth_log_out()
                logging.debug("Logged out from qBittorrent.")
            except Exception as e:
                logging.error(f"Error during logout: {e}")

    def download_new_torrents(self, queueList, dropbox):
        """
        Download new torrents from the torrentFiles folder
        queueList is returned from file_system.torrent_download_queue
        """
        for torrentDownload in queueList:
            try:
                logging.info(f"Adding torrent: {torrentDownload[0]}"
                             f" to category {torrentDownload[1]}")
                add = self.client.torrents_add(
                        torrent_files=torrentDownload[0],
                        save_path=dropbox,
                        category=torrentDownload[1],
                        forced=True
                        )
                logging.info(f"API Response: {add}")
                if add == "Ok.":
                    logging.info(f"Deleting torrent file: "
                                 f"{torrentDownload[0]}")
                    file_system.delete_by_path(torrentDownload[0])

            except qbittorrentapi.exceptions.APIError as e:
                logging.error(f"qBittorrent API error: {e}")
            except Exception as e:
                logging.error(f"Unexpected error: {e}")

    def current_torrents(self, hitAndRunTime):
        """
        Api call to qbitorrent for details on all torrents in the application
        """
        all_torrent_dict = []
        for torrent in self.client.torrents_info():
            name = torrent.name
            hash_value = torrent.hash
            tags = torrent.tags
            completion_on = torrent.completion_on
            added_on = torrent.added_on
            ratio = torrent.ratio
            tags = torrent.tags
            content_path = torrent.content_path
            category = torrent.category
            # Determine status
            status = "not finished" if completion_on == -1 else "finished"
            # Calculate age in days
            age_in_seconds = ((int(time.time()) - added_on)
                           if completion_on != -1 else 0)
            # Determine hit-and-run status
            hit_and_run = (
                "no" if ratio > 1 or age_in_seconds > hitAndRunTime else "yes"
            )
            # check if file is reseed
            reseed = (
                "yes" if category == "reseed" else "no"
            )
            # Construct the dictionary for this torrent
            info_payload = {
                "name": name,
                "hash": hash_value,
                "tags": tags,
                "path": content_path,
                "status": status,
                "age": age_in_seconds,
                "ratio": ratio,
                "hitAndrun": hit_and_run,
                "tags": tags,
                "category": category,
                "reseed": reseed,
            }
            all_torrent_dict.append(info_payload)

        return all_torrent_dict

    def tag(self, hash, tag):
        """
        add tag to torrent by hash
        """
        self.client.torrents_add_tags(
            tags=tag,
            torrent_hashes=hash
            )

    def delete_torrent(self, hash):
        """
        delete torrents by hash
        """
        self.client.torrents_delete(
            torrent_hashes=hash,
            delete_files=True
        )


def resolve_env_variables(yaml_content):
    """Replaces !ENV VAR_NAME with actual environment variables."""
    env_pattern = re.compile(r'!ENV (\w+)')

    def env_replacer(match):
        env_var = match.group(1)
        return os.getenv(env_var, f'<<MISSING:{env_var}>>')

    return env_pattern.sub(env_replacer, yaml_content)


@contextmanager
def qbtorrent_api_call(host, port, username, password):
    conn_info = {
        "host": host,  # Replace with your qBittorrent host IP
        "port": port,        # Replace with your qBittorrent Web UI port
        "username": username,  # Replace with your username
        "password": password  # Replace with your password
    }
    # Create a client
    qbt_client = qbittorrentapi.Client(**conn_info)
    # Test the connection
    try:
        # Log in to qBittorrent
        qbt_client.auth_log_in()
        logging.debug("Successfully connected to qBittorrent!")
        yield qbt_client  # Pass the client to the caller
    except qbittorrentapi.LoginFailed as e:
        logging.error("Login failed:", e)
        yield None  # Pass None if the login fails
    finally:
        try:
            qbt_client.auth_log_out()
            logging.debug("Logged out from qBittorrent.")
        except Exception as e:
            logging.error("Error during logout:", e)


if __name__ == "__main__":
    configDict = qbitorrent_config()
    with QBittorrentManager(configDict) as qbt_manager:
        if qbt_manager:

            # Check for and download new torrents
            queue_list = file_system.torrent_download_queue(
                configDict["torrentFiles"])
            downloaded_torrents = qbt_manager.download_new_torrents(
                queue_list, configDict["savePath"])

            currentTorrents = qbt_manager.current_torrents(hitAndRunTime=configDict["hitAndRunTime"])
            for torrent in currentTorrents:
                hash = torrent["hash"]
                torrentName = torrent["name"]
                hitAndRun = torrent["hitAndrun"]
                movedTag, hitAndRunTag = file_system.tag_checker(
                    torrent["tags"])
                logging.debug(f"This file has a moved value of {movedTag} "
                              f"and a hit and run value of {hitAndRunTag}")
                movedTag = 1 if torrent["reseed"] == "yes" else movedTag 

                # move completed torrents
                if torrent["status"] == "finished" and movedTag == 0:
                    sourcePath = torrent["path"]
                    sourcePathActual = configDict["savePathActual"]
                    destinationPath = (configDict["completedFolder"])
                    category = torrent["category"]
                    logging.info(f"Finished torrent {torrentName}\n"
                                 f" Copying from {sourcePath}\n"
                                 f" to {destinationPath} : {category}")
                    try:
                        file_system.move_completed(
                            sourcePath,
                            sourcePathActual,
                            destinationPath,
                            category
                            )
                        # if succesful update tag
                        logging.info(f"Adding Moved Tag "
                                     f"to torrent {torrentName}")
                        tag = qbt_manager.tag(
                            hash=hash,
                            tag="moved_to_completed"
                        )
                    except Exception as e:
                        logging.error(f"Unexpected error: {e}")
                if hitAndRun == "yes":
                    logging.debug(f"{torrentName} is currently a hit and run")
                    if hitAndRunTag == 0:
                        try:
                            logging.info(f"Adding hit and run tag "
                                         f"to {torrentName}")
                            tag = qbt_manager.tag(
                                hash=hash,
                                tag="hit_and_run"
                            )
                        except Exception as e:
                            logging.error(f"Unexpected error: {e}")
                    elif hitAndRunTag == 1:
                        logging.debug(f"{torrentName} is accurately tagged "
                                      f"hit and run")
                elif hitAndRun == "no" and movedTag == 1:
                    logging.info(f"{torrentName} has fulfilled"
                                 f"seeding requirement")
                    qbt_manager.delete_torrent(
                        hash=hash
                    )
