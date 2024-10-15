import logging
import casperfpga
from sparrow_albatros import *
host="10.10.11.99"
#fpgfile="../firmware/sparrow_albatros_spec/outputs/sparrow_albatros_spec_2023-08-22_2102-xc7z035.fpg"
fpgfile="../firmware/sparrow_albatros_spec/outputs/sparrow_albatros_spec_2024-10-11_0106-xc7z035.fpg"
fpga=casperfpga.CasperFpga(host,transport=casperfpga.KatcpTransport)
sparrow=AlbatrosDigitizer(fpga,fpgfile,250,logging.getLogger('x'))
sparrow.setup()
sparrow.tune(ref_clock=250.,fftshift=0xffff,acc_len=1<<17,dest_ip="10.10.11.99",
        dest_prt=7417,
        spectra_per_packet=14,
        bytes_per_spectrum=100)



