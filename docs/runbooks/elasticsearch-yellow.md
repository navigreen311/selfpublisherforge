# ElasticsearchClusterHealthYellow Runbook

## Alert
**Name**: ElasticsearchClusterHealthYellow
**Severity**: P2
**Fires when**: The Elasticsearch cluster health status is YELLOW for any `selfpublisherforge` cluster, sustained for 30 minutes.

## Impact
One or more replica shards in the Elasticsearch cluster are unassigned. All primary shards are assigned, so data is available and search functionality works normally. However, data redundancy is reduced, meaning the cluster cannot tolerate additional node failures without potential data loss or transitioning to RED status.

## Investigation Steps
1. Check cluster health: `curl -s <elasticsearch-host>:9200/_cluster/health?pretty`. Note `unassigned_shards` and `relocating_shards`.
2. Identify which indexes have unassigned replica shards: `curl -s <elasticsearch-host>:9200/_cat/shards?v&h=index,shard,prirep,state,unassigned.reason | grep UNASSIGNED`.
3. Check allocation explanation: `curl -s <elasticsearch-host>:9200/_cluster/allocation/explain?pretty` to understand why replicas cannot be assigned.
4. Review node status and available resources: `curl -s <elasticsearch-host>:9200/_cat/nodes?v&h=name,heap.percent,ram.percent,cpu,disk.avail,node.role`.
5. Check if the cluster is in the process of recovering (e.g., after a node restart). The `initializing_shards` count will be non-zero during recovery.

## Resolution
### Common Causes
- **Node recently restarted**: After a node restart, replicas need time to resynchronize. Monitor the `initializing_shards` count. If it is decreasing, the cluster is recovering on its own.
- **Insufficient nodes for replica count**: If the number of replicas exceeds the number of available nodes minus one, some replicas cannot be assigned. Add more nodes or reduce the replica count: `curl -X PUT <elasticsearch-host>:9200/<index>/_settings -H 'Content-Type: application/json' -d '{"index":{"number_of_replicas":1}}'`.
- **Disk watermark exceeded on some nodes**: Nodes with high disk usage cannot receive new shard allocations. Free disk space or add storage.
- **Shard awareness zone imbalance**: If using zone-aware allocation, an imbalance in node count across zones can prevent replica assignment. Ensure equal node distribution across zones.
- **Cluster recovering after scaling event**: After adding or removing nodes, the cluster rebalances shards. This is normal and the cluster should return to GREEN once rebalancing completes.

## Escalation
- **P0/P1**: Page on-call engineer immediately
- **P2**: Create ticket, address within 4 hours
- **P3**: Create ticket, address within 24 hours

## Prevention
- Maintain at least one more node than the maximum replica count to ensure all replicas can be assigned.
- Monitor disk usage on all Elasticsearch nodes and scale storage proactively.
- Configure delayed allocation to avoid unnecessary shard reallocation during brief node restarts: `index.unassigned.node_left.delayed_timeout`.
- Distribute nodes evenly across availability zones for zone-aware deployments.
- Regularly review index settings and replica counts to ensure they match the current cluster topology.
