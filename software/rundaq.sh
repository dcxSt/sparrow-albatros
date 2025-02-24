echo "Mounding /dev/sda1 to /media/BASEBAND"
sudo mount /dev/sda1 /media/BASEBAND
echo "Configuring FPGA"
/home/casper/python3-venv/bin/python configfpga.py
echo "Spawning dump spectra process"
/home/casper/python3-venv/bin/python dump_spectra.py
echo "Spawning dump baseband process"
sudo /home/casper/python3-venv/bin/python dump_baseband.py -l debug
