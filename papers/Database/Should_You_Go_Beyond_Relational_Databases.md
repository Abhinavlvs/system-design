Source: https://blog.teamtreehouse.com/should-you-go-beyond-relational-databases

# Should You Go Beyond Relational Databases?

Notes on the Treehouse Blog article of the same name (published 16 December 2024, category "Learn", about 7 minutes to read; the page shows a later "last updated" date of 12 May 2026). These notes are a paraphrased summary in the article's order, not a copy. The article's promotional passages (ETL tool, API platform, free trial) are left out.

---

## Main idea

Relational databases (MySQL, PostgreSQL and commercial products) have been the foundation for decades and are reliable and well supported. The article asks whether the relational model is still the best choice for every application. Its answer is "it depends": check how your current database is behaving before making drastic changes, because many applications run well on relational databases for years.

---

## 1. Signs you may be pushing a relational database to its limits

### 1.1 Structural symptoms

1. **Sparse tables:** tables with many columns that are mostly empty or irrelevant for most rows.
2. **Attribute tables:** tables that store (foreign key, attribute name, attribute value) triples, which force complex joins to rebuild an object.
3. **Serialized blobs:** structured data stored as JSON, XML or YAML inside one column because the schema cannot represent it.
4. **Heavy relationship modelling:** many-to-many join tables, or recursive foreign keys that model trees.
5. **Constant schema changes** to represent new kinds of data.

### 1.2 Scalability symptoms

1. You reach the **write capacity of a single server**. (For read-heavy problems, replication or caching may be enough instead.)
2. The **dataset is too large** for one server.
3. **Batch or analytical jobs** slow down the transactional workload.

If several of these appear, the article suggests looking at other database models.

---

## 2. Non-relational databases: overview

NoSQL databases multiplied over the past decade to address the limits above.

| Type | How it works | Examples | Best for | Key features |
|---|---|---|---|---|
| **Key-value store** | Like a hash table: insert and fetch a value by its unique key | Redis, DynamoDB, Aerospike | Caching, session storage, user preferences | Low latency, high throughput, horizontal scaling |
| **Document database** | Stores semi-structured documents (JSON or BSON) with a flexible schema | MongoDB, Couchbase | Content management, product catalogs, user profiles | Querying and indexing fields inside documents |
| **Column-family store** | Groups data by column families rather than rows | Apache Cassandra, HBase | Large-scale analytics, high-write workloads such as event logs and time series | Built for heavy writes at scale |
| **Graph database** | Stores nodes and relationships directly. The article says relational databases struggle with variable-length chains of relationships | Neo4j, Amazon Neptune, ArangoDB | Social networks, recommendations, fraud detection, knowledge graphs | Transitive queries (friend of a friend), many-to-many and hierarchical data, query languages such as Cypher and Gremlin |
| **Bigtable-inspired** | Based on Google's Bigtable: sparse, wide-column data where only non-empty values are stored | Google Bigtable, Cassandra, HBase | IoT, time series, analytics | Schema-less design that suits evolving datasets |
| **Distributed key-value store** | Key-value storage spread across many nodes | DynamoDB, Azure Cosmos DB, ScyllaDB | Large applications needing low latency on massive data (e-commerce, gaming, IoT) | Automatic partitioning and replication, transparent sharding, eventual consistency with optional strict consistency for some operations |

**Trade-off note:** balance latency against throughput, and remember the **CAP theorem**: of consistency, availability and partition tolerance, you can prioritize only two.

---

## 3. MapReduce and batch processing

- **MapReduce** processes large datasets in parallel using divide and conquer: split the work (map), then combine the partial results (reduce). It was popularized by Google.
- **Examples:** Apache Hadoop, Apache Spark.
- **Best for:** log analysis, ETL (moving and transforming data between systems), machine-learning workflows.
- **Features:** works with distributed storage such as HDFS or Amazon S3.
- CouchDB and MongoDB also offer smaller-scale MapReduce-style aggregation inside the database.

---

## 4. Choosing the right database

The article gives five factors:

1. **Data structure:** rows and columns fit relational databases. Hierarchical, sparse or highly interconnected data points toward document or graph databases.
2. **Scalability:** relational databases scale vertically (bigger server) and by sharding, but with limits. For massive scale, consider Cassandra or DynamoDB.
3. **Query patterns:** key-value for simple lookups by key, graph for complex relationships, document for flexible queries on semi-structured data.
4. **Operational complexity:** relational databases have mature ecosystems and are easier to manage. Non-relational systems often need specialized skills.
5. **Developer experience:** SQL is widely known, so consider the skills your team already has.

---

## 5. Trends

- **Multi-model databases:** systems such as PostgreSQL and ArangoDB support several models (relational, document, graph) in one product.
- **Serverless databases:** services on AWS and Azure that scale and manage infrastructure automatically.
- **AI-driven query optimization:** emerging databases that use AI to tune queries dynamically. No products are named.

---

## 6. Final thoughts

Relational databases are not obsolete. They remain robust, mature and versatile, but they are not a one-size-fits-all answer. Evaluate alternatives when your needs change in scale, data structure or performance. The best database is the one that fits current and future needs while balancing complexity, cost and performance.

---

## About the page's comments

The page shows 39 reader comments, all dated 2009, apparently carried over from an older version of the post. They are the commenters' opinions and are not verified. Examples:
- Standard SQL supports recursive queries (`WITH RECURSIVE`), and several relational databases implement them. This is relevant to the article's "recursive foreign keys" warning sign.
- A bank would be a poor fit for a document store.
- Other systems commenters said were missed: Berkeley DB, Persevere, db4o, Jackrabbit, CouchDB, in-memory data grids, EMC xDB.
