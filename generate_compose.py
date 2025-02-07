from env_resolver import docker_compose_config

docker_config = docker_compose_config("torrent_app")

compose_template = f"""version: "3.9"
services:
  {docker_config['service']}:
    platform: linux/arm64
    image: "{docker_config['image']}"
    container_name: "{docker_config['container_name']}"
    cap_add:
      - NET_ADMIN
    environment:
      - VPN_ENABLED={"yes" if docker_config.get('vpn_enabled', False) else "no"}
      {"- VPN_USER=" + docker_config['vpn_user'] if docker_config.get('vpn_user') else ""}
      {"- VPN_PASS=" + docker_config['vpn_pass'] if docker_config.get('vpn_pass') else ""}
      {"- VPN_PROV=" + docker_config['vpn_provider'] if docker_config.get('vpn_provider') else ""}
      - VPN_CLIENT=openvpn
      - LAN_NETWORK={docker_config.get('lan_network', '192.168.0.0/24')}
      - NAME_SERVERS={docker_config.get('name_servers', '8.8.8.8')}
      - PUID={docker_config.get('puid', '501')}
      - PGID={docker_config.get('pgid', '20')}
      - ENABLE_PORT_FORWARDING={"yes" if docker_config.get('enable_port_forwarding', True) else "no"}
      - FORWARDED_PORT_FILE=/config/forwarded_port
      - WEBUI_PORT={docker_config["port"]}
    volumes:
      - {docker_config['config_dir']}:/config
      - {docker_config['data_dir']}:/downloads
    user: "501:20"
    ports:
      - {docker_config['ports'][0]}
    restart: {docker_config.get('restart_policy', 'unless-stopped')}
    networks:
      - {docker_config["network"]}

networks:
  {docker_config["network"]}:
    driver: bridge
"""

# Save the file
output_path = docker_config["compose_path"]
with open(output_path, "w") as f:
    f.write(compose_template)

print(f"Generated {output_path} successfully "
      f"for {docker_config['env']} environment.")