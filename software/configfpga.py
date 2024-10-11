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
import lbtools_l

import casperfpga
from sparrow_albatros import *


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
configfpga_log_dir=join(LOG_DIRECTORY, "configfpga")
if not os.path.isdir(configfpga_log_dir):
    os.makedirs(configfpga_log_dir)
file_logger=logging.FileHandler(join(configfpga_log_dir,f"albatros_configfpga_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"))
file_logger.setFormatter(logging.Formatter("%(asctime)s %(name)s %(message)s", "%Y-%m-%d %H:%M:%S"))
file_logger.setLevel(logging.INFO)
logger.addHandler(file_logger)
# Logger to stdout
stdout_logger=logging.StreamHandler(sys.stdout)
stdout_logger.setLevel(logging.INFO)
logger.addHandler(stdout_logger)

## Get relevant parameters from config file & write log
logger.info("Parsing config.ini for relevant values")
MAX_BYTES_PER_PACKET=config_file.getint("networking", "max_bytes_per_packet")
CHANNELS_STRING=config_file.get("baseband", "channels")
COEFFS_STRING=config_file.get("baseband", "coeffs")
BITS=config_file.get("baseband", "bits") # 1 or 4
FPGFILE=config_file.get("paths", "fpgfile")
chans=utils.get_channels_from_str(CHANNELS_STRING, BITS)
print("chans", chans)
input('[enter]')
coeffs=utils.get_coeffs_from_str(COEFFS_STRING)
spectra_per_packet=utils.get_nspec(chans, max_nbyte=MAX_BYTES_PER_PACKET)
bytes_per_spectrum=chans.shape[0]
print(f"Spec per packet: {spectra_per_packet}")
print(f"Bytes per spectrum: {bytes_per_spectrum}")


logger.info("Writing bitstream to FPGA and initializing...")
host="10.10.11.99"
fpga=casperfpga.CasperFpga(host,transport=casperfpga.KatcpTransport)
sparrow=AlbatrosDigitizer(fpga,FPGFILE,500.,logging.getLogger('x'))
sparrow.setup()
sparrow.set_channel_order(chans, BITS)
sparrow.set_channel_coeffs(coeffs, BITS)
sparrow.tune(ref_clock=500.,fftshift=0xffff,acc_len=1<<17,dest_ip="10.10.11.99",
        dest_prt=7417,
        spectra_per_packet=spectra_per_packet,
        bytes_per_spectrum=bytes_per_spectrum)






