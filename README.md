# Kanopy

This'll let you download videos from Kanopy, credit to Yosuk for helping with this (.yosuk on Discord, you can donate to them with the Bitcoin address 1KTCVE1PQmZYwXcsN3JWoUAMZEC8ZiSDFA).

You will have to install the requirements by running `pip install -r requirements.txt`, then you can run Kanopy.py by running `python Kanopy.py <url>`.

## Instructions to grab headers

1. Borrow an item on Kanopy.
2. Open developer mode of your browser. Search for plays on Network. Do a right-click on the URL -> Copy -> Copy as cURL.
3. Go to https://curlconverter.com/ and paste the content. Select Python in the options of the output, then copy everything except the first line and everything after and including the line starting with response = requests.post. Paste it into Header.py.
