import sys
sys.stdout.buffer.write(b'\x01\x00\x00\x00\x04\xa3' + b'abc')
sys.stdout.buffer.write(b'\x02\x00\x00\x00\x00')
sys.stdin.buffer.close()

