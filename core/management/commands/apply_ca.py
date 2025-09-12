import logging
import certifi
import hashlib
from cryptography import x509
from cryptography.hazmat.backends import default_backend

from django.conf import settings
from django.core.management import BaseCommand

log = logging.getLogger(__name__)


def decode_cert(cert_string):
    oid_name = {
        'countryName': "C",
        'organizationName': "O",
        'commonName': "CN",
    }
    utf8_cert_string = cert_string.encode('utf-8')
    cert = x509.load_pem_x509_certificate(utf8_cert_string, default_backend())

    md5_fingerprint = hashlib.md5(utf8_cert_string).hexdigest()
    sha1_fingerprint = hashlib.sha1(utf8_cert_string).hexdigest()
    sha256_fingerprint = hashlib.sha256(utf8_cert_string).hexdigest()

    cert_details = {
        'Subject': " ".join(
            [f"{oid_name[attr.oid._name]}={attr.value}" for attr in cert.subject if attr.oid._name in oid_name]
        ),
        'Issuer': " ".join(
            [f"{oid_name[attr.oid._name]}={attr.value}" for attr in cert.issuer if attr.oid._name in oid_name]
        ),
        'Serial': cert.serial_number,
        'MD5 Fingerprint': ':'.join(md5_fingerprint[i:i + 2] for i in range(0, len(md5_fingerprint), 2)),
        'SHA1 Fingerprint': ':'.join(sha1_fingerprint[i:i + 2] for i in range(0, len(sha1_fingerprint), 2)),
        'SHA256 Fingerprint': ':'.join(sha256_fingerprint[i:i + 2] for i in range(0, len(sha256_fingerprint), 2)),
    }
    return cert_details


def remove_if_serial_changed(certificates_list, ca_header):
    is_present = False
    is_removed = False
    certificates = []
    for certificate in certificates_list:
        if f"Subject: {ca_header['Subject']}" in certificate:
            sha256_fingerprint = None
            for certificate_line in certificate.split("\n"):
                if certificate_line.startswith("# SHA256 Fingerprint: "):
                    sha256_fingerprint = f"{certificate_line}".replace("# SHA256 Fingerprint: ", "")

            if ca_header['SHA256 Fingerprint'] == sha256_fingerprint:
                is_present = True
                log.info("letsencrypt ca matches")
                certificates.append(certificate.strip())
            else:
                log.info("letsencrypt ca changes detected")
                is_removed = True
        else:
            certificates.append(certificate.strip())

    return certificates, is_present, is_removed


def process_certificates(file_path, ca_header):
    with open(file_path, 'r') as file:
        contents = file.read()

    certificates_list = contents.split("\n\n")
    certificates_list, is_present, is_removed = remove_if_serial_changed(
        certificates_list,
        ca_header
    )

    if is_removed:
        log.info("removing old letsencrypt ca")
        updated_contents = "\n\n".join(certificates_list)

        with open(file_path, 'w') as file:
            file.write(updated_contents + "\n")
        log.info("old letsencrypt ca removed")

    return is_removed or not is_present


def append_current_certificate(certifi_ca_path, ca_header, ca):
    with open(certifi_ca_path, 'a') as ca_file:
        ca_file.write("\n")
        for key, value in ca_header.items():
            ca_file.write(f"# {key}: {value}\n")
        ca_file.write(ca)


def apply_custom_cert():
    if hasattr(settings, "CUSTOM_CERT") and settings.CUSTOM_CERT:
        log.info("Loading letsencrypt ca...")

        certifi_ca_path = certifi.where()
        log.info(f"Certificate store: {certifi_ca_path}")

        letsencrypt_cert_header = decode_cert(settings.CUSTOM_CERT)
        do_update = process_certificates(certifi_ca_path, letsencrypt_cert_header)

        if do_update:
            log.info("Appending letsencrypt ca")
            append_current_certificate(certifi_ca_path, letsencrypt_cert_header, settings.CUSTOM_CERT)
            log.info("Letsencrypt ca appended")
        else:
            log.info("letsencrypt ca exits and is current")


class Command(BaseCommand):
    def handle(self, **options):
        apply_custom_cert()
