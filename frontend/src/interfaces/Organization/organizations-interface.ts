export interface OrganizationSummary {
  name: string;
  org_friendly_id: string;
  org_id: string;
  recipient_type?: string;
}

export interface OrgNameAndIDType {
  name: string;
  org_id: string;
}

export interface NewOrgInfo {
  org_name: string;
  org_type?: string;
  first_name: string;
  last_name: string;
  email: string;
}

export interface NetworkProviderInfo {
  network_provider_uuid: string;
  network_provider_value: string;
  description: string;
}
