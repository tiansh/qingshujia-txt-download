## 使用

### 1. 启动服务端

首先启动 server 目录下的 node 服务，启动方式参考 server 目录下的 readme。

### 2. 安装依赖

#### Python 和 pip

安装 Python 后使用 pip 安装依赖：

```
pip install -r requirements.txt
```

#### Web Driver

1. 安装 Firefox 浏览器；在 download.py 文件中修改 Firefox 的可执行文件的路径。
2. [下载 geckodriver](https://github.com/mozilla/geckodriver/releases)，并放置在本目录下

### 3. 配置文件

1. 创建配置文件 proxy.txt 或修改代码；
    文本文件，第一行是代理服务器的域名（或 IP），第二行是端口号，使用 SOCKS5 协议

2. 创建配置文件 login.txt 或修改代码；
    文本文件，第一行为登录网站的用户名，第二行为密码

### 4. 执行下载程序

使用 `python download.py` 执行程序

