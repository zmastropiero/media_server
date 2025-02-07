import os
import re
import yaml
import json


def resolve_env_variables(yaml_content):
    """Replaces !ENV VAR_NAME with actual environment variables."""
    env_pattern = re.compile(r'!ENV (\w+)')

    def env_replacer(match):
        env_var = match.group(1)
        return os.getenv(env_var, f'<<MISSING:{env_var}>>')

    return env_pattern.sub(env_replacer, yaml_content)


def load_config():
    """Dynamically determines the correct `config.yaml` path and loads it."""

    # Determine the current environment (default to "dev")
    env = os.getenv("MEDIA_SERVER_ENV", "dev")

    # Dynamically set the config path based on the environment
    if env == "dev":
        config_path = "/usr/local/srv/dev/projects/media_server/config.yaml"
    elif env == "prod":
        config_path = "/usr/local/srv/dev/scripts/media_server/config.yaml"
    else:
        raise ValueError(f"Unknown environment: {env}")

    # Read and resolve environment variables in the YAML file
    with open(config_path, "r") as file:
        yaml_content = file.read()

    resolved_yaml = resolve_env_variables(yaml_content)
    config = yaml.safe_load(resolved_yaml)

    # # Merge base config with environment-specific config
    # env_config = {**config.get("base", {}), **config[env]}
    # env_config["env"] = env  # Store the active environment in the config

    return config, env


def qbitorrent_config():
    config, env = load_config()
    baseConfig = {**config.get("base", {}), **config[env]}
    configDict = {
        "env": env,
        "torrentFiles": baseConfig["torrentfiles"],
        "savePath": baseConfig["dropbox"],
        "savePathActual": baseConfig["dropboxactual"],
        "qbitorrentHost": baseConfig["qbitorrent_host"],
        "qbitorrentUsername": baseConfig["qbitorrent_username"],
        "qbitorrentPassword": baseConfig["qbitorrent_password"],
        "qbitorrentPort": baseConfig["qbitorrent_port"],
        "completedFolder": baseConfig["completed"],
        "log": baseConfig["log"],
        "hitAndRunTime": baseConfig["hitAndRunTime"]
    }
    return configDict


def docker_compose_config(application):
    config, env = load_config()
    # Safely access the docker section and merge configurations
    dockerConfig = config.get("docker", {}).get(env, {}).get(application, {})
    configDict = {
        "env": env,
        "image": dockerConfig["image"],
        "container_name": dockerConfig["container_name"],
        "network_mode": dockerConfig["network_mode"],
        "data_dir": dockerConfig["data_dir"],
        "config_dir": dockerConfig["config_dir"],
        "port": dockerConfig["port"],
        "ports": dockerConfig["ports"],
        "restart_policy": dockerConfig["restart_policy"],
        "vpn_enabled": dockerConfig["vpn_enabled"],
        "compose_path": dockerConfig["compose_path"],
        "service": dockerConfig["service"],
        "network": dockerConfig["network"]
        # "vpn_provider": dockerConfig["vpn_provider"],
        # "vpn_user": dockerConfig["vpn_user"],
        # "vpn_pass": dockerConfig["vpn_pass"],
    }
    if env=="prod":
        configDict["vpn_provider"] = dockerConfig["vpn_provider"]
        configDict["vpn_user"] = dockerConfig["vpn_user"]
        configDict["vpn_pass"] = dockerConfig["vpn_pass"]
    return configDict


def log_config():
    config, env = load_config()
    baseConfig = {**config.get("base", {}), **config[env]}
    configDict = {
        "env": env,
        "log": baseConfig["log"],
        "log_level": baseConfig["log_level"],
    }
    return configDict
 

