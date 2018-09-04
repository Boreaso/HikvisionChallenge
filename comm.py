import json
import socket


class Communication:
    """Socket通信类"""
    BUFFER_SIZE = 1024

    def __init__(self, ip, port):
        assert isinstance(ip, str)
        assert isinstance(port, int)
        self.socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        self.ip = ip
        self.port = port
        self.receiver = None

    def connect(self):
        self.socket.connect((self.ip, self.port))

    def send(self, msg):
        self.socket.sendall(self._pack(msg))

    def _pack(self, msg):
        send_str = "%08d%s" % (len(msg), msg)
        return send_str.encode(encoding='ascii')

    def _unpack(self, msg):
        return msg.decode()[8:]

    def authorize(self, token):
        # 欢迎消息
        welcome = self.socket.recv(self.BUFFER_SIZE)
        if not welcome:
            return False
        # 发送身份消息
        msg = '{"token": "%s","action":"sendtoken"}' % token
        self.socket.sendall(self._pack(msg))
        auth_res = self.socket.recv(self.BUFFER_SIZE)
        if not auth_res:
            return False
        # 身份认证结果
        auth_res = json.loads(self._unpack(auth_res))
        if auth_res and 'result' in auth_res:
            if auth_res['result'] == 1:
                send_str = '{"token": "%s","action":"ready"}' % token
                self.socket.sendall(send_str.encode(encoding='ascii'))
                return True
        return False

    def get_global_info(self):
        """获取地图信息。发送地图信息后,表示比赛开始，该时刻为0，
        参赛者程序收到地图信息，可以移动无人机准备接送货物。此时，
        需要参赛者将他们所控制的无人机时刻为0的位置发送给服务器"""
        map_info = self.socket.recv(self.BUFFER_SIZE)
        if not map_info:
            return None
        map_info = json.loads(self._unpack(map_info))
        return map_info[map_info] if 'map' in map_info else None

    def start_receive(self, recv_callback):
        while True:
            data = self.socket.recv(self.BUFFER_SIZE)
            try:
                ret_msg = recv_callback(self._unpack(data))
                self.socket.sendall(ret_msg)
            except StopIteration:
                # 比赛结束，关闭连接
                self.socket.close()
