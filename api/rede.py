"""Endereços privados locais e origens explícitas para a demonstração na LAN."""

import ipaddress
import os
import socket


def ips_locais() -> list[str]:
    candidatos = os.environ.get("HORUS_LOCAL_IPS", "").split(",")
    if not any(candidatos):
        try:
            candidatos = [entry[4][0] for entry in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)]
        except OSError:
            candidatos = []
    resultado = []
    for candidato in candidatos:
        try:
            ip = ipaddress.ip_address(candidato.strip())
            if isinstance(ip, ipaddress.IPv4Address) and ip.is_private and not (ip.is_loopback or ip.is_link_local or ip.is_unspecified):
                resultado.append(str(ip))
        except ValueError:
            continue
    return sorted(set(resultado))


def origens_locais() -> list[str]:
    hosts = ["localhost", "127.0.0.1", *ips_locais()]
    portas = {5173, 4173}
    porta = os.environ.get("HORUS_WEB_PORT", "5173")
    if porta.isdigit() and 1 <= int(porta) <= 65535:
        portas.add(int(porta))
    return [f"{esquema}://{host}:{p}" for host in hosts for esquema in ("http", "https") for p in sorted(portas)]
