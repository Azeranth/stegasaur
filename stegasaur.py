import argparse
import os
import select
import threading
import time

import stegahttp


def getPipename(_pipename, _appendPid):
    rtn = _pipename
    if not rtn:
        rtn = time.strftime("%Y%m%d%H%M%S", time.localtime())
    if _appendPid:
        rtn += f"_{os.getpid()}"
    rtn += ".pipe"
    return rtn

def getStream(_args):
    if _args.http:
        return stegahttp.WebDataStream(_args.http)

def refillPipe(_fifoPath, _stream, _chunkSize=4096):
    fifo = open(_fifoPath, 'wb')
    try:
        while True:
            select.select([],[fifo],[])[1]
            try:
                fifo.write(_stream.read(_chunkSize))
                fifo.flush()
            except(BrokenPipeError):
                fifo = open(_fifoPath, 'wb')
    finally:
        try:
            fifo.close()
            os.remove(_fifoPath)
        except:
            pass

def main(args):
    pipename = getPipename(args.pipename, args.appendPid)
    if os.path.exists(pipename):
        os.remove(pipename)
    os.mkfifo(pipename)
    stream = getStream(args)

    refillThread = threading.Thread(target=refillPipe, args=(pipename, stream, args.chunk_size))
    refillThread.start()

parser = argparse.ArgumentParser(description="Named pipe data generator")
parser.add_argument("-P", "--no-append-pid", action="store_false",dest="appendPid", default=True, help="Append process ID to the pipe name (default: True)")
parser.add_argument("-s", "--chunk-size", type=int, default=4096, help="Refill chunk size in bytes (default: 4096)")
parser.add_argument("pipename", nargs="?", help="Name of the named pipe")
generationGroup = parser.add_mutually_exclusive_group(required=True)
generationGroup.add_argument("--http", nargs="+")

if __name__ == "__main__":
    main(parser.parse_args())