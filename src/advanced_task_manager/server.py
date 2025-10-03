"""
🚀 Advanced Task Management MCP Server
A sophisticated MCP server for comprehensive task and project management.

Features:
- Task CRUD operations with priority and categorization
- Time tracking and productivity analytics
- Project management with deadlines and dependencies
- Smart reporting and insights
- Multi-user workspace support

To run your server, use "uv run dev"
To test interactively, use "uv run playground"
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum
import json
import uuid

from mcp.server.fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

from smithery.decorators import smithery


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskCategory(str, Enum):
    WORK = "work"
    PERSONAL = "personal"
    LEARNING = "learning"
    HEALTH = "health"
    FINANCE = "finance"
    OTHER = "other"


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    status: TaskStatus = TaskStatus.TODO
    category: TaskCategory = TaskCategory.OTHER
    due_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    tags: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    assignee: Optional[str] = None
    project_id: Optional[str] = None


class TimeEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None


class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: str = "active"
    team_members: List[str] = Field(default_factory=list)
    budget: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.now)


class ConfigSchema(BaseModel):
    # User preferences
    default_priority: Priority = Field(Priority.MEDIUM, description="Default priority for new tasks")
    default_category: TaskCategory = Field(TaskCategory.OTHER, description="Default category for new tasks")
    timezone: str = Field("UTC", description="Your timezone (e.g., 'America/New_York')")
    
    # Productivity settings
    work_hours_per_day: float = Field(8.0, description="Expected work hours per day")
    focus_mode: bool = Field(False, description="Enable focus mode (fewer notifications)")
    auto_track_time: bool = Field(True, description="Automatically track time for tasks")
    
    # Integration settings
    slack_webhook: Optional[str] = Field(None, description="Slack webhook URL for notifications")
    calendar_integration: bool = Field(False, description="Enable calendar integration")
    
    # Analytics preferences
    weekly_reports: bool = Field(True, description="Generate weekly productivity reports")
    detailed_analytics: bool = Field(False, description="Enable detailed time tracking analytics")


# In-memory storage for demo purposes (in production, use a proper database)
tasks_storage: Dict[str, Task] = {}
projects_storage: Dict[str, Project] = {}
time_entries_storage: Dict[str, TimeEntry] = {}


@smithery.server(config_schema=ConfigSchema)
def create_server():
    """Create and configure the advanced MCP server."""

    server = FastMCP("Advanced Task Manager")

    # ==================== TASK MANAGEMENT TOOLS ====================

    @server.tool()
    def create_task(
        title: str,
        description: Optional[str] = None,
        priority: Optional[Priority] = None,
        category: Optional[TaskCategory] = None,
        due_date: Optional[str] = None,
        estimated_hours: Optional[float] = None,
        tags: Optional[List[str]] = None,
        project_id: Optional[str] = None,
        assignee: Optional[str] = None,
        ctx: Context = None
    ) -> str:
        """Create a new task with comprehensive details."""
        session_config = ctx.session_config
        
        # Use defaults from config if not provided
        task_priority = priority or session_config.default_priority
        task_category = category or session_config.default_category
        
        # Parse due date if provided
        parsed_due_date = None
        if due_date:
            try:
                parsed_due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            except ValueError:
                return f"Error: Invalid date format. Use ISO format (e.g., '2024-12-31T23:59:59Z')"
        
        # Create task
        task = Task(
            title=title,
            description=description,
            priority=task_priority,
            category=task_category,
            due_date=parsed_due_date,
            estimated_hours=estimated_hours,
            tags=tags or [],
            project_id=project_id,
            assignee=assignee
        )
        
        tasks_storage[task.id] = task
        
        return f"✅ Task created successfully!\n" \
               f"ID: {task.id}\n" \
               f"Title: {task.title}\n" \
               f"Priority: {task.priority.value}\n" \
               f"Category: {task.category.value}\n" \
               f"Status: {task.status.value}\n" \
               f"Due: {task.due_date.strftime('%Y-%m-%d %H:%M') if task.due_date else 'No due date'}"

    @server.tool()
    def update_task(
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[Priority] = None,
        status: Optional[TaskStatus] = None,
        category: Optional[TaskCategory] = None,
        due_date: Optional[str] = None,
        estimated_hours: Optional[float] = None,
        actual_hours: Optional[float] = None,
        tags: Optional[List[str]] = None,
        assignee: Optional[str] = None,
        ctx: Context = None
    ) -> str:
        """Update an existing task with new information."""
        if task_id not in tasks_storage:
            return f"❌ Task with ID '{task_id}' not found."
        
        task = tasks_storage[task_id]
        
        # Update fields if provided
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if priority is not None:
            task.priority = priority
        if status is not None:
            task.status = status
        if category is not None:
            task.category = category
        if due_date is not None:
            try:
                task.due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            except ValueError:
                return f"Error: Invalid date format. Use ISO format (e.g., '2024-12-31T23:59:59Z')"
        if estimated_hours is not None:
            task.estimated_hours = estimated_hours
        if actual_hours is not None:
            task.actual_hours = actual_hours
        if tags is not None:
            task.tags = tags
        if assignee is not None:
            task.assignee = assignee
        
        task.updated_at = datetime.now()
        
        return f"✅ Task updated successfully!\n" \
               f"ID: {task.id}\n" \
               f"Title: {task.title}\n" \
               f"Status: {task.status.value}\n" \
               f"Priority: {task.priority.value}\n" \
               f"Updated: {task.updated_at.strftime('%Y-%m-%d %H:%M')}"

    @server.tool()
    def delete_task(task_id: str, ctx: Context = None) -> str:
        """Delete a task permanently."""
        if task_id not in tasks_storage:
            return f"❌ Task with ID '{task_id}' not found."
        
        task = tasks_storage.pop(task_id)
        
        # Also remove associated time entries
        entries_to_remove = [entry_id for entry_id, entry in time_entries_storage.items() 
                           if entry.task_id == task_id]
        for entry_id in entries_to_remove:
            time_entries_storage.pop(entry_id)
        
        return f"✅ Task deleted successfully!\n" \
               f"Title: {task.title}\n" \
               f"Also removed {len(entries_to_remove)} associated time entries."

    @server.tool()
    def list_tasks(
        status: Optional[TaskStatus] = None,
        priority: Optional[Priority] = None,
        category: Optional[TaskCategory] = None,
        assignee: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 20,
        ctx: Context = None
    ) -> str:
        """List tasks with filtering options."""
        tasks = list(tasks_storage.values())
        
        # Apply filters
        if status:
            tasks = [t for t in tasks if t.status == status]
        if priority:
            tasks = [t for t in tasks if t.priority == priority]
        if category:
            tasks = [t for t in tasks if t.category == category]
        if assignee:
            tasks = [t for t in tasks if t.assignee == assignee]
        if project_id:
            tasks = [t for t in tasks if t.project_id == project_id]
        
        # Sort by priority and due date
        priority_order = {Priority.URGENT: 4, Priority.HIGH: 3, Priority.MEDIUM: 2, Priority.LOW: 1}
        tasks.sort(key=lambda t: (priority_order.get(t.priority, 0), t.due_date or datetime.max), reverse=True)
        
        # Limit results
        tasks = tasks[:limit]
        
        if not tasks:
            return "📝 No tasks found matching the criteria."
        
        result = f"📋 Found {len(tasks)} task(s):\n\n"
        for i, task in enumerate(tasks, 1):
            due_str = task.due_date.strftime('%Y-%m-%d') if task.due_date else "No due date"
            priority_emoji = {"urgent": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(task.priority.value, "⚪")
            status_emoji = {"todo": "📝", "in_progress": "🔄", "review": "👀", "completed": "✅", "cancelled": "❌"}.get(task.status.value, "❓")
            
            result += f"{i}. {priority_emoji} {status_emoji} **{task.title}**\n"
            result += f"   ID: {task.id}\n"
            result += f"   Priority: {task.priority.value.title()} | Category: {task.category.value.title()}\n"
            result += f"   Due: {due_str} | Assignee: {task.assignee or 'Unassigned'}\n"
            if task.description:
                result += f"   Description: {task.description[:100]}{'...' if len(task.description) > 100 else ''}\n"
            result += "\n"
        
        return result

    @server.tool()
    def get_task_details(task_id: str, ctx: Context = None) -> str:
        """Get detailed information about a specific task."""
        if task_id not in tasks_storage:
            return f"❌ Task with ID '{task_id}' not found."
        
        task = tasks_storage[task_id]
        
        # Get time entries for this task
        time_entries = [entry for entry in time_entries_storage.values() if entry.task_id == task_id]
        total_time = sum(entry.duration_minutes or 0 for entry in time_entries)
        
        result = f"📋 **Task Details**\n\n"
        result += f"**Title:** {task.title}\n"
        result += f"**ID:** {task.id}\n"
        result += f"**Status:** {task.status.value.title()}\n"
        result += f"**Priority:** {task.priority.value.title()}\n"
        result += f"**Category:** {task.category.value.title()}\n"
        result += f"**Assignee:** {task.assignee or 'Unassigned'}\n"
        result += f"**Project ID:** {task.project_id or 'No project'}\n"
        result += f"**Created:** {task.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        result += f"**Updated:** {task.updated_at.strftime('%Y-%m-%d %H:%M')}\n"
        
        if task.due_date:
            result += f"**Due Date:** {task.due_date.strftime('%Y-%m-%d %H:%M')}\n"
        
        if task.estimated_hours:
            result += f"**Estimated Hours:** {task.estimated_hours}\n"
        
        if task.actual_hours:
            result += f"**Actual Hours:** {task.actual_hours}\n"
        
        result += f"**Total Time Tracked:** {total_time // 60}h {total_time % 60}m\n"
        
        if task.tags:
            result += f"**Tags:** {', '.join(task.tags)}\n"
        
        if task.dependencies:
            result += f"**Dependencies:** {', '.join(task.dependencies)}\n"
        
        if task.description:
            result += f"\n**Description:**\n{task.description}\n"
        
        if time_entries:
            result += f"\n**Time Entries ({len(time_entries)}):**\n"
            for entry in time_entries[-5:]:  # Show last 5 entries
                duration_str = f"{entry.duration_minutes // 60}h {entry.duration_minutes % 60}m" if entry.duration_minutes else "Ongoing"
                result += f"- {entry.start_time.strftime('%Y-%m-%d %H:%M')} ({duration_str})\n"
                if entry.description:
                    result += f"  {entry.description}\n"
        
        return result

    # ==================== TIME TRACKING TOOLS ====================

    @server.tool()
    def start_timer(
        task_id: str,
        description: Optional[str] = None,
        ctx: Context = None
    ) -> str:
        """Start tracking time for a specific task."""
        if task_id not in tasks_storage:
            return f"❌ Task with ID '{task_id}' not found."
        
        # Check if there's already an active timer for this task
        active_entry = None
        for entry in time_entries_storage.values():
            if entry.task_id == task_id and entry.end_time is None:
                active_entry = entry
                break
        
        if active_entry:
            return f"⏰ Timer already running for task '{tasks_storage[task_id].title}' since {active_entry.start_time.strftime('%H:%M')}"
        
        # Create new time entry
        time_entry = TimeEntry(
            task_id=task_id,
            start_time=datetime.now(),
            description=description
        )
        
        time_entries_storage[time_entry.id] = time_entry
        
        return f"⏰ Timer started for task '{tasks_storage[task_id].title}'\n" \
               f"Entry ID: {time_entry.id}\n" \
               f"Started at: {time_entry.start_time.strftime('%Y-%m-%d %H:%M:%S')}"

    @server.tool()
    def stop_timer(
        time_entry_id: Optional[str] = None,
        task_id: Optional[str] = None,
        ctx: Context = None
    ) -> str:
        """Stop an active timer and calculate duration."""
        if time_entry_id:
            if time_entry_id not in time_entries_storage:
                return f"❌ Time entry with ID '{time_entry_id}' not found."
            entry = time_entries_storage[time_entry_id]
        elif task_id:
            # Find active timer for this task
            entry = None
            for e in time_entries_storage.values():
                if e.task_id == task_id and e.end_time is None:
                    entry = e
                    break
            if not entry:
                return f"❌ No active timer found for task '{task_id}'."
        else:
            return "❌ Please provide either time_entry_id or task_id."
        
        if entry.end_time is not None:
            return f"⏰ Timer for task '{tasks_storage[entry.task_id].title}' is already stopped."
        
        # Stop the timer
        entry.end_time = datetime.now()
        duration = entry.end_time - entry.start_time
        entry.duration_minutes = int(duration.total_seconds() / 60)
        
        # Update task's actual hours
        task = tasks_storage[entry.task_id]
        if task.actual_hours:
            task.actual_hours += duration.total_seconds() / 3600
        else:
            task.actual_hours = duration.total_seconds() / 3600
        
        hours = entry.duration_minutes // 60
        minutes = entry.duration_minutes % 60
        
        return f"⏹️ Timer stopped for task '{task.title}'\n" \
               f"Duration: {hours}h {minutes}m\n" \
               f"Total time on task: {task.actual_hours:.1f} hours"

    @server.tool()
    def log_time(
        task_id: str,
        duration_minutes: int,
        description: Optional[str] = None,
        start_time: Optional[str] = None,
        ctx: Context = None
    ) -> str:
        """Log time manually for a task without using timer."""
        if task_id not in tasks_storage:
            return f"❌ Task with ID '{task_id}' not found."
        
        # Parse start time if provided
        parsed_start_time = datetime.now()
        if start_time:
            try:
                parsed_start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                return f"Error: Invalid date format. Use ISO format (e.g., '2024-12-31T23:59:59Z')"
        
        # Create time entry
        time_entry = TimeEntry(
            task_id=task_id,
            start_time=parsed_start_time,
            end_time=parsed_start_time + timedelta(minutes=duration_minutes),
            description=description,
            duration_minutes=duration_minutes
        )
        
        time_entries_storage[time_entry.id] = time_entry
        
        # Update task's actual hours
        task = tasks_storage[task_id]
        if task.actual_hours:
            task.actual_hours += duration_minutes / 60
        else:
            task.actual_hours = duration_minutes / 60
        
        hours = duration_minutes // 60
        minutes = duration_minutes % 60
        
        return f"📝 Time logged for task '{task.title}'\n" \
               f"Duration: {hours}h {minutes}m\n" \
               f"Total time on task: {task.actual_hours:.1f} hours"

    @server.tool()
    def get_time_analytics(
        days: int = 7,
        category: Optional[TaskCategory] = None,
        project_id: Optional[str] = None,
        ctx: Context = None
    ) -> str:
        """Get detailed time tracking analytics and insights."""
        session_config = ctx.session_config
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Filter time entries
        relevant_entries = []
        for entry in time_entries_storage.values():
            if entry.start_time >= start_date and entry.duration_minutes:
                task = tasks_storage.get(entry.task_id)
                if task:
                    # Apply filters
                    if category and task.category != category:
                        continue
                    if project_id and task.project_id != project_id:
                        continue
                    relevant_entries.append((entry, task))
        
        if not relevant_entries:
            return f"📊 No time entries found for the last {days} days."
        
        # Calculate statistics
        total_minutes = sum(entry.duration_minutes for entry, _ in relevant_entries)
        total_hours = total_minutes / 60
        
        # Group by category
        category_stats = {}
        for entry, task in relevant_entries:
            cat = task.category.value
            if cat not in category_stats:
                category_stats[cat] = 0
            category_stats[cat] += entry.duration_minutes
        
        # Group by day
        daily_stats = {}
        for entry, task in relevant_entries:
            day = entry.start_time.strftime('%Y-%m-%d')
            if day not in daily_stats:
                daily_stats[day] = 0
            daily_stats[day] += entry.duration_minutes
        
        # Calculate productivity metrics
        work_hours_per_day = session_config.work_hours_per_day
        expected_hours = work_hours_per_day * days
        productivity_ratio = (total_hours / expected_hours) * 100 if expected_hours > 0 else 0
        
        # Build report
        result = f"📊 **Time Analytics Report** ({days} days)\n\n"
        result += f"**Total Time Tracked:** {total_hours:.1f} hours ({total_minutes} minutes)\n"
        result += f"**Average per Day:** {total_hours/days:.1f} hours\n"
        result += f"**Productivity Ratio:** {productivity_ratio:.1f}% (vs {work_hours_per_day}h/day target)\n\n"
        
        # Category breakdown
        result += "**Time by Category:**\n"
        for cat, minutes in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
            hours = minutes / 60
            percentage = (minutes / total_minutes) * 100
            result += f"- {cat.title()}: {hours:.1f}h ({percentage:.1f}%)\n"
        
        # Daily breakdown
        result += f"\n**Daily Breakdown:**\n"
        for day in sorted(daily_stats.keys()):
            minutes = daily_stats[day]
            hours = minutes / 60
            result += f"- {day}: {hours:.1f}h\n"
        
        # Top tasks
        task_stats = {}
        for entry, task in relevant_entries:
            if task.title not in task_stats:
                task_stats[task.title] = 0
            task_stats[task.title] += entry.duration_minutes
        
        result += f"\n**Top Tasks:**\n"
        for task_title, minutes in sorted(task_stats.items(), key=lambda x: x[1], reverse=True)[:5]:
            hours = minutes / 60
            result += f"- {task_title}: {hours:.1f}h\n"
        
        return result

    # ==================== PROJECT MANAGEMENT TOOLS ====================

    @server.tool()
    def create_project(
        name: str,
        description: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        budget: Optional[float] = None,
        team_members: Optional[List[str]] = None,
        ctx: Context = None
    ) -> str:
        """Create a new project with team and timeline."""
        # Parse dates if provided
        parsed_start_date = None
        parsed_end_date = None
        
        if start_date:
            try:
                parsed_start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                return f"Error: Invalid start date format. Use ISO format (e.g., '2024-12-31T23:59:59Z')"
        
        if end_date:
            try:
                parsed_end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                return f"Error: Invalid end date format. Use ISO format (e.g., '2024-12-31T23:59:59Z')"
        
        # Create project
        project = Project(
            name=name,
            description=description,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            budget=budget,
            team_members=team_members or []
        )
        
        projects_storage[project.id] = project
        
        return f"🚀 Project created successfully!\n" \
               f"ID: {project.id}\n" \
               f"Name: {project.name}\n" \
               f"Team Members: {len(project.team_members)}\n" \
               f"Budget: ${project.budget or 'Not set'}\n" \
               f"Timeline: {project.start_date.strftime('%Y-%m-%d') if project.start_date else 'Not set'} to {project.end_date.strftime('%Y-%m-%d') if project.end_date else 'Not set'}"

    @server.tool()
    def get_project_status(project_id: str, ctx: Context = None) -> str:
        """Get comprehensive project status and progress."""
        if project_id not in projects_storage:
            return f"❌ Project with ID '{project_id}' not found."
        
        project = projects_storage[project_id]
        
        # Get project tasks
        project_tasks = [task for task in tasks_storage.values() if task.project_id == project_id]
        
        # Calculate progress
        total_tasks = len(project_tasks)
        completed_tasks = len([t for t in project_tasks if t.status == TaskStatus.COMPLETED])
        progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Calculate time spent
        total_time_minutes = 0
        for task in project_tasks:
            task_entries = [entry for entry in time_entries_storage.values() if entry.task_id == task.id]
            total_time_minutes += sum(entry.duration_minutes or 0 for entry in task_entries)
        
        total_hours = total_time_minutes / 60
        
        # Calculate budget usage (if budget is set)
        budget_info = ""
        if project.budget:
            # This is a simplified calculation - in reality you'd track actual costs
            estimated_cost_per_hour = 50  # Example rate
            estimated_cost = total_hours * estimated_cost_per_hour
            budget_usage = (estimated_cost / project.budget) * 100
            budget_info = f"\n**Budget Usage:** ${estimated_cost:.2f} / ${project.budget} ({budget_usage:.1f}%)"
        
        result = f"📋 **Project Status: {project.name}**\n\n"
        result += f"**Progress:** {completed_tasks}/{total_tasks} tasks completed ({progress_percentage:.1f}%)\n"
        result += f"**Time Spent:** {total_hours:.1f} hours\n"
        result += f"**Team Members:** {', '.join(project.team_members) if project.team_members else 'None'}\n"
        result += f"**Status:** {project.status.title()}\n"
        result += budget_info
        
        if project.description:
            result += f"\n**Description:** {project.description}\n"
        
        # Task breakdown by status
        status_counts = {}
        for task in project_tasks:
            status = task.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        if status_counts:
            result += f"\n**Task Breakdown:**\n"
            for status, count in status_counts.items():
                result += f"- {status.title()}: {count}\n"
        
        return result

    # ==================== RESOURCES ====================

    @server.resource("tasks://all")
    def all_tasks() -> str:
        """Get a comprehensive overview of all tasks in the system."""
        if not tasks_storage:
            return "No tasks found in the system."
        
        # Calculate statistics
        total_tasks = len(tasks_storage)
        completed_tasks = len([t for t in tasks_storage.values() if t.status == TaskStatus.COMPLETED])
        in_progress_tasks = len([t for t in tasks_storage.values() if t.status == TaskStatus.IN_PROGRESS])
        
        # Priority breakdown
        priority_counts = {}
        for task in tasks_storage.values():
            priority_counts[task.priority.value] = priority_counts.get(task.priority.value, 0) + 1
        
        # Category breakdown
        category_counts = {}
        for task in tasks_storage.values():
            category_counts[task.category.value] = category_counts.get(task.category.value, 0) + 1
        
        result = f"# Task Management System Overview\n\n"
        result += f"**Total Tasks:** {total_tasks}\n"
        result += f"**Completed:** {completed_tasks} ({completed_tasks/total_tasks*100:.1f}%)\n"
        result += f"**In Progress:** {in_progress_tasks}\n\n"
        
        result += "## Priority Distribution\n"
        for priority, count in priority_counts.items():
            result += f"- {priority.title()}: {count}\n"
        
        result += "\n## Category Distribution\n"
        for category, count in category_counts.items():
            result += f"- {category.title()}: {count}\n"
        
        return result

    @server.resource("analytics://productivity")
    def productivity_analytics() -> str:
        """Get productivity analytics and insights."""
        if not time_entries_storage:
            return "No time tracking data available for analytics."
        
        # Calculate last 30 days of data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        recent_entries = []
        for entry in time_entries_storage.values():
            if entry.start_time >= start_date and entry.duration_minutes:
                task = tasks_storage.get(entry.task_id)
                if task:
                    recent_entries.append((entry, task))
        
        if not recent_entries:
            return "No time tracking data found for the last 30 days."
        
        # Calculate metrics
        total_minutes = sum(entry.duration_minutes for entry, _ in recent_entries)
        total_hours = total_minutes / 60
        avg_hours_per_day = total_hours / 30
        
        # Most productive categories
        category_hours = {}
        for entry, task in recent_entries:
            cat = task.category.value
            category_hours[cat] = category_hours.get(cat, 0) + entry.duration_minutes / 60
        
        # Most time-consuming tasks
        task_hours = {}
        for entry, task in recent_entries:
            task_hours[task.title] = task_hours.get(task.title, 0) + entry.duration_minutes / 60
        
        result = f"# Productivity Analytics (Last 30 Days)\n\n"
        result += f"**Total Time Tracked:** {total_hours:.1f} hours\n"
        result += f"**Average per Day:** {avg_hours_per_day:.1f} hours\n"
        result += f"**Total Sessions:** {len(recent_entries)}\n\n"
        
        result += "## Most Productive Categories\n"
        for cat, hours in sorted(category_hours.items(), key=lambda x: x[1], reverse=True)[:5]:
            result += f"- {cat.title()}: {hours:.1f} hours\n"
        
        result += "\n## Most Time-Consuming Tasks\n"
        for task_title, hours in sorted(task_hours.items(), key=lambda x: x[1], reverse=True)[:5]:
            result += f"- {task_title}: {hours:.1f} hours\n"
        
        return result

    @server.resource("projects://overview")
    def projects_overview() -> str:
        """Get an overview of all projects and their status."""
        if not projects_storage:
            return "No projects found in the system."
        
        result = f"# Projects Overview\n\n"
        result += f"**Total Projects:** {len(projects_storage)}\n\n"
        
        for project in projects_storage.values():
            # Get project tasks
            project_tasks = [task for task in tasks_storage.values() if task.project_id == project.id]
            completed = len([t for t in project_tasks if t.status == TaskStatus.COMPLETED])
            progress = (completed / len(project_tasks) * 100) if project_tasks else 0
            
            result += f"## {project.name}\n"
            result += f"- **Status:** {project.status.title()}\n"
            result += f"- **Progress:** {completed}/{len(project_tasks)} tasks ({progress:.1f}%)\n"
            result += f"- **Team Size:** {len(project.team_members)}\n"
            if project.budget:
                result += f"- **Budget:** ${project.budget}\n"
            result += "\n"
        
        return result

    @server.resource("help://task-management")
    def task_management_help() -> str:
        """Comprehensive help guide for the task management system."""
        return """# Task Management System Help Guide

## Core Concepts

### Tasks
Tasks are the fundamental unit of work in this system. Each task has:
- **Title**: Brief description of the work
- **Description**: Detailed information about the task
- **Priority**: low, medium, high, urgent
- **Status**: todo, in_progress, review, completed, cancelled
- **Category**: work, personal, learning, health, finance, other
- **Due Date**: When the task should be completed
- **Estimated Hours**: How long you think it will take
- **Actual Hours**: Time actually spent (tracked automatically)
- **Tags**: Custom labels for organization
- **Assignee**: Who is responsible for the task
- **Project ID**: Which project this task belongs to

### Projects
Projects group related tasks together and provide:
- **Timeline**: Start and end dates
- **Budget**: Financial constraints
- **Team Members**: People working on the project
- **Progress Tracking**: Overall completion status

### Time Tracking
The system automatically tracks time spent on tasks through:
- **Timers**: Start/stop time tracking for active work
- **Manual Logging**: Record time after the fact
- **Analytics**: Insights into productivity patterns

## Best Practices

1. **Create Clear Tasks**: Use descriptive titles and detailed descriptions
2. **Set Realistic Estimates**: Help with planning and resource allocation
3. **Use Categories**: Organize tasks by type for better insights
4. **Track Time Consistently**: Use timers or log time regularly
5. **Review Analytics**: Check productivity reports to improve efficiency
6. **Update Status**: Keep task status current for accurate progress tracking

## Workflow Tips

- Start with high-priority, urgent tasks
- Break large tasks into smaller, manageable pieces
- Use tags to create custom organization systems
- Set due dates to maintain momentum
- Review and update estimates based on actual time spent
"""

    # ==================== PROMPTS ====================

    @server.prompt()
    def plan_daily_tasks(date: str = None) -> list:
        """Generate a prompt for planning daily tasks."""
        target_date = date or datetime.now().strftime('%Y-%m-%d')
        
        return [
            {
                "role": "user",
                "content": f"Help me plan my tasks for {target_date}. I want to:\n"
                          f"1. Review my current task list\n"
                          f"2. Prioritize tasks based on urgency and importance\n"
                          f"3. Estimate time requirements\n"
                          f"4. Create a realistic daily schedule\n"
                          f"5. Identify any dependencies or blockers\n\n"
                          f"Please use the task management tools to help me organize my day effectively."
            }
        ]

    @server.prompt()
    def weekly_retrospective() -> list:
        """Generate a prompt for weekly productivity review."""
        return [
            {
                "role": "user",
                "content": "Help me conduct a weekly productivity retrospective. I want to:\n"
                          "1. Review my completed tasks from the past week\n"
                          "2. Analyze my time tracking data and productivity metrics\n"
                          "3. Identify patterns in my work habits\n"
                          "4. Recognize achievements and areas for improvement\n"
                          "5. Plan adjustments for the upcoming week\n"
                          "6. Set goals and priorities\n\n"
                          "Please use the analytics tools to provide data-driven insights and recommendations."
            }
        ]

    @server.prompt()
    def project_kickoff(project_name: str, team_size: int = 1) -> list:
        """Generate a prompt for starting a new project."""
        return [
            {
                "role": "user",
                "content": f"Help me kick off a new project called '{project_name}' with a team of {team_size} people. I need to:\n"
                          f"1. Create the project in the system\n"
                          f"2. Break down the project into manageable tasks\n"
                          f"3. Estimate timelines and resource requirements\n"
                          f"4. Assign tasks to team members\n"
                          f"5. Set up milestones and checkpoints\n"
                          f"6. Create a project timeline\n\n"
                          f"Please guide me through setting up this project for success."
            }
        ]

    @server.prompt()
    def time_management_coaching() -> list:
        """Generate a prompt for time management coaching."""
        return [
            {
                "role": "user",
                "content": "I need help improving my time management skills. Please:\n"
                          "1. Analyze my current time tracking data\n"
                          "2. Identify time management patterns and inefficiencies\n"
                          "3. Suggest specific improvements based on my data\n"
                          "4. Help me set up better time tracking habits\n"
                          "5. Recommend productivity techniques that fit my work style\n"
                          "6. Create a personalized time management plan\n\n"
                          "Use my actual productivity data to provide tailored advice."
            }
        ]

    @server.prompt()
    def task_delegation_helper(team_member: str) -> list:
        """Generate a prompt for delegating tasks to team members."""
        return [
            {
                "role": "user",
                "content": f"Help me delegate tasks effectively to {team_member}. I want to:\n"
                          f"1. Review tasks that could be delegated\n"
                          f"2. Assess {team_member}'s current workload\n"
                          f"3. Match tasks to their skills and availability\n"
                          f"4. Create clear task assignments with expectations\n"
                          f"5. Set up follow-up and progress tracking\n"
                          f"6. Ensure proper handoff and communication\n\n"
                          f"Please help me delegate responsibly and effectively."
            }
        ]

    return server
