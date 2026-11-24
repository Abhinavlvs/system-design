# HTTP (Hypertext Transfer Protocol)

Source: https://en.wikipedia.org/wiki/HTTP (semi-protected page). These notes are a section-by-section paraphrase of that page, in page order. Usage statistics are as stated on the page (W3Techs data retrieved 2026).

---

## Infobox facts

- **Full name:** Hypertext Transfer Protocol
- **Developed by:** CERN, IETF, W3C
- **Introduced:** 1991
- **Specs site:** httpwg.org/specs/
- **Governing RFCs:**

| RFC | Subject |
|---|---|
| 1945 | HTTP/1.0 |
| 9110 | HTTP Semantics |
| 9111 | HTTP Caching |
| 9112 | HTTP/1.1 |
| 9113 | HTTP/2 |
| 7541 | HPACK header compression |
| 8164 | Opportunistic Security for HTTP/2 |
| 8336 | ORIGIN frame |
| 8441 | Bootstrapping WebSockets with HTTP/2 |
| 9114 | HTTP/3 |
| 9204 | QPACK header compression |

---

## Overview (lead)

**HTTP** is an **application-layer protocol** in the Internet protocol suite, designed for **distributed, collaborative, hypermedia information systems**. It is the foundation of data communication for the **World Wide Web**, where hypertext documents contain links to other resources.

**Request-response model.**
- HTTP follows the **client-server** model.
- A transaction starts with a **client request**. The server returns a **response** that reports the disposition of the request (success, error, redirect, and so on). The response can optionally carry a resource, such as an HTML document.

**Clients.** The common client is a **web browser**. Other **user agents** include web crawlers, voice browsers, mobile apps and other software.

**Intermediaries.** HTTP is designed to let intermediate network elements help:
- **Web caches** serve content on behalf of upstream servers, which improves response time.
- **Browsers** cache previously fetched resources and reuse them.
- **Proxy servers** at the boundary of a private network relay messages for clients that have no globally routable address.

**Hop-by-hop vs end-to-end headers.** Some header fields are **hop-by-hop**, meaning intermediaries manage them. Others are **end-to-end**, managed only by the original client and the final target server.

**Addressing.** Resources are located by **URL**, using the `http` and `https` URI schemes (URIs are defined in RFC 3986).

---

## 1. Versions

HTTP has been revised over time. Versions are written **HTTP/#**. The article gives its main coverage to **HTTP/0.9, 1.0 and 1.1**. HTTP/2 and HTTP/3 have their own articles.

| Version | Introduced | Status |
|---|---|---|
| HTTP/0.9 | 1991 | Obsolete |
| HTTP/1.0 | 1996 | Obsolete |
| HTTP/1.1 | 1997 | Standard |
| HTTP/2 | 2015 | Standard |
| HTTP/3 | 2022 | Standard |

**HTTP/1.0.** Every resource request needs its **own TCP connection** to the server (RFC 1945 section 1.3).

**HTTP/1.1.** One TCP connection can be **reused for several resource requests** (HTML, frames, images, scripts, stylesheets). This cuts latency because the TCP setup cost is not paid again, which matters most under heavy traffic (RFC 9112 sections 9.1 and 9.3).

**HTTP/2** (RFC 9113 section 2) added:
- A **compressed binary representation of headers**, so headers take much less space.
- **One TCP/IP connection per server domain**, usually encrypted, instead of the 2 to 8 connections that browsers used before.
- **Bidirectional streams** within the connection. Requests and responses are split into small pieces, which largely solves **head-of-line blocking** at the HTTP level.
- **Server push**, which lets the server send data when it becomes available without the client polling.

**HTTP/3.**
- Uses **QUIC over UDP** instead of TCP, with only the IP layer below it.
- Said to improve average speed slightly and to avoid **TCP congestion stalls that block every stream**.

---

## 2. Use

- **HTTP/2** is supported by **71%** of websites (34.1% HTTP/2 alone plus 36.9% HTTP/3 with backward compatibility) and by almost all browsers (over 98% of users). Major web servers support it over **TLS** using **ALPN** (RFC 7301). TLS 1.2 or newer is required.
- **HTTP/3** is used on **40%** of websites. Browsers support it at least partially for **97%** of users. Support was first added in **2019** by **Cloudflare and Chrome**, and Firefox enabled it. It is claimed to have lower latency and, in some cases, to load **over three times faster** than HTTP/1.1. HTTP/1.1 "is still commonly the only protocol enabled".
- **HTTPS** is used by **90.1%** of websites.
- Like HTTP/2, HTTP/3 does **not obsolete** earlier major versions.

---

## 3. Technology

### 3.1 Transport layer

- HTTP **presumes a reliable transport**. **TCP** was the standard choice before HTTP/3 (RFC 9110 section 3.3). HTTP/3 uses **QUIC**, which provides reliability on top of unreliable UDP.
- HTTP/1.1 and earlier were adapted to plain UDP as **HTTPMU** (multicast) and **HTTPU** (unicast). These are used in **UPnP** and **SSDP** on local networks.

### 3.2 Data exchange

HTTP is a **stateless**, application-level protocol that needs a reliable transport connection. It runs over TCP/IP on well-known ports:
- **Port 80**: unencrypted.
- **Port 443**: encrypted (RFC 9110 sections 4.2.1 and 4.2.2).

HTTP/2 uses a single TCP/IP connection with multiple protocol channels. HTTP/3 uses QUIC over UDP.

#### 3.2.1 Request and response messages through connections

The exchange runs in this order:
1. The client opens a connection (real or virtual) to the server.
2. The server accepts it and waits for a request.
3. The client sends a request.
4. The server replies with a response: headers plus, if needed, a body. The body is typically the requested resource, but it can be an error message or other information.
5. **Either side may close the connection at any time.** Closure is usually announced by a header in the last request or response (RFC 9112 section 9.1).

#### 3.2.2 Persistent connections

| Version | Connection behavior |
|---|---|
| HTTP/0.9 | Always closed after the response. Never persistent. |
| HTTP/1.0 | Server should close after each response. An unofficial **keep-alive** extension appeared in late 1996 (see Notes). |
| HTTP/1.1 | **Keep-alive** officially introduced, so one connection carries many request/response pairs. |
| HTTP/2 | Many concurrent requests and responses **multiplexed** over one TCP/IP connection. |
| HTTP/3 | QUIC over UDP, with no TCP/IP connection. |

Benefits of persistence in 1.1:
- No **TCP three-way handshake** per request.
- TCP **slow start** makes a long-lived connection faster over time.

**Pipelining (HTTP/1.1).**
- It allows sending **several requests before reading each response**.
- It was **never considered really safe**: some servers and many proxies mishandled pipelined requests.
- Only **HEAD** and some **GET** requests (no query string, real file requests) could be pipelined safely and idempotently.
- Browsers first disabled it, then removed it, and HTTP/2 adoption made it moot.

#### 3.2.3 Content retrieval optimizations

- **HTTP/0.9:** a requested resource was **always sent in full**.
- **HTTP/1.0** added headers for client-cached resources, enabling **conditional GET**:
  - The server returns full content only if the client does not know the last-modified time, or the content changed since the last full response.
  - **Content-Encoding** says whether content is compressed.
  - For dynamic content of unknown length, `Content-Length` is omitted and the client treats the response as complete when the connection closes. A **premature close** therefore produces **undetected partial content**.
- **HTTP/1.1 and later** added:
  - Better headers for **conditional retrieval of cached resources**.
  - **Chunked transfer encoding**, to stream content of unknown length.
  - **Byte range serving**, to request part of a resource (resume downloads, show partial content).

### 3.3 Application session

- HTTP is **stateless**. The server need not keep per-user status between requests.
- Applications build sessions with **HTTP cookies**, **hidden form variables** or other mechanisms.
- **Login and logout** typically use a custom mechanism, not HTTP authentication.

### 3.4 Authentication

- HTTP supports **basic** and **digest** access authentication.
- They use **challenge-response**: the server issues a challenge before serving content.
- A general framework for **extensible challenge-response schemes** exists (RFC 9110).
- These mechanisms are part of the protocol and handled by **HTTP software**, not by web applications.
- **Realms**: an implementation-specific string combined with the canonical root URI to form the **protection space**. A server can therefore define separate authentication scopes under one root URI.

### 3.5 Encrypted connection

- The popular method is **HTTPS**.
- Two other methods exist: **Secure Hypertext Transfer Protocol (S-HTTP)**, and the HTTP/1.1 **Upgrade header** to switch to TLS. Browser support for both is **nearly non-existent**.

---

## 4. Message format

This section describes **HTTP/1.1** messages. **HTTP/2 and HTTP/3 are binary**:
- Headers are sent in a **HEADERS frame** plus zero or more **CONTINUATION frames**.
- They are compressed with **HPACK** (HTTP/2, RFC 7541) or **QPACK** (HTTP/3).
- The HTTP/1 request line and status line are replaced by **pseudo-header fields** that begin with a colon.

A message is a **header followed by a body**.

### 4.1 Header

- Lines of **ASCII text**, each ending with **CRLF**.
- Layout:
  1. A **start line**, which differs for requests and responses.
  2. Zero or more **header field lines** (at least one in HTTP/1.1).
  3. An **empty line** marking the end of the header.

### 4.2 Body

- Any format, **not limited to ASCII**.
- Must match **Content-Type** if present.
- Optional, so it can be blank.

### 4.3 Entity

Before HTTP/2, the **entity** meant the body plus its descriptive header fields, and the terms "entity header" and "entity body" were used. Modern documents just say "header" and "body".

### 4.4 Header field

Header fields carry **metadata** about the message. Examples of what they convey:
- Encoding (`Content-Encoding`).
- Session identification (cookies, IP address, user agent).
- Anonymity, such as a VPN, proxy masking, or user-agent spoofing.
- Handling instructions, such as **Do-Not-Track** and **Global Privacy Control**.
- The age of a document in a shared cache.

They are usually consumed by software and not shown to users.

**Format:** a name-value pair separated by a colon.
- No whitespace around the name. Leading and trailing whitespace on the value is ignored.
- **Field names are case-insensitive.** Method names are case-sensitive.
- Examples:
  ```
  Host: www.example.com
  Accept-Language: en
  ```
- Standards set **no limit on field size or count**, but servers do. Apache 2.3 defaults to **8190 bytes per field** and at most **100 fields** per request.
- **Line folding** (continuation lines starting with a space or tab) was **deprecated by RFC 7230**.

### 4.5 Request

A request is sent by the client. The **start line** has the method, the request URI and the protocol version, separated by single spaces:

```
GET /customer/123 HTTP/1.1
```

- Request header fields act as modifiers, like parameters of a procedure call.
- In HTTP/1.1, **all header fields except `Host` are optional**.
- A request line containing only a path is accepted for compatibility with **pre-HTTP/1.0 clients** (RFC 1945).

#### 4.5.1 Resource

HTTP treats transactions as operations on **resources**. A resource may already exist or be generated on demand, and is often a file or the output of a server-side program.

#### 4.5.2 Method

A **method** (sometimes called a verb) classifies the action to perform on a resource.

- **HTTP/1.0** defined **GET, HEAD, POST**. It listed PUT, DELETE, LINK and UNLINK as additional methods.
- **HTTP/1.1** added **PUT, DELETE, CONNECT, OPTIONS, TRACE**.
- Any client can use any method. **Unknown methods** are treated by intermediaries as **unsafe and non-idempotent**.
- There is **no limit on the number of methods**. WebDAV defined seven more, and RFC 5789 specified **PATCH**.
- A general-purpose web server **must implement at least GET and HEAD**. The rest are optional (RFC 9110 section 9.1).

**Method properties**

| Method | RFC | Request has body | Response has body | Safe | Idempotent | Cacheable |
|---|---|---|---|---|---|---|
| GET | 9110 | Optional | Yes | Yes | Yes | Yes |
| HEAD | 9110 | Optional | No | Yes | Yes | Yes |
| POST | 9110 | Yes | Yes | No | No | Yes |
| PUT | 9110 | Yes | Yes | No | Yes | No |
| DELETE | 9110 | Optional | Yes | No | Yes | No |
| CONNECT | 9110 | Optional | Yes | No | No | No |
| OPTIONS | 9110 | Optional | Yes | Yes | Yes | No |
| TRACE | 9110 | No | Yes | Yes | Yes | No |
| PATCH | 5789 | Yes | Yes | No | No | No |
| QUERY | 10008 | Yes | Yes | Yes | Yes | Yes |

**What each method does**

- **GET**: requests a representation of a resource. It should only **retrieve data** and not change state. GET is preferred over POST for retrieval because it is **URL-addressable** (bookmarking, sharing, caching). The page cites a W3C finding on GET vs POST.
- **HEAD**: like GET but with **no response body**. It is used to check that a resource is available (status code) or to learn its size from `Content-Length` without downloading it.
- **POST**: asks the server to **process** the enclosed data. Examples: posting to a forum, subscribing to a mailing list, completing a purchase.
- **PUT**: **creates or updates** a resource with the request's state. The **client specifies the target location**, which distinguishes PUT from POST.
- **DELETE**: deletes a resource.
- **CONNECT**: asks an intermediary to set up a **TCP/IP tunnel** to the origin server. Often used for **TLS through HTTP proxies**. The page cites CERT note VU#150227 about proxy default configurations that allow arbitrary TCP connections.
- **OPTIONS**: asks which methods a resource supports. `*` can be requested in place of a resource to check the server as a whole.
- **TRACE**: the server **echoes the request** it received in the body, so a client can see changes made by intermediaries. Useful for debugging.
- **PATCH**: modifies a resource with a **partial state**. Can save bandwidth compared with PUT.
- **QUERY** (RFC 10008): processes the enclosed content in a **safe and idempotent** way and returns the result. Similar to POST, but can be repeated or restarted without concern about partial state.

##### 4.5.2.1 Safe method

- A request using a **safe** method has **no intended effect on the server**.
- Safe methods: **GET, HEAD, OPTIONS, TRACE, QUERY**. They are intended as read-only.
- Safe methods can still have unseen side effects such as **logging or charging for ads**.
- **POST, PUT, DELETE, CONNECT, PATCH** are not safe, so conforming robots do not normally use them.
- A GET handler *can* make changes, but this is discouraged because **caches, search engines and bots** may trigger unintended changes. Example: a "delete" URL that is fetched with GET.
- Real incident: the **Google Web Accelerator** beta **prefetched URLs**, which altered or deleted records en masse. It was suspended a few weeks after release.

##### 4.5.2.2 Idempotent method

- A method is **idempotent** if repeating an identical request has the **same effect as sending it once**.
- **PUT, DELETE** and **all safe methods** are idempotent.
- **POST, CONNECT, PATCH** are **not necessarily** idempotent. Example: a POST that sends an email would send duplicates.
- Browsers may warn before resubmitting a POST, but this is largely left to the web application.
- The protocol **does not enforce** idempotency. A GET that inserts into a database is possible, though discouraged.

##### 4.5.2.3 Cacheable method

- **GET, HEAD and POST** are defined as cacheable.
- **PUT, DELETE, CONNECT, OPTIONS, TRACE and PATCH** are not.
- (The table above also lists QUERY as cacheable.)

### 4.6 Response

A response is sent by the server. The **start line** has the protocol version, the status code and an optional reason phrase, separated by single spaces:

```
HTTP/1.1 400 Bad Request
```

Response header fields act as modifiers. They give information about the server and about access to the resource or related resources. Each has a defined meaning that can be refined by the request method and the status code.

#### 4.6.1 Status code

A **three-digit decimal integer** describing what happened to the request. Clients act on the status code first and on the headers second.

A client **must understand the class** (the first digit). An unrecognized code is treated as the **x00** code of its class.

| Class | Meaning |
|---|---|
| 1XX | Informational: request received, processing continues |
| 2XX | Successful: request received, understood and accepted |
| 3XX | Redirection: further action is needed to complete the request |
| 4XX | Client error: the request cannot be fulfilled because of something the client may control |
| 5XX | Server error: the server failed to fulfil an apparently valid request |

The page does not list individual codes beyond the `400` example. Its sidebar mentions 301, 302, 303, 403, 404 and 451.

#### 4.6.2 Reason phrase

- Standard reason phrases are only **recommendations**. Servers may localize them.
- User agents may show them on errors, but status codes are **machine-readable** and reason phrases are **human-readable**, so programs should not interpret the phrases.

### 4.7 Worked example

An HTTP/1.1 exchange with `www.example.com` on port 80. HTTP/1.0 would use the same messages with some headers missing. HTTP/2 and HTTP/3 use the same mechanism with different header encoding.

**Request** (no body, six header fields):

```
GET / HTTP/1.1
Host: www.example.com
User-Agent: Mozilla/5.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,...
Accept-Language: en-GB,en;q=0.5
Accept-Encoding: gzip, deflate, br
Connection: keep-alive
```

- `Host` is **mandatory in HTTP/1.1** (optional in 1.0). It enables **name-based virtual hosting**.
- The minimal form is `GET / HTTP/1.1<CRLF>Host: www.example.com<CRLF><CRLF>`.

**Response:**

```
HTTP/1.1 200 OK
Date: Mon, 23 May 2005 22:38:34 GMT
Content-Type: text/html; charset=UTF-8
Content-Length: 155
Last-Modified: Wed, 08 Jan 2003 23:11:55 GMT
Server: Apache/1.3.3.7 (Unix) (Red-Hat/Linux)
ETag: "3f80f-1b6-3e1cb03b"
Accept-Ranges: bytes
Connection: close

(body: a short HTML page titled "An Example Page"
 saying "Hello World, this is a very simple HTML document.")
```

What the headers mean:
- **ETag**: lets a client check whether its cached copy matches the current resource.
- **Content-Type**: the media type of the body.
- **Content-Length**: body length in bytes.
- **Accept-Ranges: bytes**: the server supports byte serving.
- **Connection: close**: the server closes the TCP connection after this response.
- Most headers are optional. A missing `Content-Length` on a response with a body is an error in HTTP/1.0. In HTTP/1.1 it can be acceptable if `Transfer-Encoding: chunked` is used, where a chunk of size 0 marks the end.
- Some old HTTP/1.0 implementations omitted `Content-Length` and relied on the server closing the socket.
- `Content-Encoding: gzip` would mean the body is gzip-compressed.

---

## 5. Similar protocols

- **Gopher**: a content-delivery protocol displaced by HTTP in the early 1990s.
- **SPDY**: an alternative developed at Google, later superseded by HTTP/2.
- **Gemini**: inspired by Gopher, and mandates privacy-related features.

---

## 6. See also

Comparison of file transfer protocols · Constrained Application Protocol (CoAP) · Content negotiation · Digest access authentication · InterPlanetary File System (IPFS) · HTTP compression · Representational state transfer (REST) · Variant object · Web cache · WebSocket · Wireless Application Protocol (WAP, deprecated)

## 7. Notes

1. HTTP/2 streams act as multiple TCP/IP sub-connections that multiplex requests and responses. This reduces real connections on the server side from **2 to 8 per client down to 1**, so a server can handle more clients at once.
2. From late **1996**, some developers of HTTP/1.0 browsers and servers, especially those planning HTTP/1.1 support, deployed an **unofficial keep-alive** mechanism using new headers.

## 8. References (key items; the page lists 70)

**HTTP specifications**

| Document | Notes |
|---|---|
| RFC 9110 | HTTP Semantics, STD 97 (June 2022). Obsoletes 2818, 7230, 7231, 7232, 7233, 7235, 7538, 7615, 7694; updates 3864 |
| RFC 9111 | HTTP Caching, STD 98. Obsoletes 7234 |
| RFC 9112 | HTTP/1.1, STD 99. Obsoletes 7230 |
| RFC 9113 | HTTP/2. Obsoletes 8740 and 7540 |
| RFC 9114 | HTTP/3 |
| RFC 9204 | QPACK |
| RFC 9218 | Extensible Prioritization Scheme for HTTP |
| RFC 7540 | HTTP/2 (original), obsolete |
| RFC 7541 | HPACK |
| RFC 7230 to 7235 | June 2014 HTTP/1.1 split, all obsolete |
| RFC 2616 | HTTP/1.1, obsolete. Obsoletes 2068; obsoleted by 7230-7235 |
| RFC 2068 | HTTP/1.1 (January 1997), obsolete |
| RFC 1945 | HTTP/1.0 (May 1996), Informational |
| RFC 3986 | URI: Generic Syntax, STD 66 |
| RFC 7301 | TLS ALPN extension |
| RFC 5789 | PATCH method, Proposed Standard |
| RFC 10008 | The HTTP QUERY Method (June 2026), Proposed Standard |

**Other sources:** W3Techs usage statistics (HTTP/2, HTTP/3, HTTPS); caniuse.com support tables; Cloudflare and ZDNet articles on HTTP/3 support (September 2019); Google's SPDY whitepaper (2009); the HTTPbis rechartering notices (2012); the Blink "Intent to Deprecate and Remove: HTTP/0.9 Support" (2016); US-CERT note VU#150227; Berners-Lee's original HTTP documents (1991 and 1992); Gourley et al., *HTTP: The Definitive Guide* (2002); Ediger, *Advanced Rails* (2007); Cantrell on Google Web Accelerator (2005).

## 9. External links

- httpwg.org/specs/ (official site)
- IETF HTTP Working Group on GitHub (github.com/httpwg)
- W3C "Change History for HTTP"
- W3C "Design Issues for HTTP" (Berners-Lee)
- Wikibooks: Communication Networks/HTTP Protocol
- Wikimedia Commons: Hypertext Transfer Protocol category
