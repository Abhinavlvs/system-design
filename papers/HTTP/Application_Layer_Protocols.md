# Application-Layer Protocols: Postgres, Redis, SSH, SMTP, gRPC

Question this note answers: are Postgres, Redis, SSH, SMTP and gRPC application-level protocols, and does the Internet protocol suite really have many protocols for each layer?

Short answer: **yes, all five are application-layer protocols**, and the number of protocols per layer varies a lot. The application layer has hundreds, the transport layer has a handful, and the internet layer is effectively one protocol (IP).

---

## 1. What makes something an application-layer protocol

In the TCP/IP model (RFC 1122), the **application layer** covers process-to-process communication. A protocol belongs here when:

- It defines **message formats and rules** (syntax, commands, replies, error handling) between two programs.
- It relies on the layers below only to **move bytes**. It uses a transport (TCP, UDP or QUIC) through the **sockets API** and does not care how packets are routed or framed.
- It is identified by a **well-known port** (or one chosen by configuration), assigned by IANA by convention.

The TCP/IP model has **no separate presentation or session layers**. Encoding, authentication and session handling are done inside the application protocol or by libraries (see `OSI_model.md` and `Internet_protocol_suite.md`).

---

## 2. The five protocols

| Protocol | What it does | Transport | Default port | Notes |
|---|---|---|---|---|
| **PostgreSQL wire protocol** | Client/server protocol for sending SQL and receiving results | TCP | 5432 | Binary message framing. Authentication and TLS negotiation happen inside the protocol |
| **Redis (RESP)** | Command/response protocol for the Redis key-value store | TCP | 6379 | Simple text-like framing, pipelining is common |
| **SSH** | Remote login, command execution, file transfer (SFTP/SCP) and port forwarding | TCP | 22 | Has its own transport security, authentication and channel multiplexing |
| **SMTP** | Transfers email between mail servers and from clients to servers | TCP | 25 (relay), 587 (submission) | Text commands such as `HELO`, `MAIL FROM`, `RCPT TO`, `DATA` |
| **gRPC** | RPC framework: typed method calls with streaming | HTTP/2 over TCP, usually with TLS | none standard | Messages are encoded with Protocol Buffers |

### How each one uses the layers below

```
Application   Postgres / Redis / SSH / SMTP   gRPC
                                               HTTP/2
Transport                  TCP (+ TLS where used)
Internet                   IP (v4 / v6)
Link                       Ethernet / Wi-Fi / ...
```

### The gRPC special case

gRPC is an application-layer protocol that sits **on top of another application-layer protocol** (HTTP/2). That is normal in TCP/IP:

- The IETF is **not concerned with strict layering**. RFC 3439 has a section titled "Layering Considered Harmful".
- HTTP itself is used as a transport for other protocols all the time (REST, SOAP, GraphQL, WebSocket upgrade, Git over HTTP, DNS over HTTP). The OSI note lists these in its comparison table.
- **TLS** is the other well-known blurry case. It has traits of both the transport and presentation layers and does not fit one layer cleanly.

---

## 3. "The suite has many protocols for each layer": is that true?

Mostly, but not evenly.

| Layer | Examples | How many in practice |
|---|---|---|
| **Application** | HTTP, DNS, SSH, SMTP, FTP, DHCP, NTP, SNMP, IMAP, Postgres, Redis, gRPC, ... | Hundreds. Anyone can define a new one |
| **Transport** | TCP, UDP, SCTP, QUIC, DCCP | A handful. TCP and UDP carry nearly everything, and QUIC (over UDP) is growing |
| **Internet** | IPv4, IPv6, plus support protocols: ICMP, IGMP, IPsec | Effectively one: IP. Everything runs over it |
| **Link** | Ethernet, Wi-Fi, PPP, cellular, and others | Many, one or more per medium |

### The narrow waist

The internet layer is the **narrow waist** of the stack.

- Many applications sit above it and many link technologies sit below it, but nearly all traffic goes through IP.
- This is why the same application works unchanged over Wi-Fi, Ethernet or a cellular network.
- It is also why IPv6 adoption is slow: replacing the one protocol everything depends on is hard.
- The support protocols at this layer (ICMP for errors and ping, IGMP for multicast groups, IPsec for encryption) do not replace IP. They work alongside it.

### Why the link layer is "many"

The link layer is **hardware-independent** in the model. Each physical medium needs its own framing and access rules, so there is a different protocol for each. Virtual links such as VPNs and tunnels also count.

---

## 4. Practical consequences

- A **layer 4 load balancer** can front Postgres, Redis, SSH or SMTP because it only needs to forward the TCP stream. It does not need to understand the protocol. See `L4_Load_Balancers.md`.
- A **layer 7 load balancer** needs to parse the protocol. That works for HTTP (and gRPC, because it is HTTP/2), but not for protocols the balancer does not know.
- Because gRPC multiplexes many calls over **one long-lived HTTP/2 connection**, a layer 4 balancer can pin all calls to one backend. Balancing per call needs an L7 (HTTP/2-aware) balancer or client-side balancing.
- Firewalls and NAT see ports, not protocol names. A protocol on a non-standard port still works, but ops tooling that assumes the default port may not.

---

## Related notes

- `Internet_protocol_suite.md`: the four-layer TCP/IP model and RFC 1122 definitions.
- `OSI_model.md`: seven layers, and how TCP/IP maps onto them.
- `HTTP.md`: HTTP as an application-layer protocol, and the base for gRPC (HTTP/2).
- `L4_Load_Balancers.md`: why layer 4 balancers do not care which application protocol they carry.
