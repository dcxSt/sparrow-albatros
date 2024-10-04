import os
import struct
import time
import numpy as np
import ads5404
import adf4351

# Design register names
SS_NAME = "ss_adc"

def str2ip(ip):
    iplist = list(map(int, ip.split('.')))
    ipint = 0
    for i in range(4):
        ipint += (iplist[i] << (8*(3-i)))
    return ipint

def ip2str(ipint):
    ip=""
    for i in range(4):
        shift = (3-i)*8
        ip += str((ipint & (0b11111111<<shift)) >> shift)
        ip += '.'
    return ip[:-1]

class SparrowAlbatros():
    def __init__(self, cfpga, fpgfile=None, adc_clk=500.):
        """
        Constuctor for SparrowAdc2Tge control instance.

        :param cfpga: CasperFpga instance for Sparrow board connection
        :type cfpga: casperfpga.Casperfpga

        :param fpgfile: .fpg file to associate with running firmware. If
            none is provided, certain methods will be unavailable until
            either `program_fpga` or `read_fpgfile` are called.
        :type fpgfile: str

                :param adc_clk: ADC sample rate in MHz
                :type adc_clk: float
        """
        self.cfpga = cfpga
        self.adc_clk = adc_clk
        self.adc = ads5404.Ads5404(cfpga)
        self.pll = adf4351.Adf4351(cfpga, out_freq=adc_clk)
        self.fpgfile = None
        if fpgfile is not None:
            self.read_fpgfile(fpgfile)

    def initialize_adc(self):
        """
        Initialize ADC interface.
        """
        self.adc.chip_reset()
        self.adc.hw_reset()
        self.adc.enable_readback()
        self.adc.init()
        self.sync_adc()

    def sync_adc(self):
        """
        Send a sync pulse to the ADC
        """
        self.cfpga.write_int("sync", 0)
        self.cfpga.write_int("sync", 1)
        self.cfpga.write_int("sync", 0)

    def get_adc_temp(self):
        """
        Get ADC temperature.

        :return: temerature in degrees C
        :rtype: int
        """
        return self.adc.get_temp()

    def read_fpgfile(self, fpgfile):
        """
        Associate running firmware with give .fpg file.
        This does _not_ program the FPGA. For that, use `program_fpga()`.
        This is a shortcut to casperfpga's get_system_information.

        :param fpgfile: .fpg file to read
        :type fpgfile: str
        """
        if not os.path.isfile(fpgfile):
                raise RuntimeError("%s is not a file" % fpgfile)
        self.fpgfile = fpgfile
        try:
            self.cfpga.get_system_information(fpgfile)
        except:
            print("Could not process fpgfile %s. Maybe the FPGA is not programmed yet?" % fpgfile)

    def program_fpga(self, fpgfile=None):
        """
        Program the FPGA with the provided fpgfile,
        or self.fpgfile if none is provided.

        :param fpgfile: .fpg file to program. If None, the fpgfile
            provided at instantiation time will be programmed.
        :type fpgfile: str
        """
        self.fpgfile = fpgfile or self.fpgfile
        if self.fpgfile is None:
            raise RuntimeError("Don't know what .fpg file to program!")
        self.cfpga.upload_to_ram_and_program(self.fpgfile)
        time.sleep(0.3)
        self.pll.configure()
        time.sleep(0.3)
        self.adc.power_enable()

    def get_adc_snapshot(self, use_pps_trigger=False):
        """
        Get a snapshot of ADC samples simultaneously captured from
        both ADC channels.

        :param use_pps_trigger: If True, use the DSP pipeline's PPS trigger to
            start capture. Otherwise, capture immediately.
        :type use_pps_trigger: bool

        :return: x, y; a pair of numpy arrays containing a snapshot of ADC
            samples from ADC channel 0 and 1, respectively.
        :rtype: (numpy.ndarray, numpy.ndarray)
        """
        if not SS_NAME in self.cfpga.snapshots.keys():
            raise RuntimeError("%s not found in design. Have you provided an appropriate .fpg file?" % SS_NAME)
        ss = self.cfpga.snapshots[SS_NAME]
        d, t = ss.read_raw(man_trig=not use_pps_trigger)    
        v = np.array(struct.unpack(">%dh" % (d["length"]//2), d["data"]))
        x = v[0::2]
        y = v[1::2]
        return x, y

class AlbatrosDigitizer(SparrowAlbatros):
    def __init__(self, cfpga, fpgfile=None, adc_clk=500., logger=None):
        """
        Constructor binds logger, as well as parent attributes (cfpga, etc.). 
        """
        super().__init__(cfpga, fpgfile, adc_clk)
        self.logger = logger # TODO: sort out logging, default logger?
        return 

    def setup_and_tune(self, ref_clock, fftshift, acc_len, dest_ip, 
            dest_prt, spectra_per_packet, bytes_per_spectrum):
        """
        Setup the FPGA firmware by tuning the input registers.
        Perform sanity check on each after setting the value. 
        - Assumes fpga has been programmed and cfpga is running. 
        - Sets values in FPGA's programmable Registers and BRAMs. 
        - Basic health checks of FPGA output values, e.g. overflows. 

        :param ref_clock: Reference clock in MHz. 
        :type ref_clock: float (int?)

        :param fftshift: Register Value. FFT shift schedule, bits 1/0 for on/off.
        :type fftshift: int
        :param acc_len: RV. Number of spectra accumulated to integrate correlations. 
        :type acc_len: int
        :param dest_ip: RV. IP address to send packets to. Turn into int before writing. 
        :type dest_ip: str
        :param dest_prt: RV. Packet destination port number. 
        :type dest_prt: int
        :param spectra_per_packet: RV. Number of specs to write in each UDP packet. 
        :type spectra_per_packet: int
        :param bytes_per_spectrum: RV. Number of bytes in one, quantized spec. 
        :type bytes_per_spectrum: int

        JF reccomends using netcat for writing packets to file for test. 
        """
        # Assume bitstream already uploaded, data in self.cfpga
        # Assume ADCs already initialized including that get_system_information...
        # Inherit adc's logger level
        self.adc.ref = ref_clock # Set reference clock for ADC
        # ADC calibration assumed already aligned (?)
        # Need to set the ADC gain?
        # Get info from and set registers 
        self.logger.info(f"FPGA clock: {self.cfpga.estimate_fpga_clock():.2f}")
        self.logger.info(f"Set FFT shift schedule to {fftshift:b}")
        self.cfpga.registers.pfb_fft_shift.write_int(fftshift)
        fft_of_count_init = self.cfpga.registers.fft_of_count.read_uint() # start counting fft overflows above this number
        self.logger.info(f"Set correlator accumulation length to {acc_len}")
        self.cfpga.registers.acc_len.write_int(acc_len)
        # This firmware only has 4-bit qutnziation
        self.logger.info("Reset GBE (UDP packetizer)")
        self.cfpga.registers.gbe_rst.write_int(0)
        self.cfpga.registers.gbe_rst.write_int(1)
        self.cfpga.registers.gbe_rst.write_int(0)
        self.logger.info(f"Set #spectra-per-packet to {spectra_per_packet}")
        self.cfpga.registers.packetiser_spectra_per_packet.write_int(spectra_per_packet)
        self.logger.info(f"Set #bytes-per-spectrum to {bytes_per_spectrum}")
        self.cfpga.registers.packetiser_bytes_per_spectrum.write_int(bytes_per_spectrum)
        self.logger.info(f"Set destination IP address and port to {dest_ip}:{dest_prt}")
        self.cfpga.registers.dest_ip.write_int(str2ip(dest_ip))
        self.cfpga.registers.dest_prt.write_int(dest_prt)
        # Do we need to set mac address?
        self.logger.info("Resetting counters and syncing")
        self.cfpga.registers.cnt_rst.write_int(0)
        self.cfpga.registers.sync.write_int(0)
        self.cfpga.registers.sync.write_int(1)
        self.cfpga.registers.sync.write_int(0)
        self.cfpga.registers.cnt_rst.write_int(1)
        self.cfpga.registers.cnt_rst.write_int(0)
        fft_of_count = self.cfpga.registers.fft_of_count.read_uint() - fft_of_count_init
        if fft_of_count != 0:
            self.logger.warning(f"FFT overflowing: count={fft_of_count}")
        else:
            self.logger.info(f"No FFT overflows detected")
        self.logger.info("Enabling 1 GbE output")
        self.cfpga.registers.gbe_en.write_int(1)
        gbe_overflow = self.cfpga.registers.tx_of_cnt.read_uint()
        if gbe_overflow:
            self.logger.warning(f"GbE transmit overflowing: count={gbe_overflow}")
        else:
            self.logger.info("No GbE overflows detected")
        self.logger.info("Setup and tuning complete")
        return

    def read_pols(self, pols, struct_format=">2048q"):
        pols_dict = {}
        for pol in pols:
            pols_dict[pol] = np.array(struct.unpack(struct_format, self.cfpga.read(pol, 2048*8)), dtype="int64")
        return pols_dict

    def set_channels(self, channels:list):
        """
        Set reorder BRAMs to reorder channels before selection.

        :param channels: A list or array of the channels to select. 
        """
        # TODO: implement this
        return 







