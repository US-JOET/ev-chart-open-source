UPDATE evchart_data_v3.import_metadata
   SET submission_status = 'Approved'
 WHERE submission_status = 'Submitted'
   AND org_id <> parent_org
   AND upload_friendly_id IN (
	'53','55','58','92','93','125','131','132','135','136','137','140','141',
	'142','147','148','151','152','153','154','155'
   )
   AND (upload_id, upload_friendly_id) IN (
	('4bb81364-1957-4b10-9cfe-28ec2ab8075e', '53'),
	('2d6a20bf-9ca4-4e41-91a3-c8c34828c2ca', '55'),
	('d9657cc3-ad75-4a19-b53e-eea400817392', '58'),
	('f04a4f33-68c1-41bb-9d4a-12c8908504da', '92'),
	('c4531c7c-2540-4a3c-87ff-d8146c143eb2', '93'),
	('d489339e-9f0e-4ff8-9ddd-b40db589acf3', '125'),
	('0a7874f3-31ec-41e8-a999-4b334d5fe0c1', '131'),
	('d7ac8a4c-6d59-4da3-85fd-6aee64336851', '132'),
	('492a6f12-2142-4ef5-86fd-d4958eaf80d2', '135'),
	('193ce1e1-4557-4e19-aa4b-c901f5ca2350', '136'),
	('a6701d01-97be-49f8-b7af-a138de41e1b1', '137'),
	('9a915397-656c-4935-9603-53a871b4a94e', '140'),
	('23e36910-3857-4f26-bc59-2b94087a0cca', '141'),
	('7c06fb72-5a2f-4d3f-9d9b-de97df6a678a', '142'),
	('1e6ef5bd-2971-4f85-9375-3a9b8aeedf3a', '147'),
	('c105fb03-8cef-4a9c-b271-86d8810ca3a4', '148'),
	('98d26898-b814-4045-b855-6aa00eaa29d3', '151'),
	('a9e6398b-58b2-4176-a27e-7c53ec54cbfa', '152'),
	('052dad1d-c940-4588-bb33-11aa7a5b88c0', '153'),
	('d91af1da-528f-4257-a333-40ff433a21d5', '154'),
	('711f1c34-7aa3-4d8f-919f-aedbe2e07fdf', '155')
   );
