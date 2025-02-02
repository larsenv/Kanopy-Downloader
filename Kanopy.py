import platform
import shutil
import requests, re, os
from colorama import init as clr_init
import subprocess
import Header
import os
import sys
import glob

clr_init(autoreset=True)

video_url = sys.argv[1]
Kanopy_ID = "/".join(video_url.split("/")[:7]).split("/")[-1]

params = {"domainId": Header.json_data["domainId"]}

response = requests.get(
    f"https://www.kanopy.com/kapi/videos/{Kanopy_ID}/items",
    params=params,
    cookies=Header.cookies,
    headers=Header.headers,
)

try:
    lists = response.json()["list"]

except:
    response = requests.get(
        f"https://www.kanopy.com/kapi/videos/{Kanopy_ID}",
        params=params,
        cookies=Header.cookies,
        headers=Header.headers,
    )

    lists = {"list": [{}]}

    lists["list"][0]["video"] = response.json()["video"]

    lists = lists["list"]

for video in lists:
    video_id = video["video"]["videoId"]
    title = video["video"]["title"].replace("/", " ")

    if os.path.exists("output/" + title + ".mp4"):
        continue

    Header.json_data["videoId"] = video_id

    response = requests.post(
        "https://www.kanopy.com/kapi/plays",
        cookies=Header.cookies,
        headers=Header.headers,
        json=Header.json_data,
    )

    drm = True

    try:
        MPD = response.json()["manifests"][2]["url"]
        print("\nMPD: " + MPD)
    except:
        try:
            MPD = response.json()["manifests"][1]["url"]
            print("\nMPD: " + MPD)
        except:
            MPD = "https://www.kanopy.com/kapi/manifests/hls/" + str(video_id) + ".m3u8"
            print("\nMPD: " + MPD)
            drm = False

    if drm:
        try:
            drmLicenseId = response.json()["manifests"][2]["studioDrm"]["drmLicenseId"]
            licurl = "https://kcms.kanopy.com/api/v1/playback/widevine_license"
            lic_headers = {
                "Klicenseid": drmLicenseId,
            }

        except:
            customdata = response.json()["manifests"][1]["kanopyDrm"]["authXml"]
            licurl = "https://wv-keyos.licensekeyserver.com/"
            lic_headers = {
                "customdata": customdata,
            }

        page = requests.get(MPD, headers={"User-Agent": "KAIOS/2.0"}).text
        pssh = re.findall(r"<cenc:pssh>(.*?)</cenc:pssh>", str(page))[1]
        print("\nPSSH: " + pssh)

    def do_decrypt(pssh, licurl):
        try:
            headers = {
                "license": "https://kcms.kanopy.com/api/v1/playback/widevine_license",
                "Klicenseid": drmLicenseId,
            }
            licenseurl = "https://kcms.kanopy.com/api/v1/playback/widevine_license"
        except:
            headers = {
                "license": "https://wv-keyos.licensekeyserver.com/",
                "customdata": customdata,
            }
            licenseurl = "https://wv-keyos.licensekeyserver.com/"

        json_data = {
            "pssh": pssh,
            "licurl": licenseurl,
            "headers": str(headers),
        }

        return requests.post(
            "https://cdrm-project.com/api/decrypt", json=json_data
        ).json()["message"]

    if drm:
        KEYS = do_decrypt(pssh=pssh, licurl=licurl)

    print("Downloading...")

    subprocess.call(["yt-dlp", "--allow-unplayable-formats", MPD])

    if drm:
        shutil.move(glob.glob("*.mp4")[0], "Input.mp4")
        shutil.move(glob.glob("*.m4a")[0], "Input.m4a")
        subprocess.call(
            [
                "mp4decrypt",
                "--key",
                KEYS,
                "Input.mp4",
                "Output.mp4",
            ]
        )
        subprocess.call(
            [
                "mp4decrypt",
                "--key",
                KEYS,
                "Input.m4a",
                "Output.m4a",
            ]
        )
        subprocess.call(
            [
                "ffmpeg",
                "-i",
                "Output.mp4",
                "-i",
                "Output.m4a",
                "-c",
                "copy",
                title + ".mp4",
            ]
        )

        os.remove("Input.mp4")
        os.remove("Input.m4a")
        os.remove("Output.mp4")
        os.remove("Output.m4a")

    shutil.move(glob.glob("*.mp4")[0], "output/" + title + ".mp4")
