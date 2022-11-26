#! /usr/bin/env python3
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from requests import RequestException
import urllib3
import sys
import argparse
import datetime as dt
import codecs
import os

urllib3.disable_warnings()

class color:
   purple = '\033[95m'
   cyan = '\033[96m'
   darkcyan = '\033[36m'
   blue = '\033[94m'
   green = '\033[92m'
   yellow = '\033[93m'
   red = '\033[91m'
   bold = '\033[1m'
   underline = '\033[4m'
   reset = '\033[0m'
   magenta = "\033[35m"

parser = argparse.ArgumentParser()
parser.add_argument('-T', metavar='list.txt', type=str, help='File contain lists of domain')
parser.add_argument('-w', '--workers', metavar='15', nargs='?', default=4, type=int, help='Thread value. Default value is 4')
parser.add_argument("-t", "--target", metavar='google.com', type=str, help='Single domain check')
parser.add_argument("-f", "--filter", metavar='200', type=int, help='Status code filter')
parser.add_argument("-s", "--silent", default=False, action="store_true", help="Silent mode option. Don't print status code output")
parser.add_argument("-o", "--output", metavar='result.txt', type=str, help='Save the results to file')
args = parser.parse_args()
domainlist = args.T
worker = args.workers
singledomain = args.target
statuscodefilter = args.filter
silentopts = args.silent
output_file = args.output

today = dt.datetime.now()
dateonly = today.date()
date_now = str(today.replace(microsecond=0))
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
}
path = os.getcwd()
dir_name = ("scscanner", str(dateonly))
created_dirname = "-".join(dir_name)

def argscheck():
    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    elif domainlist == None and singledomain == None:
        parser.print_help(sys.stderr)
        print()
        print(f"{color.red}{color.bold}Error: Domain list or target is mandatory{color.reset}{color.reset}")
        sys.exit(1)
    elif domainlist is not None and singledomain is not None:
        parser.print_help(sys.stderr)
        print()
        print(f"{color.red}{color.bold}Error: Please chose either single target or bulk target.{color.reset}{color.reset}")
        sys.exit(1)
    elif silentopts and statuscodefilter is None:
        parser.print_help(sys.stderr)
        print()
        print(f"{color.red}{color.bold}Error: -s only work if -f is supplied.{color.reset}{color.reset}")
        sys.exit(1)
    elif domainlist is not None:
        try:
            codecs.open(domainlist, encoding="utf-8", errors="strict").readlines()
        except Exception as err:
            print(f"{color.red}{color.bold}Error: {type(err).__name__} was raised. Please provide valid domain list{color.reset}{color.reset}")
            sys.exit(1)


def banner():
    print("""
┏━━┳━━┳━━┳━━┳━━┳━┓┏━┓┏━━┳━┓
┃━━┫┏━┫━━┫┏━┫┏┓┃┏┓┫┏┓┫┃━┫┏┛
┣━━┃┗━╋━━┃┗━┫┏┓┃┃┃┃┃┃┃┃━┫┃
┗━━┻━━┻━━┻━━┻┛┗┻┛┗┻┛┗┻━━┻┛
    scscanner - Massive HTTP Status Code Scanner
    """)
if not silentopts:
    banner()
else:
    pass
def domaincheck(probed):
    if not probed.startswith("http://") and not probed.startswith("https://"):
        probed = 'http://' + probed
    else:
        probed = probed
    return requests.get(probed, headers=headers, allow_redirects=False, verify=False, timeout=7)

def savedresult(httpcode, domain):
    try:
        if output_file:
            file_name = (httpcode, output_file)
            created_filename = "-".join(file_name)
            final_dir = os.path.join(path, created_dirname, created_filename)
            os.makedirs(os.path.dirname(final_dir), exist_ok=True)
            with open(final_dir, "a") as f:
                f.write(domain + '\n')
                f.close()
    except Exception as err:
        return (f"{type(err).__name__} was raised: {err}")

class scscanner:
    def statuscode(probed):
        try:
            req = domaincheck(probed)
            if not statuscodefilter:
                savedresult(str(req.status_code), probed)
            if statuscodefilter:
                if req.status_code == statuscodefilter:
                    savedresult(str(req.status_code), probed)
                    if silentopts:                   
                        return(probed)
                    if (statuscodefilter == 301) or (statuscodefilter == 302):
                        return(f"[{color.bold}{req.status_code}{color.reset}] - {probed} --> {req.headers['Location']}")
                    return(f"[{color.bold}{req.status_code}{color.reset}] - {probed}")                  
                else:
                    pass
            else:
                if req.status_code == 200:
                    return(f"[{color.green}{req.status_code}{color.reset}] - {probed}")
                elif (req.status_code == 301) or (req.status_code == 302):
                    return(f"[{color.yellow}{req.status_code}{color.reset}] - {probed} --> {color.yellow}{req.headers['Location']}{color.reset}")
                else:
                    return(f"[{color.red}{req.status_code}{color.reset}] - {probed}")
        except RequestException as err:
            if statuscodefilter:
                pass
            else:
                savedresult(str("000"), probed)
                return(f"[000] - {probed} [{color.bold}{color.red}{type(err).__name__}{color.reset}]")

    def singlescan():
        probed = singledomain
        statusresult = scscanner.statuscode(probed)
        if statusresult is not None:
            print(statusresult)
        else:
            print(f"{color.bold}Domain status code and status code filter is not match{color.reset}")

    def masscan():
        with ThreadPoolExecutor(max_workers=worker) as executor:
            with codecs.open(domainlist, encoding="utf-8", errors="strict") as tglist:
                domainname = tglist.read().splitlines()
                try:
                    loopcheck = [executor.submit(scscanner.statuscode, probed) for probed in domainname]
                    for future in as_completed(loopcheck):
                        if future.result():
                            print(future.result())
                        else:
                            pass
                except KeyboardInterrupt:
                    executor.shutdown(wait=False, cancel_futures=True)
                    print(f"\n{color.bold}Terminate program. Please wait...{color.reset}")

if __name__ == '__main__':
    argscheck()
    try:
        if not silentopts:
            print(f"{color.bold}{date_now} - Start program{color.reset}\n")
        if output_file and not silentopts:
            print(f"{color.bold}Your result will be saved at: {color.green}{os.path.join(path, created_dirname)}{color.reset}\n")
        for _ in [0]:
            if singledomain:
                scscanner.singlescan()
            else:
                scscanner.masscan()
    except Exception as err:
        print(f"{type(err).__name__} was raised: {err}")
    finally:
        if not silentopts:
            print(f"\n{color.bold}{date_now} - Run complete{color.reset}")