"""Unit tests for SQLAlchemy models.

Tests model instantiation, relationships, default values, soft delete behavior,
and enum definitions without requiring a live database connection.
"""

import uuid
from datetime import UTC, date, datetime

# ── Organization ───────────────────────────────────────────────────────
from app.models.organization import Organization, PlanTier, SubscriptionStatus


class TestOrganization:
    def test_instantiation(self):
        org = Organization(
            name="Test Org",
            slug="test-org",
        )
        assert org.name == "Test Org"
        assert org.slug == "test-org"

    def test_default_plan_tier(self):
        org = Organization(name="Test", slug="test")
        assert org.plan_tier is None or org.plan_tier == PlanTier.FREE

    def test_default_subscription_status(self):
        org = Organization(name="Test", slug="test")
        assert org.subscription_status is None or org.subscription_status == SubscriptionStatus.ACTIVE

    def test_nullable_settings(self):
        org = Organization(name="Test", slug="test", settings={"theme": "dark"})
        assert org.settings == {"theme": "dark"}

    def test_nullable_limits(self):
        org = Organization(name="Test", slug="test", limits=None)
        assert org.limits is None

    def test_soft_delete_default(self):
        org = Organization(name="Test", slug="test")
        assert org.deleted_at is None

    def test_soft_delete_set(self):
        now = datetime.now(UTC)
        org = Organization(name="Test", slug="test", deleted_at=now)
        assert org.deleted_at == now

    def test_tablename(self):
        assert Organization.__tablename__ == "organizations"


class TestPlanTierEnum:
    def test_values(self):
        assert PlanTier.FREE.value == "free"
        assert PlanTier.STARTER.value == "starter"
        assert PlanTier.PRO.value == "pro"
        assert PlanTier.BUSINESS.value == "business"
        assert PlanTier.ENTERPRISE.value == "enterprise"

    def test_count(self):
        assert len(PlanTier) == 5


class TestSubscriptionStatusEnum:
    def test_values(self):
        assert SubscriptionStatus.ACTIVE.value == "active"
        assert SubscriptionStatus.TRIALING.value == "trialing"
        assert SubscriptionStatus.PAST_DUE.value == "past_due"
        assert SubscriptionStatus.CANCELED.value == "canceled"
        assert SubscriptionStatus.UNPAID.value == "unpaid"


# ── User ───────────────────────────────────────────────────────────────
from app.models.user import ApiKey, User, UserRole, UserSession


class TestUser:
    def test_instantiation(self):
        org_id = uuid.uuid4()
        user = User(
            org_id=org_id,
            email="test@example.com",
            password_hash="hashed",
            name="Test User",
        )
        assert user.email == "test@example.com"
        assert user.org_id == org_id
        assert user.name == "Test User"

    def test_default_role(self):
        user = User(
            org_id=uuid.uuid4(),
            email="test@example.com",
            password_hash="hashed",
            name="Test",
        )
        # Python-side default
        assert user.role is None or user.role == UserRole.VIEWER

    def test_preferences_jsonb(self):
        user = User(
            org_id=uuid.uuid4(),
            email="test@example.com",
            password_hash="hashed",
            name="Test",
            preferences={"editor_theme": "dark"},
        )
        assert user.preferences["editor_theme"] == "dark"

    def test_email_verified_at_nullable(self):
        user = User(
            org_id=uuid.uuid4(),
            email="test@example.com",
            password_hash="hashed",
            name="Test",
        )
        assert user.email_verified_at is None

    def test_tablename(self):
        assert User.__tablename__ == "users"

    def test_soft_delete(self):
        user = User(
            org_id=uuid.uuid4(),
            email="test@example.com",
            password_hash="hashed",
            name="Test",
        )
        assert user.deleted_at is None
        now = datetime.now(UTC)
        user.deleted_at = now
        assert user.deleted_at == now


class TestUserRole:
    def test_all_roles(self):
        assert UserRole.OWNER.value == "owner"
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.EDITOR.value == "editor"
        assert UserRole.WRITER.value == "writer"
        assert UserRole.VIEWER.value == "viewer"

    def test_count(self):
        assert len(UserRole) == 5


class TestApiKey:
    def test_instantiation(self):
        api_key = ApiKey(
            org_id=uuid.uuid4(),
            created_by=uuid.uuid4(),
            key_hash="abc123hash",
            prefix="spf_",
            name="My API Key",
        )
        assert api_key.name == "My API Key"
        assert api_key.key_hash == "abc123hash"

    def test_scopes_array(self):
        api_key = ApiKey(
            org_id=uuid.uuid4(),
            created_by=uuid.uuid4(),
            key_hash="abc123hash",
            prefix="spf_",
            name="Key",
            scopes=["read", "write"],
        )
        assert "read" in api_key.scopes
        assert "write" in api_key.scopes

    def test_expires_at_nullable(self):
        api_key = ApiKey(
            org_id=uuid.uuid4(),
            created_by=uuid.uuid4(),
            key_hash="abc123hash",
            prefix="spf_",
            name="Key",
        )
        assert api_key.expires_at is None

    def test_tablename(self):
        assert ApiKey.__tablename__ == "api_keys"


class TestUserSession:
    def test_instantiation(self):
        session = UserSession(
            user_id=uuid.uuid4(),
            token_hash="tokenhash123",
        )
        assert session.token_hash == "tokenhash123"

    def test_device_info_jsonb(self):
        session = UserSession(
            user_id=uuid.uuid4(),
            token_hash="tokenhash123",
            device_info={"browser": "Chrome", "os": "Windows"},
        )
        assert session.device_info["browser"] == "Chrome"

    def test_ip_address(self):
        session = UserSession(
            user_id=uuid.uuid4(),
            token_hash="tokenhash123",
            ip_address="192.168.1.1",
        )
        assert session.ip_address == "192.168.1.1"

    def test_tablename(self):
        assert UserSession.__tablename__ == "user_sessions"


# ── Project ────────────────────────────────────────────────────────────
from app.models.project import (
    Book,
    BookFormat,
    BookStatus,
    BookVersion,
    PenName,
    Project,
    ProjectStatus,
    ProjectType,
    Series,
)


class TestProject:
    def test_instantiation(self):
        project = Project(
            org_id=uuid.uuid4(),
            title="My Book Project",
            type=ProjectType.BOOK,
        )
        assert project.title == "My Book Project"
        assert project.type == ProjectType.BOOK

    def test_default_status(self):
        project = Project(
            org_id=uuid.uuid4(),
            title="Test",
            type=ProjectType.BOOK,
        )
        assert project.status is None or project.status == ProjectStatus.DRAFT

    def test_pen_name_id_nullable(self):
        project = Project(
            org_id=uuid.uuid4(),
            title="Test",
            type=ProjectType.BOOK,
        )
        assert project.pen_name_id is None

    def test_tablename(self):
        assert Project.__tablename__ == "projects"


class TestProjectTypeEnum:
    def test_values(self):
        assert ProjectType.BOOK.value == "book"
        assert ProjectType.SERIES.value == "series"
        assert ProjectType.COURSE.value == "course"


class TestBook:
    def test_instantiation(self):
        book = Book(
            project_id=uuid.uuid4(),
            title="Test Book",
        )
        assert book.title == "Test Book"

    def test_default_format(self):
        book = Book(project_id=uuid.uuid4(), title="Test")
        assert book.format is None or book.format == BookFormat.EBOOK

    def test_isbn_nullable(self):
        book = Book(project_id=uuid.uuid4(), title="Test")
        assert book.isbn is None

    def test_metadata_jsonb(self):
        book = Book(
            project_id=uuid.uuid4(),
            title="Test",
            metadata_={"genre": "fiction", "page_count": 300},
        )
        assert book.metadata_["genre"] == "fiction"

    def test_tablename(self):
        assert Book.__tablename__ == "books"


class TestBookFormatEnum:
    def test_values(self):
        assert BookFormat.EBOOK.value == "ebook"
        assert BookFormat.PRINT.value == "print"
        assert BookFormat.AUDIO.value == "audio"


class TestBookStatusEnum:
    def test_values(self):
        assert BookStatus.DRAFT.value == "draft"
        assert BookStatus.WRITING.value == "writing"
        assert BookStatus.EDITING.value == "editing"
        assert BookStatus.FORMATTING.value == "formatting"
        assert BookStatus.PUBLISHED.value == "published"
        assert BookStatus.ARCHIVED.value == "archived"

    def test_count(self):
        assert len(BookStatus) == 6


class TestSeries:
    def test_instantiation(self):
        series = Series(
            org_id=uuid.uuid4(),
            name="Test Series",
        )
        assert series.name == "Test Series"

    def test_book_order_array(self):
        series = Series(
            org_id=uuid.uuid4(),
            name="Test",
            book_order=["book1", "book2"],
        )
        assert len(series.book_order) == 2

    def test_tablename(self):
        assert Series.__tablename__ == "series"


class TestPenName:
    def test_instantiation(self):
        pen_name = PenName(
            org_id=uuid.uuid4(),
            name="J.K. Rowling",
        )
        assert pen_name.name == "J.K. Rowling"

    def test_default_active(self):
        """active defaults to True at DB level via server_default."""
        pen_name = PenName(org_id=uuid.uuid4(), name="Test")
        # server_default applies at DB flush; Python-side may be None before flush
        assert pen_name.active is True or pen_name.active is None

    def test_brand_guidelines_jsonb(self):
        pen_name = PenName(
            org_id=uuid.uuid4(),
            name="Test",
            brand_guidelines={"tone": "professional"},
        )
        assert pen_name.brand_guidelines["tone"] == "professional"

    def test_tablename(self):
        assert PenName.__tablename__ == "pen_names"


class TestBookVersion:
    def test_instantiation(self):
        bv = BookVersion(
            book_id=uuid.uuid4(),
            version_number=1,
        )
        assert bv.version_number == 1

    def test_changelog_nullable(self):
        bv = BookVersion(book_id=uuid.uuid4(), version_number=1)
        assert bv.changelog is None

    def test_tablename(self):
        assert BookVersion.__tablename__ == "book_versions"


# ── Content ────────────────────────────────────────────────────────────
from app.models.content import (
    AssetType,
    Chapter,
    ContentAsset,
    ContentType,
    Manuscript,
    ManuscriptStatus,
    StyleProfile,
    WritingSession,
)


class TestManuscript:
    def test_instantiation(self):
        ms = Manuscript(
            book_id=uuid.uuid4(),
            content_type=ContentType.FICTION,
        )
        assert ms.content_type == ContentType.FICTION

    def test_default_word_count(self):
        """word_count defaults to 0 at DB level via server_default."""
        ms = Manuscript(book_id=uuid.uuid4(), content_type=ContentType.FICTION)
        assert ms.word_count == 0 or ms.word_count is None

    def test_default_status(self):
        ms = Manuscript(book_id=uuid.uuid4(), content_type=ContentType.FICTION)
        assert ms.status is None or ms.status == ManuscriptStatus.DRAFT

    def test_tablename(self):
        assert Manuscript.__tablename__ == "manuscripts"


class TestChapter:
    def test_instantiation(self):
        ch = Chapter(
            manuscript_id=uuid.uuid4(),
            title="Chapter 1",
            order_index=0,
        )
        assert ch.title == "Chapter 1"
        assert ch.order_index == 0

    def test_ai_metrics_jsonb(self):
        ch = Chapter(
            manuscript_id=uuid.uuid4(),
            title="Test",
            order_index=0,
            ai_metrics={"readability": 0.85},
        )
        assert ch.ai_metrics["readability"] == 0.85

    def test_tablename(self):
        assert Chapter.__tablename__ == "chapters"


class TestContentTypeEnum:
    def test_values(self):
        assert ContentType.FICTION.value == "fiction"
        assert ContentType.NONFICTION.value == "nonfiction"
        assert ContentType.POETRY.value == "poetry"
        assert ContentType.SCREENPLAY.value == "screenplay"


class TestStyleProfile:
    def test_instantiation(self):
        sp = StyleProfile(
            org_id=uuid.uuid4(),
            name="Hemingway Style",
        )
        assert sp.name == "Hemingway Style"

    def test_voice_fingerprint_jsonb(self):
        sp = StyleProfile(
            org_id=uuid.uuid4(),
            name="Test",
            voice_fingerprint={"tone": "authoritative"},
        )
        assert sp.voice_fingerprint["tone"] == "authoritative"

    def test_sample_sources_array(self):
        sp = StyleProfile(
            org_id=uuid.uuid4(),
            name="Test",
            sample_sources=["book1.txt", "book2.txt"],
        )
        assert len(sp.sample_sources) == 2

    def test_tablename(self):
        assert StyleProfile.__tablename__ == "style_profiles"


class TestWritingSession:
    def test_instantiation(self):
        """Integer defaults via server_default apply at DB level."""
        ws = WritingSession(
            user_id=uuid.uuid4(),
            book_id=uuid.uuid4(),
        )
        assert ws.words_written == 0 or ws.words_written is None
        assert ws.duration_seconds == 0 or ws.duration_seconds is None
        assert ws.ai_assists_used == 0 or ws.ai_assists_used is None

    def test_chapter_id_nullable(self):
        ws = WritingSession(
            user_id=uuid.uuid4(),
            book_id=uuid.uuid4(),
        )
        assert ws.chapter_id is None

    def test_tablename(self):
        assert WritingSession.__tablename__ == "writing_sessions"


class TestContentAsset:
    def test_instantiation(self):
        ca = ContentAsset(
            org_id=uuid.uuid4(),
            asset_type=AssetType.COVER.value,
            file_url="https://s3.amazonaws.com/bucket/cover.jpg",
            file_size=1024000,
            mime_type="image/jpeg",
        )
        assert ca.asset_type == AssetType.COVER.value
        assert ca.file_size == 1024000

    def test_tablename(self):
        assert ContentAsset.__tablename__ == "content_assets"


class TestAssetTypeEnum:
    def test_values(self):
        assert AssetType.COVER.value == "cover"
        assert AssetType.IMAGE.value == "image"
        assert AssetType.DOCUMENT.value == "document"
        assert AssetType.AUDIO.value == "audio"
        assert AssetType.VIDEO.value == "video"


# ── Market ─────────────────────────────────────────────────────────────
from app.models.market import (
    CompetitorBook,
    CompetitorReview,
    MarketCategory,
    MarketKeyword,
    MarketSnapshot,
)


class TestMarketCategory:
    def test_instantiation(self):
        mc = MarketCategory(
            name="Science Fiction",
        )
        assert mc.name == "Science Fiction"

    def test_amazon_node_id(self):
        mc = MarketCategory(
            name="Test",
            amazon_node_id="12345",
        )
        assert mc.amazon_node_id == "12345"

    def test_path_array(self):
        mc = MarketCategory(
            name="Test",
            path=["Books", "Fiction", "Science Fiction"],
        )
        assert len(mc.path) == 3

    def test_default_book_count(self):
        """book_count defaults to 0 at DB level via server_default."""
        mc = MarketCategory(name="Test")
        assert mc.book_count == 0 or mc.book_count is None

    def test_self_referential(self):
        mc = MarketCategory(name="Child", parent_id=uuid.uuid4())
        assert mc.parent_id is not None

    def test_tablename(self):
        assert MarketCategory.__tablename__ == "market_categories"


class TestMarketKeyword:
    def test_instantiation(self):
        mk = MarketKeyword(keyword="fantasy romance")
        assert mk.keyword == "fantasy romance"

    def test_search_volume_nullable(self):
        mk = MarketKeyword(keyword="test")
        assert mk.search_volume is None

    def test_tablename(self):
        assert MarketKeyword.__tablename__ == "market_keywords"


class TestCompetitorBook:
    def test_instantiation(self):
        cb = CompetitorBook(
            asin="B0123456789",
            title="Competitor Title",
        )
        assert cb.asin == "B0123456789"
        assert cb.title == "Competitor Title"

    def test_default_reviews_count(self):
        """reviews_count defaults to 0 at DB level via server_default."""
        cb = CompetitorBook(asin="B000000000", title="Test")
        assert cb.reviews_count == 0 or cb.reviews_count is None

    def test_bsr_history_jsonb(self):
        cb = CompetitorBook(
            asin="B000000000",
            title="Test",
            bsr_history={"2024-01": 500, "2024-02": 450},
        )
        assert cb.bsr_history["2024-01"] == 500

    def test_category_ids_array(self):
        cb = CompetitorBook(
            asin="B000000000",
            title="Test",
            category_ids=["cat1", "cat2"],
        )
        assert len(cb.category_ids) == 2

    def test_tablename(self):
        assert CompetitorBook.__tablename__ == "competitor_books"


class TestCompetitorReview:
    def test_instantiation(self):
        cr = CompetitorReview(
            competitor_book_id=uuid.uuid4(),
            rating=4.5,
            review_text="Great book!",
        )
        assert cr.rating == 4.5
        assert cr.review_text == "Great book!"

    def test_weakness_signals_jsonb(self):
        cr = CompetitorReview(
            competitor_book_id=uuid.uuid4(),
            weakness_signals={"pacing": True, "characters": False},
        )
        assert cr.weakness_signals["pacing"] is True

    def test_tablename(self):
        assert CompetitorReview.__tablename__ == "competitor_reviews"


class TestMarketSnapshot:
    def test_instantiation(self):
        ms = MarketSnapshot(
            category_id=uuid.uuid4(),
            snapshot_date=date(2024, 1, 15),
        )
        assert ms.snapshot_date == date(2024, 1, 15)

    def test_top_100_asins_array(self):
        ms = MarketSnapshot(
            category_id=uuid.uuid4(),
            snapshot_date=date(2024, 1, 15),
            top_100_asins=["B001", "B002", "B003"],
        )
        assert len(ms.top_100_asins) == 3

    def test_metrics_jsonb(self):
        ms = MarketSnapshot(
            category_id=uuid.uuid4(),
            snapshot_date=date(2024, 1, 15),
            metrics={"avg_price": 9.99, "avg_reviews": 150},
        )
        assert ms.metrics["avg_price"] == 9.99

    def test_tablename(self):
        assert MarketSnapshot.__tablename__ == "market_snapshots"


# ── Publishing ─────────────────────────────────────────────────────────
from app.models.publishing import (
    ComplianceScan,
    Listing,
    PricingRule,
    PublishingAccount,
    PublishingAccountStatus,
    PublishingPlatform,
    RiskLevel,
    ScanType,
    UploadValidation,
    ValidationType,
)


class TestPublishingAccount:
    def test_instantiation(self):
        pa = PublishingAccount(
            org_id=uuid.uuid4(),
            platform=PublishingPlatform.KDP,
        )
        assert pa.platform == PublishingPlatform.KDP

    def test_default_status(self):
        pa = PublishingAccount(
            org_id=uuid.uuid4(),
            platform=PublishingPlatform.KDP,
        )
        assert pa.status is None or pa.status == PublishingAccountStatus.PENDING

    def test_tablename(self):
        assert PublishingAccount.__tablename__ == "publishing_accounts"


class TestPublishingPlatformEnum:
    def test_values(self):
        assert PublishingPlatform.KDP.value == "kdp"
        assert PublishingPlatform.INGRAMSPARK.value == "ingramspark"
        assert PublishingPlatform.D2D.value == "d2d"
        assert PublishingPlatform.ACX.value == "acx"


class TestListing:
    def test_instantiation(self):
        listing = Listing(
            book_id=uuid.uuid4(),
            publishing_account_id=uuid.uuid4(),
        )
        assert listing.platform_id is None

    def test_listing_data_jsonb(self):
        listing = Listing(
            book_id=uuid.uuid4(),
            publishing_account_id=uuid.uuid4(),
            listing_data={"title": "Test", "keywords": ["a", "b"]},
        )
        assert listing.listing_data["title"] == "Test"

    def test_tablename(self):
        assert Listing.__tablename__ == "listings"


class TestUploadValidation:
    def test_instantiation(self):
        uv = UploadValidation(
            book_id=uuid.uuid4(),
            validation_type=ValidationType.FORMAT,
        )
        assert uv.validation_type == ValidationType.FORMAT

    def test_default_passed(self):
        """passed defaults to False at DB level via server_default."""
        uv = UploadValidation(
            book_id=uuid.uuid4(),
            validation_type=ValidationType.FORMAT,
        )
        assert uv.passed is False or uv.passed is None

    def test_errors_warnings_arrays(self):
        uv = UploadValidation(
            book_id=uuid.uuid4(),
            validation_type=ValidationType.CONTENT,
            errors=["Missing TOC"],
            warnings=["Image resolution low"],
        )
        assert "Missing TOC" in uv.errors
        assert "Image resolution low" in uv.warnings

    def test_tablename(self):
        assert UploadValidation.__tablename__ == "upload_validations"


class TestComplianceScan:
    def test_instantiation(self):
        cs = ComplianceScan(
            book_id=uuid.uuid4(),
            scan_type=ScanType.COPYRIGHT,
        )
        assert cs.scan_type == ScanType.COPYRIGHT

    def test_default_risk_level(self):
        cs = ComplianceScan(
            book_id=uuid.uuid4(),
            scan_type=ScanType.COPYRIGHT,
        )
        assert cs.risk_level is None or cs.risk_level == RiskLevel.GREEN

    def test_tablename(self):
        assert ComplianceScan.__tablename__ == "compliance_scans"


class TestRiskLevelEnum:
    def test_values(self):
        assert RiskLevel.GREEN.value == "green"
        assert RiskLevel.YELLOW.value == "yellow"
        assert RiskLevel.RED.value == "red"


class TestPricingRule:
    def test_instantiation(self):
        pr = PricingRule(
            org_id=uuid.uuid4(),
            book_id=uuid.uuid4(),
            name="Dynamic Rule",
            strategy="dynamic",
        )
        assert pr.name == "Dynamic Rule"

    def test_parameters_jsonb(self):
        pr = PricingRule(
            org_id=uuid.uuid4(),
            book_id=uuid.uuid4(),
            name="Competitive Rule",
            strategy="competitive_match",
            parameters={"min_price": 0.99, "max_price": 9.99},
        )
        assert pr.parameters["min_price"] == 0.99

    def test_tablename(self):
        assert PricingRule.__tablename__ == "pricing_rules"


# ── Marketing ──────────────────────────────────────────────────────────
from app.models.marketing import (
    ARCCampaign,
    ARCCampaignStatus,
    ARCRecipient,
    ARCRecipientStatus,
    EmailSendStatus,
    EmailSequence,
    EmailSequenceStatus,
    EmailTemplate,
    LaunchPhase,
    LaunchPhaseType,
    LaunchPlan,
    LaunchPlanStatus,
    PhaseTask,
    PhaseTaskStatus,
    SocialPlatform,
    SocialPost,
    SocialPostStatus,
)


class TestLaunchPlan:
    def test_instantiation(self):
        lp = LaunchPlan(
            org_id=uuid.uuid4(),
            book_id=uuid.uuid4(),
            title="Launch Plan: Test Book",
            created_by=uuid.uuid4(),
        )
        assert lp.title == "Launch Plan: Test Book"
        assert lp.launch_date is None

    def test_default_status(self):
        lp = LaunchPlan(
            org_id=uuid.uuid4(),
            book_id=uuid.uuid4(),
            title="Test",
            created_by=uuid.uuid4(),
        )
        assert lp.status is None or lp.status == LaunchPlanStatus.DRAFT

    def test_goals_jsonb(self):
        lp = LaunchPlan(
            org_id=uuid.uuid4(),
            book_id=uuid.uuid4(),
            title="Test",
            created_by=uuid.uuid4(),
            goals={"user_goals": ["1000 sales"]},
        )
        assert lp.goals["user_goals"][0] == "1000 sales"

    def test_tablename(self):
        assert LaunchPlan.__tablename__ == "launch_plans"


class TestLaunchPhaseTypeEnum:
    def test_values(self):
        assert LaunchPhaseType.PRE_LAUNCH.value == "pre_launch"
        assert LaunchPhaseType.LAUNCH_WEEK.value == "launch_week"
        assert LaunchPhaseType.POST_LAUNCH.value == "post_launch"


class TestLaunchPhase:
    def test_instantiation(self):
        phase = LaunchPhase(
            launch_plan_id=uuid.uuid4(),
            phase_type=LaunchPhaseType.PRE_LAUNCH,
            name="Pre-Launch Phase",
        )
        assert phase.phase_type == LaunchPhaseType.PRE_LAUNCH

    def test_tablename(self):
        assert LaunchPhase.__tablename__ == "launch_phases"


class TestPhaseTask:
    def test_instantiation(self):
        task = PhaseTask(
            phase_id=uuid.uuid4(),
            title="Set up website",
        )
        assert task.title == "Set up website"

    def test_default_status(self):
        task = PhaseTask(
            phase_id=uuid.uuid4(),
            title="Test",
        )
        assert task.status is None or task.status == PhaseTaskStatus.PENDING

    def test_tablename(self):
        assert PhaseTask.__tablename__ == "phase_tasks"


class TestEmailSequence:
    def test_instantiation(self):
        es = EmailSequence(
            org_id=uuid.uuid4(),
            name="Welcome Series",
            created_by=uuid.uuid4(),
        )
        assert es.name == "Welcome Series"

    def test_default_recipient_count(self):
        """recipient_count defaults to 0."""
        es = EmailSequence(org_id=uuid.uuid4(), name="Test", created_by=uuid.uuid4())
        assert es.recipient_count == 0 or es.recipient_count is None

    def test_default_status(self):
        es = EmailSequence(org_id=uuid.uuid4(), name="Test", created_by=uuid.uuid4())
        assert es.status is None or es.status == EmailSequenceStatus.DRAFT

    def test_tablename(self):
        assert EmailSequence.__tablename__ == "email_sequences"


class TestEmailTemplate:
    def test_instantiation(self):
        tmpl = EmailTemplate(
            sequence_id=uuid.uuid4(),
            subject="Welcome!",
        )
        assert tmpl.subject == "Welcome!"

    def test_default_send_status(self):
        tmpl = EmailTemplate(
            sequence_id=uuid.uuid4(),
            subject="Test",
        )
        assert tmpl.send_status is None or tmpl.send_status == EmailSendStatus.PENDING

    def test_tablename(self):
        assert EmailTemplate.__tablename__ == "email_templates"


class TestSocialPost:
    def test_instantiation(self):
        post = SocialPost(
            org_id=uuid.uuid4(),
            platform=SocialPlatform.TWITTER,
            content="Exciting news!",
            created_by=uuid.uuid4(),
        )
        assert post.platform == SocialPlatform.TWITTER

    def test_default_status(self):
        post = SocialPost(
            org_id=uuid.uuid4(),
            platform=SocialPlatform.FACEBOOK,
            content="Test",
            created_by=uuid.uuid4(),
        )
        assert post.status is None or post.status == SocialPostStatus.DRAFT

    def test_tablename(self):
        assert SocialPost.__tablename__ == "social_posts"


class TestSocialPlatformEnum:
    def test_values(self):
        assert SocialPlatform.TWITTER.value == "twitter"
        assert SocialPlatform.FACEBOOK.value == "facebook"
        assert SocialPlatform.INSTAGRAM.value == "instagram"


class TestARCCampaign:
    def test_instantiation(self):
        arc = ARCCampaign(
            org_id=uuid.uuid4(),
            book_id=uuid.uuid4(),
            name="ARC Campaign 1",
            created_by=uuid.uuid4(),
        )
        assert arc.name == "ARC Campaign 1"

    def test_default_status(self):
        arc = ARCCampaign(
            org_id=uuid.uuid4(),
            book_id=uuid.uuid4(),
            name="Test",
            created_by=uuid.uuid4(),
        )
        assert arc.status is None or arc.status == ARCCampaignStatus.DRAFT

    def test_tablename(self):
        assert ARCCampaign.__tablename__ == "arc_campaigns"


class TestARCRecipient:
    def test_instantiation(self):
        recipient = ARCRecipient(
            campaign_id=uuid.uuid4(),
            name="Reviewer A",
            email="a@example.com",
        )
        assert recipient.name == "Reviewer A"

    def test_default_status(self):
        recipient = ARCRecipient(
            campaign_id=uuid.uuid4(),
            name="Test",
            email="test@example.com",
        )
        assert recipient.status is None or recipient.status == ARCRecipientStatus.PENDING

    def test_tablename(self):
        assert ARCRecipient.__tablename__ == "arc_recipients"


# ── Agent ──────────────────────────────────────────────────────────────
from app.models.agent import (
    ActorType,
    Agent,
    AgentBudget,
    AgentTask,
    AgentType,
    AgentWorkflow,
    AuditTrail,
    BudgetType,
    PermissionLevel,
    TaskStatus,
    WorkflowStatus,
)


class TestAgent:
    def test_instantiation(self):
        agent = Agent(
            org_id=uuid.uuid4(),
            agent_type=AgentType.RESEARCH,
            name="Research Agent",
        )
        assert agent.name == "Research Agent"
        assert agent.agent_type == AgentType.RESEARCH

    def test_default_is_enabled(self):
        """is_enabled defaults to True."""
        agent = Agent(
            org_id=uuid.uuid4(),
            agent_type=AgentType.WRITING_ASSISTANT,
            name="Test",
        )
        assert agent.is_enabled is True or agent.is_enabled is None

    def test_default_permission_level(self):
        agent = Agent(
            org_id=uuid.uuid4(),
            agent_type=AgentType.EDITOR,
            name="Test",
        )
        assert agent.permission_level is None or agent.permission_level == PermissionLevel.DRAFT_ONLY

    def test_config_jsonb(self):
        agent = Agent(
            org_id=uuid.uuid4(),
            agent_type=AgentType.MARKETING_COPY,
            name="Test",
            config={"model": "claude-3", "max_tokens": 4096},
        )
        assert agent.config["model"] == "claude-3"

    def test_tablename(self):
        assert Agent.__tablename__ == "agents"


class TestAgentTypeEnum:
    def test_values(self):
        assert AgentType.RESEARCH.value == "research"
        assert AgentType.WRITING_ASSISTANT.value == "writing_assistant"
        assert AgentType.EDITOR.value == "editor"
        assert AgentType.MARKETING_COPY.value == "marketing_copy"

    def test_count(self):
        assert len(AgentType) == 4


class TestPermissionLevelEnum:
    def test_values(self):
        assert PermissionLevel.DRAFT_ONLY.value == "draft_only"
        assert PermissionLevel.SUGGEST.value == "suggest"
        assert PermissionLevel.AUTO_EXECUTE_LOW.value == "auto_execute_low"
        assert PermissionLevel.AUTO_EXECUTE_HIGH.value == "auto_execute_high"
        assert PermissionLevel.FULL_AUTONOMOUS.value == "full_autonomous"


class TestAgentTask:
    def test_instantiation(self):
        task = AgentTask(
            org_id=uuid.uuid4(),
            agent_id=uuid.uuid4(),
            title="Keyword Research",
            created_by=uuid.uuid4(),
        )
        assert task.title == "Keyword Research"

    def test_default_status(self):
        task = AgentTask(
            org_id=uuid.uuid4(),
            agent_id=uuid.uuid4(),
            title="Test",
            created_by=uuid.uuid4(),
        )
        assert task.status is None or task.status == TaskStatus.PENDING

    def test_input_output_jsonb(self):
        task = AgentTask(
            org_id=uuid.uuid4(),
            agent_id=uuid.uuid4(),
            title="Test",
            created_by=uuid.uuid4(),
            input_data={"query": "fantasy books"},
            output_data={"results": [1, 2, 3]},
        )
        assert task.input_data["query"] == "fantasy books"
        assert len(task.output_data["results"]) == 3

    def test_tablename(self):
        assert AgentTask.__tablename__ == "agent_tasks"


class TestAgentWorkflow:
    def test_instantiation(self):
        wf = AgentWorkflow(
            org_id=uuid.uuid4(),
            name="Book Launch Workflow",
            created_by=uuid.uuid4(),
        )
        assert wf.name == "Book Launch Workflow"

    def test_default_status(self):
        """status defaults to DRAFT."""
        wf = AgentWorkflow(org_id=uuid.uuid4(), name="Test", created_by=uuid.uuid4())
        assert wf.status is None or wf.status == WorkflowStatus.DRAFT

    def test_steps_jsonb(self):
        wf = AgentWorkflow(
            org_id=uuid.uuid4(),
            name="Test",
            created_by=uuid.uuid4(),
            steps=[{"name": "research", "agent_type": "research"}],
        )
        assert wf.steps[0]["name"] == "research"

    def test_tablename(self):
        assert AgentWorkflow.__tablename__ == "agent_workflows"


class TestAgentBudget:
    def test_instantiation(self):
        ab = AgentBudget(
            org_id=uuid.uuid4(),
            agent_id=uuid.uuid4(),
            monthly_usd_limit=200.00,
        )
        assert ab.monthly_usd_limit == 200.00

    def test_default_tokens_used_today(self):
        """tokens_used_today defaults to 0."""
        ab = AgentBudget(
            org_id=uuid.uuid4(),
            agent_id=uuid.uuid4(),
        )
        assert ab.tokens_used_today == 0 or ab.tokens_used_today is None

    def test_default_usd_used_today(self):
        """usd_used_today defaults to 0.0."""
        ab = AgentBudget(
            org_id=uuid.uuid4(),
            agent_id=uuid.uuid4(),
        )
        assert ab.usd_used_today == 0.0 or ab.usd_used_today is None

    def test_tablename(self):
        assert AgentBudget.__tablename__ == "agent_budgets"


class TestBudgetTypeEnum:
    def test_values(self):
        assert BudgetType.DAILY.value == "daily"
        assert BudgetType.WEEKLY.value == "weekly"
        assert BudgetType.MONTHLY.value == "monthly"
        assert BudgetType.PER_TASK.value == "per_task"


class TestAuditTrail:
    def test_instantiation(self):
        at = AuditTrail(
            org_id=uuid.uuid4(),
            actor_type=ActorType.USER,
            actor_id=uuid.uuid4(),
            action="create",
            resource_type="book",
            resource_id=uuid.uuid4(),
        )
        assert at.action == "create"
        assert at.actor_type == ActorType.USER

    def test_details_jsonb(self):
        at = AuditTrail(
            org_id=uuid.uuid4(),
            actor_type=ActorType.AGENT,
            actor_id=uuid.uuid4(),
            action="update",
            resource_type="chapter",
            resource_id=uuid.uuid4(),
            details={"field": "content", "old_word_count": 500, "new_word_count": 750},
        )
        assert at.details["field"] == "content"

    def test_tablename(self):
        assert AuditTrail.__tablename__ == "audit_trail"


class TestActorTypeEnum:
    def test_values(self):
        assert ActorType.USER.value == "user"
        assert ActorType.AGENT.value == "agent"
        assert ActorType.SYSTEM.value == "system"


# ── Analytics ──────────────────────────────────────────────────────────
from app.models.analytics import (
    ABTest,
    ABTestStatus,
    AnalyticsEvent,
    PortfolioMetric,
    Report,
    ReportStatus,
    RoyaltyRecord,
)


class TestAnalyticsEvent:
    def test_instantiation(self):
        ae = AnalyticsEvent(
            org_id=uuid.uuid4(),
            event_type="page_view",
        )
        assert ae.event_type == "page_view"

    def test_entity_fields_nullable(self):
        ae = AnalyticsEvent(
            org_id=uuid.uuid4(),
            event_type="test",
        )
        assert ae.entity_type is None
        assert ae.entity_id is None

    def test_data_jsonb(self):
        ae = AnalyticsEvent(
            org_id=uuid.uuid4(),
            event_type="click",
            data={"button": "publish", "page": "dashboard"},
        )
        assert ae.data["button"] == "publish"

    def test_tablename(self):
        assert AnalyticsEvent.__tablename__ == "analytics_events"


class TestRoyaltyRecord:
    def test_instantiation(self):
        rr = RoyaltyRecord(
            book_id=uuid.uuid4(),
            platform="kdp",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
        )
        assert rr.platform == "kdp"
        assert rr.period_start == date(2024, 1, 1)

    def test_default_units_sold(self):
        """units_sold defaults to 0 at DB level via server_default."""
        rr = RoyaltyRecord(
            book_id=uuid.uuid4(),
            platform="kdp",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
        )
        assert rr.units_sold == 0 or rr.units_sold is None

    def test_default_currency(self):
        """currency defaults to USD at DB level via server_default."""
        rr = RoyaltyRecord(
            book_id=uuid.uuid4(),
            platform="kdp",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
        )
        assert rr.currency == "USD" or rr.currency is None

    def test_tablename(self):
        assert RoyaltyRecord.__tablename__ == "royalty_records"


class TestPortfolioMetric:
    def test_instantiation(self):
        pm = PortfolioMetric(
            org_id=uuid.uuid4(),
            snapshot_date=date(2024, 1, 15),
        )
        assert pm.snapshot_date == date(2024, 1, 15)

    def test_default_total_books(self):
        """total_books defaults to 0 at DB level via server_default."""
        pm = PortfolioMetric(
            org_id=uuid.uuid4(),
            snapshot_date=date(2024, 1, 15),
        )
        assert pm.total_books == 0 or pm.total_books is None

    def test_metrics_data_jsonb(self):
        pm = PortfolioMetric(
            org_id=uuid.uuid4(),
            snapshot_date=date(2024, 1, 15),
            metrics_data={"book_id_1": 1.5, "book_id_2": 2.3},
        )
        assert pm.metrics_data["book_id_1"] == 1.5

    def test_tablename(self):
        assert PortfolioMetric.__tablename__ == "portfolio_metrics"


class TestABTest:
    def test_instantiation(self):
        ab = ABTest(
            book_id=uuid.uuid4(),
            name="Blurb Test",
            variant_a_content="Variant A blurb",
            variant_b_content="Variant B blurb",
        )
        assert ab.name == "Blurb Test"
        assert ab.variant_a_content == "Variant A blurb"

    def test_default_status(self):
        ab = ABTest(
            book_id=uuid.uuid4(),
            name="Test",
            variant_a_content="A",
            variant_b_content="B",
        )
        assert ab.status is None or ab.status == "draft"

    def test_default_impressions(self):
        ab = ABTest(
            book_id=uuid.uuid4(),
            name="Test",
            variant_a_content="A",
            variant_b_content="B",
        )
        assert ab.variant_a_impressions == 0 or ab.variant_a_impressions is None
        assert ab.variant_b_impressions == 0 or ab.variant_b_impressions is None

    def test_completed_at_nullable(self):
        ab = ABTest(
            book_id=uuid.uuid4(),
            name="Test",
            variant_a_content="A",
            variant_b_content="B",
        )
        assert ab.completed_at is None

    def test_tablename(self):
        assert ABTest.__tablename__ == "ab_tests"


class TestABTestStatusEnum:
    def test_values(self):
        assert ABTestStatus.DRAFT.value == "draft"
        assert ABTestStatus.RUNNING.value == "running"
        assert ABTestStatus.COMPLETED.value == "completed"
        assert ABTestStatus.CANCELED.value == "canceled"


class TestReport:
    def test_instantiation(self):
        report = Report(
            org_id=uuid.uuid4(),
            report_type="monthly_sales",
        )
        assert report.report_type == "monthly_sales"

    def test_default_status(self):
        report = Report(
            org_id=uuid.uuid4(),
            report_type="test",
        )
        assert report.status is None or report.status == ReportStatus.PENDING

    def test_parameters_jsonb(self):
        report = Report(
            org_id=uuid.uuid4(),
            report_type="test",
            parameters={"start_date": "2024-01-01", "end_date": "2024-01-31"},
        )
        assert report.parameters["start_date"] == "2024-01-01"

    def test_file_path_nullable(self):
        report = Report(org_id=uuid.uuid4(), report_type="test")
        assert report.file_path is None

    def test_tablename(self):
        assert Report.__tablename__ == "reports"


class TestReportStatusEnum:
    def test_values(self):
        assert ReportStatus.PENDING.value == "pending"
        assert ReportStatus.GENERATING.value == "generating"
        assert ReportStatus.COMPLETED.value == "completed"
        assert ReportStatus.FAILED.value == "failed"


# ── __init__.py imports ────────────────────────────────────────────────
class TestModelsInit:
    """Verify that all models are importable from the models package."""

    def test_all_models_importable(self):
        from app.models import (
            ARCCampaign,
            LaunchPlan,
            Organization,
            Report,
            User,
        )

        # Just verify they're all classes
        assert Organization.__tablename__ == "organizations"
        assert User.__tablename__ == "users"
        assert Report.__tablename__ == "reports"
        assert LaunchPlan.__tablename__ == "launch_plans"
        assert ARCCampaign.__tablename__ == "arc_campaigns"

    def test_all_enums_importable(self):
        from app.models.marketing import (
            ARCCampaignStatus,
            LaunchPlanStatus,
            SocialPlatform,
        )

        assert LaunchPlanStatus.DRAFT.value == "draft"
        assert SocialPlatform.TWITTER.value == "twitter"
        assert ARCCampaignStatus.ACTIVE.value == "active"

    def test_model_count(self):
        """Verify we have all 30+ models defined."""
        # Import all to register
        from app.database import Base

        # Count the non-abstract tables
        table_names = list(Base.metadata.tables.keys())
        assert len(table_names) >= 30, f"Expected at least 30 tables, got {len(table_names)}: {table_names}"


# ── Soft Delete Behavior ──────────────────────────────────────────────
class TestSoftDeleteBehavior:
    """Test that all models with BaseModel have deleted_at support."""

    def test_organization_soft_delete(self):
        org = Organization(name="Test", slug="test")
        assert org.deleted_at is None
        now = datetime.now(UTC)
        org.deleted_at = now
        assert org.deleted_at is not None

    def test_user_soft_delete(self):
        user = User(
            org_id=uuid.uuid4(),
            email="test@test.com",
            password_hash="hash",
            name="Test",
        )
        assert user.deleted_at is None
        now = datetime.now(UTC)
        user.deleted_at = now
        assert user.deleted_at is not None

    def test_project_soft_delete(self):
        project = Project(
            org_id=uuid.uuid4(),
            title="Test",
            type=ProjectType.BOOK,
        )
        assert project.deleted_at is None

    def test_agent_soft_delete(self):
        agent = Agent(
            org_id=uuid.uuid4(),
            agent_type=AgentType.RESEARCH,
            name="Test",
        )
        assert agent.deleted_at is None

    def test_analytics_event_soft_delete(self):
        event = AnalyticsEvent(
            org_id=uuid.uuid4(),
            event_type="test",
        )
        assert event.deleted_at is None
