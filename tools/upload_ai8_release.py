"""Publish the verified AI8 map to the user's configured GitHub repository."""
import hashlib,json,os,subprocess,urllib.request,urllib.parse,urllib.error
from pathlib import Path

REPO='max022204/-'
TAG='v7.3.7-ai8'
MAP=Path('output/000羈絆7.3.7_AI版_八人守城.w3x')

def main():
    manifest=json.loads(Path('output/ai8_package_manifest.json').read_text('utf-8'))
    digest=hashlib.sha256(MAP.read_bytes()).hexdigest()
    assert digest==manifest['map_sha256']
    assert manifest['jass_passed'] and manifest['policy_tests_passed']==57
    head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    remote=subprocess.check_output(['git','remote','get-url','origin'],text=True).strip()
    assert remote=='https://github.com/'+REPO+'.git'
    # Credentials remain in memory and are sent only to GitHub's own API hosts.
    env=dict(os.environ,GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never')
    proc=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',text=True,capture_output=True,env=env)
    if proc.returncode:raise RuntimeError('GitHub credential unavailable; no credential output displayed')
    credential=dict(line.split('=',1) for line in proc.stdout.splitlines() if '=' in line)
    token=credential.get('password')
    if not token:raise RuntimeError('GitHub credential has no token')
    def api(method,url,body=None,media='application/json'):
        assert urllib.parse.urlparse(url).hostname in ['api.github.com','uploads.github.com']
        headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','User-Agent':'AI8-map-publisher','X-GitHub-Api-Version':'2022-11-28'}
        if isinstance(body,dict):body=json.dumps(body,ensure_ascii=False).encode('utf-8')
        if body is not None:headers['Content-Type']=media
        if hasattr(body,'read'):headers['Content-Length']=str(MAP.stat().st_size)
        req=urllib.request.Request(url,data=body,headers=headers,method=method)
        with urllib.request.urlopen(req,timeout=300) as response:return json.load(response)
    root='https://api.github.com/repos/'+REPO
    branch=api('GET',root+'/commits/main')
    assert branch['sha']==head,'Push current source before publishing'
    try:release=api('GET',root+'/releases/tags/'+TAG)
    except urllib.error.HTTPError as error:
        if error.code!=404:raise RuntimeError('GitHub release lookup failed: '+str(error.code)) from None
        releases=api('GET',root+'/releases?per_page=100')
        release=next((r for r in releases if r['tag_name']==TAG),None)
    if release is None:
        body='八人守城 AI：兩名輔助、兩名控場、一名清場、兩名爆發與一名坦克。\n\n開局送水，基地防守優先；空檔買裝、升級合成、採集石頭、挑戰鏡像及沙灘奪寶。預設兩個真人位、八個電腦位。\n\n通過 JASS 語法、57 個離線情境及 645 項資源比對，尚未遊戲實測。\n\n地圖 SHA-256：`'+digest+'`'
        release=api('POST',root+'/releases',dict(tag_name=TAG,target_commitish=head,name='羈絆 7.3.7 AI版：八人守城',body=body,draft=True,prerelease=True))
    asset_name='000_Bonds737_AI8.w3x'
    assets=api('GET',release['assets_url'])
    asset=next((a for a in assets if a['name']==asset_name),None)
    if asset is None:
        upload=release['upload_url'].split('{')[0]+'?'+urllib.parse.urlencode({'name':asset_name,'label':MAP.name})
        print('Uploading verified map asset ('+str(MAP.stat().st_size)+' bytes)...',flush=True)
        with MAP.open('rb') as file:asset=api('POST',upload,file,'application/octet-stream')
    assert asset['size']==MAP.stat().st_size and asset['state']=='uploaded','Incomplete release asset'
    assert asset.get('digest')=='sha256:'+digest,'Remote asset digest mismatch or unavailable; release stays draft'
    if release['draft']:
        release=api('PATCH',release['url'],dict(draft=False,prerelease=True))
    result=dict(release_url=release['html_url'],download_url=asset['browser_download_url'],asset_label=MAP.name,asset_sha256=digest,commit=head,tag=TAG)
    Path('output/ai8_upload_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps(result,ensure_ascii=True,indent=2),flush=True)

if __name__=='__main__':main()
