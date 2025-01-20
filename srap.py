import connections
import os
import rpcxml

import connections
import os
import rpcxml


if __name__ == "__main__":

    seedBoxUserName = "krandlehandle"
    seedBoxAddress = "ant.seedhost.eu"
    rtorrentXMLPort = 5060
    remoteHost = "127.0.0.1"
    sshKey = os.path.expanduser("~/.ssh/id_rsa")

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
        hash = "10329963D48D47D5CCF6BE3D29AB2DCDE4269572"
        methodList = "d.base_path"
        rpc.system.multicall([{"methodName": "d.custom5.set", "params": [hash, "1"]},
        {"methodName": "d.delete_tied", "params": [hash]},
        {"methodName": "d.erase", "params": [hash]},
        ])

