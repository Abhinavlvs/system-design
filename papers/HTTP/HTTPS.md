# HTTPS: Where It Fits and How It Works

Sourcing note: the HTTP Wikipedia page only covers HTTPS briefly (usage share, port 443, the TLS/ALPN requirement for HTTP/2, and two rarely-supported alternatives). Those points are marked **[HTTP page]**. The TLS handshake mechanics, certificate details and TLS version notes below are **general networking knowledge, not taken from the fetched pages**. If you want this file based strictly on Wikipedia's HTTPS and TLS articles, send those URLs.

---

## 1. The one-sentence answer

**HTTPS is not a separate protocol or a separate layer. It is ordinary HTTP carried inside a TLS-encrypted channel.**

- HTTP/1.1 and HTTP/2: HTTP, over **TLS**, over **TCP**, over IP.
- HTTP/3: HTTP, over **QUIC** (which has TLS 1.3 built in), over **UDP**, over IP.

The HTTP messages themselves (methods, headers, status codes, bodies) are byte-for-byte the same as without encryption. What changes is that those bytes are encrypted before they reach TCP.

---

## 2. Where it sits in the stack

```
HTTP (HTTP/1.1 or HTTP/2)         <- what the browser/server programs write
-----------------------------
TLS                               <- encrypts, authenticates, checks integrity
-----------------------------
TCP                               <- reliable byte stream (transport, layer 4)
-----------------------------
IP                                <- routing (internet layer)
-----------------------------
Ethernet / Wi-Fi / ...            <- link layer
```

For HTTP/3 the picture is:

```
HTTP/3
-----------------------------
QUIC  (TLS 1.3 handshake built in, own reliability, streams)
-----------------------------
UDP
-----------------------------
IP
-----------------------------
link
```

### How the layers are accessed in code

An application using HTTPS does this:

1. Opens a **TCP socket** to port 443 (a plain layer-4 connection).
2. Hands that socket to a **TLS library** (OpenSSL, BoringSSL, the OS stack).
3. The TLS library performs the handshake over the socket.
4. The application writes **plaintext HTTP** to the TLS object. The library **encrypts** it into TLS records and writes the ciphertext to the TCP socket.
5. On receipt, TCP delivers ciphertext, TLS decrypts, and the application reads plaintext HTTP.

So TCP never knows it is carrying HTTP, and HTTP never knows about packets. TLS sits between them as a library.

### Which layer is TLS in?

There is no clean answer, and that is normal.

| Model | Where TLS lands | Reason |
|---|---|---|
| TCP/IP (RFC 1122) | Part of the **application layer** (a library the application uses) | TCP/IP has no presentation or session layer, so encryption and session handling are done by the application side |
| OSI | Mixed: **presentation** (encryption, data transformation) and **session** (establishing and resuming a secure session) | The OSI notes in this folder say TLS "does not strictly fit" and has traits of both the transport and presentation layers |
| Practical view | "Between L4 and L7", sometimes called L4.5 | It needs a reliable stream underneath (TCP) and serves any application above |

The TCP/IP notes make the same point: the IETF is not concerned with strict layering (RFC 3439, "Layering Considered Harmful").

---

## 3. What HTTPS gives you

Plain HTTP is stateless and sends everything as readable text. Anyone on the path (Wi-Fi, ISP, any router) can read or change it. TLS adds three guarantees.

| Guarantee | Meaning | Mechanism |
|---|---|---|
| **Confidentiality** | On-path observers cannot read the traffic | Symmetric encryption of every TLS record |
| **Integrity** | Nobody can alter data in transit without detection | Authenticated encryption (AEAD) tags on each record |
| **Authentication** | You are really talking to the server you meant to | The server presents an X.509 **certificate** signed by a trusted CA. Optionally the client presents one too (mutual TLS) |

What it does **not** give you:
- It does not hide **who** you talk to (the IP address is visible).
- It does not hide **how much** you send or **when** (sizes and timing leak information).
- It does not make the **server** trustworthy, only that you reached the domain named in the certificate.
- It does not protect data once it reaches the server, or at a TLS-terminating proxy.

---

## 4. The URL and the port

- The `https://` URI scheme tells the client to use TLS. **[HTTP page]**
- Default port is **443** for encrypted HTTP, versus **80** for plain HTTP (RFC 9110 sections 4.2.1 and 4.2.2). **[HTTP page]**
- Usage: **90.1% of websites** use HTTPS as the default protocol. **[HTTP page]**
- The port decides the mode: a connection to 443 starts with a TLS handshake. A client does not send HTTP first and then upgrade.

---

## 5. How the connection is set up, step by step

### 5.1 Order of operations

```
Client                                        Server
  | ---- TCP SYN ------------------------->     |   \
  | <--- TCP SYN-ACK ----------------------     |    }  1 RTT: TCP handshake
  | ---- TCP ACK ------------------------->     |   /
  | ---- TLS ClientHello ----------------->     |   \
  | <--- TLS ServerHello, certificate, ... -    |    }  TLS 1.3: 1 RTT
  | ---- TLS Finished + first HTTP request ->   |   /   (TLS 1.2: 2 RTT)
  | <--- HTTP response (encrypted) ---------    |
```

Costs (from the TCP and HTTP notes, plus general TLS knowledge):

| Setup | Round trips before the first HTTP byte |
|---|---|
| HTTP over TCP | 1 (TCP) |
| HTTPS, TLS 1.2 over TCP | 1 (TCP) + 2 (TLS) = 3 |
| HTTPS, TLS 1.3 over TCP | 1 (TCP) + 1 (TLS) = 2 |
| TLS 1.3 resumption with 0-RTT over TCP | 1 (TCP), data can ride with the TLS handshake |
| HTTP/3 over QUIC | 1 (combined transport and TLS), 0 on resumption |

The TCP page makes this point: TLS handshakes run **serially after** TCP, TLS 1.2 needs two RTTs, TLS 1.3 allows zero-RTT resumption in some cases but TCP still needs one RTT. TCP Fast Open can remove one RTT, but browsers did not use it by default as of 2020.

### 5.2 What happens in the TLS handshake (TLS 1.3, simplified)

1. **ClientHello.** The client sends: supported TLS versions, supported cipher suites, a random value, a **key share** (its half of a Diffie-Hellman exchange), and extensions:
   - **SNI (Server Name Indication):** the hostname it wants, so one IP can host many sites.
   - **ALPN (Application-Layer Protocol Negotiation, RFC 7301):** the protocols it can speak, such as `h2` and `http/1.1`. **[HTTP page]** mentions ALPN as how HTTP/2 is negotiated.
2. **ServerHello.** The server picks the version and cipher suite and sends its own key share. After this both sides can compute the same **shared secret** and derive session keys. Everything after this point is encrypted.
3. **Certificate.** The server sends its certificate chain and proves it holds the matching private key by signing the handshake transcript (**CertificateVerify**).
4. **Finished.** Each side sends a MAC over the whole handshake, which detects tampering with the negotiation (downgrade attacks).
5. **Application data.** HTTP flows inside TLS records using the derived symmetric keys.

### 5.3 Certificates and trust

- A **certificate** binds a public key to a domain name and is signed by a **Certificate Authority (CA)**.
- The client checks that:
  - the chain leads to a CA in its **trust store**;
  - the certificate is valid for the **requested hostname**;
  - it is within its **validity dates** and is not **revoked**.
- This is what stops someone from impersonating the site. Encryption without authentication would still let an attacker sit in the middle.

### 5.4 Key exchange and forward secrecy

- Modern TLS uses **ephemeral Diffie-Hellman** (ECDHE). Each connection derives fresh keys that are never sent over the wire.
- That gives **forward secrecy**: if the server's long-term private key leaks later, previously recorded traffic still cannot be decrypted.
- Bulk data is protected with a fast **symmetric** cipher (such as AES-GCM or ChaCha20-Poly1305). The expensive public-key work is done only at setup.

### 5.5 Session resumption

- After one full handshake, client and server can reuse the secret for later connections with a cheaper handshake (tickets or pre-shared keys).
- TLS 1.3 can send the first request along with the resumption (**0-RTT**). That data can be **replayed** by an attacker, so it should only carry safe, idempotent requests (see the safe and idempotent methods in `HTTP.md`).

---

## 6. How HTTPS relates to each HTTP version

| HTTP version | Encryption | Notes |
|---|---|---|
| 0.9, 1.0 | None in the spec | Pre-TLS era. Encryption was added by wrapping the connection |
| 1.1 | Optional (HTTPS, or `Upgrade` to TLS) | Persistent connections cut how often the handshake is paid |
| 2 | Required in practice | The spec allows cleartext, but browsers only use HTTP/2 over TLS, and the **HTTP page** says major servers support it over TLS using ALPN with TLS 1.2 or newer |
| 3 | Always encrypted | QUIC has TLS 1.3 built into the transport, so there is no cleartext HTTP/3 |

**Two other ways to encrypt HTTP exist but are essentially unused. [HTTP page]**
- **Secure Hypertext Transfer Protocol (S-HTTP):** encrypts at the HTTP message level instead of the connection level.
- **HTTP/1.1 `Upgrade` header:** start in cleartext on port 80, then switch to TLS on the same connection.
- Browser support for both is nearly non-existent. The page cites browser bug trackers for the `Upgrade` approach never being implemented.

---

## 7. What an observer can and cannot see

Using the layer model:

| Item | Visible to an on-path observer? | Why |
|---|---|---|
| Source and destination IP | Yes | IP header is cleartext |
| TCP ports, flags, sequence numbers | Yes | TCP metadata is cleartext. The TCP notes call this the **wire image**, and it is why middleboxes can interfere with TCP (ossification) |
| TLS handshake, including the **SNI hostname** | Yes (with ordinary TLS) | The ClientHello is sent before keys exist. **Encrypted Client Hello (ECH)** is designed to hide it |
| Certificate | Visible in TLS 1.2, encrypted in TLS 1.3 | TLS 1.3 encrypts the handshake after ServerHello |
| HTTP method, path, query string, headers, cookies | **No** | Inside the TLS records |
| Request and response bodies | **No** | Inside the TLS records |
| Packet sizes and timing | Yes | Can leak which page you loaded (traffic analysis) |

The path and query string are not visible, but the **hostname** usually is, through DNS lookups and SNI.

---

## 8. Impact on load balancers, proxies and caches

This connects directly to `L4_Load_Balancers.md` and the HTTP notes.

| Device | What it can do with HTTPS |
|---|---|
| **L4 load balancer** (TLS passthrough) | Forwards the encrypted TCP stream untouched. It sees only IP and port. No HTTP-aware routing or caching. Certificates live on the backends |
| **L7 load balancer / reverse proxy** (TLS termination) | Holds the certificate, decrypts, reads HTTP, routes by host/path, then talks to backends over plain HTTP or re-encrypts. This is where header-based routing, WAF and caching happen |
| **TLS re-encryption (end-to-end)** | Terminates TLS at the LB, then opens a new TLS connection to the backend. Keeps traffic encrypted inside the network |
| **Forward proxy** | Cannot read HTTPS. The client sends `CONNECT host:443` and the proxy opens a **TCP tunnel**. The `CONNECT` method exists for this **[HTTP page]**. Inspecting content requires installing a proxy CA on clients |
| **Shared web caches** | Cannot cache HTTPS responses in transit, since they cannot read them. Caching moves to the browser, the CDN edge or a terminating reverse proxy |
| **CDN** | Terminates TLS at the edge close to the user, which also cuts handshake latency |

Reminder from the HTTP notes: intermediaries were part of HTTP's design (caches, proxies, hop-by-hop headers). HTTPS limits what they can do. It is a deliberate trade of intermediary visibility for privacy.

---

## 9. Common misconceptions

- **"HTTPS is a different protocol from HTTP."** No. Same HTTP semantics (RFC 9110), wrapped in TLS.
- **"HTTPS means the site is safe."** It means the connection is private and the domain is authenticated. A phishing site can have a valid certificate for its own domain.
- **"HTTPS hides which site I visit."** Not fully. The IP address, DNS queries and (until ECH) the SNI are visible.
- **"HTTPS is a layer."** No. It is a **combination**: application protocol plus a security library plus the transport.
- **"An L4 load balancer can route by URL if I use HTTPS."** No. It cannot read the encrypted request. Use an L7 balancer that terminates TLS.
- **"TLS replaces TCP's reliability."** No. TLS sits on top of TCP and relies on it for ordered, reliable delivery (QUIC is the case where reliability and TLS are combined in one transport).

---

## Related notes

- `HTTP.md`: HTTP semantics, versions, `CONNECT`, persistent connections, and the brief HTTPS section this builds on.
- `TCP.md`: handshake costs, the cleartext TCP wire image and ossification, and why QUIC exists.
- `Internet_protocol_suite.md` and `OSI_model.md`: layer models and why TLS does not fit them cleanly.
- `L4_Load_Balancers.md`: TLS passthrough vs termination.
- `Application_Layer_Protocols.md`: other protocols that use TLS (SMTP with STARTTLS, Postgres TLS, Redis TLS, SSH's own transport security).
