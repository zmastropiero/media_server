from env_resolver import docker_compose_config

qbt_config = docker_compose_config("torrent_app")
portainer_config = docker_compose_config("portainer")

compose_template = f"""services:
  {qbt_config['service']}:
    platform: linux/arm64
    image: "{qbt_config['image']}"
    container_name: "{qbt_config['container_name']}"
    cap_add:
      - NET_ADMIN
    environment:
      - VPN_ENABLED={"yes" if qbt_config.get('vpn_enabled', False) else "no"}
      {"- VPN_USER=" + qbt_config['vpn_user'] if qbt_config.get('vpn_user') else ""}
      {"- VPN_PASS=" + qbt_config['vpn_pass'] if qbt_config.get('vpn_pass') else ""}
      {"- VPN_PROV=" + qbt_config['vpn_provider'] if qbt_config.get('vpn_provider') else ""}
      - VPN_CLIENT=openvpn
      - LAN_NETWORK={qbt_config.get('lan_network', '192.168.0.0/24')}
      - NAME_SERVERS={qbt_config.get('name_servers', '8.8.8.8')}
      - PUID={qbt_config.get('puid', '501')}
      - PGID={qbt_config.get('pgid', '20')}
      - STRICT_PORT_FORWARD={"yes" if qbt_config.get('strict_port_forward', True) else "no"}
      - WEBUI_PORT={qbt_config["port"]}
    volumes:
      - {qbt_config['config_dir']}:/config
      - {qbt_config['data_dir']}:/downloads
    ports:
      - {qbt_config['ports'][0]}
    restart: {qbt_config.get('restart_policy', 'unless-stopped')}
    networks:
      - {qbt_config["network"]}
  {portainer_config['service']}:
    image: {portainer_config["image"]}
    container_name: "{portainer_config['container_name']}"
    restart: {portainer_config.get('restart_policy', 'unless-stopped')}
    ports:
      - {portainer_config['ports'][0]}
      - {portainer_config['ports'][1]}
    volumes:
      - {portainer_config['volumes'][0]}
      - {portainer_config['volumes'][1]}
    networks:
      - {portainer_config["network"]}
networks:
  {qbt_config["network"]}:
    driver: bridge
"""

# Save the file
output_path = qbt_config["compose_path"]
with open(output_path, "w") as f:
    f.write(compose_template)

print(f"Generated {output_path} successfully "
      f"for {qbt_config['env']} environment.")