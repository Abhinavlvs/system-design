# Layer 4 Load Balancers and Direct Use of the Transport Layer

## What "LB at layer 4" means

The load balancer makes routing decisions using only transport-layer information: source and destination IP and port, and TCP or UDP. It never parses the payload. It doesn't know whether the bytes are HTTP, a database protocol or SSH.

| | L4 LB | L7 LB |
|---|---|---|
| Reads | IP and port | HTTP method, path, headers, cookies |
| Routing choices | Per connection (e.g. hash of the 4-tuple) | Per request (e.g. `/api` goes to pool A) |
| TLS | Passes it through, still encrypted | Usually terminates it |
| Cost | Cheap and fast | More CPU, more features |
| Typical use | Any TCP/UDP service, raw throughput | HTTP routing, WAF, rewrites |

An L4 LB works in one of two ways:

- **Proxy/NAT mode:** it accepts the client's TCP connection, picks a backend, and opens or rewrites a connection to it. It copies bytes without interpreting them.
- **Passthrough (e.g. DSR):** it forwards packets to the backend, which can reply straight to the client.

Because one TCP connection stays pinned to one backend, HTTP/1.1 keep-alive and HTTP/2 multiplexing can load-balance unevenly. Many requests ride on that one connection.

## "Bypassing" the application layer

An application doesn't bypass the application layer. The application is the application layer. HTTP is just one protocol an app can speak.

Any program can use the transport layer directly through the **sockets API**:

```python
import socket
s = socket.create_connection(("db.internal", 5432))  # TCP, layer 4
s.sendall(b"any bytes you like")
```

- Postgres, Redis, SSH, SMTP and gRPC (which uses HTTP/2) all open a TCP socket and speak their own format.
- HTTP is "TCP plus a text format": `GET / HTTP/1.1\r\nHost: ...\r\n\r\n`.
- The TCP/IP model has no presentation or session layers, so the socket is the boundary between your code and the transport.

So an L4 LB in front of a Postgres service works fine. It doesn't need to understand Postgres, only to forward the TCP stream. In front of a web app, an L4 LB works too, but it can't do path-based routing or see headers. For that you need an L7 LB.

## Related notes

- `Internet_protocol_suite.md`: layer definitions (transport = host-to-host, application = process-to-process).
- `HTTP.md`: HTTP as an application-layer protocol over TCP (or QUIC/UDP for HTTP/3).
