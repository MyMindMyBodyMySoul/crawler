import os
import cPickle
from thread import start_new_thread

class Dumper(object):
    """
    """
    DUMP_LOCATION = os.path.join(os.path.dirname(__file__), '..', 'data')

    @classmethod
    def dump_counter(cls, counter):
        print('dumping counter')
        start_new_thread(cls._dump, ('counter.dmp', counter))

    @classmethod
    def dump_queue(cls, queue):
        print('dumping queue')
        start_new_thread(cls._dump, ('queue.dmp', queue))

    @classmethod
    def load(cls, cb):
        start_new_thread(cls._load_threaded, (cb,))

    @classmethod
    def _load_threaded(cls, cb):
        counter = cls._load('counter.dmp')
        queue = cls._load('queue.dmp')
        cb(counter, queue)


    @classmethod
    def _dump(cls, filename, data):
        try:
            if not os.path.exists(cls.DUMP_LOCATION):
                os.mkdir(cls.DUMP_LOCATION)
            dump_file = open(os.path.join(cls.DUMP_LOCATION, filename), 'wb+')
            try:
                cPickle.dump(data, dump_file, cPickle.HIGHEST_PROTOCOL)
                print('dumping finished')
            except (cPickle.PickleError,cPickle.PicklingError) as pe:
                print pe
            finally:
                dump_file.close()
        except OSError as oe:
                    print oe
        except Exception as ex:
            # Catch everything unexpected
            print("Unexpected error while creating dumpfile: ",ex)

    @classmethod
    def _load(cls, filename):
        if os.path.exists(os.path.join(cls.DUMP_LOCATION, filename)):
            print("Found dump %s " % filename)
            try:
                dump_file = open(os.path.join(cls.DUMP_LOCATION, filename), 'rb+')
                try:
                    data = cPickle.load(dump_file)
                    dump_file.close()
                    return data
                except (cPickle.UnpicklingError, cPickle.UnpickleableError) as pe:
                    print pe
                finally:
                    dump_file.close()
            except OSError as oe:
                print oe
            except Exception as ex:
                # Catch everything unexpected
                print("Unexpected error while reading dump file: ", ex)
        else:
            print("No dump %s found. Continuing with regular operation" % filename)

