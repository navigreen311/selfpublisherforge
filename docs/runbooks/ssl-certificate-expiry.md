# Runbook: SSL Certificate Expiry

## Alert

| Field       | Value                                                                   |
|-------------|-------------------------------------------------------------------------|
| Alert Name  | *(No dedicated Prometheus alert currently defined -- proactive monitoring)* |
| Severity    | **P1 -- Urgent** (< 7 days to expiry) / **P2 -- Warning** (< 30 days)  |
| Service     | `infrastructure`                                                        |
| Environment | `production`                                                            |

This runbook covers SSL/TLS certificate management for SelfPublisherForge. While no Prometheus alert rule currently exists in `alerts.yml` for certificate expiry, this runbook provides procedures for certificate monitoring, renewal, and emergency replacement.

**Recommendation:** Add a Prometheus blackbox exporter probe or a custom metric to alert on certificate expiry. See the "Preventive Measures" section below.

## Impact

- **Expired certificate**: All HTTPS connections fail. Browsers display security warnings and refuse to load the site. API clients reject TLS connections. The service is effectively down for all users, equivalent to a P0 outage.
- **Near-expiry certificate (< 7 days)**: No immediate user impact, but high risk of total outage if renewal does not complete before expiration.
- **Certificate mismatch or invalid chain**: Intermittent TLS errors depending on client TLS library behavior. Some clients may connect successfully while others fail.

## Domains Covered

| Domain                           | Certificate Source | Renewal   |
|----------------------------------|--------------------|-----------|
| `selfpublisherforge.com`         | AWS ACM            | Automatic |
| `*.selfpublisherforge.com`       | AWS ACM (wildcard) | Automatic |
| `api.selfpublisherforge.com`     | AWS ACM            | Automatic |
| `app.selfpublisherforge.com`     | AWS ACM            | Automatic |
| `flower.selfpublisherforge.com`  | AWS ACM            | Automatic |
| `status.selfpublisherforge.com`  | AWS ACM            | Automatic |

## Investigation

### 1. Check ACM certificate status

```bash
# List all certificates in ACM
aws acm list-certificates \
  --query 'CertificateSummaryList[].{
    Domain: DomainName,
    Status: Status,
    ARN: CertificateArn
  }' --output table

# Get detailed information for the primary certificate
aws acm describe-certificate \
  --certificate-arn <certificate-arn> \
  --query 'Certificate.{
    DomainName: DomainName,
    SubjectAlternativeNames: SubjectAlternativeNames,
    Status: Status,
    NotBefore: NotBefore,
    NotAfter: NotAfter,
    Type: Type,
    RenewalEligibility: RenewalEligibility,
    InUseBy: InUseBy,
    RenewalSummary: RenewalSummary
  }'
```

### 2. Check certificate expiry from the live endpoint

```bash
# Check expiry dates for the API domain
echo | openssl s_client -servername api.selfpublisherforge.com \
  -connect api.selfpublisherforge.com:443 2>/dev/null \
  | openssl x509 -noout -dates -subject -issuer

# Check expiry dates for the main domain
echo | openssl s_client -servername selfpublisherforge.com \
  -connect selfpublisherforge.com:443 2>/dev/null \
  | openssl x509 -noout -dates -subject -issuer

# Calculate days remaining until expiry
EXPIRY=$(echo | openssl s_client -servername api.selfpublisherforge.com \
  -connect api.selfpublisherforge.com:443 2>/dev/null \
  | openssl x509 -noout -enddate | cut -d= -f2)
DAYS_LEFT=$(( ($(date -d "$EXPIRY" +%s) - $(date +%s)) / 86400 ))
echo "Certificate expires: $EXPIRY"
echo "Days remaining: $DAYS_LEFT"
```

### 3. Verify the certificate chain

```bash
# Check the full certificate chain for completeness
echo | openssl s_client -servername api.selfpublisherforge.com \
  -connect api.selfpublisherforge.com:443 -showcerts 2>/dev/null \
  | openssl x509 -noout -text | grep -A2 "Validity"

# Quick connectivity check
curl -sI https://api.selfpublisherforge.com 2>&1 | head -5

# Verbose TLS handshake (useful for diagnosing chain issues)
curl -vI https://api.selfpublisherforge.com 2>&1 | grep -E "SSL|certificate|expire|issuer"
```

### 4. Check ACM DNS validation records

```bash
# If the certificate is pending validation or renewal failed,
# verify the DNS validation CNAME records are in place
aws acm describe-certificate \
  --certificate-arn <certificate-arn> \
  --query 'Certificate.DomainValidationOptions[].{
    Domain: DomainName,
    ValidationStatus: ValidationStatus,
    ValidationMethod: ValidationMethod,
    CNAMEName: ResourceRecord.Name,
    CNAMEValue: ResourceRecord.Value
  }' --output table

# Verify the CNAME record exists in Route 53
aws route53 list-resource-record-sets \
  --hosted-zone-id <hosted-zone-id> \
  --query "ResourceRecordSets[?Type=='CNAME' && starts_with(Name, '_')]" \
  --output table
```

### 5. Check ALB listener configuration

```bash
# Verify the ALB is using the correct certificate
aws elbv2 describe-listeners \
  --load-balancer-arn <alb-arn> \
  --query 'Listeners[?Protocol==`HTTPS`].{
    Port: Port,
    CertificateArn: Certificates[0].CertificateArn,
    SslPolicy: SslPolicy
  }' --output table
```

## Resolution

### ACM auto-renewal has failed

AWS ACM automatically renews certificates that are DNS-validated, in `ISSUED` status, and associated with an AWS resource (ALB, CloudFront, etc.).

1. **Check the renewal status:**
   ```bash
   aws acm describe-certificate \
     --certificate-arn <certificate-arn> \
     --query 'Certificate.RenewalSummary'
   ```

2. **Fix: DNS validation CNAME is missing**
   ```bash
   # Get the required validation record
   aws acm describe-certificate \
     --certificate-arn <certificate-arn> \
     --query 'Certificate.DomainValidationOptions[0].ResourceRecord'

   # Add the CNAME record to Route 53
   aws route53 change-resource-record-sets \
     --hosted-zone-id <hosted-zone-id> \
     --change-batch '{
       "Changes": [{
         "Action": "UPSERT",
         "ResourceRecordSet": {
           "Name": "<validation-cname-name>",
           "Type": "CNAME",
           "TTL": 300,
           "ResourceRecords": [{"Value": "<validation-cname-value>"}]
         }
       }]
     }'
   ```

3. **Fix: Certificate not associated with any AWS resource**
   - Attach it to the ALB listener (see step 5 of Investigation).
   - ACM only auto-renews certificates that are in use.

4. **Fix: Email validation (legacy)**
   - Respond to the validation email sent to the domain admin contacts.
   - Better: re-issue the certificate with DNS validation instead.

### Emergency: Certificate has already expired

1. **Request a new certificate immediately:**
   ```bash
   NEW_CERT_ARN=$(aws acm request-certificate \
     --domain-name selfpublisherforge.com \
     --subject-alternative-names "*.selfpublisherforge.com" \
     --validation-method DNS \
     --output text \
     --query 'CertificateArn')
   echo "New certificate ARN: $NEW_CERT_ARN"
   ```

2. **Complete DNS validation:**
   ```bash
   # Wait a few seconds for ACM to generate validation records
   sleep 10

   # Get the validation CNAME records
   aws acm describe-certificate \
     --certificate-arn $NEW_CERT_ARN \
     --query 'Certificate.DomainValidationOptions[].ResourceRecord'

   # Add each CNAME to Route 53 (repeat for each domain/SAN)
   aws route53 change-resource-record-sets \
     --hosted-zone-id <hosted-zone-id> \
     --change-batch '{
       "Changes": [{
         "Action": "UPSERT",
         "ResourceRecordSet": {
           "Name": "<cname-name>",
           "Type": "CNAME",
           "TTL": 300,
           "ResourceRecords": [{"Value": "<cname-value>"}]
         }
       }]
     }'
   ```

3. **Wait for validation** (typically 5-15 minutes with DNS):
   ```bash
   aws acm wait certificate-validated --certificate-arn $NEW_CERT_ARN
   echo "Certificate validated successfully"
   ```

4. **Update the ALB listener to use the new certificate:**
   ```bash
   aws elbv2 modify-listener \
     --listener-arn <https-listener-arn> \
     --certificates CertificateArn=$NEW_CERT_ARN
   ```

5. **Verify the new certificate is being served:**
   ```bash
   echo | openssl s_client -servername api.selfpublisherforge.com \
     -connect api.selfpublisherforge.com:443 2>/dev/null \
     | openssl x509 -noout -dates -subject

   curl -sI https://api.selfpublisherforge.com | head -3
   ```

### Preventive measures

1. **Never delete DNS validation CNAME records.** They must remain in place permanently for auto-renewal to work.

2. **Add a CloudWatch alarm for certificate expiry:**
   ```bash
   aws cloudwatch put-metric-alarm \
     --alarm-name "ACM-Certificate-Expiry-30days" \
     --namespace AWS/CertificateManager \
     --metric-name DaysToExpiry \
     --dimensions Name=CertificateArn,Value=<certificate-arn> \
     --comparison-operator LessThanThreshold \
     --threshold 30 \
     --evaluation-periods 1 \
     --period 86400 \
     --statistic Minimum \
     --alarm-actions <sns-topic-arn>
   ```

3. **Add a Prometheus blackbox exporter probe** to monitor certificate expiry:
   ```yaml
   # prometheus.yml scrape config addition
   - job_name: 'tls-expiry'
     metrics_path: /probe
     params:
       module: [tls_connect]
     static_configs:
       - targets:
           - api.selfpublisherforge.com:443
           - selfpublisherforge.com:443
     relabel_configs:
       - source_labels: [__address__]
         target_label: __param_target
       - source_labels: [__param_target]
         target_label: instance
       - target_label: __address__
         replacement: blackbox-exporter:9115
   ```

4. **Add a Prometheus alert rule** for certificate expiry:
   ```yaml
   - alert: SSLCertificateExpiringSoon
     expr: probe_ssl_earliest_cert_expiry - time() < 86400 * 30
     for: 1h
     labels:
       severity: P2
     annotations:
       summary: "SSL certificate for {{ $labels.instance }} expires in less than 30 days"
       runbook_url: "docs/runbooks/ssl-certificate-expiry.md"
   ```

## Escalation

| Condition                                     | Escalate To                         |
|-----------------------------------------------|-------------------------------------|
| Certificate expired, site unreachable          | Infrastructure Lead (immediate)     |
| ACM renewal failing for unknown reason         | AWS Support                         |
| DNS validation records missing from Route 53   | DNS/Domain administrator            |
| Certificate mismatch or chain issues           | Infrastructure Lead                 |
| Wildcard certificate scope needs expansion     | Infrastructure Lead + Security Lead |
| Domain registrar issues blocking validation    | Domain administrator + Legal        |

### Communication

- If the certificate has expired: treat as a **P0 outage**. Update the status page and post in `#incidents` immediately.
- Notify users via email and social media if the outage is expected to last more than 15 minutes.
- After resolution, conduct a post-incident review to ensure monitoring is in place to prevent recurrence.
