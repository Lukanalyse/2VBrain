export type StorageStatus = {
  is_configured: boolean;
  vault_path: string | null;
  library_path: string;
  database_url: string;
  vector_store_path: string | null;
  vector_store_provider: string | null;
  validation_message: string | null;
};

export type VaultValidation = {
  is_valid: boolean;
  vault_path: string;
  message: string;
  error_code: string | null;
  received_path: string | null;
  normalized_path: string | null;
  validated_by: string;
  failed_check: string | null;
  system_error: string | null;
  is_docker_path_issue: boolean;
};
