alter table evchart_data_v3.import_metadata 
    modify column submission_status enum(
        'Processing',
        'Draft',
        'Submitted',
        'Pending',
        'Approved',
        'Rejected',
        'Error',
        'Duplicate',
        'Archived'
    );