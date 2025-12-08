const dns = require('dns');

console.log("Attempting to resolve SRV record for: _mongodb._tcp.cluster1.z7q6q.mongodb.net");

dns.resolveSrv('_mongodb._tcp.cluster1.z7q6q.mongodb.net', (err, addresses) => {
    if (err) {
        console.error("❌ DNS Resolution Failed:");
        console.error(err);
    } else {
        console.log("✅ DNS Resolution SUCCESS:");
        console.log(addresses);
    }
});
