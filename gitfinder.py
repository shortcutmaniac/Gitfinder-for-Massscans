import argparse
from functools import partial
from multiprocessing import Pool
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
import sys
import ssl
import encodings.idna
import http.client


def findgitrepo(output_file, domain_with_port):
    domain, port = domain_with_port.split(':')
    port = int(port)
    
    try:
        domain = ".".join(encodings.idna.ToASCII(label).decode("ascii") for label in domain.strip().split("."))
    except (UnicodeError, ValueError):
        return

    try:
        # Try to download https://target.tld:8443/.git/HEAD
        with urlopen(''.join(['https://', domain, ':', str(port), '/.git/HEAD']), context=ssl._create_unverified_context(), timeout=5) as response:
            answer = response.read(200).decode('utf-8', 'ignore')

    except (HTTPError, URLError, OSError, ConnectionResetError, ValueError):
        return
    except http.client.BadStatusLine:
        print(f"BadStatusLine error for URL: https://{domain}:{port}/.git/HEAD")
        return
    except (KeyboardInterrupt, SystemExit):
        raise

    # Check if refs/heads is in the file
    if 'refs/heads' not in answer:
        return

    # Write match to output_file
    with open(output_file, 'a') as file_handle:
        file_handle.write(''.join([domain, '\n']))

    print(''.join(['[*] Found: ', domain]))


def read_file(filename):
    with open(filename) as file:
        return [line.strip() for line in file.readlines()]


def main():
    print("""
###########
# Finder is part of https://github.com/internetwache/GitTools
#
# Developed and maintained by @gehaxelt from @internetwache
#
# Use at your own risk. Usage might be illegal in certain circumstances.
# Only for educational purposes!
###########
""")

    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--inputfile', default='input.txt', help='input file')
    parser.add_argument('-o', '--outputfile', default='output.txt', help='output file')
    parser.add_argument('-t', '--threads', default=200, help='threads')
    args = parser.parse_args()

    domain_file = args.inputfile
    output_file = args.outputfile
    try:
        max_processes = int(args.threads)
    except ValueError as err:
        sys.exit(err)

    try:
        domains_with_ports = read_file(domain_file)
    except FileNotFoundError as err:
        sys.exit(err)

    fun = partial(findgitrepo, output_file)
    print("Scanning...")
    with Pool(processes=max_processes) as pool:
        pool.map(fun, domains_with_ports)
    print("Finished")


if __name__ == '__main__':
    main()
