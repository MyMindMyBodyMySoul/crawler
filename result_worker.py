"""
This module fetches results out of the queue_manager and formats it in JSON to add it to da database
"""


from queue_manager import QueueClient
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
    cert_dict = dict(
        issuer=command_result['issuer']['commonName'],
        subject=command_result['subject']['commonName'],
        publicKeyLengh=command_result['subjectPublicKeyInfo']['publicKeySize'],
        publicKeyAlgorithm=command_result['subjectPublicKeyInfo']['publicKeyAlgorithm'],
        signatureAlgorithm=command_result['signatureAlgorithm'],
        notValidBefore=command_result['validity']['notBefore'],
        notValidAfter=command_result['validity']['notAfter'],
        selfSigned=False,  # how can we get this value?
        expired=False
    )

    before = datetime.datetime.strptime(command_result['validity']['notBefore'][:20], '%b %d %H:%M:%S %Y').date()
    after = datetime.datetime.strptime(command_result['validity']['notAfter'][:20], '%b %d %H:%M:%S %Y').date()
    now = datetime.datetime.now().date()

    if(after < now and now > before):
        cert_dict['expired'] = True

    return cert_dict

def _parse_ciphers(result, protocol):

    ciphers_list = []

    key_status_list = [
        ('preferredCipherSuite', 'preferred:'),
        ('acceptedCipherSuites', 'accepted:'),
        ('errors', 'error'),
        ('rejectedCipherSuites', 'rejected:')
    ]

    for (result_key, result_status) in key_status_list:
        result_list = result[result_key]

        for ssl_cipher in result_list:

            msg = result_list.get(ssl_cipher)[0]  # msg not used until now
            bits = result_list.get(ssl_cipher)[1]
            dh_info = result_list.get(ssl_cipher)[2]
            cipher_desc = CIPHER_DESC.get(ssl_cipher)

            cipher_dict = dict(
                cipher=ssl_cipher,
                protocol=protocol,
                status=result_status,
                bits=bits,
                kx=cipher_desc.get("kx"),
                kxStrength=0,  # don't known where to get this value when it is cert
                au=cipher_desc.get("au"),
                enc=cipher_desc.get("enc"),
                mac=cipher_desc.get("mac"),
                export=cipher_desc.get("export")
            )

            if dh_info:
                if dh_info.get("Prime"):
                    cipher_dict["curve"] = "P-%s" % dh_info.get("GroupSize")
                    cipher_dict["kxStrength"] = dh_info.get("GroupSize")

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
        result = qm.next_result()

        scan_error = False
        scan_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        domain = result.get("target")[0]
        tld = get_tld('https://' + domain, as_object=True).suffix
        source = result.get("source")
        ciphers = []
        certificate = {}

        if result.get("error"):
            print(result.get("err_msg"))
            scan_error = True

        else:
            for command_result in result.get("result"):
                if command_result.get("error"):
                    # TODO handle error
                    continue
                if command_result.get("command") in tls_ver:
                    ciphers.extend(_parse_ciphers(command_result, command_result.get("command")))
                elif command_result["command"] == "certinfo":
                    certificate = _parse_cert(command_result)

                db_item = dict(
                    scans=dict(
                        scanError=scan_error,
                        scanDate=scan_date,
                        domain=domain,
                        tld=tld,
                        source=source,
                        ciphers=ciphers,
                        certificate=certificate,
                    )
                )

        mdb.insert_result(db_item)


if __name__ == "__main__":
    main()
