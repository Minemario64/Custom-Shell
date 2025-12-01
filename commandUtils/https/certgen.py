from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import datetime
from pathlib import Path
import socket, ipaddress

def generate_self_signed_cert(certfile: Path = Path.home().joinpath("Appdata/Local/Temp/").joinpath("cert.pem"), keyfile: Path = Path.home().joinpath("Appdata/Local/Temp/").joinpath("key.pem")):
    # Generate private key
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    if not certfile.exists():
        certfile.touch()

    if not keyfile.exists():
        keyfile.touch()

    # Write private key to file
    with keyfile.open("wb") as f:
        f.write(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            )
        )

    # Build certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Georgia"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"Sandy Springs"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"MyCustomShellShell"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.DNSName(f"{socket.gethostname()}"),
                x509.IPAddress(ipaddress.IPv4Address(f"{socket.gethostbyname(socket.gethostname())}"))
                ]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    # Write certificate to file
    with certfile.open("wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))