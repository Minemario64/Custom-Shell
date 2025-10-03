import psutil

for conn in psutil.net_connections(kind='inet'):
    if conn.status == 'LISTEN':
        pid = conn.pid
        try:
            proc = psutil.Process(pid)
            print(f"Port: {conn.laddr.port}, PID: {pid}, App: {proc.name()}")
        except psutil.NoSuchProcess:
            print(f"Port: {conn.laddr.port}, PID: {pid}, App: <terminated>")