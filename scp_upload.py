import paramiko
import sys

def upload(local, remote, host="pi", user="dani", password="asdf"):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=user, password=password, timeout=10)
    sftp = client.open_sftp()
    with open(local, 'rb') as f:
        data = f.read()
    with sftp.file(remote, 'wb') as fr:
        fr.write(data)
    sftp.close()
    client.close()
    print(f"Uploaded {local} -> {remote}")

if __name__ == "__main__":
    upload(sys.argv[1], sys.argv[2])
