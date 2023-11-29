#!/bin/bash

# Flush existing rules to start with a clean slate
iptables -F

# Set default policies to drop all incoming and outgoing packets
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT DROP

# Allow loopback traffic (localhost)
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Allow established connections and related traffic
iptables -A INPUT -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
iptables -A OUTPUT -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

# Allow SSH connections (replace 22 with your SSH port if modified)
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow HTTP and HTTPS connections (optional)
# iptables -A INPUT -p tcp --dport 80 -j ACCEPT
# iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow DNS (UDP)
# iptables -A OUTPUT -p udp --dport 53 -j ACCEPT

# Allow outgoing HTTP, HTTPS, and DNS requests (optional)
# iptables -A OUTPUT -p tcp --dport 80 -j ACCEPT
# iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT
# iptables -A OUTPUT -p udp --dport 53 -j ACCEPT

# Log and drop all other incoming connections (optional)
# iptables -A INPUT -j LOG --log-prefix "Dropped: "
# iptables -A INPUT -j DROP

# Log and drop all other outgoing connections (optional)
# iptables -A OUTPUT -j LOG --log-prefix "Dropped: "
# iptables -A OUTPUT -j DROP

# Save the rules to persist across reboots (may vary based on your Linux distribution)
iptables-save > /etc/iptables/rules.v4   # IPv4 rules
# ip6tables-save > /etc/iptables/rules.v6 # IPv6 rules (if needed)
