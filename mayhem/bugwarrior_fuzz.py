#!/usr/bin/env python3
import io
import sys
import atheris
import re

with atheris.instrument_imports(include=['bugwarrior']):
    from bugwarrior.config.load import BugwarriorConfigParser

def TestOneInput(data):
    fdp = atheris.FuzzedDataProvider(data)
    if len(data) == 0:
        return 0
    ran = fdp.ConsumeIntInRange(0, 20)
    consumed_bytes = fdp.ConsumeBytes(fdp.ConsumeIntInRange(0, fdp.remaining_bytes()))
    print(consumed_bytes)
    try:
        conf = BugwarriorConfigParser()
        readme = b'[HEADER]\n' + consumed_bytes
        conf.read_string(readme.decode('utf-8'))

        # # Split the string into key-value pairs
        # pairs = re.findall(r'(\S+)\s+(\S+)', consumed_bytes.decode('utf-8'))
        #
        # if pairs:
        #     # Create a dictionary from the key-value pairs
        #     data_dict = dict(pairs)
        # else:
        #     data_dict = dict((ran, readme.decode('utf-8')))
        #
        # print(data_dict)
        # conf.read_dict(data_dict)
    except (TypeError, UnicodeError):
        return
    except Exception:
        raise



def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


# Main program
if __name__ == "__main__":
    main()
