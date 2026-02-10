# ElasticsearchClusterHealthRed Runbook

## Alert
**Name**: ElasticsearchClusterHealthRed
**Severity**: P1
**Fires when**: The Elasticsearch cluster health status is RED for any `selfpublisherforge` cluster, sustained for 5 minutes.

## Impact
One or more primary shards in the Elasticsearch cluster are unassigned. This means some data is unavailable and search functionality may be partially or completely broken. Users may experience failed search queries, missing search results, or degraded search performance.

## Investigation Steps
1. Check cluster health and identify unassigned shards: `curl -s <elasticsearch-host>:9200/_cluster/health?pretty`. Note `unassigned_shards` and `number_of_pending_tasks`.
2. Identify which indexes have unassigned primary shards: `curl -s <elasticsearch-host>:9200/_cat/shards?v&h=index,shard,prirep,state,unassigned.reason | grep UNASSIGNED`.
3. Check the reason for unassigned shards: `curl -s <elasticsearch-host>:9200/_cluster/allocation/explain?pretty`. This shows why the cluster cannot allocate the shard.
4. Review Elasticsearch node status: `curl -s <elasticsearch-host>:9200/_cat/nodes?v&h=name,heap.percent,ram.percent,cpu,disk.avail,node.role`. Check for nodes that are down or resource-constrained.
5. Check Elasticsearch logs for errors related to shard allocation, disk watermarks, or node failures.

## Resolution
### Common Causes
- **Node failure**: One or more Elasticsearch nodes have gone down, taking their primary shards offline. Restart the failed nodes or add replacement nodes. Once nodes rejoin, shards will be automatically reallocated.
- **Disk watermark exceeded**: Elasticsearch stops allocating shards when disk usage exceeds the high watermark (default 90%). Free disk space or increase disk capacity, then reset the watermark: `curl -X PUT <elasticsearch-host>:9200/_cluster/settings -H 'Content-Type: application/json' -d '{"transient":{"cluster.routing.allocation.disk.watermark.flood_stage":"95%"}}'`.
- **Corrupted shard**: If a shard is corrupted and cannot be recovered, you may need to delete the affected index and reindex the data from the source database.
- **Cluster configuration issue**: Check cluster settings for allocation filters or awareness attributes that may prevent shard allocation. Reset problematic settings.
- **Insufficient nodes for replication**: If the cluster has fewer nodes than the replication factor requires, reduce the number of replicas or add more nodes.

## Escalation
- **P0/P1**: Page on-call engineer immediately
- **P2**: Create ticket, address within 4 hours
- **P3**: Create ticket, address within 24 hours

## Prevention
- Deploy Elasticsearch with at least 3 nodes for high availability.
- Monitor disk usage and set up alerts before reaching the high watermark.
- Configure automated snapshots to S3 for data recovery.
- Use index lifecycle management (ILM) to automatically manage index size and retention.
- Regularly test Elasticsearch disaster recovery procedures.
