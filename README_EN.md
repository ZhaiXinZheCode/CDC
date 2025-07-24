# CDC  
*(Composite Data Chunk)*

---

### 1. Why does this project exist?

After every training run I end up with four files in the same folder:

```
best_model.pth      # model weights
train_config.yaml   # hyper-parameters
loss_log.csv        # training losses
loss_curve.png      # visualization
```

To let someone else reproduce the experiment—or to resume my own work two months later—I have to zip/tar these four files, upload the archive, and later unzip it on the target machine.  
`tar`/`zip` work, but they always feel clunky:

- A collaborator only wants to glance at `loss_curve.png` to check for over-fitting, yet has to download the entire 500 MB bundle.  
- I only want to tweak the learning rate in `train_config.yaml`, but I must re-package the half-gigabyte `best_model.pth` every time.  
- Every README has to repeat “please put the four files in the same directory”—tedious and error-prone.

So I asked myself:  
Can I “glue” these four heterogeneous files into one, yet still slice out any single file on demand—just like Python slicing?

That itch became the seed of **CDC**—nothing more than a personal remedy for post-training housekeeping rage.

---

### 2. Design Philosophy / Goals  
*(v0.1 draft)*

1. **Minimal enough for a three-day parser**  
   If a Python newcomer cannot hand-write a working decoder over a long weekend, the format is already too heavy.  
   Keep the cognitive load *glanceable*: *start marker + length + payload*—nothing else for now.

2. **Human-readable ≈ machine-friendly**  
   In a hex dump you should still spot the filename, the UTF-8 text, the PNG header… no IDE required.

3. **Checksum / encryption / signature: optional & lazy**  
   No built-in crypto. Just reserve a **text metadata slot**.  
   Need integrity? Drop a JSON line: `{"md5":"...","algo":"CRC32"}`.  
   Need encryption? Two lines of Python + your key in the same slot.  
   Don’t care? Leave the slot empty—the file still opens.

4. **Let specialized formats do their job**  
   CDC does **not** compress, transcode, or index.  
   It only concatenates files in their native encodings—PNG stays PNG, PyTorch stays `.pth`.  
   Be the glue, not the swiss-army knife.

5. **Free & open**  
   No magic headers, no copyright bytes, no mandatory version field.  
   Fork your own dialect anytime; re-join the mainline whenever you like.

6. **Usable with one-liners**  
   One shell command to bundle the four training artefacts.  
   One API call to extract any single artefact—like Python’s `zipfile`, but lighter.

> These are **direction statements**, not commandments.  
> If any point feels unrealistic, open an issue and roast it.

---

### 3. Current Status

- Format white-paper: v0.1 (still fluid).  
- Reference Python encoder/decoder: works for “pack → unpack” demos.  
- No performance tuning, no multi-language ports, no real users yet.

We’ve turned “post-training annoyance” into “a runnable prototype”.  
Next: publish, collect punches.

---

### Draft Format Specification

```
[FF] // Chunk Start Marker (CSM)
  [E0][00 00 00][00 00 00 00 00 00 00 0A]Hello World // UTF-8 Text Segment
  [EF][00 00 00][00 00 00 00 00 00 01 00]...        // Binary Segment (256 B)
[FF] // CSM
  ...
```

#### Naming Cheat-Sheet

| Component            | Chinese         | English                 | Abbrev. |
|----------------------|-----------------|-------------------------|---------|
| Whole construct      | 复合数据块       | Composite Data Chunk    | CDC     |
| Start delimiter      | 块起始符         | Chunk Start Marker      | CSM     |
| Logical unit         | 数据段           | Data Segment            | DS      |
| Text unit            | 文本段           | Text Segment            | TS      |
| Binary unit          | 二进制段         | Binary Segment          | BS      |
| Text encoding field  | 文本编码标识      | Text Encoding Flag      | TEF     |
| Binary meta field    | 保留填充域        | Reserved Padding Field  | RPF     |
| Length field         | 数据长度声明      | Data Length Declaration | DLD     |
| Payload              | 数据负载          | Data Payload            | DP      |

#### Core Layout *(open to tuning)*

```
+------+----------------+----------------------+----------------+
| Flag | Meta (3 B)     | Length (8 B, BE)     | Payload (var.) |
+------+----------------+----------------------+----------------+
```

- **Text Segment (TS):**  
  `[0xE0][TEF (3 B)][DLD (8 B)][UTF-8 text]`

- **Binary Segment (BS):**  
  `[0xEF][RPF (3 B)][DLD (8 B)][raw bytes]`

#### Pre-defined Type Tables *(extensible)*

| 3-byte tag | Category | Format/Encoding |
|------------|----------|-----------------|
| **Text (00 xx xx)** |
| `00 00 00` | Text     | UTF-8           |
| `00 00 01` | Text     | ASCII           |
| `00 00 02` | Text     | GBK             |
| …          | …        | …               |
| **Binary (FF xx xx)** |
| `FF 00 02` | Binary   | PNG             |
| `FF 00 09` | Binary   | ZIP             |
| …          | …        | …               |

---

### Usage Example

Test hardware  
| Component | Model |
|-----------|-------|
| CPU       | Intel Core i3-10100 @ 3.6 GHz |
| RAM       | 24 GB DDR4-2133 |
| SSD       | Great Wall P300 M.2 2 TB PCIe 3.0 |

#### Encoding

```python
import os, pathlib, time, json, hashlib
import YAF  # our tiny CDC library

def file_info(path):
    p = pathlib.Path(path).expanduser().resolve()
    st = p.stat()
    return {
        "name": p.name,
        "size_MB": st.st_size / 1024**2,
        "mtime": st.st_mtime,
        "md5": hashlib.md5(p.read_bytes()).hexdigest()
    }

writer = YAF.CdcEncoder("example.cdc")

big   = file_info("bigFile")
pic   = file_info("pic.png")

t0 = time.time()

writer.add_CSM([json.dumps(big),   "bigfile", "binary test"])
writer.add_CSM([json.dumps(pic),   "pic.png", "image test"])
writer.add_CSM(["plain text sample"])

writer.flush()

print("encoded in %.2f s" % (time.time() - t0))
```

Output
```
{'name': 'bigFile', 'size_MB': 1100.0, ...} {'name': 'pic.png', 'size_MB': 2.17, ...}
encoded in 5.51 s
```

#### Decoding

```python
import YAF, time

t0 = time.time()
reader = YAF.CdcDecoder("example.cdc")
bundles = reader.decode(use_bitrange=True)  # stream large files

print("decoded in %.6f s" % (time.time() - t0))

for ds in bundles:
    print("+" * 20)
    for item in ds:
        print(f"\t{type(item)} : {item}")
```

Output
```
decoded in 0.003990 s
++++++++++++++++++++
	<class 'str'> : {"name":"bigFile", ...}
	<class 'YAF.BitRange'> : <BufferedReader>[296:1153433896]
	<class 'str'> : binary test
...
```

---

### Micro-Benchmarks *(very early numbers)*

#### Encoding

| File | Size | Time | Speed |
|------|------|------|-------|
| B0.bin | 362 MB | 676 ms | 535 MB/s |
| … 99 files … |

Average: 458 ms/file.

#### Decoding

| File | Size | Time | Speed |
|------|------|------|-------|
| encoded_B0.bin | 362 MB | 385 ms | 941 MB/s |
| … 99 files … |

Average: 181 ms/file.

#### Round-trip Integrity

100 / 100 files verified bit-exact after encode→decode.

---

*CDC is still wet clay—break it, reshape it, or ignore it as you see fit.*
