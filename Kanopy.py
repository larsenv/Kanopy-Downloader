import requests, re, os
from colorama import init as clr_init
import requests
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
    title = video["video"]["title"]

    if os.path.exists(title + ".mp4"):
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
        print("\nPSSHL: " + pssh)

    def do_decrypt(pssh, licurl):
        try:
            header = (
                'license: "https://kcms.kanopy.com/api/v1/playback/widevine_license"\nKlicenseid: "'
                + drmLicenseId
                + '"'
            )
            licenseurl = "https://kcms.kanopy.com/api/v1/playback/widevine_license"
        except:
            header = (
                'license: "https://wv-keyos.licensekeyserver.com/"\ncustomdata: "'
                + customdata
                + '"'
            )
            licenseurl = "https://wv-keyos.licensekeyserver.com/"

        json_data = {
            "license": licenseurl,
            "headers": header + '\npssh: "' + pssh + '"\nbuildInfo: ""\nproxy: ""',
            "pssh": pssh,
            "buildInfo": "",
            "proxy": "",
            "cache": False,
        }

        return requests.post("https://cdrm-project.com/wv", json=json_data).content

    def keysOnly(keys):
        return keys.split(b"</li>")[0].split(b">")[-1].decode("utf-8")

    if drm:
        KEYS = do_decrypt(pssh=pssh, licurl=licurl)

        keys_widevine = keysOnly(KEYS)

    print("Downloading...")

    subprocess.call(["yt-dlp", "--allow-unplayable-formats", MPD])
    if drm:
        subprocess.call(["mv", glob.glob("*[[]*[]].*.mp4")[0], "Input.mp4"])
        subprocess.call(["mv", glob.glob("*[[]*[]].*.m4a")[0], "Input.m4a"])
        subprocess.call(
            [
                "mp4decrypt",
                "--key",
                keys_widevine,
                "Input.mp4",
                "Output.mp4",
            ]
        )
        subprocess.call(
            [
                "mp4decrypt",
                "--key",
                keys_widevine,
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
    else:
        subprocess.call(["mv", glob.glob("*[[]*[]].mp4")[0], "Input.mp4"])
        subprocess.call(["mv", "Input.mp4", title + ".mp4"])
    if drm:
        subprocess.call(["rm", "Input.mp4"])
        subprocess.call(["rm", "Input.m4a"])
        subprocess.call(["rm", "Output.mp4"])
        subprocess.call(["rm", "Output.m4a"])
