nmcli con show



nmcli con mod "netplan-wlan0-DIGIFIBRA-PLUS-K7A4" \
  ipv4.addresses "192.168.1.170/24" \
  ipv4.gateway "192.168.1.1" \
  ipv4.dns "8.8.8.8,1.1.1.1" \
  ipv4.method manual

nmcli con up "netplan-wlan0-DIGIFIBRA-PLUS-K7A4"


ip route


nmcli con add type ethernet ifname eth0 con-name "eth0-estatica" \
  ipv4.addresses "192.168.1.171/24" \
  ipv4.gateway "192.168.1.1" \
  ipv4.dns "8.8.8.8,1.1.1.1" \
  ipv4.method manual \
  connection.autoconnect yes




nmcli con add type wifi ifname wlan0 con-name "iPhone 18" ssid "iPhone 18" \
  ipv4.method auto \
  wifi-sec.key-mgmt wpa-psk \
  wifi-sec.psk "12345678." \
  connection.autoconnect yes