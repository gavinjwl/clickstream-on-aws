# Clickstream on AWS

## 入門

我們建議使用 [AWS Cloud9](https://aws.amazon.com/cloud9/) 來進行部署，或者你可以使用自己偏好的裝置來進行部署，但是必須注意以下元件需要事先安裝好

- [Python 3.7.10](https://www.python.org/downloads/release/python-3710/): 本解決方案依賴 Python 3.7.10 或更高版本
- [AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html#getting_started_install): 用來建置此解決方案的 AWS 資源
- [Poetry](https://python-poetry.org/docs/#installation): Python 的依賴管理套件
- [Docker](https://docs.docker.com/engine/install/): 建立解決方案中的容器化資源

## 部署 AWS 環境

### 1. 複製程式碼儲存庫

```bash
git clone https://github.com/gavinjwl/clickstream-on-aws
```

### 2. 安裝 Python 依賴套件並啟用 Python 虛擬環境

```bash
# Cloud9
sudo yum update -y
sudo yum install -y amazon-linux-extras
sudo amazon-linux-extras install -y python3.8
pip3.8 install --upgrade poetry
# END cloud9

cd clickstream-on-aws

poetry install
poetry shell
source .venv/bin/activate
```

### 3. 部署 AWS CDK Stacks

部署 Provisioned 版本或 Serverless 版本

- 部署 Provisioned 版本

```bash
# Bootstrap CDK, if you never did
cdk bootstrap

export VPC_ID="<your-vpc-id>"
cdk deploy Clickstream \
  --context vpc-id='$VPC_ID' \
  --parameters RedshiftPassword='your-password'
```

- 或部署 Serverless 版本

> RedshiftServerlessSubnetIds 需要至少三個 Subnets 並且具有 Internet 的能力 (IGW 或 NAT Gateway)

```bash
# Bootstrap CDK, if you never did
cdk bootstrap

export VPC_ID="<your-vpc-id>"
cdk deploy Clickstream-Serverless \
  --context vpc-id='$VPC_ID' \
  --parameters RedshiftPassword='your-password'
```

### 4. 連線進 Amazon Redshift

我們將會透過 Amazon Redshift Query Editor V2 連線進 Amazon Redshift

預設的使用者名稱為 `awsuser`，而密碼為建立 CDK 時候您指定的密碼

![redshift-connect-with-password](images/redshift-connect-with-password.png)

### 5. 建立代表 Kinesis Stream 的 External Schema

```sql
-- Create external schema for kinesis
CREATE EXTERNAL SCHEMA IF NOT EXISTS kinesis FROM KINESIS IAM_ROLE default;
```

### 6. 建立 Materialized View 來讀取 Kinesis Stream 內的資料

```sql
-- Create schema
CREATE SCHEMA IF NOT EXISTS clickstream;

-- Create MATERIALIZED VIEW
SET enable_case_sensitive_identifier TO true;
CREATE MATERIALIZED VIEW clickstream.mv_kinesis_source
AUTO REFRESH YES
AS
SELECT
    approximate_arrival_timestamp AS _approximate_arrival_timestamp,
    partition_key AS _partition_key,
    shard_id AS _shard_id,
    sequence_number AS _sequence_number,
    refresh_time AS _refresh_time,
    -- JSON_PARSE(from_varbyte(Data, 'utf-8')) as data,
    JSON_EXTRACT_PATH_TEXT(FROM_VARBYTE(kinesis_data, 'utf-8'), 'messageId')::VARCHAR(256) AS message_id,
    JSON_EXTRACT_PATH_TEXT(FROM_VARBYTE(kinesis_data, 'utf-8'), 'timestamp')::VARCHAR(256) AS event_timestamp,
    JSON_EXTRACT_PATH_TEXT(FROM_VARBYTE(kinesis_data, 'utf-8'), 'type')::VARCHAR(256) AS event_type,
    -- Common
    JSON_EXTRACT_PATH_TEXT(FROM_VARBYTE(kinesis_data, 'utf-8'), 'userId')::VARCHAR(256) AS user_id,
    JSON_EXTRACT_PATH_TEXT(FROM_VARBYTE(kinesis_data, 'utf-8'), 'anonymousId')::VARCHAR(256) AS anonymous_id,
    JSON_EXTRACT_PATH_TEXT(FROM_VARBYTE(kinesis_data, 'utf-8'), 'context')::TEXT AS context,
    JSON_EXTRACT_PATH_TEXT(FROM_VARBYTE(kinesis_data, 'utf-8'), 'integrations')::TEXT AS integrations,

    -- Identify
    JSON_EXTRACT_PATH_TEXT(FROM_VARBYTE(kinesis_data, 'utf-8'), 'traits')::TEXT AS traits,

    -- Track
    JSON_EXTRACT_PATH_TEXT(FROM_VARBYTE(kinesis_data, 'utf-8'), 'event')::VARCHAR(256) AS event,
    JSON_EXTRACT_PATH_TEXT(FROM_VARBYTE(kinesis_data, 'utf-8'), 'properties')::TEXT AS properties,

    -- Alias
    JSON_EXTRACT_PATH_TEXT(FROM_VARBYTE(kinesis_data, 'utf-8'), 'previousId')::VARCHAR(256) AS previous_id,

    -- Group
    JSON_EXTRACT_PATH_TEXT(FROM_VARBYTE(kinesis_data, 'utf-8'), 'groupId')::VARCHAR(256) AS group_id,

    -- Page
    JSON_EXTRACT_PATH_TEXT(FROM_VARBYTE(kinesis_data, 'utf-8'), 'category')::VARCHAR(256) AS category,
    JSON_EXTRACT_PATH_TEXT(FROM_VARBYTE(kinesis_data, 'utf-8'), 'name')::VARCHAR(256) AS name
FROM kinesis.clickstream_kinesis_stream
WHERE IS_UTF8(kinesis_data) AND IS_VALID_JSON(FROM_VARBYTE(kinesis_data, 'utf-8'));

-- ALTER sort key
ALTER TABLE clickstream.mv_tbl__mv_kinesis_source__0
ALTER SORTKEY (event_timestamp);

-- Sample use case: Last 5 minutes view
CREATE OR REPLACE VIEW last_5_mins AS
SELECT
    message_id,
    event_timestamp::timestamp,
    event_type,
    user_id,
    anonymous_id,
    JSON_PARSE(context) AS context,
    JSON_PARSE(integrations) AS integrations,
    traits,
    event,
    properties,
    previous_id,
    group_id,
    category,
    name
FROM clickstream.mv_kinesis_source
WHERE event_timestamp >= DATEADD(mins, -5, GETDATE())
ORDER BY event_timestamp DESC;
```

### 7. 確認 table info

```sql
SELECT "table", tbl_rows, encoded, diststyle, sortkey1, skew_sortkey1, skew_rows
FROM svv_table_info
ORDER BY 1;
```

## 驗證

以下提供幾種簡易的驗證方式

### 簡易的網站並且已經引入 Analytics Snippet JS

更改 `samples/simple-website/local/v1/projects/default/settings` 的 **apiHost**

請注意 apiHost 的格式: 不需要 https 開頭並且結尾的反斜線也不需要

範例: `xxxxx.execute-api.<region>.amazonaws.com/prod`

```json
{
  "integrations": {
    "Segment.io": {
      "protocol": "https",
      "apiHost": "<CDK-deployed-ApiGateway-URL>",
      "deliveryStrategy": {
        "strategy": "batching",
        "config": {
          "size": 10,
          "timeout": 5000
        }
      },
...
```

在本機上啟動 http container 模擬 clickstream

```bash
cd samples/simple-website

docker build -t clickstream-simple-website .

docker run -it --rm -p 8080:80 clickstream-simple-website
```

使用瀏覽器打開 `http://localhost:8080/index.html` 並輸入 write-key: default 然後按下 load 按鈕

### 簡易的 Python 程式

可以透過下列 Python SDK 模擬 Clickstream 的資料並發送到 ApiGateway

```bash
# Enable your python venv, if not
source .venv/bin/activate

# Execute simulator
python3 samples/simple-backend-simulator/simulator.py \
    --host <API Gateway URL> \
    --writeKey <Your Write Key>
```

## 在 Amazon Redshift 中瀏覽 Clickstream 資料

使用 Amazon Redshift Query Editor V2 並輸入下述查詢語法

```sql
SET enable_case_sensitive_identifier TO true;

SELECT *
FROM clickstream.mv_kinesisSource
LIMIT 10
;
```

## 追蹤碼

### Client Side based

- Using [Google Tag Manager](https://segment.com/catalog/integrations/google-tag-manager/)
- [Pure Javascript](https://segment.com/docs/connections/sources/catalog/libraries/website/javascript/)
- [Android](https://segment.com/docs/connections/sources/catalog/libraries/mobile/android/)
- [iOS](https://segment.com/docs/connections/sources/catalog/libraries/mobile/ios/)

[Full List](https://segment.com/docs/connections/sources/catalog/#website)

### Server Side based

- [Java](https://segment.com/docs/connections/sources/catalog/libraries/server/java/)
- [.Net](https://segment.com/docs/connections/sources/catalog/libraries/server/net/)
- [PHP](https://segment.com/docs/connections/sources/catalog/libraries/server/php/)
- [Python](https://segment.com/docs/connections/sources/catalog/libraries/server/python/)

[Full List](https://segment.com/docs/connections/sources/catalog/#server)
