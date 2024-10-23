#define IP_HEADER_START 14 // Safe to assume for Ethernet, but not other link layers
#define UDP_HEADER_START (IP_HEADER_START + 20) // 20 bytes is the smallest IPV4 header size
#define UDP_PAYLOAD_START (UDP_HEADER_START + 8) // UDP header is always 8 bytes

#define DEST_IP "10.10.11.99"
#define DEST_PRT 7417
#define FILE_SIZE 0.5
#define HOST "10.10.11.99"
#define MAX_BYTES_PER_PACKET 1600
#define CHANNELS_STRING "200:240"
#define BITS 4



size_t write_header(FILE *file, uint64_t *chans, uint64_t *coeffs, uint64_t lenchans, uint64_t spec_per_packet, uint64_t bytes_per_packet, uint64_t bits);



