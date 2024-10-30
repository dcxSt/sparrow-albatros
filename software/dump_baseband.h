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
#define CONFIGINI_PATH "/home/casper/sparrow-albatros/software/config.ini"
#define MAX_STRING_LENGTH 256 // Define a reasonable limit for strings


// Struct for things to parse from config.ini and to write bb file header
typedef struct {
    uint64_t* chans;
    uint64_t* coeffs;
    uint64_t lenchans;
    uint64_t spec_per_packet;
    uint64_t bytes_per_specnum;
    uint64_t bytes_per_spec;
    uint64_t bytes_per_payload_specnum;
    uint64_t bytes_per_packet;
    uint64_t bits;
    char dump_spectra_output_directory[MAX_STRING_LENGTH];
    char dump_baseband_output_directory[MAX_STRING_LENGTH];
    char log_directory[MAX_STRING_LENGTH];
    char coeffs_binary_path[MAX_STRING_LENGTH];
    double file_size;
    uint64_t max_bytes_per_packet;
    uint64_t version;
} config_t;


void parse_chans(const char* value, config_t* config);

static int my_ini_handler(void* user, const char* section, const char* name, const char* value);

int set_coeffs_from_serialized_binary(config_t* pconfig);

uint64_t get_nspec(uint64_t lenchans, uint64_t max_nbyte);

config_t get_config_from_ini(const char* filename);

uint64_t to_big_endian(uint64_t value);

double to_big_endian_double(double value);

size_t write_header(FILE *file, uint64_t *chans, uint64_t *coeffs, uint64_t version, uint64_t lenchans, uint64_t spec_per_packet, uint64_t bytes_per_packet, uint64_t bits);

int get_packets_per_file(config_t* config);

int create_directory_if_not_exists(char* path);




