
import os
import sys
import time


def main():
    from server.queue_manager import QueueClient

    c = QueueClient()
    qm = c.queue_manager()

    while True:
        status = qm.status()

        print('#'*15 + ' Scan Status ' + '#'*15)

        print('{0:<32}{1:.2f} m'.format('scan time:', status.get('scantime')/60))
        print('{0:<32}{1:.2f} s'.format('average scan time:', status.get('avgtime')))

        print('{0:<32}{1}'.format('scans completed:', status.get('completed')))
        print('{0:<32}{1}'.format('fully scanned:', status.get('fully_scanned')))

        print('{0:<32}{1}'.format('host queue position:', status.get('counter')))
        print('{0:<32}{1}'.format('host queue is filling:', status.get('is_filling')))

        print('{0:<32}{1}'.format('host queue size:', status.get('host_queue_size')))
        print('{0:<32}{1}'.format('user queue size:', status.get('user_queue_size')))
        print('{0:<32}{1}'.format('result queue size:', status.get('result_queue_size')))

        # print('{0:<32}{1}'.format('dump threshold:', status.get('dump_limit')))
        # print('{0:<32}{1}'.format('result queue threshold:', status.get('result_queue_limit')))

        print('#'*43)

        time.sleep(10)

if __name__ == "__main__":
    sys.path.append(os.getcwd())
    main()
