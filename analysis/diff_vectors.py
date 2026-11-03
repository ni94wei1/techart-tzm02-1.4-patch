import collections
import struct

BASE = 0x5000
CORE = ["SP", "Reset", "NMI", "HardFault", "r4", "r5", "r6", "r7", "r8", "r9", "r10",
        "SVC", "r12", "r13", "PendSV", "SysTick"]
SAMD21_IRQ = ["PM", "SYSCTRL", "WDT", "RTC", "EIC", "NVMCTRL", "DMAC", "USB", "EVSYS",
              "SERCOM0", "SERCOM1", "SERCOM2", "SERCOM3", "SERCOM4", "SERCOM5",
              "TCC0", "TCC1", "TCC2", "TC3", "TC4", "TC5", "TC6", "TC7",
              "ADC", "AC", "DAC", "PTC", "I2S"]
NAMES = CORE + SAMD21_IRQ


def vectors(v):
    d = open(f"../TZM-02-VER-{v}.bin", "rb").read()
    vec = [struct.unpack_from("<I", d, 4 * i)[0] for i in range(len(NAMES))]
    default = collections.Counter(x for x in vec[2:] if x).most_common(1)[0][0]
    return vec, default


a, da = vectors("1-3-0")
b, db = vectors("1-4-0")
print(f"{'vector':10s} {'1.3.0':>12s} {'1.4.0':>12s}")
for i, name in enumerate(NAMES[2:], start=2):
    sa = "-" if a[i] == 0 else ("default" if a[i] == da else f"0x{a[i]:x}")
    sb = "-" if b[i] == 0 else ("default" if b[i] == db else f"0x{b[i]:x}")
    mark = "   <== differs" if (sa == "default") != (sb == "default") else ""
    if sa != "default" or sb != "default":
        print(f"{name:10s} {sa:>12s} {sb:>12s}{mark}")
