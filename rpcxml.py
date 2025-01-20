import connections
import time

multiCallMethods = [
        "d.name",
        "d.base_path",
        "d.completed_bytes",
        "d.size_bytes",
        "d.custom1",
        "d.is_active",
        "d.ratio",
    ]
multiCallMethodsLen = len(multiCallMethods)


def get_hash_list(rpc):
    hash = rpc.download_list("", "main")
    return hash, len(hash)


def build_multi_call(hash):
    multi_call_array = []
    for m in multiCallMethods:
        multi_call_array.append({'methodName': m, 'params': [hash]})
    return multi_call_array


def make_call(rpc):
    hashList = get_hash_list(rpc)
    payloadArray = []
    for i in range(hashList[1]):
        outputDict = {}
        outputDict["hash"] = hashList[0][i]
        call = build_multi_call(hashList[0][i])
        multiCallOutput = rpc.system.multicall(call)
        for i in range(multiCallMethodsLen):
            outputDict[multiCallMethods[i]] = multiCallOutput[i]
        payloadArray.append(outputDict)
    return payloadArray, hashList[1]


def make_call_literal(rpc, hash, method):
    multi_call_array = []
    methodList = method.split(',')
    for m in methodList:
        multi_call_array.append({'methodName': m, 'params': [hash]})
    return rpc.system.multicall(multi_call_array)


def set_custom_comment_open(rpc, hash):
    custom1 = make_call_literal(rpc, hash, "d.custom1")
    if custom1[0][0] == '':
        rpc.d.custom1.set(hash, "Only on Remote Server")


def set_custom_comment_close(rpc, hash):
    rpc.d.custom1.set(hash, "Downloaded to Home Server")


def get_torrent_data(payloadArray, hash):
    for entry in payloadArray:
        if entry["hash"] == hash:
            name = entry["d.name"][0]
            base_path = entry["d.base_path"][0]
            size_bytes = entry["d.size_bytes"][0]
            completed_bytes = entry["d.completed_bytes"][0]
            if completed_bytes == size_bytes:
                completed_flag = 1
            else:
                completed_flag = 0
            custom1 = entry["d.custom1"][0]
            if custom1.find("Home Server") > 0:
                transferred_to_homeServer = 1
            else:
                transferred_to_homeServer = 0
            isActive = entry["d.is_active"][0]
            ratio = entry["d.ratio"][0]
            return (name, base_path, size_bytes, completed_bytes,
                    completed_flag, custom1, transferred_to_homeServer,
                    isActive, ratio)


def get_file_details(base_path, ratio):
    command = f"stat -c '%Y' '{base_path}'"
    create_date = connections.execute_command_over_ssh("seedbox", command)
    command = f"stat -c '%F' '{base_path}'"
    path_type = connections.execute_command_over_ssh("seedbox", command)
    create_date = int(create_date.strip())
    current_date = int(time.time())
    age = current_date - create_date
    if age > 950400 or ratio > 1:
        delete_flag = 1
    else:
        delete_flag = 0
    return age, delete_flag, path_type


def delete_torrent(rpc, hash):
    rpc.system.multicall(
        [
            {"methodName": "d.custom5.set", "params": [hash, "1"]},
            {"methodName": "d.delete_tied", "params": [hash]},
            {"methodName": "d.erase", "params": [hash]},
        ]
    )
