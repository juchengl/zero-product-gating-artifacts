import json
d = json.load(open(r"C:\Users\Administrator\volare_releases.json", encoding="utf-8"))
for rel in d:
    tag = rel["tag_name"]
    for a in rel.get("assets", []):
        if "sky130" in a["name"].lower():
            print(tag, a["name"], round(a["size"]/1e6, 1), "MB")
            print("  ", a["browser_download_url"])