from selenium import webdriver
import requests
import re
import time
import json
import config

#第一步用selenium获得code
browser = webdriver.Chrome()
browser.implicitly_wait(10)
browser.get("https://login.live.com/oauth20_authorize.srf?client_id=00000000402b5328&response_type=code&scope=service%3A%3Auser.auth.xboxlive.com%3A%3AMBI_SSL&redirect_uri=https%3A%2F%2Flogin.live.com%2Foauth20_desktop.srf")
browser.find_element_by_id("i0116").send_keys(config.username)
browser.find_element_by_id("idSIButton9").click()
time.sleep(2)
browser.find_element_by_id("i0118").send_keys(config.password)
browser.find_element_by_id("idSIButton9").click()
code = browser.current_url[48:93]
browser.close()

# 第二步获取access_token
data={
    "client_id":"00000000402b5328",
    "code":code,
    "grant_type": "authorization_code",
    "redirect_uri": "https://login.live.com/oauth20_desktop.srf",
    "scope":"service::user.auth.xboxlive.com::MBI_SSL"
}

access_token = json.loads(requests.post("https://login.live.com/oauth20_token.srf",data).text.replace("'",'"'))['access_token']


#第三步获取xbl令牌

data="""{{
    "Properties": {{
        "AuthMethod": "RPS",
        "SiteName": "user.auth.xboxlive.com",
        "RpsTicket": "{access_token}"
    }},
    "RelyingParty": "http://auth.xboxlive.com",
    "TokenType": "JWT"
}}""".format(access_token=access_token)
headers = {'Content-Type': 'application/json'}
r=requests.post("https://user.auth.xboxlive.com/user/authenticate",headers=headers,data=data)

json3 = json.loads(r.text)
xbl_token=json3['Token']
uhs=json3['DisplayClaims']['xui'][0]['uhs']

#第四步获取xsts_token
data = """{{
    "Properties": {{
        "SandboxId": "RETAIL",
        "UserTokens": [
            "{}"
        ]
    }},
    "RelyingParty": "rp://api.minecraftservices.com/",
    "TokenType": "JWT"
}}""".format(xbl_token)
#print(data.replace("{","{{").replace("}","}}"))
headers = {'Content-Type': 'application/json'}
r=requests.post("https://xsts.auth.xboxlive.com/xsts/authorize",headers=headers,data=data)
xsts_token=json.loads(r.text)['Token']

#第五步获取第六步的Authorization来验证账户中是否有mc
data="""{{
    "identityToken": "XBL3.0 x={uhs};{xsts_token}"
}}""".format(uhs=uhs,xsts_token=xsts_token)
r = requests.post("https://api.minecraftservices.com/authentication/login_with_xbox",headers=headers,data=data)
Authorization=json.loads(r.text)['access_token']

#最后一步
headers = {
    'Authorization' : 'Bearer '+Authorization
}
r = requests.get("https://api.minecraftservices.com/minecraft/profile",headers=headers)
jsons = json.loads(r.text)

accounts=[{
    'tokenType' : 'Bearer',
    'accessToken' : Authorization,
    'uuid' : jsons['id'],
    'displayName': jsons['name'],
    'userid' : jsons['skins'][0]['id'],
    'type' : 'microsoft',
    'selected':True
}]
# print(json.dumps(accounts))

#文件操作
hcml = open("./hmcl.json","r")
reader=hcml.read()
hcml.close()
hcml = open("./hmcl.json","w+")
jsonl=json.loads(reader)
jsonl['accounts']=accounts
print(jsonl)
hcml.write(json.dumps(jsonl))