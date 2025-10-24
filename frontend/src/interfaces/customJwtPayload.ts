export interface CustomJwtPayload {
  account_status?: string;
  aud?: string[] | string;
  email?: string;
  exp?: number;
  family_name?: string;
  given_name?: string;
  iat?: number;
  iss?: string;
  jti?: string;
  name?: string;
  nbf?: number;
  org_friendly_id?: string;
  org_id?: string;
  org_name?: string;
  role?: string;
  scope?: string;
  sub?: string;
}
