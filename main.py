# -*- coding: utf-8 -*-
"""
PC DIAGNOSTIC TOOL - Python Edition
Chay tren Windows 10/11, can quyen Administrator.
"""

import os
import sys
import time
import ctypes
import platform
import subprocess
import webbrowser
from datetime import datetime

try:
    import wmi
    import pythoncom
    import psutil
    import cpuinfo
except ImportError as e:
    print(f"[LOI] Thieu thu vien: {e}")
    print("Chay: pip install -r requirements.txt")
    sys.exit(1)

# ============================================================
# KIEM TRA QUYEN ADMIN
# ============================================================
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def require_admin():
    if not is_admin():
        print("=" * 60)
        print("[LOI] Hay chay bang quyen Administrator!")
        print("Chuot phai file .exe -> Run as administrator")
        print("=" * 60)
        input("Nhan Enter de thoat...")
        sys.exit(1)


# ============================================================
# TIEN ICH
# ============================================================
def clear():
    os.system("cls" if os.name == "nt" else "clear")


def pause():
    input("\nNhan Enter de quay ve menu...")


def line(char="=", n=64):
    print(char * n)


def header(title):
    clear()
    line()
    print(f"  {title}")
    line()


def run(cmd):
    """Chay lenh shell, tra ve output."""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           timeout=60, encoding="utf-8", errors="ignore")
        return r.stdout.strip()
    except Exception as e:
        return f"[LOI] {e}"


# ============================================================
# 1. DOC CAU HINH + CANH BAO
# ============================================================
def read_config():
    header("DOC CAU HINH PHAN CUNG")
    pythoncom.CoInitialize()
    c = wmi.WMI()

    # CPU
    print("\n[CPU]")
    for cpu in c.Win32_Processor():
        print(f"  Ten          : {cpu.Name.strip()}")
        print(f"  So nhan      : {cpu.NumberOfCores}")
        print(f"  So luong     : {cpu.NumberOfLogicalProcessors}")
        print(f"  Xung toi da  : {cpu.MaxClockSpeed} MHz")

    # RAM + SERIAL
    print("\n[RAM - TUNG THANH]")
    ram_list = list(c.Win32_PhysicalMemory())
    total_gb = 0
    for i, ram in enumerate(ram_list, 1):
        cap_gb = int(ram.Capacity) // (1024 ** 3)
        total_gb += cap_gb
        print(f"  Thanh {i}:")
        print(f"    Vi tri       : {ram.DeviceLocator or 'N/A'}")
        print(f"    Bank         : {ram.BankLabel or 'N/A'}")
        print(f"    Dung luong   : {cap_gb} GB")
        print(f"    Toc do       : {ram.Speed} MHz")
        print(f"    Hang         : {ram.Manufacturer or 'N/A'}")
        print(f"    Part number  : {ram.PartNumber.strip() if ram.PartNumber else 'N/A'}")
        print(f"    SERIAL       : {ram.SerialNumber or '(BIOS khong ghi)'}")

    print(f"\n  => Tong RAM  : {total_gb} GB / {len(ram_list)} thanh")

    # Canh bao RAM
    warnings = []
    for ram in ram_list:
        sn = (ram.SerialNumber or "").strip()
        if not sn or sn.lower() in ("serialnumber", "0", "00000000"):
            warnings.append(f"  ! {ram.DeviceLocator}: khong doc duoc Serial -> dung CPU-Z/RAMMon")
    if len(ram_list) >= 2:
        sns = [(r.SerialNumber or "").strip() for r in ram_list]
        if len(set(sns)) < len(sns) and "" not in sns:
            warnings.append("  ! Nhieu thanh RAM trung Serial -> nghi van trao RAM")

    # GPU
    print("\n[GPU]")
    gpu_info = []
    for gpu in c.Win32_VideoController():
        print(f"  Ten          : {gpu.Name}")
        print(f"  Driver       : {gpu.DriverVersion}")
        print(f"  Do phan giai : {gpu.CurrentHorizontalResolution}x{gpu.CurrentVerticalResolution} @ {gpu.CurrentRefreshRate}Hz")
        gpu_info.append(gpu.Name)

    # Mainboard
    print("\n[MAINBOARD]")
    for mb in c.Win32_BaseBoard():
        print(f"  Hang         : {mb.Manufacturer}")
        print(f"  Model        : {mb.Product}")
        print(f"  SERIAL       : {mb.SerialNumber}")

    # BIOS
    print("\n[BIOS]")
    for b in c.Win32_BIOS():
        print(f"  Hang         : {b.Manufacturer}")
        print(f"  Phien ban    : {b.SMBIOSBIOSVersion}")
        print(f"  Serial       : {b.SerialNumber}")
        if b.ReleaseDate:
            # ReleaseDate format: YYYYMMDDHHMMSS.000000+000
            try:
                dt = datetime.strptime(str(b.ReleaseDate)[:8], "%Y%m%d")
                print(f"  Ngay phat hanh: {dt.strftime('%d/%m/%Y')}")
            except Exception:
                print(f"  ReleaseDate  : {b.ReleaseDate}")

    # Canh bao BIOS cu
    for b in c.Win32_BIOS():
        if b.ReleaseDate:
            try:
                dt = datetime.strptime(str(b.ReleaseDate)[:8], "%Y%m%d")
                age_days = (datetime.now() - dt).days
                if age_days > 365 * 4:
                    warnings.append(f"  ! BIOS da {age_days//365} nam tuoi -> nen kiem tra update")
            except Exception:
                pass

    # In canh bao
    if warnings:
        print("\n" + "-" * 60)
        print("CANH BAO:")
        for w in warnings:
            print(w)

    print("\n" + "-" * 60)
    print("GOI Y:")
    print("  - RAM 2133/2400MHz du mua 3200/3600 -> CHUA BAT XMP trong BIOS")
    print("  - GPU RTX 4060/4060Ti: PCIe x8 la BINH THUONG")
    print("  - Mo GPU-Z -> dau ? canh Bus Interface -> Render Test kiem tra PCIe")
    print("  - Doi chieu SerialNumber RAM/Main/GPU voi hoa don de phat hien trao do")
    pause()


# ============================================================
# 2. KIEM TRA MANG
# ============================================================
def check_network():
    header("KIEM TRA MANG & BOOTROM")
    pythoncom.CoInitialize()
    c = wmi.WMI()

    print("\n[TOC DO CONG LAN]")
    for nic in c.Win32_NetworkAdapter(NetEnabled=True):
        if nic.Speed:
            mbps = int(nic.Speed) // 1_000_000
            status = "OK" if mbps >= 1000 else "!! CHI 100Mbps - kiem tra cap!"
            print(f"  {nic.Name}")
            print(f"    MAC   : {nic.MACAddress}")
            print(f"    Speed : {mbps} Mbps  [{status}]")

    print("\n[IP / GATEWAY]")
    out = run('ipconfig | findstr /i "IPv4 Gateway"')
    print(out if out else "  (khong co)")

    # Ping gateway
    gw = input("\nNhap Gateway de ping (Enter bo qua): ").strip()
    if gw:
        print(f"\n[PING GATEWAY {gw} - 20 goi]")
        print(run(f"ping -n 20 {gw}"))

    print("\n[PING 8.8.8.8 - 20 goi]")
    out = run("ping -n 20 8.8.8.8")
    print(out)

    # Phan tich
    try:
        if "0% loss" not in out and "0% " not in out:
            print("\n!! CO ROT GOI -> kiem tra cap mang / router")
    except Exception:
        pass

    pause()


# ============================================================
# 3. KIEM TRA MAN HINH
# ============================================================
def check_monitor():
    header("KIEM TRA MAN HINH")

    print("\n[TAN SO QUET HIEN TAI]")
    pythoncom.CoInitialize()
    c = wmi.WMI()
    for vc in c.Win32_VideoController():
        print(f"  {vc.Name}: {vc.CurrentHorizontalResolution}x{vc.CurrentVerticalResolution} @ {vc.CurrentRefreshRate}Hz")

    print("\n[MO TRINH TEST DIEM CHET]")
    html = """
    <html><head><title>Dead Pixel Test</title></head>
    <body onclick="c()" style="margin:0;cursor:pointer;background:red">
    <script>
    var cs=['red','lime','blue','white','black','#808080','#00FFFF','#FF00FF'],i=0;
    function c(){i=(i+1)%cs.length;document.body.style.background=cs[i];}
    </script>
    <h1 style="text-align:center;font-family:Arial;color:white;mix-blend-mode:difference">
    Click de chuyen mau - Alt+F4 de thoat</h1>
    </body></html>
    """
    path = os.path.join(os.environ["TEMP"], "deadpixel.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    os.startfile(path)
    print(f"  Da mo: {path}")
    print("  Click chuot de chuyen mau, quan sat diem chet.")
    print("  ESC hoac Alt+F4 de thoat.")

    print("\n[GOI Y]")
    print("  - 144Hz/165Hz/240Hz neu chi nhan 60Hz: kiem tra cap + Settings > Display")
    print("  - HDMI 1.4 gioi han 1080p@120Hz, can DisplayPort")
    pause()


# ============================================================
# 4. KIEM TRA PHIM - CHUOT - TAI NGHE
# ============================================================
def check_peripheral():
    while True:
        header("KIEM TRA PHIM - CHUOT - TAI NGHE")
        print("  1. Test ban phim (phim liet/ket)")
        print("  2. Test double-click chuot")
        print("  3. Test tai nghe + mic")
        print("  0. Quay lai")
        ch = input("\nChon: ").strip()

        if ch == "1":
            test_keyboard()
        elif ch == "2":
            webbrowser.open("https://www.mouse-sensitivity.com/double-click-test/")
            print("\nDa mo trang test double-click. Click 1 lan, xem co nhay 2 khong.")
            pause()
        elif ch == "3":
            os.system("start ms-settings:sound")
            print("\nDa mo Settings > Sound.")
            print("  - Output > Test Left/Right de nghe 2 ben tai nghe")
            print("  - Input > Test mic de kiem tra micro")
            pause()
        elif ch == "0":
            return


def test_keyboard():
    header("TEST BAN PHIM - Nhan ESC de thoat")
    try:
        import msvcrt
        print("Nhan phim bat ky de kiem tra...\n")
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b'\x1b':  # ESC
                    break
                if key in (b'\x00', b'\xe0'):  # phim dac biet
                    key = msvcrt.getch()
                    print(f"  [Special] code=0x{key.hex()}")
                else:
                    try:
                        print(f"  Phim: '{key.decode('utf-8', errors='ignore')}' (0x{key.hex()})")
                    except Exception:
                        print(f"  Phim raw: 0x{key.hex()}")
    except Exception as e:
        print(f"[LOI] {e}")
    pause()


# ============================================================
# 5. STRESS TEST
# ============================================================
def stress_test():
    while True:
        header("STRESS TEST & NHIET DO")
        print("  1. Test RAM (Windows Memory Diagnostic - khoi dong lai)")
        print("  2. Test CPU (Prime95)")
        print("  3. Test GPU (FurMark)")
        print("  4. Test nguon + CPU+GPU (OCCT Power Supply)")
        print("  5. Xem nhiet do (HWiNFO)")
        print("  6. Mo Task Manager")
        print("  7. Tai cong cu (mo trang download)")
        print("  0. Quay lai")
        print("\n  LUU Y: Nguon KHONG test duoc bang phan mem.")
        print("         OCCT chi ep tai, neu TUT/REBOOT -> nghi nguon.")
        print("         Test that: dong ho van nang do 12V/5V/3.3V.")
        ch = input("\nChon: ").strip()

        tools_dir = os.path.join(os.path.dirname(sys.argv[0]), "tools")
        prime = os.path.join(tools_dir, "Prime95", "prime95.exe")
        furmark = os.path.join(tools_dir, "FurMark", "FurMark.exe")
        hwinfo = os.path.join(tools_dir, "HWiNFO", "HWiNFO64.exe")
        occt = os.path.join(tools_dir, "OCCT", "OCCT.exe")

        if ch == "1":
            os.system("mdsched.exe")
            pause()
        elif ch == "2":
            if os.path.exists(prime):
                subprocess.Popen([prime])
                print("Da mo Prime95 -> chon Torture Test -> Small FFTs -> 15-30 phut")
            else:
                print(f"Chua co Prime95 tai {prime}")
                print("Chon muc 7 de tai hoac tu tai mersenne.org")
            pause()
        elif ch == "3":
            if os.path.exists(furmark):
                subprocess.Popen([furmark])
                print("Da mo FurMark -> Burn-in test 15 phut")
            else:
                print(f"Chua co FurMark tai {furmark}")
            pause()
        elif ch == "4":
            if os.path.exists(occt):
                subprocess.Popen([occt])
                print("Da mo OCCT -> chon Power Supply test")
            else:
                print(f"Chua co OCCT tai {occt}")
            pause()
        elif ch == "5":
            if os.path.exists(hwinfo):
                subprocess.Popen([hwinfo])
            else:
                print(f"Chua co HWiNFO tai {hwinfo}")
            pause()
        elif ch == "6":
            os.system("start taskmgr")
            pause()
        elif ch == "7":
            download_tools()
        elif ch == "0":
            return


def download_tools():
    header("TAI CONG CU STRESS TEST")
    print("  1. Prime95  - https://www.mersenne.org/download/")
    print("  2. FurMark  - https://geeks3d.com/furmark/")
    print("  3. HWiNFO   - https://www.hwinfo.com/download/")
    print("  4. OCCT     - https://www.ocbase.com/download")
    print("\n  -> Tai file .zip, giai nen vao thu muc tools/ cua tool nay")
    ch = input("Mo trang nao? (1-4, Enter bo qua): ").strip()
    urls = {
        "1": "https://www.mersenne.org/download/",
        "2": "https://geeks3d.com/furmark/",
        "3": "https://www.hwinfo.com/download/",
        "4": "https://www.ocbase.com/download",
    }
    if ch in urls:
        webbrowser.open(urls[ch])
    pause()


# ============================================================
# 6. QUICK FIX
# ============================================================
def quick_fix():
    while True:
        header("QUICK FIX")
        print("  1. Reset driver man hinh (Win+Ctrl+Shift+B - phai nhan tay)")
        print("  2. Xoa temp/cache")
        print("  3. Sua mang (flushdns + winsock + ip reset)")
        print("  4. Dong bo gio")
        print("  5. Lam tat ca")
        print("  0. Quay lai")
        ch = input("\nChon: ").strip()

        if ch in ("1", "5"):
            print("\nReset driver: nhan tay Win+Ctrl+Shift+B (khong the gia lap chinh xac)")
        if ch in ("2", "5"):
            print("\nXoa temp...")
            os.system('del /q /f /s "%TEMP%\\*" >nul 2>&1')
            os.system('del /q /f /s "C:\\Windows\\Temp\\*" >nul 2>&1')
            print("  Xong.")
        if ch in ("3", "5"):
            print("\nSua mang...")
            os.system("ipconfig /flushdns")
            os.system("netsh winsock reset")
            os.system("netsh int ip reset")
            print("  Xong. Nen khoi dong lai.")
        if ch in ("4", "5"):
            print("\nDong bo gio...")
            os.system("net start w32time >nul 2>&1")
            os.system("w32tm /resync /force")
        if ch == "0":
            return
        pause()


# ============================================================
# 7. XUAT BAO CAO
# ============================================================
def export_report():
    header("XUAT BAO CAO")
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(desktop, f"PC_Report_{ts}.txt")

    pythoncom.CoInitialize()
    c = wmi.WMI()

    lines = []
    lines.append("=" * 60)
    lines.append("BAO CAO CAU HINH")
    lines.append(f"Thoi gian: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    lines.append(f"May: {platform.node()} - User: {os.getlogin() if hasattr(os, 'getlogin') else 'N/A'}")
    lines.append("=" * 60)
    lines.append("")

    lines.append("--- CPU ---")
    for cpu in c.Win32_Processor():
        lines.append(f"  Ten         : {cpu.Name.strip()}")
        lines.append(f"  Nhan/Luong  : {cpu.NumberOfCores}/{cpu.NumberOfLogicalProcessors}")
        lines.append(f"  Xung max    : {cpu.MaxClockSpeed} MHz")

    lines.append("\n--- RAM ---")
    for i, ram in enumerate(c.Win32_PhysicalMemory(), 1):
        lines.append(f"  Thanh {i}: {ram.DeviceLocator}")
        lines.append(f"    Dung luong: {int(ram.Capacity)//(1024**3)} GB")
        lines.append(f"    Toc do    : {ram.Speed} MHz")
        lines.append(f"    Hang      : {ram.Manufacturer}")
        lines.append(f"    Part      : {ram.PartNumber}")
        lines.append(f"    SERIAL    : {ram.SerialNumber}")

    lines.append("\n--- GPU ---")
    for gpu in c.Win32_VideoController():
        lines.append(f"  {gpu.Name} | Driver {gpu.DriverVersion}")

    lines.append("\n--- MAINBOARD ---")
    for mb in c.Win32_BaseBoard():
        lines.append(f"  {mb.Manufacturer} {mb.Product} | Serial: {mb.SerialNumber}")

    lines.append("\n--- BIOS ---")
    for b in c.Win32_BIOS():
        rdate = str(b.ReleaseDate)[:8] if b.ReleaseDate else "N/A"
        lines.append(f"  {b.Manufacturer} {b.SMBIOSBIOSVersion}")
        lines.append(f"  ReleaseDate: {rdate}")
        lines.append(f"  Serial     : {b.SerialNumber}")

    lines.append("\n--- MANG ---")
    for nic in c.Win32_NetworkAdapter(NetEnabled=True):
        if nic.Speed:
            lines.append(f"  {nic.Name} | MAC {nic.MACAddress} | {int(nic.Speed)//1_000_000} Mbps")

    lines.append("\n--- IP CONFIG ---")
    lines.append(run("ipconfig /all"))

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\nDa luu: {path}")
    os.startfile(path)
    pause()


# ============================================================
# MAIN MENU
# ============================================================
def main_menu():
    while True:
        clear()
        line()
        print("         PC DIAGNOSTIC TOOL - PYTHON EDITION")
        line()
        print("  1. Doc cau hinh & canh bao linh kien")
        print("  2. Kiem tra mang & bootrom")
        print("  3. Kiem tra man hinh")
        print("  4. Kiem tra phim - chuot - tai nghe")
        print("  5. Stress test & nhiet do")
        print("  6. Quick fix")
        print("  7. Xuat bao cao")
        print("  0. Thoat")
        line()
        ch = input("Chon [0-7]: ").strip()

        try:
            if ch == "1": read_config()
            elif ch == "2": check_network()
            elif ch == "3": check_monitor()
            elif ch == "4": check_peripheral()
            elif ch == "5": stress_test()
            elif ch == "6": quick_fix()
            elif ch == "7": export_report()
            elif ch == "0":
                print("Tam biet!")
                return
        except Exception as e:
            print(f"\n[LOI] {e}")
            import traceback
            traceback.print_exc()
            pause()


if __name__ == "__main__":
    require_admin()
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nDa huy.")