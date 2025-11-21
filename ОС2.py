import os
import ctypes
import pwd
import socket

#структуру для хранения информации о ядре linux
class Utsname(ctypes.Structure):
    _fields_ = [
        ("sysname", ctypes.c_char * 65),
        ("nodename", ctypes.c_char * 65),
        ("release", ctypes.c_char * 65),
        ("version", ctypes.c_char * 65),
        ("machine", ctypes.c_char * 65),
    ]

#информацию о системе
def poluchit_uname():
    libc = ctypes.CDLL("libc.so.6")
    uname_info = Utsname()
    libc.uname(ctypes.byref(uname_info))
    return (
        uname_info.sysname.decode(),
        uname_info.nodename.decode(),
        uname_info.release.decode(),
        uname_info.version.decode(),
        uname_info.machine.decode()
    )

#читаем файл /etc/os-release для получения названия дистрибутива
def poluchit_distro():
    try:
        with open("/etc/os-release") as f:
            dannye = f.read().split("\n")
        znacheniya = {}
        for stroka in dannye:
            if "=" in stroka:
                k, v = stroka.split("=", 1)
                znacheniya[k] = v.strip('"')
        return znacheniya.get("PRETTY_NAME", "unknown linux")
    except:
        return "unknown linux"

#определяем структуру sysinfo() для получения информации о памяти swap и процессах
class Sysinfo(ctypes.Structure):
    _fields_ = [
        ("uptime", ctypes.c_long),
        ("loads", ctypes.c_ulong * 3),
        ("totalram", ctypes.c_ulong),
        ("freeram", ctypes.c_ulong),
        ("sharedram", ctypes.c_ulong),
        ("bufferram", ctypes.c_ulong),
        ("totalswap", ctypes.c_ulong),
        ("freeswap", ctypes.c_ulong),
        ("procs", ctypes.c_ushort),
        ("pad", ctypes.c_ushort),
        ("totalhigh", ctypes.c_ulong),
        ("freehigh", ctypes.c_ulong),
        ("mem_unit", ctypes.c_uint)
    ]

#получаем системную информацию через sysinfo()
def poluchit_sysinfo():
    libc = ctypes.CDLL("libc.so.6")
    sys_info = Sysinfo()
    if libc.sysinfo(ctypes.byref(sys_info)) != 0:
        raise RuntimeError("sysinfo() failed")
    return sys_info

#читаем /proc/meminfo для получения виртуальной памяти и другой информации
def parse_meminfo():
    meminfo = {}
    with open("/proc/meminfo") as f:
        for stroka in f:
            key, val = stroka.split(":")
            meminfo[key] = int(val.strip().split()[0])
    return meminfo

#получаем количество логических процессоров через get_nprocs()
def poluchit_nprocs():
    libc = ctypes.CDLL("libc.so.6")
    libc.get_nprocs.restype = ctypes.c_int
    return libc.get_nprocs()

#читаем /proc/loadavg для получения загрузки процессора
def poluchit_loadavg():
    with open("/proc/loadavg") as f:
        return f.read().split()[:3]

#читаем /proc/mounts для получения списка подключенных логических дисков
def poluchit_mounts():
    mounts = []
    with open("/proc/mounts") as f:
        for stroka in f:
            parts = stroka.split()
            if len(parts) >= 3:
                device, mountpoint, fstype = parts[:3]
                mounts.append((device, mountpoint, fstype))
    return mounts

#получаем статистику диска через statvfs()
def poluchit_disk_space(punkt_montazha):
    st = os.statvfs(punkt_montazha)
    svobodnoe = st.f_bavail * st.f_frsize
    obshchee = st.f_blocks * st.f_frsize
    return svobodnoe, obshchee

#имя текущего пользователя
def poluchit_user():
    return pwd.getpwuid(os.getuid()).pw_name

#hostname
def poluchit_hostname():
    return socket.gethostname()


def main():
    sysname, nodename, release, version, arhitektura = poluchit_uname()
    distro = poluchit_distro()
    print(f"OS: {distro}")
    print(f"Kernel: {sysname} {release}")
    print(f"Architecture: {arhitektura}")
    print(f"Hostname: {poluchit_hostname()}")
    print(f"User: {poluchit_user()}")

    sys_info = poluchit_sysinfo()
    obshaya_ram = sys_info.totalram * sys_info.mem_unit // 1024 // 1024
    svobodnaya_ram = sys_info.freeram * sys_info.mem_unit // 1024 // 1024
    obshiy_swap = sys_info.totalswap * sys_info.mem_unit // 1024 // 1024
    svobodny_swap = sys_info.freeswap * sys_info.mem_unit // 1024 // 1024
    print(f"RAM: {svobodnaya_ram}MB free / {obshaya_ram}MB total")
    print(f"Swap: {obshiy_swap}MB total / {svobodny_swap}MB free")

    meminfo = parse_meminfo()
    virtual_mem = meminfo.get("VmallocTotal", 0) // 1024
    print(f"Virtual memory: {virtual_mem} MB")

    print(f"Processors: {poluchit_nprocs()}")
    load1, load5, load15 = poluchit_loadavg()
    print(f"Load average: {load1}, {load5}, {load15}")

    print("Drives:")
    for device, mountpoint, fstype in poluchit_mounts():
        try:
            svobodnoe, obshchee = poluchit_disk_space(mountpoint)
            svobodnoe_gb = svobodnoe // 1024 // 1024 // 1024
            obshchee_gb = obshchee // 1024 // 1024 // 1024
            print(f"  {mountpoint:10} {fstype:6} {svobodnoe_gb}GB free / {obshchee_gb}GB total")
        except PermissionError:
            pass

if __name__ == "__main__":
    main()