import connections
import rpcxml
import time


def media_server():

    seedBoxUserName = "krandlehandle"
    seedBoxAddress = "ant.seedhost.eu"
    rtorrentXMLPort = 5060
    remoteHost = "127.0.0.1"

    with connections.create_ssh_tunnel(
        "seedbox",
        remoteHost,
        rtorrentXMLPort
    ):
        print("Tunnel is active. You can connect to rTorrent now!")
        rpc = connections.connect_to_rtorrent(
            seedBoxUserName,
            seedBoxAddress
        )
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
                    print(f"Download {base_path} through LFTP")
                    connections.run_lftp("seedbox", path_type, base_path)
                    rpcxml.set_custom_comment_open(rpc, hash)
                if transferred_to_homeServer == 1 and delete_flag == 1:
                    print(f"Delete {base_path} from seedbox")
                    rpcxml.delete_torrent(rpc, hash)


if __name__ == "__main__":
    while True:
        media_server()
        time.sleep(10)
