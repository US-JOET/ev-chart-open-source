SET SQL_SAFE_UPDATES = 0;
UPDATE evchart_data_v3.import_metadata
   SET comments = "Apparent EV-CHaRT glitch reversing provided Boolean responses. Rejecting per EV-CHaRT guidance."
 WHERE upload_id IN (
  "0f8d7a7d-1b1e-4c7d-a74d-a6ccff73cffa",
  "401c44fb-2f6c-4987-a442-7b872d6643e1"
);

UPDATE evchart_data_v3.import_metadata
   SET comments = "Please submit outage duration in minutes and not seconds. Thanks."
 WHERE upload_id IN (
  "56a7c25a-40f5-48fa-8cb2-a93a495516c6"
);

UPDATE evchart_data_v3.import_metadata
   SET comments = "Rejected to permit further revisions."
 WHERE upload_id IN (
  "79812973-fe95-4df1-a64d-82190b9a42b5",
  "a174bfc5-6b81-4f81-8e90-dde45aca4c4e"
);

UPDATE evchart_data_v3.import_metadata
   SET comments = "Resubmit as discussed."
 WHERE upload_id IN (
  "2bcb1a52-15b5-4378-87a2-4d818980868b",
  "38e858c4-325e-47fa-9b6b-be4dc91da15b",
  "3ef81f75-ec6c-4fe9-b6a8-d3a4d8044d47",
  "829e64e0-0916-49d3-9bac-59bf8c9c88bd",
  "a8839de8-f29a-489c-8395-a3be65895f3c",
  "aba134e9-4678-4ea3-8907-0566efd1fa32"
);