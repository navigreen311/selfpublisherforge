"""Amazon Ads API client for campaign management, keyword targeting, bid management, and reporting.

Integrates with the Amazon Advertising API v3 using OAuth2 refresh-token flow.
Credentials are read from environment variables:
  AMAZON_ADS_CLIENT_ID, AMAZON_ADS_CLIENT_SECRET,
  AMAZON_ADS_REFRESH_TOKEN, AMAZON_ADS_PROFILE_ID
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from uuid import UUID

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Maximum number of times to poll a report before giving up
_REPORT_POLL_MAX_ATTEMPTS = 30
_REPORT_POLL_INTERVAL_SECONDS = 2


class AmazonAdsError(Exception):
    """Raised when an Amazon Ads API call fails."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Amazon Ads API error {status_code}: {detail}")


class AmazonAdsClient:
    """Client for interacting with Amazon Advertising API.

    Supports:
    - Sponsored Products campaigns
    - Sponsored Brands campaigns
    - Sponsored Display campaigns
    - Keyword targeting and bid management
    - Performance reporting
    """

    BASE_URL = "https://advertising-api.amazon.com"
    API_VERSION = "v3"
    TOKEN_URL = "https://api.amazon.com/auth/o2/token"

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        refresh_token: str | None = None,
        profile_id: str | None = None,
        region: str = "NA",
    ):
        self.client_id = client_id or os.environ.get("AMAZON_ADS_CLIENT_ID", "")
        self.client_secret = client_secret or os.environ.get("AMAZON_ADS_CLIENT_SECRET", "")
        self.refresh_token = refresh_token or os.environ.get("AMAZON_ADS_REFRESH_TOKEN", "")
        self.profile_id = profile_id or os.environ.get("AMAZON_ADS_PROFILE_ID", "")
        self.region = region
        self._access_token: str | None = None
        self._token_expiry: datetime | None = None

    @property
    def _is_configured(self) -> bool:
        """Return True when all required credentials are present."""
        return bool(
            self.client_id
            and self.client_secret
            and self.refresh_token
            and self.profile_id
        )

    async def _get_headers(self) -> dict[str, str]:
        """Build request headers with auth token."""
        return {
            "Amazon-Advertising-API-ClientId": self.client_id,
            "Amazon-Advertising-API-Scope": self.profile_id,
            "Authorization": f"Bearer {self._access_token or ''}",
            "Content-Type": "application/vnd.spCampaign.v3+json",
            "Accept": "application/vnd.spCampaign.v3+json",
        }

    async def _refresh_access_token(self) -> None:
        """Refresh the OAuth2 access token."""
        if not self.refresh_token:
            logger.warning("No refresh token configured for Amazon Ads")
            return

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
            )
            if response.status_code == 200:
                data = response.json()
                self._access_token = data["access_token"]
                self._token_expiry = datetime.now(timezone.utc)
                logger.info("Amazon Ads access token refreshed")
            else:
                logger.error(f"Failed to refresh Amazon Ads token: {response.text}")
                raise AmazonAdsError(response.status_code, response.text)

    async def _ensure_auth(self) -> None:
        """Ensure we have a valid access token."""
        if not self._access_token or (
            self._token_expiry
            and (datetime.now(timezone.utc) - self._token_expiry).seconds > 3000
        ):
            await self._refresh_access_token()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | list | None = None,
        params: dict | None = None,
        headers_override: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Execute an authenticated request against the Amazon Advertising API.

        Raises AmazonAdsError on non-2xx responses.
        """
        await self._ensure_auth()
        headers = await self._get_headers()
        if headers_override:
            headers.update(headers_override)

        url = f"{self.BASE_URL}/{path.lstrip('/')}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.request(
                method,
                url,
                json=json,
                params=params,
                headers=headers,
            )

        if response.status_code >= 400:
            logger.error(
                "Amazon Ads API %s %s returned %s: %s",
                method,
                url,
                response.status_code,
                response.text,
            )
            raise AmazonAdsError(response.status_code, response.text)

        return response

    # ─── Campaign Management ─────────────────────────────────────────────

    async def create_campaign(
        self,
        name: str,
        campaign_type: str,
        daily_budget: float,
        start_date: str | None = None,
        targeting_type: str = "manual",
    ) -> dict:
        """Create a Sponsored Products campaign on Amazon.

        Returns a dict with the external campaign ID and status.
        """
        logger.info(f"Creating Amazon Ads campaign: {name}")

        if not self._is_configured:
            logger.warning(
                "Amazon Ads credentials not configured; returning degraded response"
            )
            return {
                "external_campaign_id": None,
                "status": "draft",
                "campaign_type": campaign_type,
                "daily_budget": daily_budget,
                "created": False,
                "error": "Amazon Ads credentials are not configured",
            }

        effective_start = start_date or datetime.now(timezone.utc).strftime("%Y%m%d")

        payload = {
            "campaigns": [
                {
                    "name": name,
                    "campaignType": "sponsoredProducts",
                    "targetingType": targeting_type.upper(),
                    "state": "enabled",
                    "dailyBudget": daily_budget,
                    "startDate": effective_start.replace("-", ""),
                    "bidding": {
                        "strategy": "LEGACY_FOR_SALES",
                    },
                }
            ]
        }

        try:
            response = await self._request(
                "POST",
                "sp/campaigns",
                json=payload,
            )
            data = response.json()

            # The API returns a "campaigns" wrapper with "success" / "error" lists
            successes = data.get("campaigns", {}).get("success", [])
            errors = data.get("campaigns", {}).get("error", [])

            if successes:
                created = successes[0]
                return {
                    "external_campaign_id": str(created.get("campaignId", "")),
                    "status": created.get("state", "enabled"),
                    "campaign_type": campaign_type,
                    "daily_budget": daily_budget,
                    "created": True,
                }

            error_detail = errors[0] if errors else data
            logger.error("Amazon Ads campaign creation failed: %s", error_detail)
            return {
                "external_campaign_id": None,
                "status": "draft",
                "campaign_type": campaign_type,
                "daily_budget": daily_budget,
                "created": False,
                "error": str(error_detail),
            }

        except AmazonAdsError as exc:
            logger.error("Amazon Ads create_campaign error: %s", exc)
            return {
                "external_campaign_id": None,
                "status": "draft",
                "campaign_type": campaign_type,
                "daily_budget": daily_budget,
                "created": False,
                "error": exc.detail,
            }

    async def update_campaign(
        self,
        external_campaign_id: str,
        updates: dict,
    ) -> dict:
        """Update an existing Amazon Ads campaign."""
        logger.info(f"Updating Amazon Ads campaign: {external_campaign_id}")

        if not self._is_configured:
            logger.warning("Amazon Ads credentials not configured; skipping update")
            return {
                "external_campaign_id": external_campaign_id,
                "updated": False,
                "changes": updates,
                "error": "Amazon Ads credentials are not configured",
            }

        # Map internal field names to Amazon API field names
        campaign_update: dict = {"campaignId": external_campaign_id}
        field_map = {
            "status": "state",
            "daily_budget": "dailyBudget",
            "name": "name",
            "end_date": "endDate",
        }
        for internal_key, api_key in field_map.items():
            if internal_key in updates:
                campaign_update[api_key] = updates[internal_key]

        try:
            response = await self._request(
                "PUT",
                "sp/campaigns",
                json={"campaigns": [campaign_update]},
            )
            data = response.json()
            successes = data.get("campaigns", {}).get("success", [])
            return {
                "external_campaign_id": external_campaign_id,
                "updated": bool(successes),
                "changes": updates,
            }
        except AmazonAdsError as exc:
            logger.error("Amazon Ads update_campaign error: %s", exc)
            return {
                "external_campaign_id": external_campaign_id,
                "updated": False,
                "changes": updates,
                "error": exc.detail,
            }

    async def pause_campaign(self, external_campaign_id: str) -> dict:
        """Pause an Amazon Ads campaign."""
        return await self.update_campaign(
            external_campaign_id, {"status": "paused"}
        )

    async def resume_campaign(self, external_campaign_id: str) -> dict:
        """Resume a paused Amazon Ads campaign."""
        return await self.update_campaign(
            external_campaign_id, {"status": "enabled"}
        )

    # ─── Keyword & Bid Management ────────────────────────────────────────

    async def add_keywords(
        self,
        external_campaign_id: str,
        keywords: list[dict],
    ) -> list[dict]:
        """Add keywords to a campaign with bids.

        Each keyword dict should have: keyword, match_type, bid
        """
        logger.info(
            f"Adding {len(keywords)} keywords to campaign {external_campaign_id}"
        )

        if not self._is_configured:
            logger.warning("Amazon Ads credentials not configured; returning stubs")
            return [
                {
                    "keyword": kw["keyword"],
                    "match_type": kw.get("match_type", "broad"),
                    "bid": kw.get("bid", 0.75),
                    "status": "draft",
                    "external_keyword_id": None,
                }
                for kw in keywords
            ]

        sp_keywords = [
            {
                "campaignId": external_campaign_id,
                "state": "enabled",
                "keywordText": kw["keyword"],
                "matchType": kw.get("match_type", "broad").upper(),
                "bid": kw.get("bid", 0.75),
            }
            for kw in keywords
        ]

        try:
            response = await self._request(
                "POST",
                "sp/keywords",
                json={"keywords": sp_keywords},
            )
            data = response.json()
            successes = data.get("keywords", {}).get("success", [])
            errors = data.get("keywords", {}).get("error", [])

            results: list[dict] = []
            for i, kw in enumerate(keywords):
                # Correlate response items by position
                if i < len(successes):
                    entry = successes[i]
                    results.append({
                        "keyword": kw["keyword"],
                        "match_type": kw.get("match_type", "broad"),
                        "bid": kw.get("bid", 0.75),
                        "status": "enabled",
                        "external_keyword_id": str(entry.get("keywordId", "")),
                    })
                else:
                    error_entry = errors[i - len(successes)] if (i - len(successes)) < len(errors) else {}
                    results.append({
                        "keyword": kw["keyword"],
                        "match_type": kw.get("match_type", "broad"),
                        "bid": kw.get("bid", 0.75),
                        "status": "error",
                        "external_keyword_id": None,
                        "error": str(error_entry),
                    })
            return results

        except AmazonAdsError as exc:
            logger.error("Amazon Ads add_keywords error: %s", exc)
            return [
                {
                    "keyword": kw["keyword"],
                    "match_type": kw.get("match_type", "broad"),
                    "bid": kw.get("bid", 0.75),
                    "status": "error",
                    "external_keyword_id": None,
                    "error": exc.detail,
                }
                for kw in keywords
            ]

    async def update_keyword_bids(
        self,
        external_campaign_id: str,
        bid_updates: list[dict],
    ) -> list[dict]:
        """Update keyword bids for a campaign.

        Each bid_update dict should have: external_keyword_id, bid
        """
        logger.info(
            f"Updating {len(bid_updates)} keyword bids for campaign {external_campaign_id}"
        )

        if not self._is_configured:
            logger.warning("Amazon Ads credentials not configured; returning stubs")
            return [
                {
                    "external_keyword_id": update["external_keyword_id"],
                    "new_bid": update["bid"],
                    "updated": False,
                    "error": "Amazon Ads credentials are not configured",
                }
                for update in bid_updates
            ]

        sp_updates = [
            {
                "keywordId": update["external_keyword_id"],
                "bid": update["bid"],
            }
            for update in bid_updates
        ]

        try:
            response = await self._request(
                "PUT",
                "sp/keywords",
                json={"keywords": sp_updates},
            )
            data = response.json()
            successes = data.get("keywords", {}).get("success", [])

            results: list[dict] = []
            success_ids = {str(s.get("keywordId", "")) for s in successes}
            for update in bid_updates:
                results.append({
                    "external_keyword_id": update["external_keyword_id"],
                    "new_bid": update["bid"],
                    "updated": update["external_keyword_id"] in success_ids,
                })
            return results

        except AmazonAdsError as exc:
            logger.error("Amazon Ads update_keyword_bids error: %s", exc)
            return [
                {
                    "external_keyword_id": update["external_keyword_id"],
                    "new_bid": update["bid"],
                    "updated": False,
                    "error": exc.detail,
                }
                for update in bid_updates
            ]

    async def add_negative_keywords(
        self,
        external_campaign_id: str,
        keywords: list[str],
    ) -> list[dict]:
        """Add negative keywords to a campaign."""
        logger.info(
            f"Adding {len(keywords)} negative keywords to campaign {external_campaign_id}"
        )

        if not self._is_configured:
            logger.warning("Amazon Ads credentials not configured; returning stubs")
            return [
                {"keyword": kw, "match_type": "negative_exact", "status": "draft"}
                for kw in keywords
            ]

        neg_keywords = [
            {
                "campaignId": external_campaign_id,
                "state": "enabled",
                "keywordText": kw,
                "matchType": "NEGATIVE_EXACT",
            }
            for kw in keywords
        ]

        try:
            response = await self._request(
                "POST",
                "sp/negativeKeywords",
                json={"keywords": neg_keywords},
            )
            data = response.json()
            successes = data.get("keywords", {}).get("success", [])

            results: list[dict] = []
            for i, kw in enumerate(keywords):
                if i < len(successes):
                    results.append({
                        "keyword": kw,
                        "match_type": "negative_exact",
                        "status": "enabled",
                        "external_keyword_id": str(successes[i].get("keywordId", "")),
                    })
                else:
                    results.append({
                        "keyword": kw,
                        "match_type": "negative_exact",
                        "status": "error",
                    })
            return results

        except AmazonAdsError as exc:
            logger.error("Amazon Ads add_negative_keywords error: %s", exc)
            return [
                {"keyword": kw, "match_type": "negative_exact", "status": "error", "error": exc.detail}
                for kw in keywords
            ]

    # ─── Reporting ────────────────────────────────────────────────────────

    async def _request_and_poll_report(self, report_payload: dict) -> dict | None:
        """Submit a report request to Amazon and poll until completion.

        Returns the parsed report data dict, or None on failure.
        """
        # Step 1 -- create the report
        response = await self._request(
            "POST",
            "reporting/reports",
            json=report_payload,
            headers_override={
                "Content-Type": "application/vnd.createAsyncReportRequest.v3+json",
                "Accept": "application/vnd.createAsyncReportRequest.v3+json",
            },
        )
        report_meta = response.json()
        report_id = report_meta.get("reportId")
        if not report_id:
            logger.error("Amazon Ads report creation did not return a reportId: %s", report_meta)
            return None

        # Step 2 -- poll until status is COMPLETED or we time out
        for _ in range(_REPORT_POLL_MAX_ATTEMPTS):
            await asyncio.sleep(_REPORT_POLL_INTERVAL_SECONDS)
            poll_resp = await self._request(
                "GET",
                f"reporting/reports/{report_id}",
                headers_override={
                    "Content-Type": "application/json",
                    "Accept": "application/vnd.createAsyncReportRequest.v3+json",
                },
            )
            poll_data = poll_resp.json()
            status = poll_data.get("status", "")

            if status == "COMPLETED":
                download_url = poll_data.get("url")
                if not download_url:
                    logger.error("Report completed but no download URL: %s", poll_data)
                    return None
                # Download the report payload (gzipped JSON from S3)
                async with httpx.AsyncClient(timeout=120.0) as dl_client:
                    dl_resp = await dl_client.get(download_url)
                if dl_resp.status_code == 200:
                    return dl_resp.json()
                logger.error("Failed to download completed report: %s", dl_resp.status_code)
                return None

            if status == "FAILURE":
                logger.error("Amazon Ads report %s failed: %s", report_id, poll_data)
                return None

        logger.error("Amazon Ads report %s timed out after polling", report_id)
        return None

    async def get_campaign_report(
        self,
        external_campaign_id: str,
        start_date: str,
        end_date: str,
        metrics: list[str] | None = None,
    ) -> dict:
        """Fetch performance report for a campaign.

        Returns aggregated metrics for the date range.
        """
        default_metrics = [
            "impressions", "clicks", "cost", "sales",
            "acos", "roas", "ctr", "cpc",
        ]
        requested_metrics = metrics or default_metrics

        logger.info(
            f"Fetching report for {external_campaign_id} "
            f"from {start_date} to {end_date}"
        )

        if not self._is_configured:
            logger.warning("Amazon Ads credentials not configured; returning zeroed report")
            return {
                "external_campaign_id": external_campaign_id,
                "start_date": start_date,
                "end_date": end_date,
                "metrics": {m: 0.0 for m in requested_metrics},
                "report_status": "skipped",
                "error": "Amazon Ads credentials are not configured",
            }

        # Amazon Advertising v3 reporting API column names
        column_map = {
            "impressions": "impressions",
            "clicks": "clicks",
            "cost": "cost",
            "sales": "sales14d",
            "acos": "acosClicks14d",
            "roas": "roasClicks14d",
            "ctr": "clickThroughRate",
            "cpc": "costPerClick",
        }
        api_columns = [column_map.get(m, m) for m in requested_metrics]

        report_payload = {
            "reportTypeId": "spCampaigns",
            "format": "GZIP_JSON",
            "groupBy": ["campaign"],
            "columns": api_columns,
            "reportDate": {
                "startDate": start_date,
                "endDate": end_date,
            },
            "filters": [
                {
                    "field": "campaignId",
                    "values": [external_campaign_id],
                }
            ],
        }

        try:
            report_data = await self._request_and_poll_report(report_payload)

            if report_data is None:
                return {
                    "external_campaign_id": external_campaign_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "metrics": {m: 0.0 for m in requested_metrics},
                    "report_status": "failed",
                }

            # Flatten: the report is a list of row dicts; aggregate the first row
            rows = report_data if isinstance(report_data, list) else report_data.get("rows", [report_data])
            aggregated: dict[str, float] = {}
            reverse_map = {v: k for k, v in column_map.items()}
            for api_col in api_columns:
                friendly = reverse_map.get(api_col, api_col)
                total = sum(float(row.get(api_col, 0)) for row in rows)
                aggregated[friendly] = round(total, 4)

            return {
                "external_campaign_id": external_campaign_id,
                "start_date": start_date,
                "end_date": end_date,
                "metrics": aggregated,
                "report_status": "completed",
            }

        except AmazonAdsError as exc:
            logger.error("Amazon Ads get_campaign_report error: %s", exc)
            return {
                "external_campaign_id": external_campaign_id,
                "start_date": start_date,
                "end_date": end_date,
                "metrics": {m: 0.0 for m in requested_metrics},
                "report_status": "error",
                "error": exc.detail,
            }

    async def get_keyword_report(
        self,
        external_campaign_id: str,
        start_date: str,
        end_date: str,
    ) -> list[dict]:
        """Fetch keyword-level performance report."""
        logger.info(
            f"Fetching keyword report for {external_campaign_id}"
        )

        if not self._is_configured:
            logger.warning("Amazon Ads credentials not configured; returning empty keyword report")
            return []

        report_payload = {
            "reportTypeId": "spTargeting",
            "format": "GZIP_JSON",
            "groupBy": ["targeting"],
            "columns": [
                "keywordId",
                "keywordText",
                "matchType",
                "impressions",
                "clicks",
                "cost",
                "sales14d",
                "acosClicks14d",
                "roasClicks14d",
                "clickThroughRate",
                "costPerClick",
            ],
            "reportDate": {
                "startDate": start_date,
                "endDate": end_date,
            },
            "filters": [
                {
                    "field": "campaignId",
                    "values": [external_campaign_id],
                }
            ],
        }

        try:
            report_data = await self._request_and_poll_report(report_payload)

            if report_data is None:
                return []

            rows = report_data if isinstance(report_data, list) else report_data.get("rows", [])
            results: list[dict] = []
            for row in rows:
                results.append({
                    "external_keyword_id": str(row.get("keywordId", "")),
                    "keyword": row.get("keywordText", ""),
                    "match_type": str(row.get("matchType", "")).lower(),
                    "impressions": int(row.get("impressions", 0)),
                    "clicks": int(row.get("clicks", 0)),
                    "spend": float(row.get("cost", 0)),
                    "sales": float(row.get("sales14d", 0)),
                    "acos": float(row.get("acosClicks14d", 0)),
                    "roas": float(row.get("roasClicks14d", 0)),
                    "ctr": float(row.get("clickThroughRate", 0)),
                    "cpc": float(row.get("costPerClick", 0)),
                })
            return results

        except AmazonAdsError as exc:
            logger.error("Amazon Ads get_keyword_report error: %s", exc)
            return []

    async def get_search_term_report(
        self,
        external_campaign_id: str,
        start_date: str,
        end_date: str,
    ) -> list[dict]:
        """Fetch search term report to discover new keyword opportunities."""
        logger.info(
            f"Fetching search term report for {external_campaign_id}"
        )

        if not self._is_configured:
            logger.warning("Amazon Ads credentials not configured; returning empty search term report")
            return []

        report_payload = {
            "reportTypeId": "spSearchTerm",
            "format": "GZIP_JSON",
            "groupBy": ["searchTerm"],
            "columns": [
                "searchTerm",
                "keywordId",
                "keywordText",
                "impressions",
                "clicks",
                "cost",
                "sales14d",
                "acosClicks14d",
                "clickThroughRate",
                "costPerClick",
            ],
            "reportDate": {
                "startDate": start_date,
                "endDate": end_date,
            },
            "filters": [
                {
                    "field": "campaignId",
                    "values": [external_campaign_id],
                }
            ],
        }

        try:
            report_data = await self._request_and_poll_report(report_payload)

            if report_data is None:
                return []

            rows = report_data if isinstance(report_data, list) else report_data.get("rows", [])
            results: list[dict] = []
            for row in rows:
                results.append({
                    "search_term": row.get("searchTerm", ""),
                    "keyword": row.get("keywordText", ""),
                    "external_keyword_id": str(row.get("keywordId", "")),
                    "impressions": int(row.get("impressions", 0)),
                    "clicks": int(row.get("clicks", 0)),
                    "spend": float(row.get("cost", 0)),
                    "sales": float(row.get("sales14d", 0)),
                    "acos": float(row.get("acosClicks14d", 0)),
                    "ctr": float(row.get("clickThroughRate", 0)),
                    "cpc": float(row.get("costPerClick", 0)),
                })
            return results

        except AmazonAdsError as exc:
            logger.error("Amazon Ads get_search_term_report error: %s", exc)
            return []
