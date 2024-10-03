from sparrow_albatros import AlbatrosDigitizer
import casperfpga
import logging
import time
import numpy as np
import argparse

def ascii_plot(a,b,minfreq=None,maxfreq=None,char1="*",char2="o",height=20,width=80):
    assert len(a)==width
    assert len(b)==width
    grid=[[' ' for _ in range(width)] for _ in range(height)]
    min_val = min(min(a),min(b))
    max_val = max(max(a),max(b))
    scale = lambda val: int((val - min_val) / (max_val - min_val) * (height - 1))
    print('\033[H',end='') # Move cursor to top of terminal
    print('-'*(width+2))
    for x in range(width):
        y1 = height - 1 - scale(a[x])
        y2 = height - 1 - scale(b[x])
        grid[y1][x] = char1
        grid[y2][x] = char2
    for i,row in enumerate(grid):
        print('|',end="")
        print(''.join(row),end="")
        print('|',end="")
        if i%5==0 or i==len(grid)-1:print(f'{(1-i/height)*max_val + i/height*min_val:.1f}dB')
        else:print()
    print('-'*(width+2))
    if minfreq is not None and maxfreq is not None:
        print(f'{minfreq:.1f}MHz' + ' '*(width-7) + f'{maxfreq:.1f}MHz')
    return

# Create the argument parser
parser = argparse.ArgumentParser(description="Process minfreq and maxfreq arguments")
# Add positional arguments for minfreq and maxfreq
parser.add_argument('minfreq', type=float, help='Minimum frequency (MHz)')
parser.add_argument('maxfreq', type=float, help='Maximum frequency (MHz)')
# Parse the arguments
args = parser.parse_args()
# Access the arguments
minfreq = args.minfreq
maxfreq = args.maxfreq
assert minfreq>=0, "Minfreq must be greater than zero"
assert maxfreq<=250, "Maxfreq must be lesser than 250 MHz"

# Init the logger, make it print to terminal
logger=logging.getLogger("my_logger")
logger.setLevel(logging.DEBUG)
console_handler=logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.debug("This is a debug message")

host="10.10.11.99"
fpgfile="/home/casper/sparrow-albatros/firmware/sparrow_albatros_spec/outputs/sparrow_albatros_spec_2023-08-22_2102-xc7z035.fpg"
cfpga=casperfpga.CasperFpga(host, transport=casperfpga.KatcpTransport)
s=AlbatrosDigitizer(cfpga,fpgfile,500.,logger)
s.setup_and_tune(ref_clock=10, fftshift=0xffff, acc_len=(1<<17), dest_ip="127.0.0.1",dest_prt=7417,spectra_per_packet=8,bytes_per_spectrum=128)
#input('[Enter] to continue')
#print('\033[H',end='') # Move cursor to top of terminal
#print(f"{' '*190}\n"*20)
print("\n"*50)
while True:
    time.sleep(0.5)
    pols=s.read_pols(["pol00","pol11"])
    pol00,pol11=pols["pol00"],pols["pol11"]
    # 25 MHz is 250 MHz/10 so it's channel 2048/10 = 205
    width=80
    idxs = np.arange(int(minfreq*2048/250), int(maxfreq*2048/250))
    width=len(idxs)
    height=width//3
    ascii_plot(10*np.log10(pol00[idxs]),10*np.log10(pol11[idxs]),minfreq,maxfreq,
            height=height,width=width)




