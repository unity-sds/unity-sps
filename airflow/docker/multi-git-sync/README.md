# Multi-Git-Sync Container

A custom container that syncs multiple git repositories based on configuration stored in AWS S3.

## Features

- **Dynamic repository configuration**: Read repository list from S3
- **Automatic polling**: Checks for configuration changes every 60 seconds (configurable)
- **Multi-repo support**: Syncs multiple repositories to separate subdirectories
- **No restart required**: Automatically picks up new repositories without pod restart, just edit the s3 file 
- **IRSA support**: Uses IAM Roles for Service Accounts (IRSA) for AWS authentication

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `S3_BUCKET` | S3 bucket containing repo configuration file | `unity-dev-sps-config-smce` |
| `S3_KEY` | S3 object key for repo configuration file | `dag_repos_airflow.json` |
| `AWS_REGION` | AWS region for S3 | `us-west-2` |
| `SYNC_ROOT` | Root directory for synced repositories | `/dag-catalog` |
| `POLL_INTERVAL` | Polling interval in seconds | `60` |

## S3 Configuration File Format

The S3 object dag_repos_airflow.json should contain a JSON array of repository configurations:

```json
[
  {
    "url": "https://github.com/unity-sds/unity-sps.git",
    "ref": "main", (branch)
    "path": "airflow/dags", (dont need to include repo name and "." for root)
    "name": "unity-sps"
  },
  {
    "url": "https://github.com/org/another-repo.git",
    "ref": "develop",
    "path": "dags",
    "name": "another-repo"
  }
]
```

### Configuration Fields

- `url`: Git repository URL (HTTPS)
- `ref`: Git ref to checkout (branch, tag, or commit)
- `path`: Subdirectory within the repo to expose (relative path)
- `name`: Unique name for the repository (used as directory name)

## Directory Structure

```
/dag-catalog/
├── repos/
│   ├── unity-sps/          # Git clone of unity-sps repo
│   └── another-repo/       # Git clone of another-repo
└── current/
    ├── unity-sps -> ../repos/unity-sps/airflow/dags
    └── another-repo -> ../repos/another-repo/dags
```

## Building the Image

```bash
docker build -t jplmdps/multi-git-sync:v1.0.0 .
docker push jplmdps/multi-git-sync:v1.0.0
```

## Troubleshooting

### Check container logs
```bash
kubectl logs <pod-name> -c multi-git-sync -f
```

### Verify S3 configuration file
```bash
aws s3 cp s3://unity-dev-sps-config-smce/dag_repos_airflow.json - | jq .
```

### Check synced directories
```bash
kubectl exec <pod-name> -c multi-git-sync -- ls -la /dag-catalog/current/
```

### Common Issues

1. **"S3 object not found"**: Ensure the S3 object exists at the specified bucket and key, and the IAM role has access
2. **"S3 bucket not found"**: Verify the bucket name is correct and exists in the AWS account
3. **"Failed to clone repository"**: Check git URL is correct and accessible (public repo or credentials configured)
4. **"Source path does not exist"**: Verify the `path` field in the config points to a valid directory in the repo
