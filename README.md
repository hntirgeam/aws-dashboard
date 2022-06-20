# AWS-Dashboard

AWS-Dashboard is a Python CLI-tool for dealing with AWS EC2 and RDS instances.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install aws-dashboard.

```bash
pip install aws-dashboard
```

---

## You can

- Show all your available EC2 instances && RDS clusters:

```python
> aws-dashboard status

| Name                    | State   | State Time                  | Address   | Env   | Id   |
|-------------------------|---------|-----------------------------|-----------|-------|------|
| project_1_backend_prod  | running | 11 hours 46 minutes         | 8.8.8.8   | stage | <id> |
| project_2_plugin        | stopped | 1 day 13 hours 17 minutes   | 1.1.1.1   | stage | <id> |
| project_1_frontend_prod | stopped | 374 days 4 hours 58 minutes | 8.8.4.4   | prod  | <id> |

| Name    | State     | Address            | Port |
|---------|-----------|--------------------|------|
| db_prod | available | *rds.amazonaws.com | 5432 |
| db_dev  | available | *rds.amazonaws.com | 5432 |
```

- Order tables by any table name:

```python
> aws-dashboard status --order Name

| Name                    | State   | State Time                  | Address   | Env   | Id   |
|-------------------------|---------|-----------------------------|-----------|-------|------|
| project_1_backend_prod  | running | 11 hours 46 minutes         | 8.8.8.8   | stage | <id> |
| project_1_frontend_prod | stopped | 374 days 4 hours 58 minutes | 8.8.4.4   | prod  | <id> |
| project_2_plugin        | stopped | 1 day 13 hours 17 minutes   | 1.1.1.1   | stage | <id> |

| Name    | State     | Address            | Port |
|---------|-----------|--------------------|------|
| db_dev  | available | *rds.amazonaws.com | 5432 |
| db_prod | available | *rds.amazonaws.com | 5432 |
```

- Show only tables that match given `env`:

```python
> aws-monitor status --env prod

| Name                    | State   | State Time                  | Address   | Env   | Id   |
|-------------------------|---------|-----------------------------|-----------|-------|------|
| project_1_backend_prod  | running | 11 hours 46 minutes         | 8.8.8.8   | prod | <id> |
| project_1_frontend_prod | stopped | 374 days 4 hours 58 minutes | 8.8.4.4   | prod  | <id> |

| Name    | State     | Address            | Port |
|---------|-----------|--------------------|------|
| db_prod | available | *rds.amazonaws.com | 5432 |
```

- Make output shell-compatible (and change separator with `--sh-separator` flag):

```python
> aws-dashboard status --order Name --sh --no-db

project_1_backend_prod|running|11 hours 46 minutes|8.8.8.8|stage|<id>
project_1_frontend_prod|stopped|374 days 4 hours 58 minutes|8.8.4.4|prod|<id>
project_2_plugin|stopped|1 day 13 hours 17 minutes|1.1.1.1|stage|<id>
```

- Start or stop ec2 instances using their id(s):

```python
> aws-dashboard stop --order Name --sh --no-db
Are you sure you want to stop this instance(s)? [y/N]: y
Stopping
```

- Bulk start or stop ec2 instances using their env:

```python
> aws-dashboard bulk_stop --env stage
<name> <id1>
<name> <id2>
<name> <id3>
Are you sure you want to stop this instance(s)? [y/N]: y
Stopping
```

---

## Note

You should consider adding `Tags` to your EC2 or RDS instances with `key="environment"` and `value="<env>"`

---

## License

[MIT](https://choosealicense.com/licenses/mit/)
