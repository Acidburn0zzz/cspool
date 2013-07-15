# Server-side implementation of the spool.
# File-based, just because it is easy.

import os
import fcntl
import contextlib
import struct


class Error(Exception):
    pass


@contextlib.contextmanager
def flock(path):
    with open(path, 'r+') as fd:
        fcntl.lockf(fd, fcntl.LOCK_EX)
        yield
        fcntl.lockf(fd, fcntl.LOCK_UN)


def logread(fd):
    pos = fd.tell()
    szbuf = fd.read(4)
    if not szbuf:
        return pos, None
    sz = struct.unpack('i', szbuf)[0]
    data = fd.read(sz)
    if len(data) != sz:
        raise Error('short read')
    return pos, data


def logwrite(entry, fd):
    pos = fd.tell()
    fd.write(struct.pack('i', len(entry)))
    fd.write(entry)
    return pos


class Spool(object):

    SPOOL_ROOT = './spool'

    def __init__(self, user):
        self._root = os.path.join(self.SPOOL_ROOT, user)
        if not os.path.isdir(self._root):
            os.makedirs(self._root)
        self._lock_file_path = os.path.join(self._root, 'lock')
        self._log_file_path = os.path.join(self._root, 'log')

    def scan(self, start_pos=0):
        with open(self._log_file_path, 'r') as fd:
            fd.seek(0, 2)
            end_pos = fd.tell()

            if start_pos >= end_pos:
                return

            fd.seek(start_pos, 0)
            while True:
                pos, entry = logread(fd)
                yield pos, entry
                if entry is None:
                    break

    def append(self, entry):
        with open(self._log_file_path, 'a') as fd:
            return logwrite(entry, fd)


if __name__ == '__main__':
    # Start a local test spool server on port 3999
    from flask import Flask, request, make_response
    import json
    import optparse

    app = Flask('spool')
    app.debug = True

    parser = optparse.OptionParser()
    parser.add_option('--port', type='int', default=3999)
    opts, args = parser.parse_args()

    @app.route('/scan')
    def handler():
        spool = Spool(request.args['user'])
        start_pos = int(request.args['start_pos'])
        out = [{'pos': pos, 'entry': entry}
               for pos, entry in spool.scan(start_pos)]
        response = make_response(json.dumps(out))
        response.headers['Content-Type'] = 'application/json'
        return response

    app.run('127.0.0.1', opts.port)
