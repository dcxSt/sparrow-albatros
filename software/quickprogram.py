import logging
import casperfpga
from sparrow_albatros import *
host="10.10.11.99"
fpgfile="../firmware/sparrow_albatros_spec/outputs/sparrow_albatros_spec_2023-08-22_2102-xc7z035.fpg"
fpga=casperfpga.CasperFpga(host,transport=casperfpga.KatcpTransport)
sparrow=AlbatrosDigitizer(fpga,fpgfile,500.,logging.getLogger('x'))
sparrow.program_fpga()
sparrow.initialize_adc()
