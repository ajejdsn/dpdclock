    
    ##################################################
    # DPDCLOCK V1.0     github.com/ajejdsn/dpd-201   #
    # rawrr~~ >v<                                    #
    #                                                #
    ##################################################


import asyncio
import time
import psutil
import serial
import winrt.windows.media.control as wmc

PORT = "COM5"
BAUD_RATE = 9600

cmd_sot = b"\x02"
cmd_eot = b"\x03"

map_vis = {
    'А': 'A', 'а': 'a', 'В': 'B', 'Е': 'E', 'е': 'e', 'К': 'K', 'к': 'k',
    'М': 'M', 'Н': 'H', 'О': 'O', 'о': 'o', 'Р': 'P', 'р': 'p', 'С': 'C',
    'с': 'c', 'Т': 'T', 'У': 'Y', 'у': 'y', 'Х': 'X', 'х': 'x'
}

map_tr = {
    'Б': 'B', 'б': 'b', 'В': 'B', 'в': 'v', 'т': 't', 'т': 't', 'Г': 'G', 'Н': 'H', 'н': 'n', 'г': 'g', 'Д': 'D', 'д': 'd', 'Ё': 'Yo', 'ё': 'yo',
    'Ж': 'Zh', 'ж': 'zh', 'З': 'Z', 'з': 'z', 'И': 'I', 'и': 'i', 'Й': 'Y', 'й': 'y',
    'Л': 'L', 'л': 'l', 'П': 'P', 'п': 'p', 'Ф': 'F', 'ф': 'f', 'Ц': 'Ts', 'ц': 'ts',
    'Ч': 'Ch', 'ч': 'ch', 'Ш': 'Sh', 'ш': 'sh', 'Щ': 'Sch', 'щ': 'sch', 'Ъ': '', 'ъ': '',
    'Ы': 'Y', 'ы': 'y', 'Ь': '', 'ь': '', 'Э': 'E', 'э': 'e', 'Ю': 'Yu', 'ю': 'yu',
    'Я': 'Ya', 'я': 'ya'
}


l_title = ""
l_rawp = 0.0
l_updt = 0.0

def d_transl(text: str) -> str:
    result = []
    for char in text:
        if char in map_vis:
            result.append(map_vis[char])
        elif char in map_tr:
            result.append(map_tr[char])
        else:
            code = ord(char)
            result.append(char if 32 <= code <= 255 else '?')
    return "".join(result)

def d_timeto12(seconds: float) -> str:
    if not seconds or seconds < 0:
        return "00:00"
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"

async def d_getmus():
    global l_title, l_rawp, l_updt
    try:
        manager = await wmc.GlobalSystemMediaTransportControlsSessionManager.request_async()
        session = manager.get_current_session()
        if session:
            info = await session.try_get_media_properties_async()
            timeline = session.get_timeline_properties()
            playback = session.get_playback_info()
            status = playback.playback_status if playback else None
            isply = (status == wmc.GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING)
            ispaus = (status == wmc.GlobalSystemMediaTransportControlsSessionPlaybackStatus.PAUSED)
            currtitle = info.title or "Unknown"
            raw_pos = 0.0
            end = 0.0
            if timeline:
                if hasattr(timeline.position, 'total_seconds'):
                    raw_pos = timeline.position.total_seconds()
                if hasattr(timeline.end_time, 'total_seconds'):
                    end = timeline.end_time.total_seconds()
            now = time.time()
            if currtitle != l_title or abs(raw_pos - l_rawp) > 1.5:
                l_title = currtitle
                l_rawp = raw_pos
                l_updt = now
                    # is this thing works? i guess. but please, if it's not its not reason to fuck me >.<
            if isply:
                live_pos = l_rawp + (now - l_updt)
            else:
                live_pos = raw_pos
                l_rawp = raw_pos
                l_updt = now
            if end > 0 and live_pos > end:
                live_pos = end

            return { # used ai here, pls dont touch me -.-
                "artist": info.artist or "Unknown",
                "title": currtitle,
                "isply": isply,
                "ispaus": ispaus,
                "position": live_pos,
                "duration": end,
            }
    except Exception:
        pass
    return None

c_lsp = ""

def t_sendf(ser, line1: str, line2: str):
    global c_lsp
    
    l1 = line1.ljust(20)[:20]
    l2 = line2.ljust(20)[:20]
    full_text = l1 + l2

    if full_text == c_lsp:
        return

    c_lsp = full_text

    rawbyte = full_text.encode("cp1251", errors="replace")
    b_clean = bytes([b if 32 <= b <= 255 else 63 for b in rawbyte])

    packet = cmd_sot + b_clean + cmd_eot
    ser.write(packet)

async def main():
    try:
        ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        print(f"DPDCLOCK")
        print(f"VER:1.0") # not the 1.0
        print(f"[+] Started on: {PORT}")

        scroll_pos = 0

        while True:
            media = await d_getmus()

            if media and (media["isply"] or media["ispaus"]):
                artist = d_transl(media["artist"])
                title = d_transl(media["title"])
                tr_str = f"{artist} - {title}"

                if len(tr_str) > 20:
                    padded_str = tr_str + "   "
                    line1 = (padded_str + padded_str)[scroll_pos : scroll_pos + 20]
                    if media["isply"]:
                        scroll_pos = (scroll_pos + 1) % len(padded_str)
                else:
                    line1 = tr_str
                    scroll_pos = 0

                status_part = "PLAY" if media["isply"] else "PAUS"

                pos_str = d_timeto12(media["position"])
                dur_str = d_timeto12(media["duration"])
                left_part = f"{pos_str}/{dur_str}"

                spaces = 20 - len(left_part) - len(status_part)
                line2 = left_part + (" " * spaces) + status_part

                t_sendf(ser, line1, line2)
                await asyncio.sleep(0.4)

            else:
                scroll_pos = 0

                line1 = time.strftime("%Y %b %d | %I:%M%p").upper()
                
                cpu_usage = int(psutil.cpu_percent(interval=None))
                cpu_str = f"CPU:{cpu_usage}%"
                day_str = time.strftime("%a").upper()
                
                spaces = 20 - len(cpu_str) - len(day_str)
                line2 = cpu_str + (" " * spaces) + day_str

                t_sendf(ser, line1, line2)
                await asyncio.sleep(0.5)

    except serial.SerialException as e:
        print(f"[-] Error!\nVerbose: {e}")
    except KeyboardInterrupt:
        print("\nBye-bye...")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    asyncio.run(main())
    
