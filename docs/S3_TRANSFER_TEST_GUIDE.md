# S3 Transfer Testing Guide

## Prerequisites
- File Orbit services running on your Mac
- AWS S3 bucket created with test files
- AWS credentials configured in `backend/.env`

## Step 1: Start File Orbit Services

```bash
cd /Users/tkitchens/projects/consumer-apps/file-orbit
./manage.sh start
```

Wait for all services to start (about 30 seconds).

## Step 2: Create S3 Endpoint

1. Open browser to http://localhost:3000
2. Navigate to **Endpoints** page
3. Click **"Add Endpoint"**
4. Fill in the form:
   - **Name**: `AWS S3 Test`
   - **Type**: `S3`
   - **Bucket**: `file-orbit-test-bucket` (or your bucket name)
   - **Region**: `us-east-1` (or your region)
   - **Access Key**: (copy from your .env file)
   - **Secret Key**: (copy from your .env file)
5. Click **"Create"**

## Step 3: Create Local Destination Endpoint

1. Still on Endpoints page, click **"Add Endpoint"** again
2. Fill in:
   - **Name**: `Local Downloads`
   - **Type**: `Local`
   - **Path**: `/Users/tkitchens/Downloads/s3-transfers`
3. Click **"Create"**

## Step 4: Execute Transfer

1. Navigate to **Transfers** page
2. Click **"Create Transfer"**
3. Fill in the form:
   - **Source Endpoint**: `AWS S3 Test`
   - **Source Path**: `/` (to see all files)
   - **Destination Endpoint**: `Local Downloads`
   - **Destination Path**: `/` 
4. Click **"Create & Execute"**

## Step 5: Monitor Transfer

1. The transfer will start immediately
2. Watch the progress bar on the dashboard
3. Check the destination folder:
   ```bash
   ls -la /Users/tkitchens/Downloads/s3-transfers/
   ```

## Expected Results

You should see all your test files transferred:
- episode-1.mp4
- episode-2.mp4
- episode-3.mp4
- test1.mp4
- test2.mp4
- test3.mov
- chain_test_*.mxf files

## Troubleshooting

If transfers fail:

1. **Check backend logs**:
   ```bash
   docker logs file-orbit-backend-1
   ```

2. **Check worker logs**:
   ```bash
   docker logs file-orbit-worker-1
   ```

3. **Common issues**:
   - Wrong bucket name or region
   - Invalid AWS credentials
   - Destination directory not writable
   - Network connectivity issues

## Important Notes

- **No public IP needed**: File Orbit makes outbound connections only
- **Credentials are secure**: They're only used server-side
- **Transfer speed**: Depends on your internet connection
- **File integrity**: Rclone verifies checksums automatically

## Next Steps

Once basic transfers work, try:
1. Transferring specific file patterns (e.g., `*.mp4`)
2. Setting up bandwidth limits
3. Creating scheduled transfers
4. Setting up event-driven transfers when new files appear in S3