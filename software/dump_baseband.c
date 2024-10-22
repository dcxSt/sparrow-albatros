#include <pcap.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <arpa/inet.h>
#include "dump_baseband.h"
#include "ini.h" // Ensure inih is installed

#define MAX_STRING_LENGTH 256 // Define a reasonable limit for strings

// Struct for things to parse from config.ini and to write bb file header
typedef struct {
    uint64_t* chans;
    uint64_t* coeffs;
    uint64_t lenchans;
    uint64_t spec_per_packet;
    uint64_t bytes_per_spec;
    uint64_t bytes_per_payload_specnum;
    uint64_t bytes_per_packet;
    uint64_t bits;
    char dump_spectra_output_directory[MAX_STRING_LENGTH];
} config_t;

// Parse chans in config.ini format (e.g. chans=190:210 220:230)
void parse_chans(const char* value, config_t* config) {
    // Count the number of ranges (space-separated)
    char* str_copy = strdup(value); // Copy input string to avoid modifying it
    char* token = strtok(str_copy, " ");
    size_t count = 0;
    while (token != NULL) {
        char* colon = strchr(token, ':');
        if (colon != NULL) {
            uint64_t start = strtoull(token, NULL, 10);
            uint64_t end = strtoull(colon + 1, NULL, 10);
            count += (end - start + 1); // Add size of range
        }
        token = strtok(NULL, " ");
    }
}

// Callback function for parsing the ini file
static int ini_handler(void* user, const char* section, const char* name, const char* value) {
    config_t* pconfig = (config_t*)user;

    if (strcmp(section, "Settings") == 0) {
        if (strcmp(name, "chans") == 0) {
            // Count the number of elements
            size_t num_chans = count_commas(value);
            pconfig->chans = (uint64_t*)malloc(num_chans * sizeof(uint64_t));

            // Parse and fill the chans array
            char* token = strtok((char*)value, ",");
            size_t i = 0;
            while (token != NULL) {
                pconfig->chans[i++] = strtoull(token, NULL, 10);
                token = strtok(NULL, ",");
            }
            pconfig->lenchans = num_chans; // Set the number of channels
        } else if (strcmp(name, "coeffs") == 0) {
            // Count the number of elements
            size_t num_coeffs = count_commas(value);
            pconfig->coeffs = (uint64_t*)malloc(num_coeffs * sizeof(uint64_t));

            // Parse and fill the coeffs array
            char* token = strtok((char*)value, ",");
            size_t i = 0;
            while (token != NULL) {
                pconfig->coeffs[i++] = strtoull(token, NULL, 10);
                token = strtok(NULL, ",");
            }
        } else if (strcmp(name, "spec_per_packet") == 0) {
            pconfig->spec_per_packet = strtoull(value, NULL, 10);
        } else if (strcmp(name, "bytes_per_spec") == 0) {
            pconfig->bytes_per_spec = strtoull(value, NULL, 10);
        } else if (strcmp(name, "bytes_per_payload_specnum") == 0) {
            pconfig->bytes_per_payload_specnum = strtoull(value, NULL, 10);
        } else if (strcmp(name, "bits") == 0) {
            pconfig->bits = strtoull(value, NULL, 10);
        }
    }
    return 1; // Continue parsing
}

uint64_t to_big_endian(uint64_t value) {
    uint64_t result =
        ((value & 0x00000000000000FF) << 56) |
        ((value & 0x000000000000FF00) << 40) |
        ((value & 0x0000000000FF0000) << 24) |
        ((value & 0x00000000FF000000) << 8)  |
        ((value & 0x000000FF00000000) >> 8)  |
        ((value & 0x0000FF0000000000) >> 24) |
        ((value & 0x00FF000000000000) >> 40) |
        ((value & 0xFF00000000000000) >> 56);
    return result;
}

double to_big_endian_double(double value) {
    uint64_t temp = *(uint64_t*)&value; // Reinterpret as double 
    uint64_t result = to_big_endian(temp); // to big endian
    return *(double*)&result; // Cast the result back to double
}

//double to_big_endian_double(double value) {
//    double result;
//    uint8_t *value_ptr = (uint8_t*)&value;
//    uint8_t *result_ptr = (uint8_t*)&result;
//    // Reverse the byte order
//    for (int i = 0; i < sizeof(double); i++) {
//        result_ptr[i] = value_ptr[sizeof(double) - 1 - i];
//    }
//    return result;
//}

void write_header(FILE *file, uint64_t *chans, uint64_t *coeffs, uint64_t lenchans, uint64_t spec_per_packet, uint64_t bytes_per_packet, uint64_t bits) {
    uint64_t have_gps = 1; // bool, 1-true, 0-false
    uint64_t header_bytes = (11 + 2 * lenchans) * 8; // 2xlenchans for coeffs
    //uint64_t header_bytes = 8 * 10 + 8 * lenchans; // add smt for coeffs
    // TODO: Read LeoBodnar, for now, dummy 
    uint64_t gps_week  = 0; // This is set to zero for whatever reason
    uint64_t gps_time  = 0; // IRL read gps time with lbtools
    uint64_t lattitude = 0; // IRL read gps time with lbtools
    uint64_t longitude = 0; // IRL read gps time with lbtools
    uint64_t elevation = 0; // IRL read gps time with lbtools
    uint64_t file_header0[] = {
        to_big_endian(header_bytes),     // 1
        to_big_endian(bytes_per_packet), // 2
        to_big_endian(lenchans),         // 3
        to_big_endian(spec_per_packet),  // 4
        to_big_endian(bits),             // 5
        to_big_endian(have_gps),         // 6
        to_big_endian(gps_week),         // 7
        to_big_endian(gps_time)          // 8
    };
    size_t elements_written = fwrite(file_header0, sizeof(uint64_t), 8, file);
    if (elements_written != 8) {
        perror("Error writing header-preamble to file");
    }
    double file_header1[] = {
        to_big_endian_double(lattitude), // 9
        to_big_endian_double(longitude), // 10
        to_big_endian_double(elevation), // 11
    };
    elements_written = fwrite(file_header1, sizeof(double), 3, file);
    if (elements_written != 3) {
        perror("Error writing header-gps to file");
    }
    elements_written = fwrite(chans, sizeof(uint64_t), (size_t)lenchans, file);
    if (elements_written != (size_t)lenchans) {
        perror("Error writing header-chans to file");
    }
    elements_written = fwrite(coeffs, sizeof(uint64_t), (size_t)lenchans, file);
    if (elements_written != (size_t)lenchans) {
        perror("Error writing header-coeffs to file");
    }
    return;
}

int main() {
    char errbuf[PCAP_ERRBUF_SIZE];
    pcap_t *handle;
    struct bpf_program fp; // The compiled filter
    char filter_exp[] = "udp and dst port 7417 and dst host 10.10.11.99 and src host 192.168.41.10";
    bpf_u_int32 net;
    
    // Create sniffing device
    handle = pcap_create("eth0", errbuf);
    if (handle == NULL) {
        fprintf(stderr, "Couldn't open device: %s\n", errbuf);
        return 1;
    }
    // Promiscuous mode
    if (pcap_set_promisc(handle, 1) != 0) {
        fprintf(stderr, "Couldn't set promiscuous mode: %s\n", pcap_geterr(handle));
        return 1;
    }
    // Set timeout
    if (pcap_set_timeout(handle, 1000) !=  0) {
        fprintf(stderr, "Couldn't set timeout: %s\n", pcap_geterr(handle));
        return 1;
    }
    // Set buffer size to 20 MB 20*1024*1024=20971520 bytes
    if (pcap_set_buffer_size(handle, 20971520) != 0) {
        fprintf(stderr, "Couldn't set buffer size: %s\n", pcap_geterr(handle));
        return 1;
    }
    if (pcap_set_snaplen(handle, BUFSIZ) != 0) {
        fprintf(stderr, "Couldn't set snap buffer: %s\n", pcap_geterr(handle));
        return 1;
    }
    // Activate
    if (pcap_activate(handle) != 0) {
        fprintf(stderr, "Couldn't activate pcap handle: %s\n", pcap_geterr(handle));
        return 1;
    }
    // Compile the filter expression
    if (pcap_compile(handle, &fp, filter_exp, 0, net) == -1) {
        fprintf(stderr, "Couldn't parse filter %s: %s\n", filter_exp, pcap_geterr(handle));
        return 1;
    }
    // Set the compiled filter
    if (pcap_setfilter(handle, &fp) == -1) {
        fprintf(stderr, "Couldn't install filter %s: %s\n", filter_exp, pcap_geterr(handle));
        return 1;
    }

    // Open a binary file to write
    // TODO: implement proper file location on disk
    FILE *file = fopen("out.bin", "wb");
    if (file == NULL) {
        perror("Error opening file");
        return 1;
    }
    // Set the buffer size to 20 MB
    size_t buffer_size = 20 * 1024 * 1024;
    char *buffer = malloc(buffer_size); // Allocate buffer
    if (setvbuf(file, buffer, _IOFBF, buffer_size) != 0) {
        perror("Error setting buffer");
        return 1;
    }
    // Write the header
    // TODO: get chans, lenchans, spec_per_packet, bytes_per_packet, bits, for now dummy
    uint64_t chans[] = {190,191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209};
    uint64_t coeffs[] = {500,501,502,503,504,505,506,507,508,509,510,511,512,513,514,515,516,517,518,519};
    uint64_t lenchans = 20;
    uint64_t spec_per_packet = 30;
    uint64_t bytes_per_spec = 2 * 20;
    uint64_t bytes_per_payload_specnum = 4; // in firmware
    uint64_t bytes_per_packet = spec_per_packet * bytes_per_spec + bytes_per_payload_specnum;
    uint64_t bits = 4; // 4 or 1
    write_header(file, chans, coeffs, lenchans, spec_per_packet, bytes_per_packet, bits);

    // Capture and write packets_per_file packets
    int packets_per_file = 6;
    for (int i = 0; i < packets_per_file; i++) {
        struct pcap_pkthdr header;
        const u_char *packet = pcap_next(handle, &header);
        if (packet == NULL) {
            printf("Failed to capture a packet\n");
            return 1;
        }
        printf("Captured a packet with length: %d\n", header.len);
        // Parse the packet, assumes already filtered correctly
        // Write the packet to the binary file, use pointer arithmetic to seek payload starting point
        size_t bytes_written = fwrite(packet + UDP_PAYLOAD_START, 1, (size_t)bytes_per_packet, file);
        if (bytes_written != (size_t)bytes_per_packet) {
            fprintf(stderr, "Failed to write all bytes to file\n");
        }
    }

    // Cleanup
    fclose(file);       // Close the file
    free(buffer);       // Clean up mallocated buffer space
    pcap_freecode(&fp); // Free the compiled filter
    pcap_close(handle); // Close the handle
    return 0;
}









