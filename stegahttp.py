import random
import re
import requests
import sys
from urllib.parse import urljoin

class WebDataStream:
    def __init__(self, _sources, _sourceReuse = False, _trimBias = .3):
        self.sources = [(source, False) for source in _sources]
        self.sourceReuse = _sourceReuse
        self.trimBias = _trimBias
        self.chunkSize = 1024
        self.currentSource = None
        self.currentOffset = 0
        self.buffer = b''

    srcPattern = re.compile(r'(src|href)\s*=\s*"([^"]*)"')

    def _fetchData(self):
        unusedSources = [source for source, used in self.sources if not used]

        if not unusedSources:
            if not self.sourceReuse:
                raise Exception("No sources available and source reuse is disabled.")
            else:
                self.sources = [(source, False) for source, _ in self.sources]  # Mark all sources as unused again
                unusedSources = self.sources

        # Randomly choose a source and mark it as used
        self.currentSource = random.choice(unusedSources)
        self.sources = [(source, used) if source != self.currentSource else (source, True) for source, used in self.sources]
        print(f"Current Source: {self.currentSource}")
        try:
            response = requests.get(self.currentSource)
            content = response.content

            # Pass the content to the extractor to find new sources within it
            newSources = self._extractResources(content)

            # Trim a random chunk from the start and/or end of the content
            trimStart = 0
            trimEnd = 0
            if random.random() >= self.trimBias:
                trimStart = random.randint(0, int(len(content)/4))
                trimEnd = random.randint(0, int(len(content)/4))
            if trimStart or trimEnd:
                content = content[trimStart:len(content)-trimEnd]

            # Update current offset based on fetched content size, modulus division with allocation unit size
            self.currentOffset = (self.currentOffset + len(content)) % self.chunkSize

            # Populate the buffer with the new content
            self.buffer += content
        except requests.exceptions.RequestException:
            print(f"Error in Request for resource '{self.currentSource}'")
            pass

    def _extractResources(self, _content):
        try:
            decoded = _content.decode()
        except:
            return
        matches = WebDataStream.srcPattern.findall(decoded)
        newSources = []
        for match in matches:
            source = match[-1].strip()
            source = urljoin(self.currentSource, source)
            newSources.append(source)
        for src in [(source, False) for source in newSources if not self._isSourceInSource(source)]:
            self.sources.append(src)

    def _isSourceInSource(self, _source):
        for src,_ in self.sources:
            if src == _source:
                return True
        return False

    def read(self, size=-1):
        while len(self.buffer) < size:
            self._fetchData()

        if size == -1 and len(self.buffer) == 0:
            self._fetchData()
            rtn = self.buffer
            self.buffer = b''
            return rtn

        data = self.buffer[:size]
        self.buffer = self.buffer[size:]
        return data
    
    def readline(self):
        isNewline = 0
        while not isNewline:
            try:
                isNewline = self.buffer.index(10)
            except ValueError:
                self._fetchData()
        
        
    def readlines(self):
        rtn = self.buffer.split(b'\n')
        buffer = b''
        return rtn

    def write(self, data):
        return 0
    
    def flush(self):
        pass
    
    def close(self):
        buffer = b''
        self.sources = []

    def __iter__(self):
        return self

    def __next__(self):
        data = self.read()
        if not data:
            raise StopIteration
        return data
    
    def sizedIterator(self, _size):
        chunk = self.read(_size)
        while chunk:
            yield chunk
            chunk = self.read(_size)

# Example usage
# sources = ['http://python.org']
# stream = WebDataStream(sources)

# for i in range(100):
#     print(stream.read())