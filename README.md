# CDC

### 1. 为什么有这个想法？

每次训练完一个模型，我都会在同一目录下留下 4 个文件：

```
best_model.pth      # 权重
train_config.yaml   # 超参数
loss_log.csv        # 训练损失
loss_curve.png      # 可视化曲线
```

发给别人复现或者自己 2 个月后再跑实验，就要把这 4 个文件一起打包、压缩、上传、解压。  
tar/zip 当然能用，但总是让我心里别扭：

- 对方只想看一眼 `loss_curve.png` 确认有没有过拟合，却得把整个压缩包拉下来。  
- 我回头想只改 `train_config.yaml` 里的学习率，却要重新打包 500 MB 的 `best_model.pth`。  
- 每次写 README 都要提醒“别忘了把 4 个文件放同一目录”，真的很啰嗦。  

于是冒出一个念头：  
能不能把这 4 个文件优雅地“粘”成一个文件，  
同时又能像 Python 切片一样随时只取我想要的那个？  

这就是 CDC 的起点——纯粹为了解决我自己训练后收拾残局的烦躁。

### 2. 设计思想 / 哲学 / 目标  
（初版）

1. **极简到我自己能一次手写解析器**  
   如果一段 Python 新手三天写不出解析器，设计就太重。  
   保留“一眼看完”的复杂度：起始标记 + 长度 + 数据，别的先别加。

2. **人类可读 ≈ 机器易解**  
   十六进制里能看到文件名、看到 UTF-8 文本、看到 PNG 头，  
   调试时不用打开 IDE，也能用 `hexdump -C` 认出来。

3. **校验 / 加密 / 签名 “可选且偷懒”**  
   不内置算法，只留一段**文本元数据槽**。  
   需要校验？扔一行 JSON：`{"md5":"...","algo":"CRC32"}` 就行。  
   想加密？自己写两行 Python，把密钥也塞同一槽。  
   不想用？留空，文件照样能打开。

4. **把专业事还给专业格式**  
   CDC 不做压缩、不做编码转换、不做数据库索引，  
   只做“把不同格式的文件按顺序放一起”，  
   让 PNG 还是 PNG、让 PyTorch 还是 `.pth`，  
   我们当好胶水，不抢别人饭碗。

5. **自由 & 开放**  
   没有魔法头、没有版权字节、没有强制版本号，  
   任何人都能 fork 出自己的方言，也随时能回到主线。

6. **易用到“顺手打包”**  
   一行命令能把 4 个训练产物粘成一个文件；  
   一行代码能把其中任意一个拆出来，  
   像 Python 的 `zipfile` 一样成为基础设施，而不是新负担。

—— 以上只是“方向宣言”，具体要不要 8 字节长度、要不要目录索引、要不要流式边下边读，都留给后续讨论。  
如果你觉得哪条太理想化，直接开 Issue 打脸。


### 3. 目前阶段

还在“纸面 + 草稿代码”阶段：  
- 格式白皮书写完 0.1 版，尚未冻结；  
- 有套能跑通“打包 → 解包”的 Python 参考实现，仅供验证思路；  
- 没性能测试、没跨语言实现、没真实用户。  

刚把“训练完 4 个文件的烦躁”变成“能跑起来的原型”，接下来准备公开挨打。

### 初稿

```plaintext
[FF] // 块起始符(CSM)
  [E0][00 00 00][00 00 00 00 00 00 00 0A]Hello World // UTF-8文本段
  [EF][00 00 00][00 00 00 00 00 00 01 00]... // 二进制段(256B)
[FF] // 块起始符(CSM)
  [E0][00 00 00][00 00 00 00 00 00 00 0A]Hello World // UTF-8文本段
  [EF][00 00 00][00 00 00 00 00 00 01 00]... // 二进制段(256B)
  [E0]......
  ....
... //均可无限追加
```


#### 命名规范（欢迎优化）

| **组件**| 中文命名| 英文命名| 缩写 |
|--------------------|-------------|-----------------------------|------|
| 整体结构| 复合数据块| Composite Data Chunk| CDC|
| 起始标识| 块起始符| Chunk Start Marker| CSM|
| 数据单元| 数据段| Data Segment| DS|
| 文本类型数据段| 文本段| Text Segment| TS|
| 二进制类型数据段| 二进制段| Binary Segment| BS|
| 文本编码字段| 文本编码标识 | Text Encoding Flag| TEF|
| 二进制元数据字段| 保留填充域| Reserved Padding Field| RPF|
| 长度字段| 数据长度声明 | Data Length Declaration| DLD|
| 实际数据内容| 数据负载| Data Payload| DP|

#### 核心设计（开放调整）

##### 数据段结构
```plaintext
+------+----------------+----------------------+----------------+
| 标记 | 元数据(3字节) | 数据长度声明(8字节) | 数据负载(变长) |
+------+----------------+----------------------+----------------+
```


##### 文本段(TS)设计
```
[0xE0][TEF(3B)][DLD(8B)][文本数据]
```


##### 二进制段(BS)设计
```
[0xEF][RPF(3B)][DLD(8B)][二进制数据]
```


#### 预定义类型表（草案）

##### 文本编码（部分示例）

| 字节序列 (3字节) | 类型       | 对应编码/格式      | 说明 |
|------------------|------------|-------------------|------|
| **文本编码 (00 XX XX)** | | |
| `00 00 00` | 文本      | UTF-8            | Unicode 标准变长编码 |
| `00 00 01` | 文本      | ASCII            | 基础英文字符集 |
| `00 00 02` | 文本      | GBK              | 简体中文扩展编码 |
| `00 00 03` | 文本      | Big5             | 繁体中文标准编码 |
| `00 00 04` | 文本      | UTF-16 BE        | Unicode 大端序 |
| `00 00 05` | 文本      | UTF-16 LE        | Unicode 小端序 |
| `00 00 06` | 文本      | UTF-32           | Unicode 定长编码 |
| `00 00 07` | 文本      | ISO-8859-1       | 西欧拉丁字母 |
| `00 00 08` | 文本      | Windows-1252     | 西欧扩展 |
| `00 00 09` | 文本      | EUC-JP           | 日文编码 |

##### 二进制类型（部分示例）

| 字节序列 (3字节) | 类型       | 对应编码/格式      | 说明 |
|------------------|------------|-------------------|------|
| **二进制编码 (FF XX XX)** | | |
| `FF 00 01` | 二进制    | JPEG             | 联合图像专家组 |
| `FF 00 02` | 二进制    | PNG              | 便携式网络图形 |
| `FF 00 03` | 二进制    | GIF              | 图形交换格式 |
| `FF 00 04` | 二进制    | WEBP             | 谷歌动态图像 |
| `FF 00 05` | 二进制    | BMP              | Windows位图 |
| `FF 00 06` | 二进制    | TIFF             | 标签图像文件 |
| `FF 00 07` | 二进制    | SVG              | 可缩放矢量图形 |
| `FF 00 08` | 二进制    | HEIC             | 高效图像格式 |
| `FF 00 09` | 二进制    | ZIP              | 通用压缩格式 |

> 类型表完全可扩展 - 您需要支持哪些专业格式？



### 使用示例

测试环境:

|硬件|型号|
|-|-|
|CPU|Intel(R) Core(TM) i3-10100 CPU @ 3.60GHz|
|内存|DDR4 24G 2133MHz|
|硬盘|Great Wall P300 M.2 2280 PCIe3.0 2TB|


编码示例:

```python
import YAF #库


import os
import stat
import time
import hashlib
import pathlib
from typing import Dict, Any, Union
import json

def file_info(path: Union[str, os.PathLike]) -> Dict[str, Any]:
    """
    获取指定文件的详细信息

    返回 dict 结构如下：
        {
            'name': str,           # 文件名
            'absolute_path': str,  # 绝对路径
            'size': int,           # 字节大小
            'mode': int,           # 原始 st_mode
            'permissions': str,    # 形如 '-rw-r--r--'
            'owner': str,          # 用户名
            'group': str,          # 组名
            'mtime': str,          # 最后修改时间，格式 YYYY-mm-dd HH:MM:SS
            'ctime': str,          # 创建时间(Windows) / 元数据变动时间(Linux)
            'is_file': bool,
            'is_dir': bool,
            'is_link': bool,
            'link_target': str | None,  # 如果是符号链接，指向哪里
            'checksum_md5': str,   # 文件 MD5 值（目录为 None）
        }
    """
    path = pathlib.Path(path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(path)

    st = path.stat()           # 如果是链接，stat() 跟随链接；用 lstat() 则不跟随
    lst = path.lstat()         # 用于区分链接自身还是指向目标

    # 权限字符串，例如 -rw-r--r--
    def perm_str(mode: int) -> str:
        is_dir = 'd' if stat.S_ISDIR(mode) else '-'
        perms = stat.filemode(mode)[1:]  # 返回形如 '-rw-r--r--'
        return is_dir + perms[1:]

    # 尝试获取用户名/组名，失败则回退到 UID/GID


    # 计算 MD5（大文件采用流式读取）
    def md5_of_file(p: pathlib.Path, buf_size: int = 8192) -> str:
        h = hashlib.md5()
        with p.open('rb') as f:
            for chunk in iter(lambda: f.read(buf_size), b''):
                h.update(chunk)
        return h.hexdigest()

    is_link = path.is_symlink()
    info = {
        'name': path.name,
        # 'absolute_path': str(path),
        'size(MB)': st.st_size / 1024**2 ,
        'mode': st.st_mode,
        'permissions': perm_str(st.st_mode),

        'mtime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st.st_mtime)),
        'ctime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st.st_ctime)),
        'is_file': path.is_file(),
        'is_dir': path.is_dir(),
        'is_link': is_link,
        'link_target': str(path.readlink()) if is_link else None,
        'checksum_md5': md5_of_file(path) if path.is_file() else None,
    }
    return info





writer = YAF.CdcEncoder("example.cdc")

file_dict_0 = file_info("bigFile")
file_dict_1 = file_info("pic.png")
print(file_dict_0,file_dict_1)

s_t = time.time()

writer.add_CSM([json.dumps(file_dict_0),"bigfile","这是一个二进制测试文件"])
writer.add_CSM([json.dumps(file_dict_1),"pic.png","这是一个图片测试文件"])
writer.add_CSM(["这是测试文本"])

writer.Flush()

e_t = time.time()


print(f"花费了{e_t - s_t :.2f}s。")
```

运行结果:

```
D:\program\Python\python-3.11.9\python.exe D:/temp/YAF_test/YAF_test.py
{'name': 'bigFile', 'size(MB)': 1100.0, 'mode': 33206, 'permissions': '-w-rw-rw-', 'mtime': '2025-07-17 10:36:32', 'ctime': '2025-07-24 20:16:07', 'is_file': True, 'is_dir': False, 'is_link': False, 'link_target': None, 'checksum_md5': 'd166f079a3167bcd36b3bfb38e5051ec'} {'name': 'pic.png', 'size(MB)': 2.16501522064209, 'mode': 33206, 'permissions': '-w-rw-rw-', 'mtime': '2024-10-05 17:54:53', 'ctime': '2025-07-24 20:16:17', 'is_file': True, 'is_dir': False, 'is_link': False, 'link_target': None, 'checksum_md5': '8a7b4845a9f2bd39cb83557a02228ced'}
花费了5.51s。
```

解码示例:
```python
import YAF
import time

s_t = time.time()

reader = YAF.CdcDecoder("example.cdc")
result = reader.decode(use_bitrange=True) #使用流式读写(存在文件>1G)

e_t = time.time()

print(f"花费了{e_t - s_t : .6f}秒。")

for DS in result:
    print("+"*20)
    for data in DS:
        print(f"\t {type(data)} : {data}")
```
运行结果:
```
D:\program\Python\python-3.11.9\python.exe D:/temp/YAF_test/De.py
花费了 0.003990秒。
++++++++++++++++++++
	 <class 'str'> : {"name": "bigFile", "size(MB)": 1100.0, "mode": 33206, "permissions": "-w-rw-rw-", "mtime": "2025-07-17 10:36:32", "ctime": "2025-07-24 20:16:07", "is_file": true, "is_dir": false, "is_link": false, "link_target": null, "checksum_md5": "d166f079a3167bcd36b3bfb38e5051ec"}
	 <class 'YAF.bitRange'> : <_io.BufferedReader name='example.cdc'>[296:1153433896]
	 <class 'str'> : 这是一个二进制测试文件
++++++++++++++++++++
	 <class 'str'> : {"name": "pic.png", "size(MB)": 2.16501522064209, "mode": 33206, "permissions": "-w-rw-rw-", "mtime": "2024-10-05 17:54:53", "ctime": "2025-07-24 20:16:17", "is_file": true, "is_dir": false, "is_link": false, "link_target": null, "checksum_md5": "8a7b4845a9f2bd39cb83557a02228ced"}
	 <class 'YAF.bitRange'> : <_io.BufferedReader name='example.cdc'>[1153434247:1155704430]
	 <class 'str'> : 这是一个图片测试文件
++++++++++++++++++++
	 <class 'str'> : 这是测试文本
```

### 性能测试

虽然只是测试未完工阶段，也小小的测试了一下自己写的屎山代码，就当看个乐子吧

=== 编码测试 ===

|文件:大小|时间|速度|
|-|-|-|
|B0.bin: 371093.75KB | 耗时: 676.31ms | 速度: 535.84MB/s|
|B1.bin: 288085.94KB | 耗时: 618.72ms | 速度: 454.70MB/s|
|B2.bin: 795898.44KB | 耗时: 1852.48ms | 速度: 419.57MB/s|
|B3.bin: 278320.31KB | 耗时: 622.15ms | 速度: 436.87MB/s|
|B4.bin: 73242.19KB | 耗时: 152.04ms | 速度: 470.43MB/s|
|B5.bin: 668945.31KB | 耗时: 1574.85ms | 速度: 414.81MB/s|
|B6.bin: 859375.00KB | 耗时: 2250.84ms | 速度: 372.85MB/s|
|B7.bin: 375976.56KB | 耗时: 927.26ms | 速度: 395.97MB/s|
|B8.bin: 219726.56KB | 耗时: 482.97ms | 速度: 444.28MB/s|
|B9.bin: 170898.44KB | 耗时: 397.30ms | 速度: 420.07MB/s|
|B10.bin: 131835.94KB | 耗时: 304.70ms | 速度: 422.53MB/s|
|B11.bin: 683593.75KB | 耗时: 1558.94ms | 速度: 428.22MB/s|
|B12.bin: 698242.19KB | 耗时: 1683.89ms | 速度: 404.94MB/s|
|B13.bin: 73242.19KB | 耗时: 147.55ms | 速度: 484.74MB/s|
|B14.bin: 751953.12KB | 耗时: 2160.23ms | 速度: 339.93MB/s|
|B15.bin: 239257.81KB | 耗时: 628.44ms | 速度: 371.80MB/s|
|B16.bin: 483398.44KB | 耗时: 1177.64ms | 速度: 400.86MB/s|
|B17.bin: 488281.25KB | 耗时: 1310.46ms | 速度: 363.87MB/s|
|B18.bin: 102539.06KB | 耗时: 207.92ms | 速度: 481.60MB/s|
|B19.bin: 83007.81KB | 耗时: 175.17ms | 速度: 462.75MB/s|
|B20.bin: 986328.12KB | 耗时: 2246.05ms | 速度: 428.85MB/s|
|B21.bin: 463867.19KB | 耗时: 1090.80ms | 速度: 415.29MB/s|
|B22.bin: 581054.69KB | 耗时: 1414.07ms | 速度: 401.28MB/s|
|B23.bin: 649414.06KB | 耗时: 1452.22ms | 速度: 436.70MB/s|
|B24.bin: 991210.94KB | 耗时: 2330.29ms | 速度: 415.39MB/s|
|B25.bin: 424804.69KB | 耗时: 1085.87ms | 速度: 382.04MB/s|
|B26.bin: 366210.94KB | 耗时: 979.47ms | 速度: 365.13MB/s|
|B27.bin: 234375.00KB | 耗时: 532.45ms | 速度: 429.86MB/s|
|B28.bin: 351562.50KB | 耗时: 844.93ms | 速度: 406.33MB/s|
|B29.bin: 1000976.56KB | 耗时: 2537.91ms | 速度: 385.17MB/s|
|B30.bin: 737304.69KB | 耗时: 2741.43ms | 速度: 262.65MB/s|
|B31.bin: 581054.69KB | 耗时: 3739.19ms | 速度: 151.75MB/s|
|B32.bin: 947265.62KB | 耗时: 5819.67ms | 速度: 158.95MB/s|
|B33.bin: 193.25KB | 耗时: 2.05ms | 速度: 92.08MB/s|
|B34.bin: 10.39KB | 耗时: 0.67ms | 速度: 15.05MB/s|
|B35.bin: 348.66KB | 耗时: 1.49ms | 速度: 229.26MB/s|
|B36.bin: 414.20KB | 耗时: 1.42ms | 速度: 283.97MB/s|
|B37.bin: 494.30KB | 耗时: 1.67ms | 速度: 289.19MB/s|
|B38.bin: 83.52KB | 耗时: 0.86ms | 速度: 94.69MB/s|
|B39.bin: 334.36KB | 耗时: 1.41ms | 速度: 230.84MB/s|
|B40.bin: 599.61KB | 耗时: 1.78ms | 速度: 328.08MB/s|
|B41.bin: 505.62KB | 耗时: 1.51ms | 速度: 326.91MB/s|
|B42.bin: 846.48KB | 耗时: 1.76ms | 速度: 469.55MB/s|
|B43.bin: 762.36KB | 耗时: 2.14ms | 速度: 347.26MB/s|
|B44.bin: 863.35KB | 耗时: 1.74ms | 速度: 485.83MB/s|
|B45.bin: 767.36KB | 耗时: 2.29ms | 速度: 327.45MB/s|
|B46.bin: 697.05KB | 耗时: 1.88ms | 速度: 362.50MB/s|
|B47.bin: 918.00KB | 耗时: 1.76ms | 速度: 509.94MB/s|
|B48.bin: 98.51KB | 耗时: 0.94ms | 速度: 101.91MB/s|
|B49.bin: 953.32KB | 耗时: 2.09ms | 速度: 446.02MB/s|
|B50.bin: 593.68KB | 耗时: 1.53ms | 速度: 379.41MB/s|
|B51.bin: 351.62KB | 耗时: 1.70ms | 速度: 202.44MB/s|
|B52.bin: 666.65KB | 耗时: 1.48ms | 速度: 440.12MB/s|
|B53.bin: 512.32KB | 耗时: 1.32ms | 速度: 378.97MB/s|
|B54.bin: 863.49KB | 耗时: 1.66ms | 速度: 507.37MB/s|
|B55.bin: 76.89KB | 耗时: 1.00ms | 速度: 75.11MB/s|
|B56.bin: 20.71KB | 耗时: 0.80ms | 速度: 25.22MB/s|
|B57.bin: 386.60KB | 耗时: 1.14ms | 速度: 331.55MB/s|
|B58.bin: 71.35KB | 耗时: 0.70ms | 速度: 98.98MB/s|
|B59.bin: 497.95KB | 耗时: 1.52ms | 速度: 320.09MB/s|
|B60.bin: 522.26KB | 耗时: 1.73ms | 速度: 294.08MB/s|
|B61.bin: 461.20KB | 耗时: 1.69ms | 速度: 266.58MB/s|
|B62.bin: 979.56KB | 耗时: 2.18ms | 速度: 438.43MB/s|
|B63.bin: 519.65KB | 耗时: 1.70ms | 速度: 298.83MB/s|
|B64.bin: 691.37KB | 耗时: 2.19ms | 速度: 308.49MB/s|
|B65.bin: 925.09KB | 耗时: 2.06ms | 速度: 438.59MB/s|
|B66.bin: 652.64KB | 耗时: 1.79ms | 速度: 356.67MB/s|
|B67.bin: 662.02KB | 耗时: 1.56ms | 速度: 415.12MB/s|
|B68.bin: 485.05KB | 耗时: 1.64ms | 速度: 289.49MB/s|
|B69.bin: 159.69KB | 耗时: 1.30ms | 速度: 119.83MB/s|
|B70.bin: 114.61KB | 耗时: 0.89ms | 速度: 125.18MB/s|
|B71.bin: 641.17KB | 耗时: 1.56ms | 速度: 400.20MB/s|
|B72.bin: 276.54KB | 耗时: 1.13ms | 速度: 238.27MB/s|
|B73.bin: 534.79KB | 耗时: 1.36ms | 速度: 382.66MB/s|
|B74.bin: 876.28KB | 耗时: 2.01ms | 速度: 426.46MB/s|
|B75.bin: 667.77KB | 耗时: 2.39ms | 速度: 273.01MB/s|
|B76.bin: 78.82KB | 耗时: 1.23ms | 速度: 62.34MB/s|
|B77.bin: 326.91KB | 耗时: 1.24ms | 速度: 256.82MB/s|
|B78.bin: 486.19KB | 耗时: 1.09ms | 速度: 434.75MB/s|
|B79.bin: 768.94KB | 耗时: 2.05ms | 速度: 366.12MB/s|
|B80.bin: 426.54KB | 耗时: 1.73ms | 速度: 240.57MB/s|
|B81.bin: 171.99KB | 耗时: 1.00ms | 速度: 168.16MB/s|
|B82.bin: 822.97KB | 耗时: 2.16ms | 速度: 372.40MB/s|
|B83.bin: 351.37KB | 耗时: 1.66ms | 速度: 206.85MB/s|
|B84.bin: 1008.90KB | 耗时: 2.53ms | 速度: 389.04MB/s|
|B85.bin: 752.08KB | 耗时: 2.01ms | 速度: 365.89MB/s|
|B86.bin: 978.31KB | 耗时: 2.26ms | 速度: 422.29MB/s|
|B87.bin: 396.74KB | 耗时: 1.54ms | 速度: 252.29MB/s|
|B88.bin: 36.31KB | 耗时: 0.77ms | 速度: 46.21MB/s|
|B89.bin: 66.97KB | 耗时: 0.95ms | 速度: 68.98MB/s|
|B90.bin: 540.52KB | 耗时: 1.17ms | 速度: 453.01MB/s|
|B91.bin: 369.92KB | 耗时: 1.45ms | 速度: 248.33MB/s|
|B92.bin: 1022.73KB | 耗时: 2.48ms | 速度: 402.98MB/s|
|B93.bin: 1016.54KB | 耗时: 2.79ms | 速度: 355.24MB/s|
|B94.bin: 413.54KB | 耗时: 1.48ms | 速度: 273.70MB/s|
|B95.bin: 484.19KB | 耗时: 1.43ms | 速度: 329.83MB/s|
|B96.bin: 379.68KB | 耗时: 1.14ms | 速度: 324.03MB/s|
|B97.bin: 171.64KB | 耗时: 0.83ms | 速度: 201.03MB/s|
|B98.bin: 52.85KB | 耗时: 0.75ms | 速度: 68.49MB/s|
|B99.bin: 888.75KB | 耗时: 2.26ms | 速度: 384.62MB/s|

平均编码时间: 458.30ms/文件

=== 解码测试 ===

|文件:大小|时间|速度|
|-|-|-|
|encoded_B0.bin: 371093.76KB | 耗时: 384.97ms | 速度: 941.37MB/s|
|encoded_B1.bin: 288085.95KB | 耗时: 340.44ms | 速度: 826.38MB/s|
|encoded_B2.bin: 795898.45KB | 耗时: 830.67ms | 速度: 935.68MB/s|
|encoded_B3.bin: 278320.33KB | 耗时: 358.75ms | 速度: 757.62MB/s|
|encoded_B4.bin: 73242.20KB | 耗时: 94.86ms | 速度: 753.98MB/s|
|encoded_B5.bin: 668945.33KB | 耗时: 682.85ms | 速度: 956.68MB/s|
|encoded_B6.bin: 859375.01KB | 耗时: 969.19ms | 速度: 865.91MB/s|
|encoded_B7.bin: 375976.58KB | 耗时: 432.23ms | 速度: 849.46MB/s|
|encoded_B8.bin: 219726.58KB | 耗时: 246.94ms | 速度: 868.94MB/s|
|encoded_B9.bin: 170898.45KB | 耗时: 174.97ms | 速度: 953.83MB/s|
|encoded_B10.bin: 131835.95KB | 耗时: 140.75ms | 速度: 914.72MB/s|
|encoded_B11.bin: 683593.76KB | 耗时: 691.46ms | 速度: 965.46MB/s|
|encoded_B12.bin: 698242.20KB | 耗时: 764.58ms | 速度: 891.83MB/s|
|encoded_B13.bin: 73242.20KB | 耗时: 138.27ms | 速度: 517.28MB/s|
|encoded_B14.bin: 751953.14KB | 耗时: 695.02ms | 速度: 1056.55MB/s|
|encoded_B15.bin: 239257.83KB | 耗时: 315.43ms | 速度: 740.73MB/s|
|encoded_B16.bin: 483398.45KB | 耗时: 509.73ms | 速度: 926.11MB/s|
|encoded_B17.bin: 488281.26KB | 耗时: 541.62ms | 速度: 880.39MB/s|
|encoded_B18.bin: 102539.08KB | 耗时: 130.05ms | 速度: 770.00MB/s|
|encoded_B19.bin: 83007.83KB | 耗时: 83.54ms | 速度: 970.36MB/s|
|encoded_B20.bin: 986328.14KB | 耗时: 1013.06ms | 速度: 950.80MB/s|
|encoded_B21.bin: 463867.20KB | 耗时: 559.91ms | 速度: 809.06MB/s|
|encoded_B22.bin: 581054.70KB | 耗时: 691.98ms | 速度: 820.01MB/s|
|encoded_B23.bin: 649414.08KB | 耗时: 692.37ms | 速度: 915.98MB/s|
|encoded_B24.bin: 991210.95KB | 耗时: 1101.79ms | 速度: 878.55MB/s|
|encoded_B25.bin: 424804.70KB | 耗时: 529.43ms | 速度: 783.57MB/s|
|encoded_B26.bin: 366210.95KB | 耗时: 414.78ms | 速度: 862.20MB/s|
|encoded_B27.bin: 234375.01KB | 耗时: 248.05ms | 速度: 922.72MB/s|
|encoded_B28.bin: 351562.51KB | 耗时: 336.28ms | 速度: 1020.94MB/s|
|encoded_B29.bin: 1000976.58KB | 耗时: 1082.42ms | 速度: 903.09MB/s|
|encoded_B30.bin: 737304.70KB | 耗时: 1061.88ms | 速度: 678.06MB/s|
|encoded_B31.bin: 581054.70KB | 耗时: 627.94ms | 速度: 903.65MB/s|
|encoded_B32.bin: 947265.64KB | 耗时: 1071.28ms | 速度: 863.51MB/s|
|encoded_B33.bin: 193.26KB | 耗时: 91.22ms | 速度: 2.07MB/s|
|encoded_B34.bin: 10.40KB | 耗时: 0.97ms | 速度: 10.47MB/s|
|encoded_B35.bin: 348.67KB | 耗时: 0.81ms | 速度: 422.46MB/s|
|encoded_B36.bin: 414.21KB | 耗时: 1.17ms | 速度: 344.79MB/s|
|encoded_B37.bin: 494.31KB | 耗时: 1.18ms | 速度: 410.03MB/s|
|encoded_B38.bin: 83.53KB | 耗时: 0.70ms | 速度: 116.36MB/s|
|encoded_B39.bin: 334.37KB | 耗时: 0.83ms | 速度: 392.47MB/s|
|encoded_B40.bin: 599.62KB | 耗时: 1.04ms | 速度: 563.26MB/s|
|encoded_B41.bin: 505.63KB | 耗时: 0.92ms | 速度: 535.73MB/s|
|encoded_B42.bin: 846.49KB | 耗时: 1.86ms | 速度: 444.94MB/s|
|encoded_B43.bin: 762.37KB | 耗时: 1.56ms | 速度: 476.54MB/s|
|encoded_B44.bin: 863.36KB | 耗时: 1.41ms | 速度: 596.23MB/s|
|encoded_B45.bin: 767.38KB | 耗时: 0.97ms | 速度: 771.14MB/s|
|encoded_B46.bin: 697.06KB | 耗时: 1.25ms | 速度: 545.01MB/s|
|encoded_B47.bin: 918.01KB | 耗时: 1.12ms | 速度: 797.02MB/s|
|encoded_B48.bin: 98.52KB | 耗时: 0.75ms | 速度: 128.87MB/s|
|encoded_B49.bin: 953.33KB | 耗时: 1.43ms | 速度: 652.87MB/s|
|encoded_B50.bin: 593.70KB | 耗时: 1.27ms | 速度: 455.98MB/s|
|encoded_B51.bin: 351.63KB | 耗时: 1.05ms | 速度: 326.01MB/s|
|encoded_B52.bin: 666.66KB | 耗时: 1.10ms | 速度: 591.69MB/s|
|encoded_B53.bin: 512.33KB | 耗时: 1.42ms | 速度: 353.14MB/s|
|encoded_B54.bin: 863.50KB | 耗时: 1.55ms | 速度: 544.32MB/s|
|encoded_B55.bin: 76.90KB | 耗时: 1.14ms | 速度: 65.62MB/s|
|encoded_B56.bin: 20.72KB | 耗时: 1.11ms | 速度: 18.22MB/s|
|encoded_B57.bin: 386.61KB | 耗时: 1.06ms | 速度: 354.70MB/s|
|encoded_B58.bin: 71.37KB | 耗时: 0.79ms | 速度: 88.54MB/s|
|encoded_B59.bin: 497.96KB | 耗时: 1.11ms | 速度: 437.35MB/s|
|encoded_B60.bin: 522.27KB | 耗时: 0.92ms | 速度: 554.26MB/s|
|encoded_B61.bin: 461.21KB | 耗时: 1.04ms | 速度: 433.95MB/s|
|encoded_B62.bin: 979.58KB | 耗时: 1.27ms | 速度: 756.10MB/s|
|encoded_B63.bin: 519.66KB | 耗时: 1.07ms | 速度: 474.33MB/s|
|encoded_B64.bin: 691.38KB | 耗时: 1.08ms | 速度: 624.24MB/s|
|encoded_B65.bin: 925.10KB | 耗时: 2.18ms | 速度: 413.90MB/s|
|encoded_B66.bin: 652.65KB | 耗时: 1.33ms | 速度: 479.68MB/s|
|encoded_B67.bin: 662.04KB | 耗时: 1.08ms | 速度: 600.41MB/s|
|encoded_B68.bin: 485.07KB | 耗时: 1.09ms | 速度: 432.68MB/s|
|encoded_B69.bin: 159.70KB | 耗时: 0.97ms | 速度: 160.90MB/s|
|encoded_B70.bin: 114.62KB | 耗时: 0.88ms | 速度: 127.37MB/s|
|encoded_B71.bin: 641.19KB | 耗时: 1.34ms | 速度: 466.31MB/s|
|encoded_B72.bin: 276.55KB | 耗时: 1.37ms | 速度: 197.50MB/s|
|encoded_B73.bin: 534.81KB | 耗时: 1.13ms | 速度: 463.05MB/s|
|encoded_B74.bin: 876.29KB | 耗时: 1.24ms | 速度: 689.46MB/s|
|encoded_B75.bin: 667.78KB | 耗时: 1.05ms | 速度: 618.60MB/s|
|encoded_B76.bin: 78.83KB | 耗时: 1.19ms | 速度: 64.58MB/s|
|encoded_B77.bin: 326.93KB | 耗时: 0.93ms | 速度: 342.52MB/s|
|encoded_B78.bin: 486.20KB | 耗时: 1.24ms | 速度: 382.94MB/s|
|encoded_B79.bin: 768.95KB | 耗时: 1.59ms | 速度: 470.98MB/s|
|encoded_B80.bin: 426.55KB | 耗时: 1.01ms | 速度: 412.76MB/s|
|encoded_B81.bin: 172.00KB | 耗时: 0.84ms | 速度: 198.90MB/s|
|encoded_B82.bin: 822.98KB | 耗时: 1.21ms | 速度: 666.58MB/s|
|encoded_B83.bin: 351.38KB | 耗时: 0.85ms | 速度: 401.86MB/s|
|encoded_B84.bin: 1008.91KB | 耗时: 1.10ms | 速度: 897.90MB/s|
|encoded_B85.bin: 752.09KB | 耗时: 1.04ms | 速度: 706.08MB/s|
|encoded_B86.bin: 978.33KB | 耗时: 0.93ms | 速度: 1030.41MB/s|
|encoded_B87.bin: 396.75KB | 耗时: 1.09ms | 速度: 354.20MB/s|
|encoded_B88.bin: 36.33KB | 耗时: 1.08ms | 速度: 32.84MB/s|
|encoded_B89.bin: 66.99KB | 耗时: 1.07ms | 速度: 61.34MB/s|
|encoded_B90.bin: 540.53KB | 耗时: 1.27ms | 速度: 415.28MB/s|
|encoded_B91.bin: 369.93KB | 耗时: 1.30ms | 速度: 278.07MB/s|
|encoded_B92.bin: 1022.74KB | 耗时: 1.38ms | 速度: 723.59MB/s|
|encoded_B93.bin: 1016.55KB | 耗时: 1.28ms | 速度: 773.45MB/s|
|encoded_B94.bin: 413.55KB | 耗时: 1.23ms | 速度: 328.45MB/s|
|encoded_B95.bin: 484.20KB | 耗时: 1.01ms | 速度: 470.03MB/s|
|encoded_B96.bin: 379.70KB | 耗时: 1.19ms | 速度: 310.39MB/s|
|encoded_B97.bin: 171.65KB | 耗时: 0.96ms | 速度: 175.51MB/s|
|encoded_B98.bin: 52.86KB | 耗时: 0.88ms | 速度: 58.40MB/s|
|encoded_B99.bin: 888.77KB | 耗时: 1.29ms | 速度: 672.56MB/s|

平均解码时间: 181.24ms/文件

=== 往返测试 ===
一致性验证: 100/100 文件通过
