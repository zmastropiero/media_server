import os
import re
import yaml


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
        config_path = "/usr/local/srv/dev/scripts/config.yaml"
    else:
        raise ValueError(f"Unknown environment: {env}")

    # Read and resolve environment variables in the YAML file
    with open(config_path, "r") as file:
        yaml_content = file.read()

    resolved_yaml = resolve_env_variables(yaml_content)
    config = yaml.safe_load(resolved_yaml)

    # Merge base config with environment-specific config
    env_config = {**config.get("base", {}), **config[env]}
    env_config["env"] = env  # Store the active environment in the config

    return env_config


def qbitorrent_config(env_config):
    configDict = {
        "env": env_config["env"],
        "torrentFiles": env_config["torrentfiles"],
        "savePath": env_config["dropbox"],
        "savePathActual": env_config["dropboxactual"],
        "qbitorrentHost": env_config["qbitorrent_host"],
        "qbitorrentUsername": env_config["qbitorrent_username"],
        "qbitorrentPassword": env_config["qbitorrent_password"],
        "qbitorrentPort": env_config["qbitorrent_port"],
        "completedFolder": env_config["completed"],
        "log": env_config["log"],
    }
    return configDict



load_config()
