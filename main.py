from __future__ import annotations
from winreg import ConnectRegistry, HKEY_USERS, OpenKey, KEY_ALL_ACCESS, SetValueEx, REG_SZ, HKEY_LOCAL_MACHINE
from winreg import QueryInfoKey, QueryValueEx, EnumKey
from wmi import WMI
import pythoncom
from time import sleep
from os import path
from shutil import copy


def get_username(pc_: str) -> str | None:
    try:
        pythoncom.CoInitialize()
        conc = WMI(computer=pc_)
        rec = conc.query("SELECT * FROM Win32_ComputerSystem")
        for user_ in rec:
            try:
                user_ = user_.UserName.split("\\")[1]
                return user_
            except AttributeError:
                pass
        try:
            processes = conc.query("SELECT * FROM Win32_Process WHERE Name='explorer.exe'")
            for process in processes:
                _, _, user_ = process.GetOwner()
                return user_
        except Exception as e:
            print(e)
    except Exception as e:
        print(e)


while True:
    pc = input("Enter PC name: ")
    try:
        pt = input("Enter path to image: ").replace('"', "")
        ct = pt.split("\\")[-1]
    except:
        print("invalid path")
        continue
    pt = pt.replace('"', '')
    if not path.exists(fr"\\{pc}\c$"):
        print("Computer does not exist or it is offline")
        continue
    if not path.isfile(pt):
        print("Could not locate the image")
        continue
    user = get_username(pc)
    sleep(0.3)
    if not user:
        print("No current user was found")
        continue
    copy(pt, f"\\\\{pc}\\c$\\{ct}")
    try:
        with ConnectRegistry(pc, HKEY_USERS) as reg:
            users_dict = {}
            sid_list = []
            with OpenKey(reg, "") as users:
                users_len = QueryInfoKey(users)[0]
                for i in range(users_len):
                    try:
                        sid_list.append(EnumKey(users, i))
                    except FileNotFoundError:
                        pass

            with ConnectRegistry(pc, HKEY_LOCAL_MACHINE) as users_path:
                for sid in set(sid_list):
                    try:
                        with OpenKey(users_path,
                                     fr"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\{sid}") as profiles:
                            username = QueryValueEx(profiles, "ProfileImagePath")
                            if username[0].startswith("C:\\"):
                                username = username[0].split("\\")[-1]
                                if user == username:
                                    sid_ = sid
                                    break
                    except:
                        pass
                else:
                    print("Could not locate the current user")
    except:
        print("Could not connect to remote registry")
        continue
    try:
        with ConnectRegistry(pc, HKEY_USERS) as reg:
            try:
                with OpenKey(reg, fr"{sid_}\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", 0,
                             KEY_ALL_ACCESS) as key:
                    SetValueEx(key, "Wallpaper", 0, REG_SZ, f"c:\\{ct}")
                    SetValueEx(key, "WallpaperStyle", 0, REG_SZ, "3")
            except ValueError:
                pass
    except Exception as e:
        print("Could not connect to remote computer's registry \nmaybe theres no active user?")
        print("error -", e)
        continue
    con = WMI(computer=pc)
    procs = con.Win32_Process(name="explorer.exe")
    for proc in procs:
        proc.Terminate()
    sleep(0.6)
    con.Win32_Process.Create(CommandLine="explorer.exe")
    print("Changed background image successfully")
