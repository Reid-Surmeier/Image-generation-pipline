export type GenerationErrorCode =
  | "REFERENCE_BYTES_MISMATCH"
  | "PAYLOAD_DESTINATION_INVALID"
  | "ADAPTER_NOT_STARTED"
  | "ADAPTER_RESULT_INVALID"
  | "PROVIDER_SUBSTITUTION"
  | "OUTPUT_COUNT_MISMATCH"
  | "PROVIDER_AMBIGUOUS"

export type ProviderDiagnostic = Readonly<{
  statusCode: number
  requestId: string | null
  reason: string | null
}>

export class GenerationError extends Error {
  readonly code: GenerationErrorCode
  readonly providerDiagnostic: ProviderDiagnostic | undefined

  constructor(code: GenerationErrorCode, message: string, providerDiagnostic?: ProviderDiagnostic) {
    super(`${code}: ${message}`)
    this.name = "GenerationError"
    this.code = code
    this.providerDiagnostic = providerDiagnostic
  }
}
