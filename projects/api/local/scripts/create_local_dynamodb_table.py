import argparse

import boto3


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the local DynamoDB table.")
    parser.add_argument(
        "--endpoint-url",
        default="http://127.0.0.1:8000",
        help="DynamoDB endpoint URL (default: http://127.0.0.1:8000)",
    )
    parser.add_argument(
        "--table-name",
        default="lit-up-dev-configs",
        help="Table name (default: lit-up-dev-configs)",
    )
    args = parser.parse_args()

    session = boto3.session.Session(region_name="us-east-1")
    client = session.client("dynamodb", endpoint_url=args.endpoint_url)

    existing = client.list_tables().get("TableNames", [])
    if args.table_name in existing:
        print(f"✅ Table already exists: {args.table_name}")
        return

    client.create_table(
        TableName=args.table_name,
        AttributeDefinitions=[{"AttributeName": "version", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "version", "KeyType": "HASH"}],
        BillingMode="PAY_PER_REQUEST",
    )
    client.get_waiter("table_exists").wait(TableName=args.table_name)
    print(f"✅ Created table: {args.table_name}")


if __name__ == "__main__":
    main()
