Module for writing/reading binary files being continuously written to disk.
Designed for supporting scihi.

Usage:  

scio.append(arr,filename,[overwrite=False])
write the array arr to the end of file filename.  If overwrite is
True, then erase what's there and start fresh.  
Routine does *not* check that dtype/size of succeeding arrays matches
what's already in the file.  

arr=scio.read(filename)
return as a numpy array of the same dtype the set of arrays written.

Currently supported dtypes are int32, int64, uint32, uint64, float32, and float64.

