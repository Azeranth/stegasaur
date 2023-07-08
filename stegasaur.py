import argparse
import os
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

def getStream(args):
    if args.http:
        return stegahttp.WebDataStream(args.http)

def refillPipe(_fifoPath, _stream, _chunkSize=1024):
    # Open the FIFO for writing
    with open(_fifoPath, 'wb') as fifo:
        while True:
            if os.stat(_fifoPath).st_size == 0:
                fifo.write(_stream.read(_chunkSize))
                fifo.flush()

def main(args):
    pipename = getPipename(args.pipename, args.appendPid)
    os.remove(pipename)
    os.mkfifo(pipename)
    stream = getStream(args.generationType)

    refillThread = threading.Thread(target=refillPipe, args=(pipename, stream, args.chunk_size))
    refillThread.start()

parser = argparse.ArgumentParser(description="Named pipe data generator")
generationGroup = parser.add_mutually_exclusive_group(required=True)
generationGroup.add_argument("--http", nargs="+")
parser.add_argument("-P", "--no-append-pid", action="store_false",dest="appendPid", default=True, help="Append process ID to the pipe name (default: True)")
parser.add_argument("-s", "--chunk-size", type=int, default=4096, help="Refill chunk size in bytes (default: 4096)")
parser.add_argument("pipename", nargs="?", help="Name of the named pipe")

if __name__ == "__main__":
    main(parser.parse_args())