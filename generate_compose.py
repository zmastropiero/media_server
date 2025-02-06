import yaml
import os

config_path = "/usr/local/srv/dev/projects/media_server/config.yaml"
with open(config_path, "r") as f:
    config = yaml.safe_load(f)

env = os.getenv("MEDIA_SERVER_ENV", "dev")

docker_config = config["docker"][env]["torrent_app"]

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
      - VPN_USER={os.getenv('VPN_USER', '')}
      - VPN_PASS={os.getenv('VPN_PASS', '')}
    volumes:
      - {docker_config['config_dir']}:/config
      - {docker_config['data_dir']}:/downloads
    ports:
      - {docker_config['ports'][0]}
    restart: {docker_config['restart_policy']}
"""

# Save the file
output_path = os.path.join(os.getenv("MEDIA_SERVER_PATH"),
                           "docker-compose.yml")
with open(output_path, "w") as f:
    f.write(compose_template)

print(f"Generated {output_path} successfully "
      f"for {env} environment.")
