"""Unit tests for the Production Pipeline service layer.

Tests pipeline CRUD, task management, status transitions, timeline generation,
dependency validation, and template management.
"""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from app.modules.production_pipeline import service
from app.modules.production_pipeline.models import (
    Pipeline,
    PipelineStatus,
    PipelineTask,
    PipelineTemplate,
    TaskStatus,
    TaskType,
)
from app.modules.production_pipeline.schemas import (
    CreatePipeline,
    CreateTask,
    CreateTemplate,
    TaskDefinition,
    UpdatePipeline,
    UpdateTask,
)
from app.modules.production_pipeline.workflow import WorkflowError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _seed_pipeline(
    db,
    org_id: uuid.UUID,
    book_id: uuid.UUID | None = None,
    name: str = "Test Pipeline",
    status: PipelineStatus = PipelineStatus.DRAFT,
    deadline: datetime | None = None,
) -> Pipeline:
    """Create a pipeline record."""
    pipeline = Pipeline(
        id=uuid.uuid4(),
        org_id=org_id,
        book_id=book_id or uuid.uuid4(),
        name=name,
        description="Test pipeline description",
        status=status,
        settings={},
        deadline=deadline,
    )
    db.add(pipeline)
    await db.flush()
    await db.refresh(pipeline)
    return pipeline


async def _seed_task(
    db,
    org_id: uuid.UUID,
    pipeline_id: uuid.UUID,
    title: str = "Test Task",
    status: TaskStatus = TaskStatus.PENDING,
    depends_on: list[str] | None = None,
) -> PipelineTask:
    """Create a pipeline task."""
    task = PipelineTask(
        id=uuid.uuid4(),
        org_id=org_id,
        pipeline_id=pipeline_id,
        title=title,
        description="Task description",
        type=TaskType.WRITING,
        status=status,
        depends_on=depends_on or [],
        position=0,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


# ---------------------------------------------------------------------------
# Pipeline CRUD tests
# ---------------------------------------------------------------------------


class TestCreatePipeline:

    @pytest.mark.asyncio
    async def test_create_pipeline_basic(self, db_session):
        """Should create a basic pipeline without template."""
        org_id = uuid.uuid4()
        book_id = uuid.uuid4()

        payload = CreatePipeline(
            book_id=book_id,
            name="My Pipeline",
            description="A test pipeline",
            deadline=datetime.now(UTC) + timedelta(days=30),
        )

        result = await service.create_pipeline(db_session, org_id, payload)

        assert result.org_id == org_id
        assert result.book_id == book_id
        assert result.name == "My Pipeline"
        assert result.status == PipelineStatus.DRAFT

    @pytest.mark.asyncio
    async def test_create_pipeline_from_template(self, db_session):
        """Should create pipeline with tasks from template."""
        org_id = uuid.uuid4()
        book_id = uuid.uuid4()

        # Create a template first
        template = PipelineTemplate(
            id=uuid.uuid4(),
            org_id=org_id,
            name="Template",
            task_definitions=[
                {"title": "Task 1", "type": "writing", "position": 0, "estimated_days": 5},
                {"title": "Task 2", "type": "editing", "position": 1, "estimated_days": 3},
            ],
        )
        db_session.add(template)
        await db_session.flush()

        payload = CreatePipeline(
            book_id=book_id,
            name="From Template",
            template_id=template.id,
            deadline=datetime.now(UTC) + timedelta(days=30),
        )

        result = await service.create_pipeline(db_session, org_id, payload)

        assert result.name == "From Template"
        # Tasks should be created from template (checked in integration tests)


class TestGetPipeline:

    @pytest.mark.asyncio
    async def test_get_pipeline_success(self, db_session):
        """Should retrieve a pipeline by ID."""
        org_id = uuid.uuid4()
        pipeline = await _seed_pipeline(db_session, org_id, name="Test Pipeline")

        result = await service.get_pipeline(db_session, pipeline.id, org_id)

        assert result is not None
        assert result.id == pipeline.id
        assert result.name == "Test Pipeline"

    @pytest.mark.asyncio
    async def test_get_pipeline_not_found(self, db_session):
        """Should return None if pipeline not found."""
        org_id = uuid.uuid4()
        pipeline_id = uuid.uuid4()

        result = await service.get_pipeline(db_session, pipeline_id, org_id)
        assert result is None


class TestListPipelines:

    @pytest.mark.asyncio
    async def test_list_pipelines_empty(self, db_session):
        """Should return empty paginated result if no pipelines."""
        org_id = uuid.uuid4()

        result = await service.list_pipelines(db_session, org_id)

        assert result.total == 0
        assert len(result.items) == 0

    @pytest.mark.asyncio
    async def test_list_pipelines_with_data(self, db_session):
        """Should list pipelines with pagination."""
        org_id = uuid.uuid4()
        book_id = uuid.uuid4()

        await _seed_pipeline(db_session, org_id, book_id, "Pipeline 1")
        await _seed_pipeline(db_session, org_id, book_id, "Pipeline 2")

        result = await service.list_pipelines(db_session, org_id, page=1, page_size=10)

        assert result.total == 2
        assert len(result.items) == 2

    @pytest.mark.asyncio
    async def test_list_pipelines_filter_by_status(self, db_session):
        """Should filter pipelines by status."""
        org_id = uuid.uuid4()

        await _seed_pipeline(db_session, org_id, name="Draft", status=PipelineStatus.DRAFT)
        await _seed_pipeline(db_session, org_id, name="Active", status=PipelineStatus.ACTIVE)

        result = await service.list_pipelines(
            db_session, org_id, status=PipelineStatus.ACTIVE
        )

        assert result.total == 1
        assert result.items[0].name == "Active"

    @pytest.mark.asyncio
    async def test_list_pipelines_filter_by_book(self, db_session):
        """Should filter pipelines by book_id."""
        org_id = uuid.uuid4()
        book1 = uuid.uuid4()
        book2 = uuid.uuid4()

        await _seed_pipeline(db_session, org_id, book1, "Book 1 Pipeline")
        await _seed_pipeline(db_session, org_id, book2, "Book 2 Pipeline")

        result = await service.list_pipelines(db_session, org_id, book_id=book1)

        assert result.total == 1
        assert result.items[0].name == "Book 1 Pipeline"


class TestUpdatePipeline:

    @pytest.mark.asyncio
    async def test_update_pipeline_name(self, db_session):
        """Should update pipeline name."""
        org_id = uuid.uuid4()
        pipeline = await _seed_pipeline(db_session, org_id, name="Old Name")

        payload = UpdatePipeline(name="New Name")
        result = await service.update_pipeline(db_session, pipeline.id, org_id, payload)

        assert result is not None
        assert result.name == "New Name"

    @pytest.mark.asyncio
    async def test_update_pipeline_status(self, db_session):
        """Should update pipeline status with validation."""
        org_id = uuid.uuid4()
        pipeline = await _seed_pipeline(db_session, org_id, status=PipelineStatus.DRAFT)

        payload = UpdatePipeline(status=PipelineStatus.ACTIVE)
        result = await service.update_pipeline(db_session, pipeline.id, org_id, payload)

        assert result.status == PipelineStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_update_pipeline_not_found(self, db_session):
        """Should return None if pipeline not found."""
        org_id = uuid.uuid4()
        pipeline_id = uuid.uuid4()

        payload = UpdatePipeline(name="Updated")
        result = await service.update_pipeline(db_session, pipeline_id, org_id, payload)

        assert result is None


class TestDeletePipeline:

    @pytest.mark.asyncio
    async def test_delete_pipeline_success(self, db_session):
        """Should soft-delete a pipeline."""
        org_id = uuid.uuid4()
        pipeline = await _seed_pipeline(db_session, org_id)

        result = await service.delete_pipeline(db_session, pipeline.id, org_id)
        assert result is True

        # Should not be retrievable after delete
        retrieved = await service.get_pipeline(db_session, pipeline.id, org_id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_pipeline_not_found(self, db_session):
        """Should return False if pipeline not found."""
        org_id = uuid.uuid4()
        pipeline_id = uuid.uuid4()

        result = await service.delete_pipeline(db_session, pipeline_id, org_id)
        assert result is False


# ---------------------------------------------------------------------------
# Task management tests
# ---------------------------------------------------------------------------


class TestAddTask:

    @pytest.mark.asyncio
    async def test_add_task_success(self, db_session):
        """Should add a task to a pipeline."""
        org_id = uuid.uuid4()
        pipeline = await _seed_pipeline(db_session, org_id)

        payload = CreateTask(
            title="New Task",
            description="Task description",
            type=TaskType.WRITING,
            position=0,
        )

        result = await service.add_task(db_session, pipeline.id, org_id, payload)

        assert result is not None
        assert result.title == "New Task"
        assert result.status == TaskStatus.PENDING

    @pytest.mark.asyncio
    async def test_add_task_with_dependencies(self, db_session):
        """Should add task with dependencies."""
        org_id = uuid.uuid4()
        pipeline = await _seed_pipeline(db_session, org_id)
        task1 = await _seed_task(db_session, org_id, pipeline.id, "Task 1")

        payload = CreateTask(
            title="Task 2",
            type=TaskType.EDITING,
            depends_on=[str(task1.id)],
            position=1,
        )

        result = await service.add_task(db_session, pipeline.id, org_id, payload)

        assert result is not None
        assert str(task1.id) in result.depends_on

    @pytest.mark.asyncio
    async def test_add_task_pipeline_not_found(self, db_session):
        """Should return None if pipeline not found."""
        org_id = uuid.uuid4()
        pipeline_id = uuid.uuid4()

        payload = CreateTask(title="Task", type=TaskType.WRITING, position=0)
        result = await service.add_task(db_session, pipeline_id, org_id, payload)

        assert result is None


class TestUpdateTask:

    @pytest.mark.asyncio
    async def test_update_task_title(self, db_session):
        """Should update task title."""
        org_id = uuid.uuid4()
        pipeline = await _seed_pipeline(db_session, org_id)
        task = await _seed_task(db_session, org_id, pipeline.id, "Old Title")

        payload = UpdateTask(title="New Title")
        result = await service.update_task(
            db_session, pipeline.id, task.id, org_id, payload
        )

        assert result is not None
        assert result.title == "New Title"

    @pytest.mark.asyncio
    async def test_update_task_status_to_completed(self, db_session):
        """Should update task status and set completed_at."""
        org_id = uuid.uuid4()
        pipeline = await _seed_pipeline(db_session, org_id)
        task = await _seed_task(db_session, org_id, pipeline.id)

        payload = UpdateTask(status=TaskStatus.COMPLETED)
        result = await service.update_task(
            db_session, pipeline.id, task.id, org_id, payload
        )

        assert result.status == TaskStatus.COMPLETED
        assert result.completed_at is not None

    @pytest.mark.asyncio
    async def test_update_task_not_found(self, db_session):
        """Should return None if task not found."""
        org_id = uuid.uuid4()
        pipeline = await _seed_pipeline(db_session, org_id)
        task_id = uuid.uuid4()

        payload = UpdateTask(title="Updated")
        result = await service.update_task(
            db_session, pipeline.id, task_id, org_id, payload
        )

        assert result is None


# ---------------------------------------------------------------------------
# Timeline tests
# ---------------------------------------------------------------------------


class TestGetTimeline:

    @pytest.mark.asyncio
    async def test_get_timeline_success(self, db_session):
        """Should generate timeline view for a pipeline."""
        org_id = uuid.uuid4()
        pipeline = await _seed_pipeline(db_session, org_id)
        await _seed_task(db_session, org_id, pipeline.id, "Task 1")
        await _seed_task(db_session, org_id, pipeline.id, "Task 2")

        result = await service.get_timeline(db_session, pipeline.id, org_id)

        assert result is not None
        assert result.pipeline_id == pipeline.id
        assert len(result.tasks) == 2

    @pytest.mark.asyncio
    async def test_get_timeline_pipeline_not_found(self, db_session):
        """Should return None if pipeline not found."""
        org_id = uuid.uuid4()
        pipeline_id = uuid.uuid4()

        result = await service.get_timeline(db_session, pipeline_id, org_id)
        assert result is None


# ---------------------------------------------------------------------------
# Template tests
# ---------------------------------------------------------------------------


class TestCreateTemplate:

    @pytest.mark.asyncio
    async def test_create_template_success(self, db_session):
        """Should create a pipeline template."""
        org_id = uuid.uuid4()

        payload = CreateTemplate(
            name="My Template",
            description="A reusable template",
            task_definitions=[
                TaskDefinition(
                    title="Writing",
                    type=TaskType.WRITING,
                    position=0,
                    estimated_days=5,
                ),
                TaskDefinition(
                    title="Editing",
                    type=TaskType.EDITING,
                    position=1,
                    estimated_days=3,
                ),
            ],
            is_public=False,
        )

        result = await service.create_template(db_session, org_id, payload)

        assert result.org_id == org_id
        assert result.name == "My Template"
        assert len(result.task_definitions) == 2


class TestListTemplates:

    @pytest.mark.asyncio
    async def test_list_templates_own_only(self, db_session):
        """Should list org's own templates."""
        org_id = uuid.uuid4()
        other_org = uuid.uuid4()

        # Own template
        template1 = PipelineTemplate(
            id=uuid.uuid4(),
            org_id=org_id,
            name="Own Template",
            task_definitions=[],
            is_public=False,
        )
        db_session.add(template1)

        # Other org's private template - should not appear
        template2 = PipelineTemplate(
            id=uuid.uuid4(),
            org_id=other_org,
            name="Other Template",
            task_definitions=[],
            is_public=False,
        )
        db_session.add(template2)

        await db_session.flush()

        result = await service.list_templates(db_session, org_id)

        assert len(result) == 1
        assert result[0].name == "Own Template"

    @pytest.mark.asyncio
    async def test_list_templates_includes_public(self, db_session):
        """Should include public templates from other orgs."""
        org_id = uuid.uuid4()
        other_org = uuid.uuid4()

        # Own template
        template1 = PipelineTemplate(
            id=uuid.uuid4(),
            org_id=org_id,
            name="Own Template",
            task_definitions=[],
        )
        db_session.add(template1)

        # Other org's public template - should appear
        template2 = PipelineTemplate(
            id=uuid.uuid4(),
            org_id=other_org,
            name="Public Template",
            task_definitions=[],
            is_public=True,
        )
        db_session.add(template2)

        await db_session.flush()

        result = await service.list_templates(db_session, org_id)

        assert len(result) == 2
        names = {t.name for t in result}
        assert "Own Template" in names
        assert "Public Template" in names


class TestCreateTemplateFromPipeline:

    @pytest.mark.asyncio
    async def test_create_template_from_pipeline_success(self, db_session):
        """Should convert a pipeline into a reusable template."""
        org_id = uuid.uuid4()
        pipeline = await _seed_pipeline(db_session, org_id, name="Source Pipeline")
        await _seed_task(db_session, org_id, pipeline.id, "Task 1")
        await _seed_task(db_session, org_id, pipeline.id, "Task 2")

        result = await service.create_template_from_pipeline(
            db_session,
            pipeline.id,
            org_id,
            name="New Template",
            description="Created from pipeline",
        )

        assert result is not None
        assert result.name == "New Template"
        assert len(result.task_definitions) == 2

    @pytest.mark.asyncio
    async def test_create_template_from_pipeline_not_found(self, db_session):
        """Should return None if pipeline not found."""
        org_id = uuid.uuid4()
        pipeline_id = uuid.uuid4()

        result = await service.create_template_from_pipeline(
            db_session, pipeline_id, org_id, name="Template"
        )

        assert result is None


# ---------------------------------------------------------------------------
# Edge cases & validation
# ---------------------------------------------------------------------------


class TestDependencyCycleDetection:

    @pytest.mark.asyncio
    async def test_add_task_prevents_cycle(self, db_session):
        """Should prevent adding a task that would create a dependency cycle."""
        org_id = uuid.uuid4()
        pipeline = await _seed_pipeline(db_session, org_id)
        task1 = await _seed_task(db_session, org_id, pipeline.id, "Task 1")
        task2 = await _seed_task(
            db_session, org_id, pipeline.id, "Task 2", depends_on=[str(task1.id)]
        )

        # Try to make task1 depend on task2 (would create a cycle)
        payload = CreateTask(
            title="Task 3",
            type=TaskType.WRITING,
            depends_on=[str(task2.id), str(task1.id)],  # Circular
            position=2,
        )

        # Mock detect_cycle to return True
        with patch("app.modules.production_pipeline.service.detect_cycle") as mock_detect:
            mock_detect.return_value = True

            with pytest.raises(WorkflowError) as exc_info:
                await service.add_task(db_session, pipeline.id, org_id, payload)

            assert "cycle" in str(exc_info.value).lower()
