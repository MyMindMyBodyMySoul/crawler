"""
This module fetches results out of the queue_manager and formats it in JSON to add it to da database
"""


from server.queue_manager import QueueClient
from pymongo import MongoClient, errors
from time import sleep
import datetime
from tld import get_tld
from cipher_desc import CIPHER_DESC


class Database(object):
    """
    This is the database wrapper class.
    An instance of it holds the connection to the Database and contains methods
    for operations on the Database.
    """

    def __init__(self):
        self.db_client = MongoClient('localhost', 27017)
        self.db = self.db_client.tls_crawler
        self.coll = self.db.tls_scan_results

    def insert_result(self, scan):
        """
        Putting result to The Database.

        :param scan: the result of the current scan.
        :return:
        """
        # retry the insert, if the connection to the database is lost
        for i in range(60):
            try:
                self.coll.insert_one(scan)
                break
            except errors.AutoReconnect as e:
                print e
                sleep(5)
        else:
            raise Exception("Could not insert!")
        return


def _parse_cert(command_result):

    not_before = datetime.datetime.strptime(command_result['validity']['notBefore'], '%b %d %H:%M:%S %Y %Z')
    not_after = datetime.datetime.strptime(command_result['validity']['notAfter'], '%b %d %H:%M:%S %Y %Z')
    utc_ts = datetime.datetime.utcnow()

    trusted_result = _is_trusted(command_result.get("trusted"))

    cert_dict = dict(
        issuer=command_result['issuer'].get('commonName'),
        subject=command_result['subject'].get('commonName'),
        publicKeyLengh=int(command_result['subjectPublicKeyInfo'].get('publicKeySize')),
        publicKeyAlgorithm=command_result['subjectPublicKeyInfo'].get('publicKeyAlgorithm'),
        signatureAlgorithm=command_result.get('signatureAlgorithm'),
        notValidBefore=not_before,
        notValidAfter=not_after,
        selfSigned=trusted_result.get('selfSigned'),
        trusted=trusted_result.get('trusted'),
        expired=False
    )

    if not_after < utc_ts and utc_ts > not_before:
        cert_dict['expired'] = True
    return cert_dict


def _is_trusted(signed_result):
    trusted_result = dict(
        selfSigned=True,
        trusted=False
    )
    if signed_result.get('Google') == 'ok':
        trusted_result['selfSigned'] = False
        trusted_result['trusted'] = True
    return trusted_result


def _parse_ciphers(result, protocol, public_key_size):

    ciphers_list = []
    key_status_list = [
        ('preferredCipherSuite', 'preferred'),
        ('acceptedCipherSuites', 'accepted'),
        ('errors', 'error'),
        ('rejectedCipherSuites', 'rejected')
    ]
    protocol_dict = dict(
        tlsv1='TLSv1.0',
        tlsv1_1='TLSv1.1',
        tlsv1_2='TLSv1.2',
        sslv2='SSLv2',
        sslv3='SSLv3',
    )

    preferred_cipher = None
    for (result_key, result_status) in key_status_list:
        if result_status == 'rejected':
            continue
        result_list = result[result_key]

        for ssl_cipher in result_list:

            # exclude the preferred cipher suite from the accepted ones
            if result_status == 'preferred':
                preferred_cipher = ssl_cipher
            if result_status == 'accepted' and preferred_cipher == ssl_cipher:
                preferred_cipher = None
                continue

            msg = result_list.get(ssl_cipher)[0]  # msg not used until now
            bits = result_list.get(ssl_cipher)[1]
            dh_info = result_list.get(ssl_cipher)[2]
            cipher_desc = CIPHER_DESC.get(ssl_cipher)

            cipher_dict = dict(
                cipher=ssl_cipher,
                protocol=protocol_dict.get(protocol),
                status=result_status,
                bits=bits,
                kx=cipher_desc.get("kx"),
                au=cipher_desc.get("au"),
                enc=cipher_desc.get("enc"),
                mac=cipher_desc.get("mac"),
                export=cipher_desc.get("export")
            )

            if dh_info:
                if dh_info.get("Prime"):
                    cipher_dict["curve"] = "P-%s" % dh_info.get("GroupSize")
                    cipher_dict["kxStrength"] = int(dh_info.get("GroupSize"))
            else:
                if public_key_size:
                    cipher_dict["kxStrength"] = int(public_key_size)

            ciphers_list.append(cipher_dict)

    return ciphers_list


def main():
    # get instance of QueueClient
    c = QueueClient()
    # get appropriate queue from QueueClient
    qm = c.queue_manager()
    # get instance of Database
    mdb = Database()

    tls_ver = ['tlsv1_2', 'tlsv1_1', 'sslv3', 'sslv2', 'tlsv1']

    while True:
        try:
            result = qm.next_result()

            scan_error = False
            scan_date = datetime.datetime.now()
            domain = result.get("target")[0]
            tld = get_tld('https://' + domain, as_object=True, fail_silently=True).suffix
            sources = result.get("source")
            ciphers = []
            certificate = {}

            if result.get("error"):
                # print(result.get("err_msg"))
                scan_error = True

            else:
                result_list = result.get('result')

                public_key_size = None

                #  move the result of certinfo to the front of the result_list
                for i, result in enumerate(result_list):
                    if result.get('command') == 'certinfo':
                        result_list.insert(0, result_list.pop(i))
                        break

                for command_result in result_list:
                    if command_result.get("error"):
                        # TODO handle error
                        continue

                    if command_result.get("command") in tls_ver:
                        ciphers.extend(_parse_ciphers(command_result, command_result.get("command"), public_key_size))
                    elif command_result["command"] == "certinfo":
                        public_key_size = command_result.get('subjectPublicKeyInfo').get('publicKeySize')
                        certificate = _parse_cert(command_result)

            db_item = dict(
                    scanError=scan_error,
                    scanDate=scan_date,
                    domain=domain,
                    tld=tld,
                    sources=sources,
                    ciphers=ciphers,
                    certificate=certificate,
            )

            mdb.insert_result(db_item)

        except Exception as e:
            print(e)


if __name__ == "__main__":
    main()
