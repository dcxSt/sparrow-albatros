import logging
import casperfpga
from sparrow_albatros import *
host="10.10.11.99"
fpgfile="../firmware/sparrow_albatros_spec/outputs/sparrow_albatros_spec_2023-08-22_2102-xc7z035.fpg"
fpga=casperfpga.CasperFpga(host,transport=casperfpga.KatcpTransport)
sparrow=AlbatrosDigitizer(fpga,fpgfile,500.,logging.getLogger('x'))
sparrow.setup()
sparrow.tune(ref_clock=500.,fftshift=0xffff,acc_len=1<<17,dest_ip="10.10.11.99",
        dest_prt=7417,
        spectra_per_packet=7,
        bytes_per_spectrum=200)


