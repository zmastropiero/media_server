import yaml
import os
from env_resolver import docker_compose_config

docker_config = docker_compose_config("torrent_app")

compose_template = f"""version: "3.9"
services:
  qbittorrent:
    image: "{docker_config['image']}"
    container_name: "{docker_config['container_name']}"
    network_mode: "{docker_config['network_mode']}"
    environment:
      - VPN_ENABLED={"yes" if docker_config.get('vpn_enabled',
                                                False) else "no"}
      - VPN_PROV={docker_config.get('vpn_provider', '')}
      - VPN_USER={docker_config.get('vpn_user', '')}
      - VPN_PASS={docker_config.get('vpn_pass', '')}
    volumes:
      - {docker_config['config_dir']}:/config
      - {docker_config['data_dir']}:/downloads
    ports:
      - {docker_config['ports'][0]}
    restart: {docker_config['restart_policy']}
"""

# Save the file
output_path = docker_config["compose_path"]
with open(output_path, "w") as f:
    f.write(compose_template)

print(f"Generated {output_path} successfully "
      f"for {docker_config['env']} environment.")