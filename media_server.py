import connections
import rpcxml
import time


def media_server():

    with connections.create_ssh_tunnel():
        print("Tunnel is active. You can connect to rTorrent now!")
        rpc = connections.connect_to_rtorrent()
        apiOutput = rpcxml.make_call(rpc)
        apiOutputArray = apiOutput[0]
        apiOutputCount = apiOutput[1]

        for i in range(apiOutputCount):
            hash = apiOutputArray[i]["hash"]
            (
                name,
                base_path,
                size_bytes,
                completed_bytes,
                completed_flag,
                custom1,
                transferred_to_homeServer,
                isActive,
                ratio
            ) = rpcxml.get_torrent_data(
                apiOutputArray,
                hash
                )
            (
                age,
                delete_flag,
                path_type
            ) = rpcxml.get_file_details(
                base_path,
                ratio
                )
            rpcxml.set_custom_comment_open(rpc, hash)
            if completed_flag == 1:
                print(transferred_to_homeServer)
                if transferred_to_homeServer == 0:
                    # print(f"Download {base_path} through LFTP")
                    # connections.run_lftp("seedbox", path_type, base_path)
                    print(f"Download {base_path} through rsync")
                    rsyncResult = connections.run_rsync(base_path)
                    if rsyncResult == 0:
                        rpcxml.set_custom_comment_close(rpc, hash)
                    else:
                        break
                if transferred_to_homeServer == 1 and delete_flag == 1:
                    print(f"Delete {base_path} from seedbox")
                    rpcxml.delete_torrent(rpc, hash)


if __name__ == "__main__":
    while True:
        media_server()
        time.sleep(10)
