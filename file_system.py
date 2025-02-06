import os
import shutil
import logging


def torrent_download_queue(torrentFileFolder):
    """
    check for .torrent files in the torrentfilefolder #
    return a list of tuples (path to .torrent,torrent category) #
    """
    logging.debug(f"Scanning for torrent files in {torrentFileFolder}")
    torrentFileList = []
    for torrentTypeFolder in os.scandir(torrentFileFolder):
        if torrentTypeFolder.is_dir():
            logging.debug(f"Entering directory {torrentTypeFolder}")
            for torrentFile in os.scandir(torrentTypeFolder):
                if (os.path.splitext(torrentFile)[1] == ".torrent"):
                    logging.info(f".torrent file found:{torrentFile.path}")
                    torrentFileList.append(tuple([torrentFile.path,
                                           torrentTypeFolder.name]))
        else:
            logging.warning(f"Non-Directory in {torrentFileFolder} : "
                            f"{torrentTypeFolder}")
    return torrentFileList


def delete_by_path(file_path):
    """
    Delete and file by its path
    """
    if os.path.exists(file_path):
        os.remove(file_path)
        logging.info(f"File '{file_path}' deleted successfully.")
    else:
        logging.warning(f"File '{file_path}' not found.")


def move_completed(sourcePath: str, sourcePathActual: str,
                   completedPath, category):
    """
    soucePath - a completed download file or directory
    completedPath - location of completed torrent
    category - category in app & folder within completed path to store torrent
    """
    sourcePath = sourcePath.replace("/downloads/", sourcePathActual)
    destinationDir = completedPath+"/"+category
    if not os.path.exists(destinationDir):
        logging.warning(f"No folder for category {category}"
                        f"directory {destinationDir} created")
        os.makedirs(destinationDir)

    destinationPath = os.path.join(destinationDir,
                                   os.path.basename(sourcePath))

    if os.path.exists(sourcePath):
        if os.path.isfile(sourcePath):
            try:
                shutil.copyfileobj(sourcePath, destinationPath, length=16*1024)
                logging.info(f"File {sourcePath} copied successfully"
                             f"to {destinationPath}")
                return destinationPath
            except Exception as e:
                logging.error(f"Error copying file: {e}")
                return None
        elif os.path.isdir(sourcePath):
            try:
                shutil.copytree(sourcePath,
                                destinationPath,
                                dirs_exist_ok=True,
                                )
                logging.info(f"Directory {sourcePath} copied successfully"
                             f"to {destinationPath}")
                return destinationPath
            except Exception as e:
                logging.error(f"Error copying directory: {e}")
                return None

    return None


def tag_checker(tags):
    """
    Accepts a comma seperated list of tags from qbitorrent
    [0] - If 1 torrent has already been moved to completed folder
    [1] - If 1 torrent is a still hit_and_run
    """
    tagList = tags.split(',')
    moved = 0
    hit_and_run = 0
    for tag in tagList:
        if tag == "moved_to_completed":
            moved = 1
        if tag == "hit_and_run":
            hit_and_run = 1
    return moved, hit_and_run
