# What "Runs Over TCP" Means

"Runs over TCP" means a protocol hands its bytes to a TCP connection and relies on TCP to deliver them reliably and in order. The protocol only defines what the bytes mean. TCP never looks inside them.

---

## 1. Example in code: HTTP over a raw TCP socket (Python)

No HTTP library is used. The program opens a TCP connection and writes HTTP text into it.

```python
import socket

s = socket.create_connection(("example.com", 80))   # TCP: SYN, SYN-ACK, ACK
s.sendall(b"GET / HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n")
print(s.recv(4096).decode())                        # TCP hands back the bytes
s.close()                                           # TCP: FIN, ACK
```

| Line | Layer doing the work |
|---|---|
| `create_connection(...)` | **TCP**: the three-way handshake |
| The bytes passed to `sendall` | **HTTP**: just text. TCP does not know what it means |
| `recv(...)` | **TCP**: returns the ordered bytes the server sent |
| `close()` | **TCP**: connection teardown (FIN, ACK) |

What TCP does in between: it splits the bytes into segments, numbers them, retransmits lost ones, and delivers them in order as one byte stream.

---

## 2. Example on the command line: HTTP with `nc`

```
$ nc example.com 80
GET / HTTP/1.1
Host: example.com
Connection: close

```

(Press Enter twice after the last header line.)

1. `nc` opens a **TCP connection** to port 80.
2. The text you type goes through the connection. That text is **HTTP**.
3. The server replies with `HTTP/1.1 200 OK ...` and the page, through the same connection.

### What you would see on the wire (`tcpdump` or Wireshark)

```
SYN                                  <- TCP opening the connection
SYN-ACK
ACK
[PSH,ACK] "GET / HTTP/1.1 ..."       <- your HTTP text, inside a TCP segment
ACK
[PSH,ACK] "HTTP/1.1 200 OK ..."      <- the server's HTTP reply, inside TCP segments
FIN, ACK ...                         <- TCP closing the connection
```

The SYN, ACK and FIN lines are TCP. The quoted text is HTTP.

---

## 3. Same idea, different protocol: Redis by hand

```
$ nc localhost 6379
PING            <- you type this (Redis's own text format)
+PONG           <- the reply
```

The TCP connection is the same kind as for HTTP. Only the bytes you send differ.

---

## 4. How the bytes are wrapped on the way out

```
Your bytes:   GET / HTTP/1.1 ...                  <- application protocol (HTTP)
+ TCP header: ports 51234 -> 80, seq, ack, flags  <- TCP wraps it into a segment
+ IP header:  your IP -> server IP                <- IP wraps it into a packet
+ Ethernet:   MAC addresses                       <- link layer wraps it into a frame
```

Each layer adds its own header. The receiver strips them in reverse order and gives the original bytes to the server program.

---

## 5. Contrast: protocols that do not run over TCP

DNS usually sends a query as one UDP packet and gets one UDP packet back. There is no connection and the transport does no retransmission, so DNS "runs over UDP".

| Protocol | Runs over | What the transport gives it |
|---|---|---|
| HTTP/1.1, HTTP/2, Postgres, Redis, SSH, SMTP | TCP | Ordered, reliable byte stream |
| HTTPS | TLS over TCP | Same, with encryption added |
| DNS lookups | UDP | Single packets, no guarantee |
| HTTP/3 | QUIC (on UDP) | Reliable streams without TCP |

---

## 6. Example: HTTPS (HTTP over TLS over TCP)

The HTTP text is identical. The only difference is a TLS layer between your code and the TCP socket, and the traffic on port 443 is encrypted.

### Python: the same code with one extra step

```python
import socket, ssl

ctx = ssl.create_default_context()                                    # trusted CAs, cert checks on
raw = socket.create_connection(("example.com", 443))                  # TCP: SYN, SYN-ACK, ACK
s = ctx.wrap_socket(raw, server_hostname="example.com")               # TLS handshake runs over that TCP connection

s.sendall(b"GET / HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n")   # same HTTP text as before
print(s.recv(4096).decode())                                          # TLS decrypts what TCP delivered
s.close()
```

| Line | Layer doing the work |
|---|---|
| `create_connection(..., 443)` | **TCP**: plain handshake, no encryption yet |
| `wrap_socket(...)` | **TLS**: handshake over the TCP connection, certificate check, keys agreed |
| `sendall(b"GET ...")` | **HTTP** text, which TLS encrypts before handing it to TCP |
| `recv(...)` | TCP delivers ciphertext, TLS decrypts it, you read plain HTTP |

### Command line: `openssl` in place of `nc`

```
$ openssl s_client -connect example.com:443 -servername example.com -quiet
GET / HTTP/1.1
Host: example.com
Connection: close

```

(Press Enter twice after the last header line.)

`-servername` sends the hostname in the TLS handshake. That is the SNI, so a server hosting many sites knows which certificate to use. `openssl` does the TCP connect and the TLS handshake. What you type is the same HTTP text as before.

### What you would see on the wire (`tcpdump` or Wireshark)

```
SYN / SYN-ACK / ACK                    <- TCP handshake, same as plain HTTP
ClientHello  (SNI: example.com)        <- TLS starts; this part is readable
ServerHello                            <- after this, the rest is encrypted
{certificate, Finished} ...            <- encrypted in TLS 1.3
Application Data  (unreadable bytes)   <- your GET request, encrypted
Application Data  (unreadable bytes)   <- the server's response, encrypted
FIN / ACK                              <- TCP closing the connection
```

Compared with the plain HTTP capture, the `GET /` and `200 OK` text no longer appears. You only see TCP flags, the TLS handshake (including the hostname) and opaque Application Data. Packet sizes and timing are still visible.

### The wrapping on the way out

```
HTTP text:     GET / HTTP/1.1 ...                 <- application protocol
+ TLS record:  encrypted, integrity-protected     <- TLS wraps it
+ TCP header:  ports 51234 -> 443, seq, ack       <- TCP wraps the TLS records into segments
+ IP header, Ethernet header                      <- as before
```

TCP does not know it is carrying TLS, and TLS does not know it is carrying HTTP. Each layer only sees bytes from the one above it.

---

## 7. Example: Postgres (a binary protocol over TCP)

Postgres is a binary protocol, so you cannot type it into `nc` like HTTP. The normal way is `psql`, which opens a TCP connection to port 5432 and speaks the Postgres wire protocol over it:

```
$ psql -h localhost -p 5432 -U postgres -c "SELECT 1"
```

To see the bytes yourself, here is a raw-socket version in Python. It has not been run. It assumes a local dev server with `trust` authentication, so no password is asked for. A server that requires a password replies with an authentication request instead, and the script will not reach `ReadyForQuery`.

```python
import socket, struct

def read_msg(s):
    tag = s.recv(1)                                   # 1-byte message type
    length = struct.unpack("!I", s.recv(4))[0]        # 4-byte length, includes itself
    data = b""
    while len(data) < length - 4:
        data += s.recv(length - 4 - len(data))
    return tag, data

def read_until_ready(s):
    msgs = []
    while True:
        tag, data = read_msg(s)
        msgs.append((tag, data))
        if tag == b"Z":                               # ReadyForQuery
            return msgs

s = socket.create_connection(("localhost", 5432))     # TCP handshake

# StartupMessage: length, protocol version 3.0, key/value pairs, final \0
params = b"user\0postgres\0database\0postgres\0\0"
body = struct.pack("!I", 196608) + params             # 196608 = version 3.0
s.sendall(struct.pack("!I", len(body) + 4) + body)
read_until_ready(s)                                   # AuthenticationOk, ParameterStatus..., ReadyForQuery

# Simple Query: 'Q' + length + SQL + \0
sql = b"SELECT 1\0"
s.sendall(b"Q" + struct.pack("!I", len(sql) + 4) + sql)
for tag, data in read_until_ready(s):
    print(tag, data)                                  # T (columns), D (row), C (done), Z (ready)

s.sendall(b"X" + struct.pack("!I", 4))                # Terminate
s.close()
```

### What the messages look like on the wire

```
SYN / SYN-ACK / ACK                       <- TCP handshake
StartupMessage (user, database)           <- client, Postgres protocol
'R' AuthenticationOk                      <- server
'S' ParameterStatus x N                   <- server settings (encoding, timezone, ...)
'K' BackendKeyData, 'Z' ReadyForQuery     <- server is idle and ready
'Q' "SELECT 1"                            <- client sends the query
'T' RowDescription, 'D' DataRow ("1")     <- server returns the result
'C' CommandComplete, 'Z' ReadyForQuery
'X' Terminate, FIN / ACK                  <- close
```

The query message `'Q' "SELECT 1"` as raw bytes:

```
51  00 00 00 0d  53 45 4c 45 43 54 20 31 00
Q   length = 13  S  E  L  E  C  T  ' ' 1  \0
```

The length (13) counts the 4 length bytes plus the 9 bytes of SQL text including the final zero byte. It does not count the tag byte.

### What is different from HTTP

- **Message framing:** HTTP/1.1 uses text, line endings, and `Content-Length` or chunking. Postgres puts a 1-byte tag and a 4-byte length in front of every message. This is how it works around TCP having no message boundaries (see `TCP.md`).
- **Same connection, many messages:** one TCP connection stays open for many queries, like HTTP keep-alive, but it also holds session state (open transaction, settings).
- **TLS works differently:** HTTPS starts TLS immediately on port 443. Postgres first sends an 8-byte `SSLRequest` over the same TCP connection, and the server answers `S` (yes) or `N` (no). Only after `S` does the TLS handshake start, and then the startup message goes inside TLS. This is the "upgrade a plain connection to TLS" style, like SMTP's `STARTTLS`.

### Where this matters for load balancing

- **Layer 4:** an L4 balancer can forward Postgres traffic, because it only needs the TCP connection.
- **Layer 7:** a typical L7 HTTP balancer cannot, because the protocol is not HTTP.
- **Why a pooler is used:** each connection holds session state, so people usually put a Postgres-aware pooler such as PgBouncer in front of it instead of a generic balancer.

---

## 8. What is a binary protocol?

TCP only carries bytes. A protocol decides **how to write information as bytes**. There are two broad styles.

| | Text protocol | Binary protocol |
|---|---|---|
| Bytes represent | Readable characters (ASCII or UTF-8) | Packed values: integers, flags and lengths stored as raw bytes |
| Human can read it on the wire | Yes (`nc`, `curl -v`, a text editor) | No, you need a tool (Wireshark, hexdump, a client library) |
| Fields are separated by | Delimiters such as spaces, `:` and `\r\n` | Fixed positions, tags and length prefixes |
| Numbers | Written as digits (`"1000"`) | Stored as binary integers (`0x000003E8`) |
| Examples | HTTP/1.1, SMTP, FTP, Redis (RESP), IMAP | Postgres, MySQL, HTTP/2, HTTP/3, gRPC (protobuf), Thrift binary, Kafka, TLS records, the TCP and IP headers themselves |

### The same number in both styles

The number 1000:

```
Text:    "1000"     ->  31 30 30 30         (4 bytes: ASCII '1', '0', '0', '0')
Binary:  1000       ->  00 00 03 e8         (4 bytes: a 32-bit integer)
```

The sizes here are the same, but the binary form scales better. The number 4,000,000,000 takes 10 text bytes and still 4 binary bytes. Binary values also need no parsing from digits, so reading them is fast.

### The same idea at the protocol level

HTTP/1.1 (text) request line:

```
47 45 54 20 2f 20 48 54 54 50 2f 31 2e 31 0d 0a
G  E  T  ' ' /  ' ' H  T  T  P  /  1  .  1  \r \n
```

HTTP/2 (binary) starts every frame with a fixed 9-byte header:

```
| length (24 bits) | type (8) | flags (8) | R (1) + stream id (31) |
```

There are no words, spaces or line endings. The receiver reads exactly 9 bytes, learns how long the payload is, and reads that many more.

### How a binary protocol finds message boundaries

Since TCP has no message boundaries, every protocol must add its own. Binary protocols mostly use a **length prefix**:

1. Read a fixed-size header (for example Postgres: 1-byte tag + 4-byte length).
2. Read the length field.
3. Read exactly that many more bytes. That is one complete message.
4. Repeat.

Text protocols usually use **delimiters** (a blank line ends HTTP headers, `\r\n` ends an SMTP command) plus a length (`Content-Length`) for the body.

### Byte order

A binary integer longer than one byte needs an agreed byte order. Network protocols use **network byte order** (big-endian: most significant byte first). That is why the Python code uses `struct.pack("!I", ...)`. The `!` means network order and `I` means a 4-byte unsigned integer.

### Trade-offs

| | Text | Binary |
|---|---|---|
| Debugging | Easy: read it directly | Harder: needs a decoder or tooling |
| Size on the wire | Larger | Smaller |
| Parsing speed | Slower (parse digits, find delimiters) | Faster (read at fixed offsets) |
| Strictness | Looser; easy to produce sloppy or ambiguous input | Stricter; rigid format reduces ambiguity |
| Extensibility | Easy to add a header line | Needs version fields, tags or schemas |

### Common mix-ups

- **"Binary protocol" is about the protocol's own messages, not the data in them.** HTTP/1.1 is a text protocol even though its body can hold an image (binary data). Postgres is a binary protocol even though it can carry text columns.
- **Binary does not mean encrypted.** It only means not human-readable. Anyone with a decoder can read it, which is why binary protocols still use TLS.
- **TCP does not care.** To TCP, text and binary protocols are both just bytes.
- **Schemas and IDLs go with binary.** Formats such as Protocol Buffers and Thrift define the message layout in a schema file, then generate code that reads and writes the binary form (see `Protocols_By_Layer.md`).

---

## 9. Does HTTP have serialization?

Not for your data. HTTP has no built-in format for turning objects into bytes. It does serialize its own messages, and it has headers for labelling whichever format the body uses.

### 1. HTTP serializes its own message structure

- In HTTP/1.1, the request line, status line and headers are written as ASCII text with `\r\n` line endings.
- In HTTP/2 and HTTP/3, the same information is written as binary frames, with headers compressed by HPACK or QPACK (see `HTTP.md`).
- That is serialization of HTTP's own structure (method, URL, headers, status), not of your application data.

### 2. HTTP carries a body without interpreting it

The body is just bytes. You pick the format, and the headers say what you picked:

| Header | Role |
|---|---|
| `Content-Type` | Format of the body being sent (`application/json`, `application/xml`, `application/x-protobuf`, `image/png`) |
| `Accept` | Formats the client can understand in the response |
| `Content-Encoding` | Compression applied to the body (`gzip`, `br`) |
| `Content-Length` / `Transfer-Encoding: chunked` | How many bytes the body has |

This labelling-and-choosing process is called **content negotiation**.

### 3. Example: JSON over HTTP

```
POST /orders HTTP/1.1
Host: api.example.com
Content-Type: application/json          <- tells the server how to parse the body
Content-Length: 31

{"item": "book", "quantity": 2}         <- your serialization (JSON), chosen by you
```

The client code serializes a dict to JSON text (`json.dumps`), and the server parses it back. HTTP only moved the bytes and labelled them.

### 4. Serialization formats commonly used inside HTTP

| Format | `Content-Type` | Style |
|---|---|---|
| JSON | `application/json` | Text, most common for REST APIs |
| XML | `application/xml` | Text, used by SOAP and older APIs |
| Form encoding | `application/x-www-form-urlencoded` | Text, `a=1&b=2`, used by HTML forms |
| Multipart | `multipart/form-data` | Mixed text and binary parts, used for file uploads |
| Protocol Buffers | `application/x-protobuf` | Binary, used by gRPC and some REST APIs |
| Raw binary | `image/png`, `application/octet-stream` | Files and blobs |

### 5. How this compares with other protocols

| | Serialization built into the protocol? |
|---|---|
| **HTTP** | No, bring your own and label it with `Content-Type` |
| **gRPC** | Yes, Protocol Buffers (runs over HTTP/2) |
| **Thrift** | Yes, the Thrift "protocol" layer (binary, compact or JSON) |
| **Postgres** | Yes, its wire format defines how rows and values are encoded |
| **Redis** | Yes, RESP defines how commands and values are written |

That is why gRPC and Thrift are called RPC frameworks while plain HTTP is just a transport for whatever format you choose. In the layer models, serialization is a presentation-layer job (OSI layer 6). TCP/IP has no separate presentation layer, so it happens in the application or its libraries.

---

## 10. Apache Arrow: is it over TCP?

Arrow itself is not a network protocol, so it does not run over TCP by itself. Arrow defines a data format. When Arrow data crosses a network, it travels over some transport, and the main one, Arrow Flight, runs over TCP via gRPC and HTTP/2.

### 1. What Arrow is

Apache Arrow is a specification for a columnar in-memory format. Each column is stored as a contiguous block of bytes with a fixed layout, the same in every language (C++, Python, Java, Rust, ...).

- **No serialization step in memory:** two Arrow-aware programs can share data without converting it. A pointer or a shared-memory region is enough. This is called zero-copy.
- **Contrast with JSON or Protocol Buffers:** those are row-oriented serialization formats. You must encode and decode them at each end. Arrow's layout is already the "wire" form.

### 2. Three ways Arrow data is moved

| Mechanism | What it is | Runs over |
|---|---|---|
| **Arrow IPC format** (stream or file) | Arrow's own serialization: a sequence of messages made of a small metadata header followed by the raw column buffers. The file form is also called Feather | Any byte stream: a file, a pipe, a plain TCP socket, shared memory |
| **Arrow Flight** | An RPC framework for moving Arrow data between services. Calls include `GetFlightInfo`, `DoGet` (download), `DoPut` (upload) and `DoExchange` (both ways). Control messages use Protocol Buffers, and the data uses Arrow IPC | **gRPC, which is HTTP/2, which is TCP** (usually with TLS). It has no standard port, so examples pick one |
| **Flight SQL / ADBC** | A database-access layer on top of Flight (query a database and get Arrow results back) | Same as Flight |

### 3. The stack for Arrow Flight

```
Arrow data (columnar buffers, in Arrow IPC form)
Arrow Flight (DoGet, DoPut, ...)
gRPC
HTTP/2
TLS (optional but typical)
TCP
IP
```

So the answer for Flight is yes, it is over TCP, but indirectly: Flight rides on gRPC, and gRPC rides on HTTP/2 over TCP. This is the same layering idea as in the earlier sections: Arrow's job is the data format, and TCP just moves bytes.

### 4. Where Arrow is not over TCP at all

- A pandas or Spark process handing data to another process through **shared memory** has no network involved.
- Reading an **`.arrow` or Feather file** from disk is a file, not a network.
- An Arrow IPC stream written to a **pipe** between two local programs uses no TCP.

### 5. How it compares with the other formats in these notes

| | Layout | Network protocol included? | Typical use |
|---|---|---|---|
| **JSON over HTTP** | Text, row-oriented | HTTP carries it | Web APIs |
| **Protocol Buffers / gRPC** | Binary, row-oriented messages | gRPC (HTTP/2) | Service-to-service RPC |
| **Thrift** | Binary, row-oriented messages | Thrift transports (often raw TCP) | Service-to-service RPC |
| **Arrow** | Binary, **columnar** | Only via Flight (gRPC), or any byte stream you choose | Large analytical datasets, moving data between engines |
| **Parquet** | Binary, columnar, compressed, **on disk** | No, it is a file format | Storage for analytics |

Arrow and Parquet are often used together. Parquet is compact for storage, and Arrow is the in-memory form the data is decoded into.

**Why a columnar format helps analytics:** a query that needs one column out of fifty reads only that column's bytes, and values of the same type sit next to each other, which is fast for the CPU. Row formats like JSON must read every field of every row.

Sourcing note: this section is general knowledge, not from the Wikipedia pages. Check the Arrow documentation for details such as Flight's message layout.

---

## Related notes

- `TCP.md`: how TCP provides the byte stream (handshake, ACKs, retransmission, windows).
- `L4_Load_Balancers.md`: why a layer 4 device only needs the TCP connection, not the protocol inside it.
- `Protocols_By_Layer.md`: which protocols run over which transport.
- `HTTPS.md`: what changes when TLS sits between HTTP and TCP.
