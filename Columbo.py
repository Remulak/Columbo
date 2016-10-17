# Columbo.py
# Rod Rickenbach
# 10/16/16
#
# Columbo determines where page elements that utilize a src attribute (images, 
# audio, videos, javascript, etc) loaded for a web page are actually served 
# from.  While the source html may show files originating from a given server, 
# they may be served by another host, such as a content delivery network (CDN)

import argparse
import urllib
import os
import psutil
import socket
import tldextract
import csv
from bs4 import BeautifulSoup
from collections import namedtuple

##############################################################################
# get_and_parse_html will read a given URL and retrieve the html for parsing.
# It then passes the html data through BeautifulSoup to find all src 
##############################################################################

def get_and_parse_html(url):

    # Retrieve info from the URL we provide 
    u = urllib.urlopen(url)

    # If we get an "OK" response (200) ie web page exists and is returned, then we
    # will process it
    if u.getcode()==200:
        # Read the data.  This action makes the connection get the html from
        # the true source.
        data = u.read()
        
        # Record information about the read
        recordResource(url,url)
        
        # Use beautiful soup to get all tags with src attributes
        soup = BeautifulSoup(data, "html.parser")
        all_src = soup.find_all(src=True)
        
        # Once we have them, check each one...
        for i in all_src:
            getElement(i["src"])


##############################################################################
# getElement downloads a src file and records details of the source
# ##############################################################################

def getElement(url):

    # Fix up the URL if it's a relative path
    if url.startswith('http://') or url.startswith('https://'):
        pass
    else:
        url = urlString + "/" + url
   
    # Grab the filename off the end of the url string
    filename = url.split('/').pop()

    # Santitize the filename for some crazy things I've seen...
    # http://stackoverflow.com/questions/7406102/create-sane-safe-filename-from-any-unsafe-string
    keepcharacters = (' ','.','_')
    filename="".join(c for c in filename if c.isalnum() or c in keepcharacters).rstrip()
    
    # Open sesame
    u =  urllib.urlopen(url)
    
    # If we get an "OK" response (200) ie web page exists and is returned, then we
    # will process it
    if u.getcode()==200:   
        # Read the data.  This action makes the connection get the data from
        # the true source.
        data = u.read()

        # Record information about the read   
        recordResource(url,filename)

        # If we set the option to save, save the file (binary format)
        if args.save:
            f = open(os.path.join(output_dir,filename), 'wb')
            f.write(data)
            f.close()


##############################################################################
# getFullDomain returns the "full" name (subdomain+domain+suffix) of a given url
# and conveniently strips off the ugliness at the end
# https://github.com/john-kurkowski/tldextract
##############################################################################
def getFullDomainName(url):
    hostinfo = tldextract.extract(url)
    return '.'.join(part for part in hostinfo if part)


##############################################################################
# recordResource stores the appropriate info about what we observed when
# we retrieved a resource.  Records the 
##############################################################################
def recordResource(url,name):

    # Loop to add TCP connection info, checking to ensure we haven't
    # recorded the connection from the source port previously (ie this
    # information would have been added on a previous iteration)

    for i in p.connections():
        
        # Give some human friendly names to things from 'i'
        source_port = i.laddr[1]
        remote_IP = i.raddr[0]
      
        # If we haven't seen this before, recpre the relevant information
        if source_port not in tcp_source_ports:
            tcp_source_ports.append(source_port)

            # Now get the info we seek
            original_FQDN = getFullDomainName(url)
            original_IP = socket.gethostbyname(original_FQDN)
            real_FQDN = socket.getfqdn(remote_IP)
            
            # if the IP's don't match, we are retrieving the information
            # from an unexpected server.  Note as such
            if original_IP != remote_IP:
                IP_mismatch = 1
            else:
                IP_mismatch = 0

                
            # if the names don't match, we are retrieving the information
            # from an unexpected place, ie a CDN.  Note it
            if original_FQDN != real_FQDN:
                FQDN_mismatch = 1
            else:
                FQDN_mismatch = 0

            # Create instance of named tuple
            resource = Resource(name,IP_mismatch,original_IP,remote_IP,
                            FQDN_mismatch,original_FQDN,real_FQDN,url)
            
            # Add to the master list
            all_resources.append(resource)


##############################################################################
# The main program
##############################################################################

# Set up the arguments list using argparse
parser = argparse.ArgumentParser(description='Find where image elements of a url are served from')
parser.add_argument('-d', '--dir', help='change output directory from current directory')
parser.add_argument('-s', '--save', action='store_true', help='save copies of the files examined')
parser.add_argument('-o','--output', help='provide a filename to save output in csv format')
group = parser.add_mutually_exclusive_group()
group.add_argument('-u', '--urls', help = 'text file containing list of urls to process (one URL per line)')
group.add_argument('-i', '--individual', help='single URL to process')
args = parser.parse_args()

# Start making sense of the args

if not args.urls and not args.individual:
    print 'Must have a single url (-i) or list of urls (-u) to process'
    print '\n use -h argument for basic help.'
    exit()

if args.dir == None:
    args.dir = '.'
# Create output directory if it doesn't exist
elif not os.path.exists(args.dir):
    os.makedirs(args.dir)

#determine path to the output directory and create appropriate variable
output_dir=os.path.abspath(args.dir)

# Get info on current running process (this program) from psutil
p=psutil.Process(os.getpid())

# List of outgoing port numbers
tcp_source_ports = []

# Named tuple to store information about resources examined
Resource=namedtuple('Resource',['name', 'IP_mismatch', 'original_IP', 'real_IP',
                    'FQDN_mismatch', 'original_FQDN', 'real_FQDN',  'full_url'])

# List of all resources
all_resources = []

# Work on individual or lists of urls
if args.individual:
    urlString=args.individual
    get_and_parse_html(args.individual)
else:
    #Loop to parse urls from file
    with open(args.urls) as fp:
        for line in fp:
            line=line.rstrip('\n')
            urlString=line
            get_and_parse_html(line)

# create the csv output if requested
# Learned a bit from here:
# http://stackoverflow.com/questions/10573915/python-transposing-a-list-and-writing-to-a-csv-file
if args.output:
    item_length = len(all_resources[0])

    # Note must open the csv write file as wb to avoid every other row
    # being blank
    with open(os.path.join(output_dir,args.output),'wb') as csv_file:
        file_writer = csv.writer(csv_file, delimiter = ',')
        # Write the header
        file_writer.writerow(Resource._fields)
        # Write the rows
        file_writer.writerows(all_resources)
    csv_file.close()

# Dump output to the screen
for i in all_resources:
    print i