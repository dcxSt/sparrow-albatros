import argparse
import time
import numpy as np
import sys
import os
from os.path import join
from configparser import ConfigParser
import utils
import logging
import datetime
from sparrow_albatros import str2ip
import lbtools_l
#from pcapy import open_live
import socket
import struct
import pcapy
import dpkt

def write_header(file_object, chans, spec_per_packet, bytes_per_packet, bits):
    have_trimble = True
    header_bytes = 8*10 + 8*len(chans) # 8 bytes per element in the header
    gpsread = lbtools_l.lb_read()
    gps_time = gpsread[0]
    if gps_time is None:
        logger.info('File timestamp coming from Sparrow clock. This is unreliable.')
        have_trimble = False
        gps_time = time.time()
    #print('GPS time is now ', gps_time)
    file_header=np.asarray([header_bytes, bytes_per_packet, len(chans), spec_per_packet, bits, have_trimble], dtype='>Q')
    file_header.tofile(file_object)
    np.asarray(chans, dtype=">Q").tofile(file_object)
    gps_time=np.asarray([0, gps_time], dtype='>Q') # setting gps_week = 0 to flag the new header format with GPS ctime timestamp
    gps_time.tofile(file_object)
    lat_lon = gpsread[1]
    if lat_lon is None:
        logger.info("Can't speak to LB, so no position information")
        latlon={}
        latlon['lat']=0
        latlon['lon']=0
        latlon['elev']=0
    else:
        latlon={}
        latlon['lat']=lat_lon[3]
        latlon['lon']=lat_lon[2]
        latlon['elev']=lat_lon[4]
        #print('lat/lon/elev are ',latlon['lat'],latlon['lon'],latlon['elev'])

    latlon=np.asarray([latlon['lat'],latlon['lon'],latlon['elev']],dtype='>d')
    latlon.tofile(file_object)

if __name__=="__main__":
    parser=argparse.ArgumentParser(description="Script to save baseband to disk")
    parser.add_argument('-l','--loggerlevel', type=str, default='INFO', help='Level of the logger, default is INFO, (Options are: DEBUG, INFO, WARNING)')
    parser.add_argument('-c','--configfile', type=str, default='/home/casper/sparrow-albatros/software/config.ini', help='.ini file with parameters to configure firmware')
    args=parser.parse_args()
    
    # Set up the logger
    logger=logging.getLogger('albatros_dump_baseband')
    if args.loggerlevel.upper() == 'INFO':
        logger_level = logging.INFO
    elif args.loggerlevel.upper() == 'DEBUG':
        logger_level = logging.DEBUG
    elif args.loggerlevel.upper() == 'WARNING':
        logger_level = logging.WARNING
    else:
        raise Exception(f"Did not recognise logger level {args.loggerlevel.upper()}")
    logger.setLevel(logger_level)
    logger.propagate=False # log messages are passed to handlers of logger's ancestors

    # Load config file
    config_file=ConfigParser()
    config_file.read(args.configfile)

    # Logger settings
    logger=logging.getLogger("sparrow_albatros_dump_baseband")
    logger.propagate=False
    logger.setLevel(logging.INFO)
    LOG_DIRECTORY=config_file.get("paths", "log_directory")
    baseband_log_dir=join(LOG_DIRECTORY, "baseband")
    if not os.path.isdir(baseband_log_dir):
        os.makedirs(baseband_log_dir)
    file_logger=logging.FileHandler(join(baseband_log_dir,f"albatros_dump_baseband_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"))
    file_logger.setFormatter(logging.Formatter("%(asctime)s %(name)s %(message)s", "%Y-%m-%d %H:%M:%S"))
    file_logger.setLevel(logging.INFO)
    logger.addHandler(file_logger)
    # Logger to stdout
    stdout_logger=logging.StreamHandler(sys.stdout)
    stdout_logger.setLevel(logging.INFO)
    logger.addHandler(stdout_logger)

    ## Get relevant parameters from config file & write log
    #logger.info("#"*50)
    DEST_IP=config_file.get("fpga_register_vals", "dest_ip")
    #logger.info(f"# (1) Arm processor IP address: {SNAP_IP}")
    DEST_PRT=config_file.getint("fpga_register_vals", "dest_prt")
    #logger.info(f"# (2) UDP packet destination port: {dest_prt}")
    FILE_SIZE=config_file.getfloat("baseband", "file_size")
    HOST=config_file.get("networking", "host")
    MAX_BYTES_PER_PACKET=config_file.getint("networking", "max_bytes_per_packet")
    CHANNELS_STRING=config_file.get("baseband", "channels")
    BITS=config_file.get("baseband", "bits") # 1 or 4

    ## ==== Set up comms ====
    max_bytes=65565
    #sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #bufsize=sock.getsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF)
    #logger.info(f"UDP buf size in bytes: {bufsize}")
    ## timeout prevents hanging on sock.recvfrom_into(packet, bytes_per_packet) after overheat
    #sock.settimeout(10)
    #try:
    #    sock.bind((DEST_IP, DEST_PRT))
    #    #sock.bind(('0.0.0.0', DEST_PRT))
    #    logger.info(f"Connected to {DEST_IP}:{DEST_PRT}")
    #except:
    #    logger.error(f"Cannot bind to {DEST_IP}:{DEST_PRT}")

    #sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(3))
    #sock.bind(('eth0', 0))
    cap = pcapy.open_live('eth0', 65535, 1, 100)
    cap.setfilter("udp and dst port 7417 and dst host 10.10.11.99 and src host 192.168.41.10") 
    UDP_PORT = 7417

    chans=utils.get_channels_from_str(CHANNELS_STRING, BITS)
    spec_per_packet=utils.get_nspec(chans, max_nbyte=MAX_BYTES_PER_PACKET)
    bytes_per_spectrum=chans.shape[0]
    print(f"Spec per packet: {spec_per_packet}")
    print(f"Bytes per spectrum: {bytes_per_spectrum}")
    input("[Enter]")
    bytes_per_packet=bytes_per_spectrum*spec_per_packet+4 #the 4 extra bytes is for the spectrum number
    #packet=bytearray(bytes_per_packet)
    num_of_packets_per_file=int(FILE_SIZE*1.0e9/bytes_per_packet)
    spec_per_file = spec_per_packet * num_of_packets_per_file
    logger.info(f"Spectra per packet: {spec_per_packet}")
    logger.info(f"Bytes per packet: {bytes_per_packet}")
    logger.info(f"Num packets per file: {num_of_packets_per_file}")
    logger.info(f"Num spectra per file: {spec_per_file}")
    
    # Autotuning
    # TODO

    # Figure out drive situation
    # TODO
    # copy from here: https://github.com/ALBATROS-Experiment/albatros_daq/blob/py38_port/new_daq/dump_baseband.py#L27

    # Write baseband
    # for now just this hacky thing, assume the drive has been mounted and has space
    bbpath="/media/BASEBAND/baseband"
    assert os.path.isdir(bbpath), "Drive not mounted, crashing program"
    ip_header_start = 14
    udp_header_start = ip_header_start + 20
    udp_payload_start = udp_header_start + 8 # udp header is 8 bytes
    print("bytes_per_packet", bytes_per_packet)
    while True:
        dirtime=str(int(time.time()))[:5] # first five digitis of ctime
        if not os.path.isdir(join(bbpath, dirtime)):
            os.mkdir(join(bbpath, dirtime))
        fname=f"{int(time.time())}.raw"
        fpath=join(bbpath, dirtime, fname)
        with open(fpath, "wb", buffering=1024*1024) as bbfile:
            write_header(bbfile, chans, spec_per_packet, bytes_per_packet, BITS)
            for i in range(num_of_packets_per_file):
                try:
                    (header, packet) = cap.next()
                    bbfile.write(packet[udp_payload_start:udp_payload_start + bytes_per_packet])
                    sn = int.from_bytes(packet[udp_payload_start:udp_payload_start + 4], byteorder='big', signed=False)
                    if i == 0:
                        start_sn = sn
                except Exception as e:
                    logger.warning(f"Ignoring exception {e}")
                    continue
        print(f"num packets per file {num_of_packets_per_file}")
        print(f"spec_per_packet {spec_per_packet}")
        print(f"sn {sn}")
        print(f"start sn {start_sn}")
        missing_frac = 1. - float(num_of_packets_per_file * spec_per_packet)/(sn - start_sn + spec_per_packet)
        perc_missing = missing_frac * 100
        logger.info(f"Wrote file to {fpath}. Missing percentage of packets is {perc_missing:.5f}")














