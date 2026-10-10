/*
 * U14: QEMU-only Wayland protocol client for a real Labwc compositor.
 * Native ARM64 executable, statically linked. NOT a GUI screenshot.
 * Check a REAL wl_registry.global response, not just socket existence.
 * This program only connects to a Unix socket; no device access.
 */
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/time.h>
#include <unistd.h>

static uint32_t le32(const unsigned char *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
static void write32(unsigned char *p, uint32_t n) {
    p[0] = n & 255;
    p[1] = (n >> 8) & 255;
    p[2] = (n >> 16) & 255;
    p[3] = (n >> 24) & 255;
}
int main(int argc, char **argv) {
    if (argc != 2 || argv[1][0] != '/') {
        fprintf(stderr, "usage: u14-wayland-probe /absolute/wayland-socket\n");
        return 2;
    }
    struct sockaddr_un addr = {.sun_family = AF_UNIX};
    if (strlen(argv[1]) >= sizeof(addr.sun_path)) return 2;
    strcpy(addr.sun_path, argv[1]);
    int fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (fd < 0) { perror("socket"); return 3; }
    struct timeval t = {.tv_sec = 5, .tv_usec = 0};
    if (setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &t, sizeof(t)) != 0) {
        perror("timeout"); close(fd); return 3;
    }
    if (connect(fd, (struct sockaddr *)&addr, sizeof(addr)) != 0) {
        perror("connect"); close(fd); return 3;
    }
    /* wl_display@1.get_registry(new_id wl_registry@2), 12 bytes. */
    unsigned char message[12];
    write32(message, 1);
    write32(message + 4, (12u << 16) | 1u);
    write32(message + 8, 2);
    if (send(fd, message, sizeof(message), 0) != (ssize_t)sizeof(message)) {
        perror("send Wayland request"); close(fd); return 3;
    }
    unsigned char rx[8192];
    int saw_global = 0;
    /* Messages can arrive across partial reads; buffer and parse framing. */
    size_t used = 0;
    for (int round = 0; round < 8 && !saw_global; round++) {
        ssize_t n = recv(fd, rx + used, sizeof(rx) - used, 0);
        if (n <= 0) { perror("recv Wayland reply"); break; }
        used += (size_t)n;
        size_t pos = 0;
        while (used - pos >= 8) {
            uint32_t obj = le32(rx + pos);
            uint32_t opcode_size = le32(rx + pos + 4);
            uint32_t size = opcode_size >> 16;
            uint32_t opcode = opcode_size & 0xffff;
            if (size < 8 || size > 8192) {
                fprintf(stderr, "Invalid Wayland response frame\n");
                close(fd); return 4;
            }
            if (used - pos < size) break;
            if (obj == 2 && opcode == 0 && size >= 20) {
                /* wl_registry.global(name, interface, version) */
                saw_global = 1;
                break;
            }
            if (obj == 1 && opcode == 0) {
                fprintf(stderr, "Wayland display protocol error\n");
                close(fd); return 4;
            }
            pos += size;
        }
        if (pos) {
            memmove(rx, rx + pos, used - pos);
            used -= pos;
        }
        if (used == sizeof(rx)) break;
    }
    close(fd);
    if (!saw_global) {
        fprintf(stderr, "No wl_registry.global response, handshake failed\n");
        return 4;
    }
    puts("U14_REAL_WAYLAND_PROTOCOL_REGISTRY_OK");
    return 0;
}
