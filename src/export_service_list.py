#!/usr/bin/python3 

import os
import time
import requests
from requests.auth import HTTPDigestAuth
import json
import datetime
import time
import random
from random import randint
import shutil


tvheadend_ip="192.168.5.5"
tvheadend_port="9981"
tvheadend_user="teletext"
tvheadend_pass="teletext"

if "TVHEADEND_IP" in os.environ:
    tvheadend_ip=os.environ["TVHEADEND_IP"]

if "TVHEADEND_PORT" in os.environ:
    tvheadend_port=os.environ["TVHEADEND_PORT"]

if "TVHEADEND_USER" in os.environ:
    tvheadend_user=os.environ["TVHEADEND_USER"]

if "TVHEADEND_PASS" in os.environ:
    tvheadend_pass=os.environ["TVHEADEND_PASS"]


outdir="../data"
if "OUTDIR" in os.environ:
    outdir=os.environ["OUTDIR"]

tmpdir="/tmp/"
if "TMPDIR" in os.environ:
    tmpdir=os.environ["TMPDIR"]

rsync_target=None
if "RSYNC_TARGET" in os.environ:
    rsync_target=os.environ["RSYNC_TARGET"]

rsync_remove=0
if "RSYNC_REMOVE" in os.environ:
    rsync_remove=1


mux_properties=[
        "delsys",
        "frequency",
        "symbolrate",
        "polarization",
        "modulation",
        "fec",
        "rolloff",
        "pilot",
        "stream_id",
        "pls",
        "onid",
        "tsid",
        "pls_mode",
        "pls_code"
]


block_number=0

def prefix():
    global block_number
    return "|"*block_number

def block(s):
    print(prefix()+s)

def block_start(s):
    global block_number
    block("+"+s)
    block_number=block_number+1

def block_end():
    global block_number
    block_number=block_number-1


base_url="http://"+tvheadend_ip+":"+tvheadend_port+"/"
base_url_auth="http://"+tvheadend_user+":"+tvheadend_pass+"@"+tvheadend_ip+":"+tvheadend_port+"/"

url=base_url+"api/raw/export?class=dvb_mux"
req=requests.get(url, auth=HTTPDigestAuth(tvheadend_user, tvheadend_pass))
req.encoding="UTF-8"

if req.status_code != 200:
    print("Couldn't get multiplex list. Maybe user has insufficient rights. Code: ", req.status_code)
    exit()

muxes=json.loads(req.text)


url=base_url+"api/raw/export?class=service"
req=requests.get(url, auth=HTTPDigestAuth(tvheadend_user, tvheadend_pass))
req.encoding="UTF-8"

if req.status_code != 200:
    print("Couldn't get service list. Maybe user has insufficient rights. Code: ", req.status_code)
    exit()

services=json.loads(req.text)
service_hash={}
for service in services:
    muxname=service["uuid"]
    service_hash[muxname]=service

orbitals={}
#annotate_and_filter_muxes
for mux in muxes:
    mux_name=""
    position=""
    switch_input=""
    if "delsys" in mux:
        mux_name=mux_name+mux["delsys"]+"-"
        position=mux["delsys"]
    if "frequency" in mux:
        mux_name=mux_name+str(mux["frequency"]);
    if "polarisation" in mux:
        mux_name=mux_name+mux["polarisation"]
    if "orbital" in mux:
        mux_name=mux_name+"-"+mux["orbital"]
    mux["mux_name"]=mux_name
    mux_service=[]
    if "services" in mux and len(mux["services"])>0:
        for suuid in mux["services"]:
            service=service_hash[suuid]
            if not "last_seen" in service:
                continue
            sname=suuid
            last_seen=service["last_seen"]
            last_seen_age=int(time.time())-last_seen
            if last_seen_age>(24*2)*3600:
                continue 
            if len(service["stream"])<=0:
                continue
            del service["uuid"]
            del service["last_seen"]
            del service["created"]
            if "epg_ignore_eit" in service:
                del service["epg_ignore_eit"]
            mux_service.append(service)
    mux["services"]=mux_service
    del mux["uuid"]
    del mux["scan_first"]
    del mux["scan_last"]
    del mux["scan_result"]
    del mux["created"]
    del mux["enabled"]
    del mux["epg"]
    if "epg_module_id" in mux:
        del mux["epg_module_id"]
    if "dvb_satip_dvbc_freq" in mux:
        del mux["dvb_satip_dvbc_freq"]
    if "dvb_satip_dvbt_freq" in mux:
        del mux["dvb_satip_dvbt_freq"]
    if "orbital" in mux:
        orbit=mux["orbital"]
        if orbit in orbitals:
            orbitals[orbit].append(mux)
        else:
            orbitals[orbit]=[mux]

for o in orbitals:
    print(o)
    with open(outdir+'/'+o+'.json','w') as t_file:
        json.dump(orbitals[o],fp=t_file,indent=4, sort_keys=True)
