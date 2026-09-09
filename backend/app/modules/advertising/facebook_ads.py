"""Facebook Ads API client for campaign creation, audience targeting, and reporting.

Uses httpx to call the Facebook Marketing API REST endpoints directly.
The API version defaults to v18.0 and can be overridden with FACEBOOK_ADS_API_VERSION.
Credentials are read from environment variables:
  - FACEBOOK_APP_ID
  - FACEBOOK_APP_SECRET
  - FACEBOOK_ACCESS_TOKEN
  - FACEBOOK_AD_ACCOUNT_ID
  - FACEBOOK_ADS_API_VERSION (optional, default: v18.0)
"""

import logging
import os
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

FACEBOOK_ADS_API_VERSION = os.environ.get("FACEBOOK_ADS_API_VERSION", "v18.0")
FACEBOOK_GRAPH_API_BASE = f"https://graph.facebook.com/{FACEBOOK_ADS_API_VERSION}"

# Timeout for all Facebook API requests (connect, read, write, pool)
_DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


class FacebookAdsError(Exception):
    """Raised when a Facebook Marketing API call fails."""

    def __init__(self, message: str, status_code: int | None = None, fb_error: dict | None = None):
        self.status_code = status_code
        self.fb_error = fb_error or {}
        super().__init__(message)


class FacebookAdsClient:
    """Client for interacting with Facebook Marketing API.

    Supports:
    - Campaign creation and management
    - Ad set creation
    - Ad creative creation
    - Custom audience targeting
    - Lookalike audience creation
    - Performance reporting
    """

    BASE_URL = FACEBOOK_GRAPH_API_BASE

    def __init__(
        self,
        access_token: str | None = None,
        ad_account_id: str | None = None,
        app_id: str | None = None,
        app_secret: str | None = None,
    ):
        self.access_token = access_token or os.environ.get("FACEBOOK_ACCESS_TOKEN", "")
        self.ad_account_id = ad_account_id or os.environ.get("FACEBOOK_AD_ACCOUNT_ID", "")
        self.app_id = app_id or os.environ.get("FACEBOOK_APP_ID", "")
        self.app_secret = app_secret or os.environ.get("FACEBOOK_APP_SECRET", "")

    # ─── Internal Helpers ─────────────────────────────────────────────────

    def _ensure_credentials(self) -> None:
        """Validate that required credentials are present.

        Raises FacebookAdsError when the access token or ad account ID are
        missing so callers get a clear, actionable message instead of a
        cryptic 400 from the Graph API.
        """
        if not self.access_token or not self.ad_account_id:
            raise FacebookAdsError(
                "Facebook Ads credentials not configured. "
                "Set FACEBOOK_ACCESS_TOKEN and FACEBOOK_AD_ACCOUNT_ID environment variables."
            )

    def _account_path(self) -> str:
        """Return the Graph API path prefix for the configured ad account.

        Facebook ad-account IDs in the API are prefixed with ``act_``.  If the
        caller already supplied the prefix we use it as-is; otherwise we add it.
        """
        acct = self.ad_account_id
        if not acct.startswith("act_"):
            acct = f"act_{acct}"
        return acct

    async def _get_headers(self) -> dict[str, str]:
        """Build request headers."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict | None = None,
        json_body: dict | None = None,
    ) -> dict:
        """Execute an HTTP request against the Graph API and return the JSON
        response body.

        Raises ``FacebookAdsError`` on non-2xx status codes or network errors.
        """
        headers = await self._get_headers()

        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
            try:
                response = await client.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    json=json_body,
                )
            except httpx.HTTPError as exc:
                logger.error("Facebook API network error: %s", exc)
                raise FacebookAdsError(f"Network error calling Facebook API: {exc}") from exc

        if response.status_code >= 400:
            try:
                error_data = response.json()
            except (ValueError, UnicodeDecodeError) as exc:
                logger.warning("Failed to parse Facebook error response as JSON: %s", exc)
                error_data = {"raw": response.text}

            fb_error = error_data.get("error", error_data)
            msg = fb_error.get("message", response.text) if isinstance(fb_error, dict) else str(fb_error)
            logger.error(
                "Facebook API error %s: %s",
                response.status_code,
                msg,
            )
            raise FacebookAdsError(
                f"Facebook API error ({response.status_code}): {msg}",
                status_code=response.status_code,
                fb_error=fb_error if isinstance(fb_error, dict) else {"message": str(fb_error)},
            )

        return response.json()

    # ─── Campaign Management ─────────────────────────────────────────────

    async def list_campaigns(
        self,
        limit: int = 50,
        status_filter: str | None = None,
    ) -> dict:
        """List campaigns for the configured ad account.

        Returns a dict with a ``campaigns`` list and ``total_count``.

        See: https://developers.facebook.com/docs/marketing-api/reference/ad-campaign-group
        """
        self._ensure_credentials()

        url = f"{self.BASE_URL}/{self._account_path()}/campaigns"

        fields = "id,name,objective,status,daily_budget,created_time,updated_time"
        params: dict = {
            "fields": fields,
            "limit": str(limit),
        }
        if status_filter:
            params["effective_status"] = f'["{status_filter.upper()}"]'

        logger.info("Listing Facebook Ads campaigns (limit=%s)", limit)
        data = await self._request("GET", url, params=params)

        campaigns = []
        for item in data.get("data", []):
            # daily_budget comes back in cents from the API
            raw_budget = item.get("daily_budget")
            budget_dollars = float(raw_budget) / 100.0 if raw_budget else 0.0
            campaigns.append(
                {
                    "external_campaign_id": item.get("id", ""),
                    "name": item.get("name", ""),
                    "objective": item.get("objective", ""),
                    "status": item.get("status", "").lower(),
                    "daily_budget": budget_dollars,
                }
            )

        return {
            "campaigns": campaigns,
            "total_count": len(campaigns),
        }

    async def get_campaign(self, external_campaign_id: str) -> dict:
        """Get details for a single Facebook Ads campaign.

        Returns a dict with campaign fields.

        See: https://developers.facebook.com/docs/marketing-api/reference/ad-campaign-group
        """
        self._ensure_credentials()

        url = f"{self.BASE_URL}/{external_campaign_id}"
        params = {
            "fields": "id,name,objective,status,daily_budget,created_time,updated_time,start_time,stop_time",
        }

        logger.info("Getting Facebook Ads campaign: %s", external_campaign_id)
        data = await self._request("GET", url, params=params)

        raw_budget = data.get("daily_budget")
        budget_dollars = float(raw_budget) / 100.0 if raw_budget else 0.0

        return {
            "external_campaign_id": data.get("id", ""),
            "name": data.get("name", ""),
            "objective": data.get("objective", ""),
            "status": data.get("status", "").lower(),
            "daily_budget": budget_dollars,
            "created_time": data.get("created_time"),
            "updated_time": data.get("updated_time"),
        }

    async def create_campaign(
        self,
        name: str,
        objective: str = "OUTCOME_SALES",
        daily_budget: float = 0.0,
        status: str = "PAUSED",
    ) -> dict:
        """Create a Facebook Ads campaign.

        Returns a dict with the external campaign ID and status.

        See: https://developers.facebook.com/docs/marketing-api/reference/ad-campaign-group
        """
        self._ensure_credentials()

        url = f"{self.BASE_URL}/{self._account_path()}/campaigns"

        # daily_budget is in the currency's smallest unit (e.g. cents for USD)
        budget_cents = int(round(daily_budget * 100))

        payload: dict[str, Any] = {
            "name": name,
            "objective": objective,
            "status": status,
            "special_ad_categories": [],
        }
        if budget_cents > 0:
            payload["daily_budget"] = budget_cents

        logger.info("Creating Facebook Ads campaign: %s (objective=%s)", name, objective)
        data = await self._request("POST", url, json_body=payload)

        return {
            "external_campaign_id": data.get("id", ""),
            "status": status.lower(),
            "objective": objective,
            "daily_budget": daily_budget,
            "created": True,
        }

    async def update_campaign(
        self,
        external_campaign_id: str,
        updates: dict,
    ) -> dict:
        """Update an existing Facebook Ads campaign.

        ``updates`` may contain any writable campaign field accepted by the
        Graph API (e.g. ``name``, ``status``, ``daily_budget``).
        """
        self._ensure_credentials()

        url = f"{self.BASE_URL}/{external_campaign_id}"

        # Convert daily_budget from dollars to cents if present
        payload = dict(updates)
        if "daily_budget" in payload and isinstance(payload["daily_budget"], int | float):
            payload["daily_budget"] = int(round(payload["daily_budget"] * 100))

        logger.info("Updating Facebook Ads campaign: %s", external_campaign_id)
        await self._request("POST", url, json_body=payload)

        return {
            "external_campaign_id": external_campaign_id,
            "updated": True,
            "changes": updates,
        }

    async def pause_campaign(self, external_campaign_id: str) -> dict:
        """Pause a Facebook Ads campaign."""
        return await self.update_campaign(external_campaign_id, {"status": "PAUSED"})

    async def resume_campaign(self, external_campaign_id: str) -> dict:
        """Resume a paused Facebook Ads campaign."""
        return await self.update_campaign(external_campaign_id, {"status": "ACTIVE"})

    # ─── Ad Set Management ────────────────────────────────────────────────

    async def create_ad_set(
        self,
        campaign_id: str,
        name: str,
        daily_budget: float = 0.0,
        billing_event: str = "IMPRESSIONS",
        optimization_goal: str = "LINK_CLICKS",
        targeting: dict | None = None,
        status: str = "PAUSED",
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> dict:
        """Create an ad set within a campaign.

        ``targeting`` follows the Facebook Targeting Spec format, e.g.::

            {
                "geo_locations": {"countries": ["US"]},
                "age_min": 25,
                "age_max": 55,
                "interests": [{"id": "6003139266461", "name": "Books"}],
            }

        See: https://developers.facebook.com/docs/marketing-api/reference/ad-campaign
        """
        self._ensure_credentials()

        url = f"{self.BASE_URL}/{self._account_path()}/adsets"

        budget_cents = int(round(daily_budget * 100))

        payload: dict = {
            "campaign_id": campaign_id,
            "name": name,
            "billing_event": billing_event,
            "optimization_goal": optimization_goal,
            "status": status,
            "targeting": targeting or {"geo_locations": {"countries": ["US"]}},
        }
        if budget_cents > 0:
            payload["daily_budget"] = budget_cents
        if start_time:
            payload["start_time"] = start_time
        if end_time:
            payload["end_time"] = end_time

        logger.info(
            "Creating Facebook ad set '%s' for campaign %s",
            name,
            campaign_id,
        )
        data = await self._request("POST", url, json_body=payload)

        return {
            "ad_set_id": data.get("id", ""),
            "campaign_id": campaign_id,
            "name": name,
            "status": status.lower(),
            "created": True,
        }

    # ─── Ad Creative Management ───────────────────────────────────────────

    async def create_ad_creative(
        self,
        name: str,
        page_id: str,
        link_url: str,
        message: str = "",
        headline: str = "",
        description: str = "",
        image_hash: str | None = None,
        image_url: str | None = None,
        call_to_action_type: str = "LEARN_MORE",
    ) -> dict:
        """Create an ad creative.

        Either ``image_hash`` (from a previously uploaded image) or
        ``image_url`` should be supplied for link ads.

        See: https://developers.facebook.com/docs/marketing-api/reference/ad-creative
        """
        self._ensure_credentials()

        url = f"{self.BASE_URL}/{self._account_path()}/adcreatives"

        link_data: dict = {
            "link": link_url,
            "message": message,
        }
        if headline:
            link_data["name"] = headline
        if description:
            link_data["description"] = description
        if image_hash:
            link_data["image_hash"] = image_hash
        elif image_url:
            link_data["picture"] = image_url
        if call_to_action_type:
            link_data["call_to_action"] = {"type": call_to_action_type}

        payload = {
            "name": name,
            "object_story_spec": {
                "page_id": page_id,
                "link_data": link_data,
            },
        }

        logger.info("Creating Facebook ad creative: %s", name)
        data = await self._request("POST", url, json_body=payload)

        return {
            "creative_id": data.get("id", ""),
            "name": name,
            "created": True,
        }

    # ─── Audience Targeting ──────────────────────────────────────────────

    async def create_custom_audience(
        self,
        name: str,
        description: str = "",
        source_type: str = "CUSTOM",
    ) -> dict:
        """Create a custom audience for targeting.

        See: https://developers.facebook.com/docs/marketing-api/reference/custom-audience
        """
        self._ensure_credentials()

        url = f"{self.BASE_URL}/{self._account_path()}/customaudiences"

        # Map friendly source_type values to Facebook subtype enum
        subtype_map = {
            "CUSTOM": "CUSTOM",
            "WEBSITE": "WEBSITE",
            "APP": "APP",
            "OFFLINE": "OFFLINE_CONVERSION",
            "ENGAGEMENT": "ENGAGEMENT",
        }
        subtype = subtype_map.get(source_type.upper(), "CUSTOM")

        payload = {
            "name": name,
            "subtype": subtype,
            "description": description,
            "customer_file_source": "USER_PROVIDED_ONLY",
        }

        logger.info("Creating custom audience: %s (subtype=%s)", name, subtype)
        data = await self._request("POST", url, json_body=payload)

        return {
            "audience_id": data.get("id", ""),
            "name": name,
            "source_type": source_type,
            "created": True,
        }

    async def create_lookalike_audience(
        self,
        source_audience_id: str,
        country: str = "US",
        ratio: float = 0.01,
    ) -> dict:
        """Create a lookalike audience from an existing audience.

        ``ratio`` controls the audience size (0.01 = top 1% most similar).

        See: https://developers.facebook.com/docs/marketing-api/reference/custom-audience
        """
        self._ensure_credentials()

        url = f"{self.BASE_URL}/{self._account_path()}/customaudiences"

        payload = {
            "name": f"Lookalike ({country}, {int(ratio * 100)}%) - {source_audience_id}",
            "subtype": "LOOKALIKE",
            "origin_audience_id": source_audience_id,
            "lookalike_spec": {
                "type": "similarity",
                "country": country,
                "ratio": ratio,
            },
        }

        logger.info(
            "Creating lookalike audience from %s (country=%s, ratio=%s)",
            source_audience_id,
            country,
            ratio,
        )
        data = await self._request("POST", url, json_body=payload)

        return {
            "audience_id": data.get("id", ""),
            "source": source_audience_id,
            "country": country,
            "ratio": ratio,
            "created": True,
        }

    async def get_audience_insights(
        self,
        audience_id: str,
    ) -> dict:
        """Get delivery estimate / insights for an audience.

        Uses the delivery_estimate edge to obtain estimated reach and
        demographic breakdowns.
        """
        self._ensure_credentials()

        # Retrieve basic audience metadata
        audience_url = f"{self.BASE_URL}/{audience_id}"
        audience_params = {
            "fields": "name,approximate_count_lower_bound,approximate_count_upper_bound,description",
        }

        logger.info("Fetching audience insights for %s", audience_id)
        audience_data = await self._request("GET", audience_url, params=audience_params)

        lower = audience_data.get("approximate_count_lower_bound", 0)
        upper = audience_data.get("approximate_count_upper_bound", 0)

        # Fetch delivery estimate for richer reach information
        estimate_url = f"{self.BASE_URL}/{self._account_path()}/delivery_estimate"
        estimate_params = {
            "targeting_spec": f'{{"custom_audiences":[{{"id":"{audience_id}"}}]}}',
            "optimization_goal": "LINK_CLICKS",
        }

        try:
            estimate_data = await self._request("GET", estimate_url, params=estimate_params)
            estimate_list = estimate_data.get("data", [])
            estimated_reach = estimate_list[0].get("estimate_dau", 0) if estimate_list else 0
        except FacebookAdsError:
            # Delivery estimate may not be available for all audience types
            estimated_reach = (lower + upper) // 2 if (lower or upper) else 0

        return {
            "audience_id": audience_id,
            "estimated_reach": estimated_reach,
            "demographics": {
                "approximate_count_lower_bound": lower,
                "approximate_count_upper_bound": upper,
            },
            "interests": [],
        }

    # ─── Reporting ────────────────────────────────────────────────────────

    async def get_campaign_insights(
        self,
        external_campaign_id: str,
        start_date: str,
        end_date: str,
        fields: list[str] | None = None,
    ) -> dict:
        """Fetch performance insights for a campaign.

        ``start_date`` and ``end_date`` should be in ``YYYY-MM-DD`` format.

        See: https://developers.facebook.com/docs/marketing-api/insights
        """
        self._ensure_credentials()

        default_fields = [
            "impressions",
            "clicks",
            "spend",
            "actions",
            "ctr",
            "cpc",
            "cpm",
            "reach",
        ]
        requested_fields = fields or default_fields

        url = f"{self.BASE_URL}/{external_campaign_id}/insights"
        params = {
            "fields": ",".join(requested_fields),
            "time_range": f'{{"since":"{start_date}","until":"{end_date}"}}',
        }

        logger.info(
            "Fetching insights for %s from %s to %s",
            external_campaign_id,
            start_date,
            end_date,
        )
        data = await self._request("GET", url, params=params)

        # The insights endpoint returns data inside a "data" array
        insights_list = data.get("data", [])
        metrics = insights_list[0] if insights_list else {f: "0" for f in requested_fields}

        # Normalise metric values to floats
        normalised: dict[str, float | list | dict] = {}
        for key in requested_fields:
            value = metrics.get(key, 0)
            if isinstance(value, list | dict):
                normalised[key] = value
            else:
                try:
                    normalised[key] = float(value)
                except (TypeError, ValueError):
                    normalised[key] = 0.0

        return {
            "external_campaign_id": external_campaign_id,
            "start_date": start_date,
            "end_date": end_date,
            "metrics": normalised,
            "report_status": "completed",
        }

    async def get_ad_set_insights(
        self,
        ad_set_id: str,
        start_date: str,
        end_date: str,
    ) -> dict:
        """Fetch ad set level insights.

        Returns the same structure as campaign insights but scoped to a
        single ad set.
        """
        self._ensure_credentials()

        url = f"{self.BASE_URL}/{ad_set_id}/insights"
        fields = [
            "impressions",
            "clicks",
            "spend",
            "actions",
            "ctr",
            "cpc",
            "cpm",
            "reach",
        ]
        params = {
            "fields": ",".join(fields),
            "time_range": f'{{"since":"{start_date}","until":"{end_date}"}}',
        }

        logger.info("Fetching ad set insights for %s", ad_set_id)
        data = await self._request("GET", url, params=params)

        insights_list = data.get("data", [])
        metrics: dict = {}
        if insights_list:
            raw = insights_list[0]
            for key in fields:
                value = raw.get(key, 0)
                if isinstance(value, list | dict):
                    metrics[key] = value
                else:
                    try:
                        metrics[key] = float(value)
                    except (TypeError, ValueError):
                        metrics[key] = 0.0

        return {
            "ad_set_id": ad_set_id,
            "start_date": start_date,
            "end_date": end_date,
            "metrics": metrics,
        }
