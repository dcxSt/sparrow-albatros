# Default rule
all: dump_baseband

dump_baseband: dump_baseband.c
	gcc -o dump_baseband dump_baseband.c -lpcap -linih

clean:
	rm -f dump_baseband
