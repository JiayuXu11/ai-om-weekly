import argparse
import json
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description="Render AI weekly report, schema v1/v2")
    p.add_argument("input",type=Path)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    data=json.loads(a.input.read_text(encoding="utf-8-sig"))
    if data.get("schema_version")==2:
        from render_dashboard import render
    else:
        from render_legacy import render
    result=render(data)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(result,encoding="utf-8")
    print("HTML: "+str(a.output.resolve()))

if __name__=="__main__": main()
