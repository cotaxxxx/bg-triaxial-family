/* Pause the unchanged kernel at each flushed stdout stage row.
 * The inherited pipe carries only permission to continue to the next row.
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int fflush(FILE *stream) {
    int (*libc_flush)(FILE *) = dlsym(RTLD_NEXT, "fflush");
    if (!libc_flush)
        _exit(125);
    int status = libc_flush(stream);
    if (status || stream != stdout)
        return status;

    const char *descriptor = getenv("E4_STAGE_FD");
    if (!descriptor)
        _exit(125);
    char *end;
    errno = 0;
    long fd = strtol(descriptor, &end, 10);
    if (errno || end == descriptor || *end || fd < 3 || fd > INT_MAX)
        _exit(125);

    char permission;
    ssize_t size;
    do {
        size = read((int)fd, &permission, 1);
    } while (size < 0 && errno == EINTR);
    if (!size)
        _exit(0);
    if (size != 1 || permission != '+')
        _exit(125);
    return status;
}
