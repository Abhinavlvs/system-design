# gRPC vs HTTPS

Sourcing note: general networking knowledge, not taken from the Wikipedia pages.

---

## 1. They are not alternatives at the same level

**HTTPS** is HTTP wrapped in TLS, so it is about how the connection is secured. **gRPC** is an RPC framework that sits on top of HTTP/2. A typical gRPC call is itself carried over an HTTPS-style connection (HTTP/2 inside TLS).

```
REST / JSON API          gRPC
HTTP/1.1 or HTTP/2       HTTP/2
TLS                      TLS
TCP                      TCP
```

On both sides, TLS is what makes it "HTTPS". The difference is in the layers above.

gRPC runs over **HTTP/2 specifically**, not over HTTP in general:
- It needs HTTP/2 features: multiplexed streams (one per call), trailers (where the gRPC status code goes), and binary framing. HTTP/1.1 cannot provide them.
- HTTP/3 runs over QUIC on UDP, so a gRPC-over-HTTP/3 setup would not be over TCP. The standard, widely deployed form is HTTP/2 over TCP.

---

## 2. The real comparison: gRPC vs REST/JSON over HTTPS

| | REST/JSON over HTTPS | gRPC |
|---|---|---|
| What it is | An architectural style over plain HTTP | A framework with a defined protocol, schema and generated code |
| HTTP version | 1.1, 2 or 3 | HTTP/2 only |
| Body format | Usually JSON (text), your choice | Protocol Buffers (binary) |
| Contract | Optional (OpenAPI is separate) | Required: a `.proto` file defines services and messages |
| How you call it | Build a URL, pick a method, parse the response | Call a generated function like a local method (`client.GetUser(id)`) |
| Addressing | Resources and URLs (`GET /users/42`) | One method per call (`POST /pkg.UserService/GetUser`) |
| Streaming | Awkward (SSE, WebSocket, chunking) | Built in: server, client and bidirectional streaming |
| Errors | HTTP status codes (404, 500) | gRPC status codes (returned in HTTP/2 trailers) |
| Browsers | Work natively | Need gRPC-Web and a proxy |
| Debugging | Easy: `curl`, readable text | Harder: binary, needs tools like `grpcurl` |
| Typical use | Public APIs, browser apps | Service-to-service calls inside a system |

---

## 3. What this means in practice

- **Security:** both get encryption, integrity and server authentication from TLS. gRPC also supports mutual TLS and token-based auth.
- **Speed:** gRPC is usually smaller and faster to parse because of binary Protocol Buffers and HTTP/2 multiplexing. REST over HTTP/2 with JSON gets the multiplexing but not the compact encoding.
- **Compatibility:** REST works with any client that can send HTTP. gRPC needs a gRPC client library and the `.proto` file.
- **Load balancing:** gRPC reuses one long-lived HTTP/2 connection for many calls, so a layer 4 balancer can pin them all to one backend. Use an HTTP/2-aware balancer or client-side balancing (see `L4_Load_Balancers.md` and `Protocols_By_Layer.md`).

---

## Related notes

- `HTTPS.md`: how TLS wraps HTTP.
- `HTTP.md`: HTTP versions and message format.
- `Protocols_By_Layer.md`: where gRPC fits among the other protocols.
- `Running_Over_TCP.md`: serialization, binary protocols and what "over TCP" means.
