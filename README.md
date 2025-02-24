:warning: This fork is no longer being developed or maintained. Find the up-to-date version here: [https://github.com/ALBATROS-Experiment/sparrow-albatros/](https://github.com/ALBATROS-Experiment/sparrow-albatros/)

# sparrow-albatros
A repository for ALBATROS firmware targetting the Sparrow FPGA board

## Software Versions:
- Ubuntu 20.04
- Xilinx Vivado System Edition 2021.2
- MATLAB/Simulink 2021a

## To open/modify/compile:

1. Clone this repository
2. Clone submodules:
```
git submodule update --init --recursive
```
3. Create a local environment specification file `firmware/startsg.local`.
4. From `firmware/`, run `startsg` (if your environment file is called `startsg.local`) or `startsg <my_local_environment_file.local>`.

## Repository Layout

 - `firmware/` -- Firmware source files and libraries
 - `software/` -- Libraries providing communication to FPGA hardware and firmware
 - `docs/` -- Documentation
