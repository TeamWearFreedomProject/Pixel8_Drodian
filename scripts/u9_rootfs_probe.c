/*
 * U9 research-only rootfs probe.  READ-ONLY ext4 superblock verification.
 *
 * Unlike BusyBox blkid, this works without the optional blkid applet.
 * Does not mount, format, partition, write or modify a device.
 * Production scan: independently confirmed UUID + ext4 magic + exact label,
 * one unique block-device match from kernel-advertised /sys/class/block.
 * --image is an OFFLINE-only unit-test mode for a local regular .img file.
 */
#define _POSIX_C_SOURCE 200809L
#include <ctype.h>
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#define SUPER_OFFSET 1024
#define EXT4_MAGIC_OFFSET 0x38
#define EXT4_UUID_OFFSET 0x68
#define EXT4_LABEL_OFFSET 0x78
#define SUPER_SIZE 1024
#define MAX_CANDIDATES 256

static int hex_nibble(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    c = (char)tolower((unsigned char)c);
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    return -1;
}

static int parse_uuid(const char *in, uint8_t out[16]) {
    if (!in || strlen(in) != 36) return -1;
    int j = 0, high = -1;
    for (int i = 0; i < 36; i++) {
        if (i == 8 || i == 13 || i == 18 || i == 23) {
            if (in[i] != '-') return -1;
            continue;
        }
        int v = hex_nibble(in[i]);
        if (v < 0) return -1;
        if (high == -1) high = v;
        else {
            if (j >= 16) return -1;
            out[j++] = (uint8_t)((high << 4) | v);
            high = -1;
        }
    }
    return j == 16 && high == -1 ? 0 : -1;
}

static int valid_kernel_block_name(const char *s) {
    if (!s || !*s) return 0;
    size_t n = strlen(s);
    if (n > 90) return 0;
    for (size_t i = 0; i < n; i++) {
        char c = s[i];
        if (!((c >= 'a' && c <= 'z') ||
              (c >= 'A' && c <= 'Z') ||
              (c >= '0' && c <= '9') ||
              c == '_' || c == '-' || c == '.')) return 0;
    }
    if (!strcmp(s, ".") || !strcmp(s, "..")) return 0;
    return 1;
}

static int filesystem_matches(const char *path, int allow_file,
                              const uint8_t requested_uuid[16]) {
    struct stat st;
    if (stat(path, &st) != 0) return 0;
    if (allow_file ? !S_ISREG(st.st_mode) : !S_ISBLK(st.st_mode)) return 0;
    int fd = open(path, O_RDONLY | O_CLOEXEC | O_NONBLOCK);
    if (fd < 0) return 0;
    unsigned char sb[SUPER_SIZE];
    ssize_t got = pread(fd, sb, sizeof(sb), SUPER_OFFSET);
    close(fd);
    if (got != sizeof(sb)) return 0;
    if (sb[EXT4_MAGIC_OFFSET] != 0x53 || sb[EXT4_MAGIC_OFFSET + 1] != 0xEF)
        return 0;
    if (memcmp(sb + EXT4_UUID_OFFSET, requested_uuid, 16) != 0)
        return 0;
    char label[17];
    memcpy(label, sb + EXT4_LABEL_OFFSET, 16);
    label[16] = '\0';
    if (strcmp(label, "SHIBA_UBUNTU") != 0) return 0;
    return 1;
}

int main(int argc, char **argv) {
    if (argc != 2 && argc != 4) {
        fprintf(stderr, "Usage: u8-rootfs-probe UUID [--image FILE]\n");
        return 2;
    }
    uint8_t expected[16];
    if (parse_uuid(argv[1], expected) != 0) {
        fputs("Invalid explicitly requested filesystem UUID\n", stderr);
        return 2;
    }
    if (argc == 4) {
        if (strcmp(argv[2], "--image") != 0 || argv[3][0] != '/') return 2;
        if (!filesystem_matches(argv[3], 1, expected)) {
            fputs("OFFLINE ext4 image UUID/label did not match\n", stderr);
            return 3;
        }
        puts(argv[3]);
        return 0;
    }

    DIR *dir = opendir("/sys/class/block");
    if (!dir) {
        fputs("Could not enumerate kernel block devices\n", stderr);
        return 3;
    }
    char matched[256] = {0};
    int matches = 0, scanned = 0;
    struct dirent *ent;
    while ((ent = readdir(dir)) != NULL) {
        if (!valid_kernel_block_name(ent->d_name)) continue;
        if (++scanned > MAX_CANDIDATES) {
            closedir(dir);
            fputs("Too many devices; refusing ambiguous scan\n", stderr);
            return 4;
        }
        char sysentry[256], path[256];
        int n = snprintf(sysentry, sizeof(sysentry),
                         "/sys/class/block/%s/dev", ent->d_name);
        if (n <= 0 || (size_t)n >= sizeof(sysentry) ||
            access(sysentry, R_OK) != 0) continue;
        n = snprintf(path, sizeof(path), "/dev/%s", ent->d_name);
        if (n <= 0 || (size_t)n >= sizeof(path)) continue;
        if (!filesystem_matches(path, 0, expected)) continue;
        matches++;
        if (matches == 1) snprintf(matched, sizeof(matched), "%s", path);
    }
    closedir(dir);
    if (matches != 1) {
        fprintf(stderr, "Expected exactly 1 matching ext4 volume, found %d\n",
                matches);
        return matches == 0 ? 3 : 4;
    }
    puts(matched);
    return 0;
}
