## 使用

### 安装依赖

安装 node 之后，用 `npm i` 安装依赖

### 字体文件

下载 MI LANTING 字体，并保存为 `MI-LANTING.ttf`。

该字体可以从如下网址找到： https://www.onlinewebfonts.com/download/796a8aac411b7d0cce8b49865160eb63

从上述网页中找到 ttf 格式的文件的网址即可下载。

### 执行

使用 `node index.js` 可以执行这个服务器。

不过不知道是不是字体处理的库有内存泄漏，用时间长了会开始崩溃。所以代码里面写了处理 100 个文件就退出的逻辑。所以需要在这个 node 服务退出之后再反复执行他。 Windows 上的话可以使用这里的 `run.bat` ，其他平台可以参考着自己配置一下。
