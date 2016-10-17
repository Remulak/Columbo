# Columbo

Columbo determines where page elements that utilize a src attribute (images, 
audio, videos, javascript, etc) loaded for a web page are actually served 
from.  While the source html may show files originating from a given server, 
they may be served by another host, such as a content delivery network (CDN)

usage: Columbo.py [-h] [-d DIR] [-s] [-o OUTPUT] [-u URLS | -i INDIVIDUAL]

Find where image elements of a url are served from

optional arguments:

  -h, --help                              show this help message and exit
  
  -d DIR, --dir DIR                       change output directory from current directory
  
  -s, --save                              save copies of the files examined
  
  -o OUTPUT, --output OUTPUT              provide a filename to save output in csv format
                        
  -u URLS, --urls URLS                    text file containing list of urls to process (one URLper line)
                        
  -i INDIVIDUAL, --individual INDIVIDUAL  single URL to process

Dependencies:

beautifulsoup4

tldextract
