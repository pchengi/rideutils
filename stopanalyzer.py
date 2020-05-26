#!/usr/bin/env python

#
__author__ = 'Prashanth Dwarakanath'
__license__ = 'GPLv3'

import argparse,sys,math
import datetime
from collections import OrderedDict
import re

aparser=argparse.ArgumentParser()
aparser.add_argument('-f', type=str,default='none',help='input file')
aparser.add_argument('-g', type=str,default='none', help='time in minutes, for filtering on stops')
aparser.add_argument('--utc-offset', '-u', type=str,default='none', help='offset in hours, from UTC')
args=aparser.parse_args()

def td(totalsecs):
    secs=totalsecs%60
    totalmins=(totalsecs/60)
    mins=totalmins%60
    totalhrs=totalmins/60
    hrs=totalhrs%24
    days=totalhrs/24
    return(days,hrs,mins,secs)
    
if args.f == 'none':
    print('No input file provided')
    sys.exit(-1)
if args.f == 'none':
    print('No input file provided')
if args.g != 'none':
    minpause=float(args.g)
else:
    minpause=-1
with open(args.f,'r') as inp:
    lines=inp.readlines()

if args.utc_offset != 'none':
    utcoffset=int(args.utc_offset)
else:
    utcoffset=0
latlongreg=re.compile('.*<trkpt lat="(.*)" lon="(.*)"',flags=re.DOTALL)
speedreg=re.compile('.*<speed>(.*)</speed>')
timereg=re.compile('.*<time>(.*)</time>')
compobj=OrderedDict()
offsetdelta=datetime.timedelta(0,utcoffset*3600)
pointlist=list()
nottrk=1
firsttstamp=1
foundspeed=False
for line in lines:
    if nottrk:
        #if line.find('trkpt') == -1 and line.find('Trackpoint') == -1:
        if line.find('trkpt') == -1:
            continue
        nottrk=0
    if line.find('<trkpt') != -1:
        pt=OrderedDict()
        mat=latlongreg.match(line)
        pt['latlng']=(float(mat.group(1)),float(mat.group(2)))
        continue
    
    if line.find('time') != -1:
        mat=timereg.match(line)
        tstxt=mat.group(1)
        try:
            timestamp=datetime.datetime.strptime(tstxt,"%Y-%m-%dT%H:%M:%SZ")+offsetdelta
        except ValueError:
            try:
                timestamp=datetime.datetime.strptime(tstxt,"%Y-%m-%dT%H:%M:%S.000Z")+offsetdelta
            except:
                print("Secondary exception")
                sys.exit(-1)
        if firsttstamp == 1:
            starttime=timestamp
            firsttstamp=0
        pt['time']=timestamp
        pt['ridetime']=timestamp-starttime
        continue
    if line.find('<speed>') != -1:
        mat=speedreg.match(line)
        pt['speed']=mat.group(1)
        foundspeed=True
        continue

    if line.find('/trkpt') != -1 or line.find('/Trackpoint') != -1:
        pointlist.append(pt)
        nottrk=1
        continue
if foundspeed == False:
    print("No speed information was found in the input file.")
    sys.exit(-1)
firstpoint=1
pauselist=list()
pausestart=0
pausesecs=0
for point in pointlist:
    if point['speed'].find('0.0') != -1:
        if pausestart == 0:
            pausestart=1
            pauseitem=dict()
            pausesecs=0
            pauseitem['latlng']=point['latlng']
            try:
                tstr=datetime.datetime.strftime(point['time'],"%b %d %Y %H:%M:%S")
            except ValueError:
                try:
                    tstr=datetime.datetime.strftime(point['time'],"%b %d %Y %H:%M:%S.000Z")
                except:
                    print("Secondary exception")
                    sys.exit(-1)
            ridetimevals=td(point['ridetime'].seconds)
            pauseitem['pausestart']=tstr
            pauseitem['ridetimevals']=ridetimevals
            prevpt=point
            continue
        
        pausesecs+=(point['time']-prevpt['time']).seconds
        prevpt=point
        continue

    if pausestart == 1:
        pausestart=0
        pauseitem['pausedtime']=pausesecs
        pauselist.append(pauseitem)
        pausesecs=0
        
totalpause=0
#print "Latlong\tTime Elapsed\t Pause start time"
ct=1
for pause in pauselist:
    totalpause+=pause['pausedtime']
    if minpause != -1:
        if minpause > (pause['pausedtime']/60.0):
            ct+=1
            continue
    print("%d. %s %.2f %s %d:%d:%d:%d"%(ct,pause['latlng'],pause['pausedtime']/60.0,pause['pausestart'],int(pause['ridetimevals'][0]),int(pause['ridetimevals'][1]),int(pause['ridetimevals'][2]),int(pause['ridetimevals'][3])))
    ct+=1

print("Cumulative stoppage time in minutes: %0.2f"%(totalpause/60.0))
