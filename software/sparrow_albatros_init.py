#! /usr/bin/env python
import sys
import time
import argparse
import logging
import casperfpga
from sparrow_albatros import AlbatrosDigitizer

#Firmware location /home/casper/sparrow-albatros/firmware/sparrow_albatros_spec/outputs/sparrow_albatros_spec_2023-08-22_2102-xc7z035.fpg

def run(host, fpgfile,
        adc_clk=500,
        skipprog=False,
        ):

    logger = logging.getLogger(__file__)
    logger.setLevel(logging.DEBUG)
    # Create a console handler to output logs to the terminal
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # Set the handler's logging level
    # Create a formatter for the log messages
    formatter=logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    # Add the handler to the logger
    logger.addHandler(console_handler)

    logger.info("Connecting to board with hostname %s" % host)
    cfpga = casperfpga.CasperFpga(host, transport=casperfpga.KatcpTransport)

    logger.info("Instantiating control object with fpgfile %s" % fpgfile)
    sparrow = AlbatrosDigitizer(cfpga, fpgfile=fpgfile, adc_clk=adc_clk, logger=logger)

    if not skipprog:
        logger.info("Programming FPGA at %s with %s" % (host, fpgfile))
        sparrow.program_fpga()

    fpga_clock_mhz = sparrow.cfpga.estimate_fpga_clock()
    logger.info("Estimated FPGA clock is %.2f MHz" % fpga_clock_mhz)

    if fpga_clock_mhz < 1:
        raise RuntimeError("FPGA doesn't seem to be clocking correctly")

    logger.info("Tuning FPGA registers")
    sparrow.setup_and_tune(ref_clock=10, fftshift=0xffff, acc_len=(1<<17),
            dest_ip="10.10.255.255", dest_prt=4321, 
            spectra_per_packet=128, bytes_per_spectrum=16)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Program and initialize a Sparrow ADC->10GbE design',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('host', type=str,
                        help = 'Hostname / IP of Sparrow board')
    parser.add_argument('fpgfile', type=str, 
                        help = '.fpgfile to program or /read')
    parser.add_argument('--adc_clk', type=float, default=500.0,
                        help ='ADC sample rate in MHz')
    parser.add_argument('--skipprog', dest='skipprog', action='store_true', default=False,
                        help='Skip programming .fpg file')

    args = parser.parse_args()
    run(args.host, args.fpgfile,
        adc_clk = args.adc_clk,
        skipprog=args.skipprog,
        )
