# Notiq

![Status](https://img.shields.io/badge/status-in%20development-yellow)
![Python](https://img.shields.io/badge/python-3.14%2B-blue)
![License](https://img.shields.io/badge/license-GPL--3.0-green)

A powerful Python utility library for task scheduling, monitoring, analytics, and an event driven observer services built on Celery and Redis.

---

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [Testing](#testing)
- [License](#license)
- [Roadmap](#roadmap)
- [Acknowledgements](#acknowledgements)

---

## Installation

### Prerequisites

- Python 3.14+
- Redis/rabbitmq server running locally or accessible via network

### Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/Heritage-XioN/notiq.git
cd notiq

# Install with uv
uv sync --all-groups
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/Heritage-XioN/notiq.git
cd notiq

# Install in development mode
pip install -e .
```




---

## Usage

### Task Definition

Create background tasks using the `@notiq_task` decorator:

```python
from notiq import notiq_task
from celery import Task

@notiq_task(name=notiq.process_data)
def process_data(self: Task, data: dict) -> dict:
    # Your processing logic here
    return {"processed": True}

# Trigger task immediately
process_data.delay({data: "to process"})
```

### Task Scheduling

Schedule tasks with flexible timing options:

```python
from notiq import notiq_scheduler, notiq_unscheduler
from celery.schedules import crontab

# Interval-based scheduling (every 1 minute of every hour eg: 12:01, 13:01, 14:01)
task = notiq_scheduler(
    name="unique-task-id-123",
    task="tasks.send_notification",
    schedule=crontab(minute=1),
    args=[1000],
).save()

# Remove a scheduled task
notiq_unscheduler("unique-task-id-123")
```

### Monitoring & Logging

Monitor function execution with built-in decorators and structured logging:

```python
from notiq import monitor, Logger, MetricBuilder

# Create a logger
logger = Logger("my_service", json_serialize=True).setup()

# Monitor function execution with metrics
@monitor(metric_name="api_request", log_level="INFO")
def handle_request(request_id: str):
    logger.info("Processing request", extra={"request_id": request_id})
    return {"success": True}

# Create custom Prometheus metrics
metrics = MetricBuilder("my_app")
counter = metrics.counter("requests_total", "Total requests processed")
```

### Configuration

setup the worker config using `NotiqConfig`
```python
# Configure Notiq
NotiqConfig(
    BROKER_URL="redis://localhost:6379/0",
    RESULT_BACKEND="redis://localhost:6379/0",
    task_dir="./tasks"
)
```
OR Configure via environment variables or `.env` file:
```env
# prefix it with NOTIQ_
NOTIQ_BROKER_URL=amqp://guest:guest@localhost:5672/
NOTIQ_RESULT_BACKEND=redis://localhost:6379/0
NOTIQ_TASK_DIR=./tasks
```


### Running Workers

```bash
# Start the Celery worker
uv run celery -A notiq worker --loglevel=info

# for windows
uv run celery -A notiq worker --loglevel=info --pool=solo

# Start the scheduler (RedBeat)
uv run celery -A notiq beat -S redbeat.RedBeatScheduler --loglevel=info
```

---

## Documentation

> 🚧 **Coming Soon** - Full documentation will be available at a later date.

---

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on how to:

- Report bugs and request features
- Set up your development environment
- Submit pull requests

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

---

## Testing

> 🚧 **Coming Soon** - Testing instructions will be added in a future release.

---

## License

This project is licensed under the **GNU General Public License v3.0** - see the [LICENSE](LICENSE) file for details.

---

## Roadmap

Upcoming features planned for future releases:

### 📧 Messaging Service
Background messaging capabilities supporting multiple providers:
- Email integration (SMTP, SendGrid, AWS SES)
- SMS integration (Twilio, AWS SNS)
- Push notifications

### 📊 Data Aggregation Services
Centralized data collection and processing:
- Metrics aggregation from multiple sources
- Real-time data pipelines
- Analytics dashboards integration

### 🔔 Event-Driven Observer Services
Flexible event system for triggering tasks:
- Custom event definitions
- Webhook listeners
- Database change observers
- File system watchers

---

## Acknowledgements

Notiq is built on top of these excellent open-source projects:

- [Celery](https://docs.celeryq.dev/) - Distributed task queue
- [Redis](https://redis.io/) - In-memory data store
- [RedBeat](https://github.com/sibson/redbeat) - Redis-based Celery beat scheduler
- [Prometheus Client](https://github.com/prometheus/client_python) - Metrics and monitoring
- [Pydantic](https://docs.pydantic.dev/) - Data validation

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/Heritage-XioN">HERITAGE-XION</a>
</p>
