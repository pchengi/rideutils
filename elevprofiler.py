#!/usr/bin/env python2

import argparse,sys,math
import datetime
from collections import OrderedDict
import numpy as np
from numpy.random import rand
#from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
def onclick(event):
    if onclick.ctr == 0:
        onclick.stm=float(event.xdata)*1000
        onclick.stelev=float(event.ydata)
        onclick.ctr+=1
        return
    onclick.endm=float(event.xdata)*1000
    onclick.endelev=float(event.ydata)
    elevm=onclick.endelev-onclick.stelev
    diff=onclick.endm-onclick.stm
    grade=elevm/(math.sqrt(math.pow(diff,2)-math.pow(elevm,2)))*100
    print ('Segment distance(m):',diff)
    print ('Segment grade:',grade)
    onclick.ctr=0
    return

onclick.ctr=0
onclick.stm=0
onclick.endm=0
onclick.stelev=0
onclick.endelev=0

def line_picker(line, mouseevent):
    if mouseevent.xdata is None:
        return False, dict()
    xdata = line.get_xdata()
    ydata = line.get_ydata()
    maxd = 0.05
    d = np.sqrt((xdata - mouseevent.xdata)**2. + (ydata - mouseevent.ydata)**2.)
    ind = np.nonzero(np.less_equal(d, maxd))
    if len(ind):
        pickx = np.take(xdata, ind)
        picky = np.take(ydata, ind)
        props = dict(ind=ind, pickx=pickx, picky=picky)
        print (pickx)
        print (picky)
        print (props)
        return True, props
    else:
        return False, dict()

aparser=argparse.ArgumentParser()
aparser.add_argument('-f', type=str,default='none',help='input file')
aparser.add_argument('-s', type=str,default='none',help='starting point')
aparser.add_argument('-e', type=str,default='none',help='ending point')
aparser.add_argument('-t', type=str,default='none',help='title for graph')
aparser.add_argument('-m', type=str,default='none',nargs='?',help='specify values in miles instead of meters (output will still be in km)')
aparser.add_argument('-n', type=str,default='none',nargs='?',help='no graph display, just output elevation information and write output.pdf)')
meg=aparser.add_mutually_exclusive_group()
meg.add_argument('-c', type=str,default='none',nargs='?',help='not currently implemented')
meg.add_argument('-a', type=str,default='none',nargs='?',help='additional filters')
args=aparser.parse_args()
if args.f == 'none':
    print ('No input file provided')
    sys.exit(-1)
if args.a != 'none':
    if args.s == 'none' or args.e == 'none':
        print ("Please provide -s 'start meters' and -e 'end meters' for activity.")
        sys.exit(-1)
    try:
        startm=float(args.s)
        endm=float(args.e)
        if args.m != 'none':
            startm=startm*1.6*1000
            endm=endm*1.6*1000
    except:
        print ("Invalid date format. hint: Jan 31 2015 11:22")
        raise
        sys.exit(-1)
if args.f == 'none':
    print ('No input file provided')
fp=open(args.f,'r')
lines=fp.readlines()
fp.close()
utcoffset=2
offsetdelta=datetime.timedelta(0,utcoffset*3600)
pointlist=list()
xyvals=dict()
xyvals['alts']=list()
xyvals['times']=list()
xyvals['distances']=list()
xyvals['distances'].append(0)
xyvals['alts'].append(0)
xyvals['grades']=list()
xyvals['grades'].append(0)
xyvals['grade-dists']=list()
xyvals['grade-dists'].append(0)
prevdist=-1000
prevalt=-1000
curdist=0
curalt=0
nottrk=1
first100=1
for line in lines:
    if nottrk:
        if line.find('trkpt') == -1 and line.find('Trackpoint') == -1:
            continue
        nottrk=0
    if line.find('<trkpt') != -1 or line.find('<Trackpoint') != -1:
        pt=OrderedDict()
        continue
    if line.find('ele') != -1 or line.find('AltitudeMeters') != -1:
        val=float(line.split('<')[1].split('>')[1])
        pt['ele']=val
        xyvals['alts'].append(val)
        if prevalt == -1000: #first timer
            prevalt=val
        curalt=val
        continue
    if line.find('DistanceMeters') != -1:
        val=float(line.split('<')[1].split('>')[1])
        pt['distance']=val
        xyvals['distances'].append(val/1000)
        if prevdist == -1000: #first timer
            prevdist=val
        curdist=val
        elevm=curalt-prevalt
        diff=curdist-prevdist
        try:
            grade=elevm/(math.sqrt(math.pow(diff,2)-math.pow(elevm,2)))*100
        except:
            grade=0.0
        xyvals['grades'].append(grade)
        xyvals['grade-dists'].append(curdist/1000)
        prevalt=curalt
        prevdist=curdist
        continue
    if line.find('time') != -1 or line.find('Time') != -1:
        timestamp=datetime.datetime.strptime(line.split('<')[1].split('>')[1],"%Y-%m-%dT%H:%M:%SZ")+offsetdelta
        tstr=datetime.datetime.strftime(timestamp,"%b %d %Y %H:%M:%S")
        pt['time']=tstr
        continue
    if line.find('/trkpt') != -1 or line.find('/Trackpoint') != -1:
        pointlist.append(pt)
        nottrk=1
        continue
firstpoint=1
climb=0
descent=0
travd=0
print ("Total points: "+str(len(pointlist)))
poplist=list()
if args.a != 'none':
    ct=-1
    for val in xyvals['distances']:
        ct+=1
        if val * 1000 < startm or val * 1000 >endm:
            poplist.append(ct)
    print ("will eject %d points"%len(poplist))
    poplist.sort(reverse=True)
    for i in poplist:
        xyvals['distances'].pop(i)
        xyvals['alts'].pop(i)
        xyvals['grades'].pop(i)
        xyvals['grade-dists'].pop(i)
    for i in range(0,len(xyvals['distances'])):
        xyvals['distances'][i]=xyvals['distances'][i]-(startm/1000)
        xyvals['grade-dists'][i]=xyvals['grade-dists'][i]-(startm/1000)

for point in pointlist:
    if args.a != 'none':
        if point['distance'] < startm:
            continue
        if point['distance'] > endm:
            break
    if firstpoint:
        firstpoint=0
        prev=point['ele']
        prevd=point['distance']
    cur=point['ele']
    curd=point['distance']
    if cur > prev:
        inc=cur-prev
        climb+=inc
    if cur <prev:
        dec=prev-cur
        descent+=dec
    if curd > prevd:
        travd+=(curd-prevd)
    prev=cur
    prevd=curd
print ("Total climb: %0.2f m\nTotal descent: %02.f m"%(climb,descent))
if len(xyvals['distances'])>1:
    print ("Total distance: %0.2f m"%(travd))
    maxx=max(xyvals['distances'])
    #print ('max distance is %d'%maxx)
    try:
        xind=np.arange(0,maxx, (maxx-maxx%25)/10)
    except:
        print ('ride distance too low; trying steps of 5 km')
        xind=np.arange(0,maxx, (maxx-maxx%5)/10)
    #if args.n != 'none':
     #   sys.exit(0)
    maxy=max(xyvals['alts'])
    miny=min(xyvals['alts'])
    yind=np.arange(miny,maxy, (maxy-maxy%50)/10)
    fig = plt.figure('ElevProfiler')
    profilename=args.f.split('.')[0]
    if args.t != 'none':
        profilename=args.t
    fig.suptitle(profilename, fontsize=14, fontweight='bold')
    cid = fig.canvas.mpl_connect('button_press_event', onclick)
    ax = fig.add_subplot(211)
    ax.set_ylabel('Altitude in meters')
    ax.set_xlabel('Distance in kilometers')
    ax.plot(xyvals['distances'],xyvals['alts'],'g-')
    plt.xticks(xind)
    plt.yticks(yind)
    #print (len(xyvals['alts']))
    #print (len(xyvals['distances']))
    #print (len(xyvals['grades']))
    #print (len(xyvals['grade-dists']))
    startalt=xyvals['alts'][0]
    endalt=xyvals['alts'][len(xyvals['alts'])-1]
    if endalt >= startalt:
        print ('Net alt gain: %s'%(str(endalt-startalt)))
    else:
        print ('Net alt loss: %s'%(str(startalt-endalt)))
    
    ax = fig.add_subplot(212)
    ax.set_ylabel('% Gradient')
    ax.set_xlabel('Distance in kilometers')
    maxx=max(xyvals['grade-dists'])
    try:
        xind=np.arange(0,maxx, (maxx-maxx%25)/10)
    except:
        print ('ride distance too low; trying steps of 5 km')
        xind=np.arange(0,maxx, (maxx-maxx%10)/10)
    maxy=max(xyvals['grades'])
    miny=min(xyvals['grades'])
    upl=2
    while True:
        yind=np.arange(miny-2,maxy+2,upl)
        if len(yind) <=10:
            break
        upl+=1
    ax.plot(xyvals['grade-dists'],xyvals['grades'],'g-')
    plt.axhline(0, color='blue')
    plt.xticks(xind)
    plt.yticks(yind)
    if args.n == 'none':
        plt.show()
    fig.savefig('output.pdf', bbox_inches='tight')
    maxgrade=0
    maxgdist=0
    for i in range(0, len(xyvals['grades'])-1):
        if maxgrade <xyvals['grades'][i]:
            maxgrade=xyvals['grades'][i]
            maxgdist=xyvals['grade-dists'][i]
    #print (maxgrade)
    #print (maxgdist)
