# Clickstream on AWS

## Getting started

Before starting, you must ensure you had installed [Poetry](https://python-poetry.org/docs/#installation) for Pythen dependency management and [AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html#getting_started_install) for constructing AWS environment.

### Deploying your AWS environment

1. Create a Redshift provisioned cluster or serverless workgroup
2. [Working with query editor v2](https://docs.aws.amazon.com/redshift/latest/mgmt/query-editor-v2-using.html)

    ```sql
    -- Create external schema for kinesis
    CREATE EXTERNAL SCHEMA IF NOT EXISTS kinesis
    FROM KINESIS
    IAM_ROLE default;

    -- Create schema for clickstream
    CREATE SCHEMA IF NOT EXISTS clickstream;

    -- Create clickstream user and grant required permissions
    -- Please do not change `IAMR:ClickstreamRedshiftRole`
    CREATE USER "IAMR:ClickstreamRedshiftRole" PASSWORD DISABLE;
    GRANT ALL ON SCHEMA kinesis TO "IAMR:ClickstreamRedshiftRole";
    GRANT ALL ON SCHEMA clickstream TO "IAMR:ClickstreamRedshiftRole";
    GRANT ALL ON ALL TABLES IN SCHEMA clickstream TO "IAMR:ClickstreamRedshiftRole";
    ```

3. Clone solution and install python dependencies

    ```bash
    # Clone repo
    git clone https://github.com/gavinjwl/clickstream-on-aws.git
    cd clickstream-on-aws

    # Install python dependencies 
    poetry update
    ```

4. Using CDK to deploy AWS resources.

    ```bash
    # WORKDIR: clickstream-on-aws
    cdk synth
    cdk deploy \
        --parameters WriteKey=<YOUR-WRITE-KEY> \
        --parameters RedshiftMode=serverless \
        --parameters RedshiftName=clickstream-workgroup \
        --parameters RedshiftDatabase=dev \
        --parameters KinesisSchema=kinesis \
        --parameters ClickstreamSchema=clickstream \
        --parameters ClickstreamMaterializedView=mv_kinesisSource
    ```

### Simulating user clickstream

- The easiest way to simulate is doing follow command, [for more detail](simulator.py)

    ```bash
    # Enable your python venv, if not
    source .venv/bin/activate
    
    # Execute simulator
    python3 simulator.py --host <API Gateway URL> --writeKey <Your Write Key>
    ```

- If you want to simulate more users, you can leverage [Locust](https://docs.locust.io/en/stable/).

    ```bash
    # Enable your python venv, if not
    source .venv/bin/activate

    # Start locust
    locust -f benchmark/main.py \
        --web-port 8089
    
    # Open your browser and input <API Gateway URL> and how many users you want.
    ```

## Install Tracking Code

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
