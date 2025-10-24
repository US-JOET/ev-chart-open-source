"""
CopyRDSSnapshot

On a schedule, automatically take the system-generated daily RDS snapshot for the database and
replicate it to the dedicated DR region, maintaining a maximum of 30 days of snapshots there.
"""
import logging

from evchart_helper.boto3_manager import boto3_manager

rds_client = boto3_manager.client("rds")
rds_client_dr = boto3_manager.client("rds", region_name="us-east-2")
ssm_client = boto3_manager.client("ssm")

logger = logging.getLogger("CopyRDSSnapshot")
logger.setLevel(logging.INFO)


def copy_rds_snapshot(latest_rds_snapshot):
    rds_client_dr.copy_db_cluster_snapshot(
        KmsKeyId="alias/ev-chart/general",
        SourceDBClusterSnapshotIdentifier=latest_rds_snapshot["DBClusterSnapshotArn"],
        SourceRegion="us-east-1",
        TargetDBClusterSnapshotIdentifier=f"copy-{latest_rds_snapshot['DBClusterSnapshotIdentifier'].replace(':', '-')}" # pylint: disable=line-too-long
    )


def get_db_cluster_identifier():
    return ssm_client.get_parameter(
        Name="/ev-chart/aurora/endpoint_address"
    )["Parameter"]["Value"].split(".")[0]


def get_latest_rds_snapshot(db_cluster_identifier):
    response = rds_client.describe_db_cluster_snapshots(
        DBClusterIdentifier=db_cluster_identifier,
        SnapshotType="automated"
    )["DBClusterSnapshots"]

    response.sort(
        key=lambda snapshot_data: snapshot_data["SnapshotCreateTime"],
        reverse=True
    )

    return response[0]


def manage_copied_rds_snapshots(db_cluster_identifier):
    response = rds_client_dr.describe_db_cluster_snapshots(
        DBClusterIdentifier=db_cluster_identifier,
        SnapshotType="manual"
    )["DBClusterSnapshots"]

    response.sort(
        key=lambda snapshot_data: snapshot_data["SnapshotCreateTime"],
        reverse=True
    )

    while len(response) > 30:
        logger.debug("Deleting old DR snapshot: %s", response[-1]["DBClusterSnapshotIdentifier"])

        rds_client_dr.delete_db_cluster_snapshot(
            DBClusterSnapshotIdentifier=response[-1]["DBClusterSnapshotIdentifier"]
        )

        del response[-1]


def handler(_event, _context):
    db_cluster_identifier = get_db_cluster_identifier()
    latest_rds_snapshot = get_latest_rds_snapshot(db_cluster_identifier)

    manage_copied_rds_snapshots(db_cluster_identifier)
    copy_rds_snapshot(latest_rds_snapshot)
