from unittest.mock import patch

from ScheduledMetadataCleanup.index import (
    format_removed_uploads_email_table,
)
import pandas as pd


def get_upload_data_frame():
    data = {
        "upload_id": ["111", "222", "333"],
        "org_id": ["1", "2", "1"],
        "parent_org": ["3", "3", "4"],
        "quarter": ["1", "1", "2"],
        "updated_on": ["now", "then", "sometime"],
        "year": [2024, 2023, 2025],
        "module_id": [3, 4, 5]
    }
    return pd.DataFrame(data)


def get_valid_formatted_table():
    return """
<tr>
    <td>111</td>
    <td>3</td>
    <td>2024</td>
    <td>1</td>
    <td>Pennsylvania DOT</td>
    <td>now</td>
</tr>
<tr>
    <td>333</td>
    <td>5</td>
    <td>2025</td>
    <td>2</td>
    <td>Pennsylvania DOT</td>
    <td>sometime</td>
</tr>"""


def get_valid_formatted_table_two():
    return """
<tr>
    <td>222</td>
    <td>4</td>
    <td>2023</td>
    <td>1</td>
    <td>Pennsylvania DOT</td>
    <td>then</td>
</tr>"""


@patch("ScheduledMetadataCleanup.index.get_org_info_dynamo")
def test_email_table_formatting(
    mock_get_org_info_dynamo
):
    mock_get_org_info_dynamo.return_value = {"name": "Pennsylvania DOT"}
    combined_table = \
        format_removed_uploads_email_table(get_upload_data_frame())
    assert combined_table['1'] == get_valid_formatted_table()
    assert combined_table['2'] == get_valid_formatted_table_two()
