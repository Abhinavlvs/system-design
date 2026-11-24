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

## Related notes

- `TCP.md`: how TCP provides the byte stream (handshake, ACKs, retransmission, windows).
- `L4_Load_Balancers.md`: why a layer 4 device only needs the TCP connection, not the protocol inside it.
- `Protocols_By_Layer.md`: which protocols run over which transport.
- `HTTPS.md`: what changes when TLS sits between HTTP and TCP.
