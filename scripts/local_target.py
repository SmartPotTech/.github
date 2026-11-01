"""Destino de las herramientas de QA: solo la propia máquina.

Las suites de auditoría, contraste A/B y estrés envían credenciales de la cuenta demo y tokens JWT al destino que
reciben por línea de comandos. Sin validar, ese destino podía ser cualquier URL que entienda urllib (otro host, la
red interna del runner o file://), y un agente o una persona podía terminar reenviando el token o cargando un
servidor compartido. La URL se rearma aquí solo con valores conocidos: esquema http/https, un host de loopback y un
puerto numérico.
"""

from urllib.parse import urlsplit

_SCHEMES = ("http", "https")
_LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1")


def loopback_base_url(raw: str) -> str:
    """Devuelve la URL base normalizada o termina el programa si el destino no es local."""
    parts = urlsplit(raw.strip())
    scheme = next((known for known in _SCHEMES if known == parts.scheme.lower()), None)
    host = next((known for known in _LOOPBACK_HOSTS if known == (parts.hostname or "")), None)
    try:
        port = parts.port or (443 if scheme == "https" else 80)
    except ValueError:
        port = None
    if scheme is None or host is None or port is None:
        raise SystemExit(
            f"Destino no permitido: {raw!r}. Las pruebas de QA solo apuntan a la máquina local "
            "(http o https en 127.0.0.1, localhost o ::1, con un puerto válido)."
        )
    port = int(port)
    # localhost se fija en IPv4: en Windows resolver ::1 primero suma ~2 s por conexión.
    if host == "localhost":
        host = "127.0.0.1"
    netloc = f"[{host}]:{port}" if ":" in host else f"{host}:{port}"
    return f"{scheme}://{netloc}"
