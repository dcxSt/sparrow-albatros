import lbtools_l

def check_lb():
    """Checks the status of the Leo Bodnar GPS. 
    Return values indicating status. If unable to set LB, first arg False."""
    if lbtools_l.lb_set():
        gps_data = lbtools_l.lb_read()
        ctime = gps_data[0]
        gpsloc = gps_data[1][2:] # GPS location
        htime = str(gps_data[2]) # human-readable time
        loc_reliable = False if gps_data[1][1][-4:][1] == '0' else True
        time_reliable = False if gps_data[1][1][-4:][2] == '0' else True
        return True,  ctime, gpsloc, htime, loc_reliable, time_reliable
    else:
        return False, None,  None,   None,  None,         None

if __name__ == "__main__":
    """Check and print status of Leo Bodnar"""
    lbstatus, ctime, gpsloc, htime, loc_reliable, time_reliable = check_lb()
    if lbstatus is True:
        print(f"GPS time: {htime}")
        print(f"Timestamp: {ctime}")
        print(f"Latitude: {gpsloc[1]}")
        print(f"Longitude: {gpsloc[0]}")
        print(f"Elevation: {gpsloc[2]}")
        if loc_reliable is False:
            print("WARNING: GPS location is not reliable.")
        if time_reliable is False:
            print("WARNING: GPS time and date is not reliable.")
    else:
        print("Something went wrong.")
