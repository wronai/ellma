"""
Mock implementation of the audioop module for testing purposes.
"""

def add(a, b, c):
    """Mock implementation of audioop.add"""
    return b"\x00" * len(a)

def adpcm2lin(a, b, c, d):
    """Mock implementation of audioop.adpcm2lin"""
    return (b"\x00" * len(a) * 2, (0, 0))

def alaw2lin(a, b, c):
    """Mock implementation of audioop.alaw2lin"""
    return b"\x00" * (len(a) * 2)

def avg(a, b):
    """Mock implementation of audioop.avg"""
    return 0

def avgpp(a, b):
    """Mock implementation of audioop.avgpp"""
    return 0

def bias(a, b, c):
    """Mock implementation of audioop.bias"""
    return a

def byteswap(a, b):
    """Mock implementation of audioop.byteswap"""
    return a

def cross(a, b):
    """Mock implementation of audioop.cross"""
    return 0

def findfactor(a, b):
    """Mock implementation of audioop.findfactor"""
    return 1.0

def findfit(a, b):
    """Mock implementation of audioop.findfit"""
    return (0, 1.0)

def findmax(a, b):
    """Mock implementation of audioop.findmax"""
    return 0

def getsample(a, b, c):
    """Mock implementation of audioop.getsample"""
    return 0

def lin2adpcm(a, b, c):
    """Mock implementation of audioop.lin2adpcm"""
    return (b"\x00" * (len(a) // 2), (0, 0))

def lin2alaw(a, b):
    """Mock implementation of audioop.lin2alaw"""
    return b"\x00" * (len(a) // 2)

def lin2lin(a, b, c, d):
    """Mock implementation of audioop.lin2lin"""
    return b"\x00" * (len(a) * d // c)

def lin2ulaw(a, b):
    """Mock implementation of audioop.lin2ulaw"""
    return b"\x00" * len(a)

def max(a, b):
    """Mock implementation of audioop.max"""
    return 0

def maxpp(a, b):
    """Mock implementation of audioop.maxpp"""
    return 0

def minmax(a, b):
    """Mock implementation of audioop.minmax"""
    return (0, 0)

def mul(a, b, c):
    """Mock implementation of audioop.mul"""
    return a

def ratecv(a, b, c, d, e, f, g):
    """Mock implementation of audioop.ratecv"""
    return (a, (0, 0, 0, 0))

def reverse(a, b):
    """Mock implementation of audioop.reverse"""
    return a

def rms(a, b):
    """Mock implementation of audioop.rms"""
    return 0

def tomono(a, b, c, d, e):
    """Mock implementation of audioop.tomono"""
    return a

def tostereo(a, b, c, d, e):
    """Mock implementation of audioop.tostereo"""
    return a + a

def ulaw2lin(a, b, c):
    """Mock implementation of audioop.ulaw2lin"""
    return b"\x00" * (len(a) * 2)
