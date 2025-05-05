def recv_movie(connection, filesize) -> bytes:
    data = b''
    while len(data) < filesize:
        chunk = connection.recv(min(1400, filesize - len(data)))
        if not chunk:
            raise Exception('Connection is closed')
        data += chunk
    
    return data